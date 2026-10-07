"""Агент числа на каркасе (ЛР-2, шаг 5: явная подписка)."""

from __future__ import annotations

from thespian.actors import ActorAddress

from agent_base import AgentBase
from message import Message, MessageType


class NumberAgent(AgentBase):
    def __init__(self):
        super().__init__()
        self.name = 'Агент числа'
        self.value = 0
        self.subscribe(MessageType.INITIALIZATION, self.handle_initialization)

    def handle_initialization(self, message: Message, sender: ActorAddress):
        print(f'Актор числа с адресом {self.myAddress} получил {message} от {sender}')
        body = message.msg_body or {}
        self.value = body.get('init_value')
        calculator_address = body.get('calculator_address')
        new_message = Message(MessageType.HELLO_WORLD, self.value)
        self.send(calculator_address, new_message)
