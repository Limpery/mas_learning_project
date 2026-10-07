"""Агент с меняющимся поведением (СР-3: unsubscribe + отказ после 10 сообщений)."""

from __future__ import annotations

from thespian.actors import ActorAddress

from agent_base import AgentBase
from message import Message, MessageType

LIMIT = 10


class SwitchableNumberAgent(AgentBase):
    """Принимает числа, после LIMIT — отписывается и отвечает отказом."""

    def __init__(self):
        super().__init__()
        self.name = 'Переключаемый агент'
        self.value = 0
        self.counter = 0
        self.refusing = False
        self.subscribe(MessageType.INITIALIZATION, self.handle_initialization)

    def handle_initialization(self, message: Message, sender: ActorAddress):
        self.counter += 1
        if self.refusing:
            print(f'[{self.name}] Отказ: лимит {LIMIT} исчерпан, сообщение {self.counter} отклонено.')
            self.send(sender, Message(MessageType.REJECTED, {'error': 'limit exceeded'}))
            return
        body = message.msg_body or {}
        self.value = body.get('init_value')
        calculator_address = body.get('calculator_address')
        print(f'[{self.name} {self.myAddress}] принял значение {self.value} ({self.counter}/{LIMIT})')
        self.send(calculator_address, Message(MessageType.HELLO_WORLD, self.value))
        if self.counter >= LIMIT:
            # Демонстрация unsubscribe: снимаем унаследованную подписку
            # на HELLO_WORLD, а INITIALIZATION оставляем для явных отказов.
            self.unsubscribe(MessageType.HELLO_WORLD)
            self.refusing = True
            print(f'[{self.name}] Достигнут лимит {LIMIT}: отписался от HELLO_WORLD, дальше — отказы.')
