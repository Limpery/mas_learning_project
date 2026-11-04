"""Сообщения протокола планирования ЛР6."""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class MessageType(Enum):
    NEW_COURIER = 'Новый курьер'
    DELETED_COURIER = 'Курьер удален'
    RELEASE_ORDER = 'Освободить записи заказа'
    PARAMETERS_CHANGED = 'Параметры изменены'
    START_PLANNING = 'Начать переговоры'
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
