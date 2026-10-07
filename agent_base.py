"""Базовый класс агента каркаса МАС (ЛР-2 + СР-2/СР-3)."""

from __future__ import annotations

import logging
import time
import traceback
from abc import ABC
from typing import Any, Callable, Dict

from thespian.actors import Actor, ActorAddress

from message import Message, MessageType

logging.basicConfig(level=logging.WARNING, format='[%(levelname)s] %(message)s')


class AgentBase(ABC, Actor):
    """Базовая реализация агента: подписки + диспетчеризация."""

    def __init__(self):
        # NB: у Thespian Actor нет __init__ с обязательными аргументами,
        # super().__init__() не вызываем намеренно (как в методичке).
        self.name = 'Базовый агент'
        self.handlers: Dict[MessageType, Callable[[Message, ActorAddress], None]] = {}
        self.subscribe(MessageType.HELLO_WORLD, self.handle_hello_world)

    # --- Подписка (шаг 3) + отписка (СР-3) ---
    def subscribe(self, msg_type: MessageType, handler: Callable[[Message, ActorAddress], None]):
        """Подписка на события определённого типа."""
        if msg_type in self.handlers:
            logging.warning('Повторная подписка на сообщение: %s', msg_type)
        self.handlers[msg_type] = handler

    def unsubscribe(self, msg_type: MessageType):
        """Отписка от событий типа (СР-3: смена поведения на ходу)."""
        if msg_type in self.handlers:
            del self.handlers[msg_type]
        else:
            logging.warning('%s: нет подписки для отписки: %s', self.name, msg_type)

    # --- Диспетчеризация (шаг 4) ---
    def receiveMessage(self, msg, sender):  # noqa: N802 (имя требует Thespian)
        """Только поиск обработчика по типу + перехват исключений."""
        logging.debug('%s получил сообщение: %s', self.name, msg)

        if not isinstance(msg, Message):
            logging.warning('%s: нетипизированное сообщение %r игнорирую', self.name, msg)
            return

        # СР-2: задержка между отправкой и обработкой
        try:
            delay_ms = (time.time() - float(msg.created_at)) * 1000.0
        except (TypeError, ValueError):
            delay_ms = float('nan')
        print(f'[{self.name} {self.myAddress}] {msg.msg_type.value}, задержка: {delay_ms:.2f} мс')

        handler = self.handlers.get(msg.msg_type)
        if handler is None:
            logging.warning('%s: отсутствует подписка на сообщение: %s', self.name, msg.msg_type)
            print(f'[{self.name}] Нет подписки на {msg.msg_type}, продолжаю работать.')
            return
        try:
            handler(msg, sender)
        except Exception as ex:  # падение обработчика не должно убивать агента
            traceback.print_exc()
            logging.error(ex)

    def handle_hello_world(self, message: Message, sender: ActorAddress):
        print('Hello, world')
