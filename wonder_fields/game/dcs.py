from dataclasses import field
from typing import ClassVar, Type, Optional

from marshmallow_dataclass import dataclass
from marshmallow import Schema, EXCLUDE


@dataclass
class MessageFrom:
    id: int
    is_bot: bool
    first_name: str
    username: str
    last_name: Optional[str]

    class Meta:
        unknown = EXCLUDE


@dataclass
class Chat:
    id: int
    type: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    title: Optional[str] = None

    class Meta:
        unknown = EXCLUDE


@dataclass
class Message:
    message_id: int
    from_: MessageFrom = field(metadata={"data_key": "from"})
    chat: Chat
    text: Optional[str] = None

    class Meta:
        unknown = EXCLUDE


@dataclass
class MessageUpdate:
    update_id: int
    message: Message

    Schema: ClassVar[Type[Schema]] = Schema

    class Meta:
        unknown = EXCLUDE


@dataclass
class CallbackFrom:
    id: int
    is_bot: bool
    username: str
    first_name: Optional[str] = ''
    language_code: Optional[str] = None

    class Meta:
        unknown = EXCLUDE


@dataclass
class Callback:
    id: str
    from_: CallbackFrom = field(metadata={"data_key": "from"})
    message: Message
    data: str
    chat_instance: Optional[str] = None

    class Meta:
        unknown = EXCLUDE


@dataclass
class CallbackUpdate:
    update_id: int
    callback_query: Callback

    Schema: ClassVar[Type[Schema]] = Schema

    class Meta:
        unknown = EXCLUDE
