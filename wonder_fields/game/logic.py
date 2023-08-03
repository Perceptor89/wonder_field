import logging
import os
import random
from time import sleep

from celery import current_app as ca
from celery.exceptions import Terminated
from django.db import transaction
from dotenv import load_dotenv

from tg.sender import send_request
from wonder_fields.models import Game, Score

from . import db_accessor as ac
from . import dcs, utils

load_dotenv()
MSG_PAUSE = int(os.getenv('MSG_PAUSE'))
MAX_MEMBERS = int(os.getenv('MAX_MEMBERS'))
HOST_ID = int(os.getenv('HOST_ID'))
Q_TIME = int(os.getenv('Q_TIME'))


def build_send_check_pause(
        chat_id: int, method: str, text: str = None, keyboard: dict = None,
        parse_mode: str = 'MarkdownV2', message_id: int = None,
        is_check: bool = True, sleep_time: int = MSG_PAUSE,
        reply_to: int = None) -> dict:

    request = utils.get_request_dict(chat_id, text, keyboard, parse_mode,
                                     message_id, reply_to)
    result = send_request(method, request)
    if is_check:
        if not result.get('ok'):
            result['query_text'] = text
            raise Terminated(result)
    if sleep_time:
        sleep(sleep_time)

    return result


def add_context(game: Game, text: str, word: bool = False,
                description: bool = False, members: bool = False,
                turn: bool = False) -> str:
    game.refresh_from_db()
    text = utils.hide_symbols(text)

    if turn:
        turn = game.scores.all().filter(is_turn=True).get()
        username = turn.player.username
        turn_line = '__ходит {}__'.format(utils.build_mention(username))
        text = '{}\n\n{}'.format(turn_line, text)

    if word:
        word_str = '\n\n\n' + '{:^50}'.format(game.word_state) + '\n'
        word_str = word_str.replace('*', '❓')
        text = text + word_str

    if description:
        description = utils.hide_symbols(game.question.description)
        d_str = f'\n\n_{description}_'
        text = text + d_str

    if members:
        scores = game.scores.all()
        if scores.exists():
            score_strs = [utils.build_mention(s.player.username,
                          s.earned_points) for s in scores]
            score_strs = ' | '.join(score_strs)
            text = f'{text}\n\n{score_strs}'

    return text


def process_message_update(message: dcs.Message) -> dict | None:
    chat_id = message.chat.id
    message_id = message.message_id
    tg_id = message.from_.id

    if message.text in ['/start_game', '/start_game@kts_game_master_bot']:
        build_send_check_pause(chat_id, 'deleteMessage', message_id=message_id,
                               sleep_time=0)
        game = process_start(chat_id)
        if game:
            registration_message(game)
    elif message.text in ['/end_game', '/end_game@kts_game_master_bot']:
        game = ac.get_active_game(chat_id)
        if not game:
            text = 'В чате нет активной игры 🤷‍♂️'
            ca.send_task(args=[chat_id, message_id, text], name='short_reply')
        else:
            prove_end_game(game, message_id)
            build_send_check_pause(chat_id, 'deleteMessage',
                                   message_id=message_id,
                                   sleep_time=0)
    elif message.text == '/start':
        # send bot info
        pass
    else:
        game = ac.get_active_game(chat_id)
        if not game:
            return

        score_id, warning = check_is_turn(chat_id, tg_id, True)
        if warning:
            ca.send_task(args=[chat_id, message_id, warning],
                         name='short_reply')
            return

        score, warning = process_answer_text(score_id, message.text)
        if warning:
            ca.send_task(args=[chat_id, message_id, warning],
                         name='short_reply')
            return

        build_send_check_pause(chat_id, 'deleteMessage',
                               message_id=message_id,
                               sleep_time=0)

        if score:
            game.refresh_from_db()
            if not game.word_state == game.question.word:
                score = get_wheel_points(score)
                ask_answer_type(game, score)
            else:
                end_game(game, score)
        else:
            turn = get_turn(game)
            if not turn:
                end_game(game)
            else:
                turn = get_wheel_points(turn)
                ask_answer_type(game, turn)


