"""Типизированный формат сообщений каркаса МАС (ЛР-2 + СР-2: метка времени)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MessageType(Enum):
    INITIALIZATION = 'Инициализация'
    CREATE_ACTOR = 'Создание актора'
    HELLO_WORLD = 'Приветствие'
    SET_OPERATION = 'Установка операции'
    REJECTED = 'Отказ'


@dataclass
class Message:
    """Типизированное сообщение: тип + тело + время формирования (СР-2)."""
    msg_type: MessageType
    msg_body: Any = None
    created_at: float = field(default_factory=time.time)
