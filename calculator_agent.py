"""Агент-калькулятор на каркасе (ЛР-2, шаг 5 + СР-1: SET_OPERATION).

Второй способ задания поведения: переопределение handle_hello_world
базового класса (явной подписки нет — она уже сделана в AgentBase).
Плюс подписка на SET_OPERATION для арифметики.
"""

from __future__ import annotations

import operator

from thespian.actors import ActorAddress

from agent_base import AgentBase
from message import Message, MessageType

OPERATIONS = {
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '/': operator.truediv,
}


class CalculatorAgent(AgentBase):
    def __init__(self):
        super().__init__()
        self.name = 'Агент-калькулятор'
        self.values = []
        self.pending_values = []
        self.operation = None
        self.subscribe(MessageType.SET_OPERATION, self.handle_set_operation)

    # Переопределённый обработчик базового класса (способ №2)
    def handle_hello_world(self, message: Message, sender: ActorAddress):
        new_value = message.msg_body
        self.values.append(new_value)
        self.pending_values.append(new_value)
        total_sum = sum(self.values)
        print(f'Актор-калькулятор с адресом {self.myAddress} получил {message} '
              f'от {sender}, итоговая сумма: {total_sum}')
        self._try_compute()

    def handle_set_operation(self, message: Message, sender: ActorAddress):
        self.operation = message.msg_body
        print(f'[Калькулятор] Установлена операция: {self.operation}')
        self._try_compute()

    def _try_compute(self):
        if self.operation is not None and len(self.pending_values) >= 2:
            a, b = self.pending_values[-2], self.pending_values[-1]
            op = self.operation
            if op in OPERATIONS:
                if op == '/' and b == 0:
                    result = 'Ошибка: деление на ноль'
                else:
                    result = OPERATIONS[op](a, b)
            else:
                result = f'Неизвестная операция: {op}'
            print(f'Выражение: {a} {op} {b} = {result}')
            self.pending_values = []
            self.operation = None