def process_callback_update(callback: dcs.Callback) -> None:
    chat_id = callback.message.chat.id
    tg_id = callback.from_.id
    message_id = callback.message.message_id

    if callback.data == 'reg_in':
        score: Score = reg_member(callback)
        if not score:
            return
        registration_message(score.game)
        if len(score.game.scores.all()) == MAX_MEMBERS:
            end_reg(score.game)
            start_guessing(score.game)
    elif callback.data == 'end_reg':
        is_member = check_if_members(callback)
        if is_member:
            prove_end_reg(callback)
    elif callback.data == 'end_reg_yes':
        game = ac.get_active_game(chat_id)
        end_reg(game)
        start_guessing(game)
    elif callback.data == 'end_reg_no':
        game = ac.get_active_game(chat_id)
        registration_message(game)
    elif callback.data in ['letter', 'word']:
        score_id, _ = check_is_turn(chat_id, tg_id, False)
        if score_id:
            process_answer_type(score_id, callback.data)
    elif callback.data == 'end_game_yes':
        game = ac.get_active_game(chat_id)
        if game:
            end_game(game)
        else:
            text = 'Game already does not exist 👻'
            build_send_check_pause(chat_id, 'editMessageText', text,
                                   message_id=message_id)
        build_send_check_pause(chat_id, 'deleteMessage', message_id=message_id,
                               sleep_time=0)
    elif callback.data == 'end_game_no':
        build_send_check_pause(chat_id, 'deleteMessage', message_id=message_id,
                               sleep_time=0)


def process_start(chat_id: int) -> Game | None:
    game = ac.get_active_game(chat_id)

    if game:
        text = ('В чате есть активная игра. Сначала завершите ее 🔚')
        text = add_context(game, text)
        buttons = (('завершить', 'end_game_yes'),)
        buttons = [utils.get_inline_button(b[0], b[1]) for b in buttons]
        keyboard = utils.get_inline_keyboard(buttons)
        build_send_check_pause(game.chat_id, 'sendMessage', text, keyboard)
    else:
        game = ac.create_game(chat_id)

        text = 'Начинаем игру 🧩'
        request = utils.get_request_dict(chat_id, text)
        result = send_request('sendMessage', request)

        if not result.get('ok'):
            raise Terminated('Start game message failure')
        else:
            msg_id = result['result']['message_id']
            game.message_id = msg_id
            game.save()
            request = utils.get_request_dict(chat_id,
                                             message_id=game.message_id)
            send_request('pinChatMessage', request)

            return game


def registration_message(game: Game) -> None:
    game.refresh_from_db()
    text = 'Регистрируем участников 🏃‍♀️🏃🏻‍♂️'
    text = add_context(game, text, members=True)
    buttons = [('в игру', 'reg_in'), ('начать', 'end_reg')]
    buttons = [utils.get_inline_button(b[0], b[1]) for b in buttons]
    keyboard = utils.get_inline_keyboard(buttons)
    build_send_check_pause(game.chat_id, 'editMessageText', text, keyboard,
                           message_id=game.message_id, is_check=True)


def reg_member(callback: dcs.Callback) -> Score | None:
    username = callback.from_.username
    first_name = callback.from_.first_name
    chat_id = callback.message.chat.id
    tg_id = callback.from_.id
    active_game = ac.get_active_game(chat_id)
    user = ac.get_user_by_tg_id(tg_id)
    if not user:
        user = ac.create_user(username, tg_id, first_name)
    score = ac.get_score(active_game.id, tg_id)
    if score:
        logging.info(f'User {user.tg_id} is already registered')
        new_score = None
    else:
        new_score = ac.create_score(active_game, user)

    return new_score


def check_if_members(callback: dcs.Callback) -> bool:
    game = ac.get_active_game(callback.message.chat.id)
    members = game.scores.all()
    if not members:
        text = 'Для начала игры нужен хотя бы один доброволец 🦸‍♂️'
        build_send_check_pause(game.chat_id, 'editMessageText', text=text,
                               message_id=game.message_id, is_check=False)
        registration_message(game)
        return False
    else:
        return True


