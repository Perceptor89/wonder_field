import random
from ..models import Game, Question, Score, TGUser
from django.core import exceptions


def get_game_by_id(id: int) -> Game | None:
    game = Game.objects.filter(id=id)
    if game.exists():
        return game.get()


def get_user_by_tg_id(tg_id: int) -> TGUser | None:
    user = TGUser.objects.filter(tg_id=tg_id)
    if user.exists():
        return user.get()


def get_score(game_id: int, tg_id: int) -> Score | None:
    score = Score.objects.filter(game__id=game_id, player__tg_id=tg_id)
    if score.exists():
        return score.get()


def get_score_by_id(id: int) -> Score | None:
    score = Score.objects.filter(id=id)
    if score.exists():
        return score.get()


def get_active_game(chat_id: int) -> Game | None:
    game = Game.objects.filter(chat_id=chat_id, game_state__in=['R', 'G'])
    if game.exists():
        return game.get()


def create_game(chat_id: int) -> Game:
    questions_pks = Question.objects.values_list('pk', flat=True)

    if not questions_pks.exists():
        raise exceptions.EmptyResultSet('No any questions in database.')

    q_pk = random.choice(questions_pks)
    question = Question.objects.get(pk=q_pk)
    word_state = '*' * len(question.word)
    game = Game.objects.create(chat_id=chat_id, question=question,
                               word_state=word_state)
    return game


def create_user(username: str, tg_id: int, first_name: str) -> TGUser:
    return TGUser.objects.create(username=username, tg_id=tg_id,
                                 first_name=first_name)


def create_score(game: Game, player: TGUser) -> Score:
    score = Score.objects.create(game=game, player=player)
    return score
