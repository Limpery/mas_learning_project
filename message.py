"""Сообщения протокола планирования ЛР5."""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class MessageType(Enum):
    REMOVE_ORDER = 'Удаление заказа'
    CONSENT_REQUEST = 'Запрос согласия'
    CONSENT_RESPONSE = 'Ответ о согласии'
    INIT_MESSAGE = 'Инициализация'
    PRICE_REQUEST = 'Запрос параметров'
    PRICE_RESPONSE = 'Ответ с параметрами'
    PLANNING_REQUEST = 'Запрос планирования'
    PLANNING_RESPONSE = 'Результат планирования'


@dataclass
class Message:
    msg_type: MessageType
    msg_body: Any = None