def prove_end_reg(callback: dcs.Callback) -> None:
    game = ac.get_active_game(callback.message.chat.id)
    text = 'Вы уверены, что хотите завершить регистрацию? 🙅🏼‍♂️'
    text = add_context(game, text, members=True)
    buttons = (('Да', 'end_reg_yes'), ('Нет', 'end_reg_no'))
    keyboard = utils.get_inline_keyboard([utils.get_inline_button(b[0], b[1])
                                         for b in buttons])
    build_send_check_pause(game.chat_id, 'editMessageText', text, keyboard,
                           message_id=game.message_id, is_check=True)


def end_reg(game: Game) -> None:
    with transaction.atomic():
        game.game_state = 'G'
        game.save()
    text = 'Регистрация завершена ✅'
    text = add_context(game, text, members=True)
    build_send_check_pause(game.chat_id, 'editMessageText', text,
                           message_id=game.message_id, is_check=True)


def start_guessing(game: Game) -> None:
    text = 'Внимание вопрос❓'
    text = add_context(game, text, description=True, members=True)
    build_send_check_pause(game.chat_id, 'editMessageText', text,
                           message_id=game.message_id, is_check=True,
                           sleep_time=Q_TIME)

    turn = get_wheel_points(get_turn(game))
    ask_answer_type(game, turn)


def get_turn(game: Game) -> Score | None:
    with transaction.atomic():
        members = game.scores.order_by('id')\
            .filter(is_active=True)\
            .select_for_update()
        if not members.exists():
            return

        last_turn = members.filter(is_turn=True)
        if last_turn.exists():
            last_turn = last_turn.get()
            last_in_queue = members.latest('id')
            if last_turn == last_in_queue:
                cur_turn = members.earliest('id')
            else:
                cur_turn = members.filter(id__gt=last_turn.id).earliest('id')

            last_turn.is_turn = False
            last_turn.save()
        else:
            cur_turn = members.earliest('id')

        cur_turn.is_turn = True
        cur_turn.save()

    return cur_turn


def get_wheel_points(score: Score) -> Score:
    score.wheel_points = random.randint(1, 10) * 100
    score.save()

    return score


def ask_answer_type(game: Game, turn: Score) -> None:
    # time limit and check active status
    text = (f'На барабане {turn.wheel_points} очков 🎲'
            ' Буква или слово?')
    text = add_context(game, text, True, True, True, True)
    buttons = (('Буква', 'letter'), ('Слово', 'word'))
    buttons = [utils.get_inline_button(b[0], b[1]) for b in buttons]
    keyboard = utils.get_inline_keyboard(buttons)
    build_send_check_pause(game.chat_id, 'editMessageText', text, keyboard,
                           message_id=game.message_id, is_check=True)


def check_is_turn(chat_id: int, tg_id: int,
                  check_type: bool) -> tuple[int | None, str | None]:
    ''' Check is user's turn. Returns score id or warning line.'''
    game = ac.get_active_game(chat_id)

    if not game:
        return

    score = Score.objects.filter(game=game, player__tg_id=tg_id)
    if not score.exists():
        return (None, 'Вы не в игре. Придется подождать новой ⏳')

    score = score.get()
    if not score.is_turn:
        # not your turn reply
        return (None, 'Пожалуйста, ждите своего хода ⏳')

    if check_type:
        if score.answer_type == 'n':
            return (None, 'Нужно выбрать тип ответа 👆')

    return (score.id, None)


def process_answer_type(score_id: int, choosed_type: str) -> None:
    # choices can be combined with buttons in constant
    choices = {
        'word': 'Ваше слово?',
        'letter': 'Ваша буква?',
    }
    with transaction.atomic():
        score = Score.objects.filter(id=score_id).select_for_update().get()
        if score.answer_type != 'n':
            return

        score.answer_type = choosed_type[0]
        score.save()
        # time limit task

    text = choices.get(choosed_type) + ' ⏰'
    text = add_context(score.game, text, True, True, True, True)
    build_send_check_pause(score.game.chat_id, 'editMessageText', text,
                           message_id=score.game.message_id, is_check=True)


