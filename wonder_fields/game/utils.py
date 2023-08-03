import re
from .dcs import MessageUpdate, CallbackUpdate
import json


def update_to_class(update: str):
    update = json.loads(update)
    if update.get('message'):
        return MessageUpdate.Schema().load(update)
    elif update.get('callback_query'):
        return CallbackUpdate.Schema().load(update)


def get_keyboard_button(text: str):
    return {'text': text}


def get_inline_button(text: str, callback_data: str = ' ') -> dict:
    return {'text': text, 'callback_data': callback_data}


def get_reply_keyboard(buttons: list[dict], is_persistent: bool = False,
                       one_time_keyboard: bool = True,
                       resize_keyboard: bool = True) -> dict:

    keyboard = {'keyboard': [buttons]}
    keyboard['is_persistent'] = is_persistent
    keyboard['one_time_keyboard'] = one_time_keyboard
    keyboard['resize_keyboard'] = resize_keyboard

    return keyboard


def get_inline_keyboard(buttons: list[dict]) -> dict:
    keyboard = {'inline_keyboard': [buttons]}
    return keyboard


def get_remove_keyboard(selective: int = None):
    keyboard = {'remove_keyboard': True}
    if selective:
        keyboard['selective'] = selective
    return {'remove_keyboard': True}


def get_request_dict(chat_id: int, text: str = None, keyboard: dict = None,
                     parse_mode: str = 'MarkdownV2',
                     message_id: int = None, reply_to: int = None) -> dict:
    message = {
        'chat_id': chat_id,
        'parse_mode': parse_mode,
    }
    if text:
        message['text'] = text
    if keyboard:
        message['reply_markup'] = keyboard
    if message_id:
        message['message_id'] = message_id
    if reply_to:
        message['reply_to_message_id'] = reply_to

    return message


def build_mention(username: str, points: int | None = None) -> str:
    # username = hide_symbols(username)
    mention = f'@{username}'
    if points is not None:
        mention = f'{mention} [{points}]'
    return mention


def hide_symbols(text: str) -> str:
    for s in '.!|-_[]':
        text = text.replace(s, f'\\{s}')

    return text


def is_cyrillic(text: str) -> bool:
    valid = re.compile(r'[а-яА-ЯёЁ]')
    for s in text:
        if not valid.match(s):
            return False
    else:
        return True


def get_word_state(word: str, word_state: str, letter: str) -> str:
    indexes = [i for i, l in enumerate(word) if l == letter]
    word_state = [l if i not in indexes else letter for i, l in
                  enumerate(word_state)]

    return ''.join(word_state)
