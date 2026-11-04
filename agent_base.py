"""Базовый агент: подписки, диспетчеризация и инициализация."""

import logging

from thespian.actors import Actor, ActorExitRequest

from message import Message, MessageType


class AgentBase(Actor):
    def __init__(self):
        self.name = type(self).__name__
        self.handlers = {}
        self.subscribe(MessageType.INIT_MESSAGE, self.handle_init_message)

    def subscribe(self, msg_type, handler):
        self.handlers[msg_type] = handler

    def receiveMessage(self, message, sender):
        if isinstance(message, ActorExitRequest):
            self.handle_delete_message()
            return
        if not isinstance(message, Message):
            return
        if hasattr(self, 'entity'):
            self.dispatcher.notified_agents.add(self.entity.uri)
        handler = self.handlers.get(message.msg_type)
        if handler is None:
            logging.warning('%s: нет обработчика %s', self.name, message.msg_type)
            return
        logging.info('%s <- %s: %s', self.name, sender, message.msg_type.value)
        try:
            handler(message, sender)
        except Exception:
            logging.exception('Ошибка обработки сообщения агентом %s', self.name)
            raise

    def handle_init_message(self, message, sender):
        self.scene = message.msg_body['scene']
        self.dispatcher = message.msg_body['dispatcher']
        self.entity = message.msg_body['entity']
        self.name += ' ' + self.entity.name

    def handle_delete_message(self):
        self.entity.is_deleting = True

    def send(self, target, message):
        self.dispatcher.message_counts[message.msg_type.value] += 1
        super().send(target, message)

    @staticmethod
    def get_decreasing_kpi_value(value, min_value, max_value):
        if max_value == min_value:
            return 1
        if value > max_value or value < min_value:
            return -1
        if abs(value - min_value) < 0.000001:
            return 1
        if abs(value - max_value) < 0.000001:
            return 0
        return 1 - (value - min_value) / (max_value - min_value)

    @staticmethod
    def get_increasing_kpi_value(value, min_value, max_value):
        if max_value == min_value:
            return 1
        if value > max_value or value < min_value:
            return -1
        if abs(value - min_value) < 0.000001:
            return 0
        if abs(value - max_value) < 0.000001:
            return 1
        return (value - min_value) / (max_value - min_value)