def process_answer_text(score_id: int,
                        answer: str) -> tuple[Score | None, str | None]:
    '''Process answer, returns currenr score if right, else None'''
    answer = answer.strip().upper()

    with transaction.atomic():
        score = Score.objects.filter(id=score_id).select_for_update().get()
        game = score.game
        word = game.question.word
        username = score.player.username

        if score.answer_type == 'l':
            if not utils.is_cyrillic(answer) or len(answer) > 1:
                warning = 'Необходимо ввести одну русскую букву ❗️'
                return (None, warning)

            word_state: str = game.word_state
            if answer in word_state:
                warning = 'Буква уже разгадана ❗️'
                return (None, warning)

            if answer in word:
                wheel_points: int = score.wheel_points

                game.word_state = utils.get_word_state(word, word_state,
                                                       answer)
                game.save()
                text = 'Есть буква *{}*!\n{} зарабатывает {} очков 👍'.format(
                    answer, utils.build_mention(username), wheel_points
                )
                is_right = True
            else:
                text = 'Буквы *{}* нет в слове 🤷‍♂️'.format(answer)
                is_right = False
        elif score.answer_type == 'w':
            if not utils.is_cyrillic(answer) or len(answer) < 2:
                warning = 'Необходимо ввести более одной русской буквы ❗️'
                return (None, warning)

            if answer == word:
                game.word_state = word
                game.save()
                text = 'Слово *{}* разгадано 💥'.format(word)
                is_right = True
            else:
                text = 'Слово не разгадано. {} выбывает 👋'.format(
                    utils.build_mention(username),
                )
                score.is_active = False
                is_right = False

    if is_right:
        score.earned_points += score.wheel_points

    score.wheel_points = 0
    score.answer_type = 'n'
    score.save()

    text = add_context(game, text, members=True, turn=True)
    build_send_check_pause(game.chat_id, 'editMessageText', text,
                           message_id=game.message_id)

    return (score, None) if is_right else (None, None)


def end_game(game: Game, w_score: Score = None) -> None:
    game.game_state = 'F'
    game.save()

    if w_score:
        text = 'Поздравляем {} c победой 🥇'.format(
            utils.build_mention(w_score.player.username),
        )
        text = add_context(game, text)
        build_send_check_pause(game.chat_id, 'editMessageText',
                               text, message_id=game.message_id)

    title = f'<u>Итоги игры: {game.id}</u>'
    c_w = 15
    table = []
    table.append('|{:^{count}}|{:^{count}}|'
                 .format('Участник', 'Очки', count=c_w))
    table.append('|{}|{}|'.format('-' * c_w, '-' * c_w))
    for s in game.scores.order_by('-earned_points').all():
        table.append('|{:^{count}}|{:^{count}}|'
                     .format(s.player.username, s.earned_points, count=c_w))
    table = "\n".join(table)
    last_word = 'Благодарим всех участников 😎'
    text = f'{title}\n\n<pre>{table}</pre>\n\n{last_word}'

    build_send_check_pause(game.chat_id, 'editMessageText', parse_mode='HTML',
                           text=text, message_id=game.message_id)

    request = utils.get_request_dict(game.chat_id, message_id=game.message_id)
    send_request('unpinChatMessage', request)


def prove_end_game(game: Game, reply_to: int) -> None:
    print(f'reply_to: {reply_to}')
    text = 'Вы уверены, что хотите завершить активную игру? 🙅🏼‍♂️'
    text = add_context(game, text)
    buttons = (('Да', 'end_game_yes'), ('Нет', 'end_game_no'))
    keyboard = utils.get_inline_keyboard([utils.get_inline_button(b[0], b[1])
                                         for b in buttons])
    build_send_check_pause(game.chat_id, 'sendMessage', text, keyboard,
                           is_check=True, reply_to=reply_to)


def short_reply(chat_id: int, reply_to: int, text: str) -> None:
    '''
        Build and send reply, delete reply after pause,
        delete original message
    '''
    result = build_send_check_pause(chat_id, 'sendMessage', text,
                                    reply_to=reply_to)

    message_id = result['result']['message_id']
    build_send_check_pause(chat_id, 'deleteMessage', message_id=message_id,
                           sleep_time=0)

    build_send_check_pause(chat_id, 'deleteMessage', message_id=reply_to,
                           sleep_time=0)
