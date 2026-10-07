"""ЛР-2. Каркас МАС: точка входа.

База (шаг 5): CalculatorAgent + 2x NumberAgent (1 и 3, итог 4).
СР-1: SET_OPERATION (арифметика) + сообщение без подписки (warning).
СР-3: SwitchableNumberAgent — после 10 сообщений отказы (unsubscribe).

Вывод: редирект stdout в output_lab2.txt (UTF-8), запись изнутри
акторов не используется (дочерние процессы Thespian).
"""

import time

from thespian.actors import ActorSystem

from calculator_agent import CalculatorAgent
from message import Message, MessageType
from number_agent import NumberAgent
from switchable_agent import SwitchableNumberAgent


def demo_base(actorSystem):
    print("\n" + "=" * 60)
    print("ДЕМО 1 (база): калькулятор на каркасе, 1 + 3 = 4")
    print("=" * 60)
    calculator_address = actorSystem.createActor(CalculatorAgent)
    time.sleep(0.3)
    number_1 = actorSystem.createActor(NumberAgent)
    number_2 = actorSystem.createActor(NumberAgent)
    time.sleep(0.5)

    actorSystem.tell(number_1, Message(
        MessageType.INITIALIZATION,
        {'init_value': 1, 'calculator_address': calculator_address}))
    time.sleep(0.5)
    actorSystem.tell(number_2, Message(
        MessageType.INITIALIZATION,
        {'init_value': 3, 'calculator_address': calculator_address}))
    time.sleep(1.5)


def demo_operations(actorSystem):
    print("\n" + "=" * 60)
    print("ДЕМО 2 (СР-1): SET_OPERATION + сообщение без подписки")
    print("=" * 60)
    calculator_address = actorSystem.createActor(CalculatorAgent)
    time.sleep(0.3)
    number_1 = actorSystem.createActor(NumberAgent)
    number_2 = actorSystem.createActor(NumberAgent)
    time.sleep(0.5)

    actorSystem.tell(number_1, Message(
        MessageType.INITIALIZATION,
        {'init_value': 10, 'calculator_address': calculator_address}))
    actorSystem.tell(number_2, Message(
        MessageType.INITIALIZATION,
        {'init_value': 7, 'calculator_address': calculator_address}))
    time.sleep(0.8)
    actorSystem.tell(calculator_address, Message(MessageType.SET_OPERATION, '+'))
    time.sleep(1.0)

    # Сообщение без подписки: агент пишет warning и продолжает работать
    print('--- Шлём калькулятору INITIALIZATION (подписки нет) ---')
    actorSystem.tell(calculator_address, Message(MessageType.INITIALIZATION, {'ping': 1}))
    time.sleep(0.8)


def demo_switchable(actorSystem):
    print("\n" + "=" * 60)
    print("ДЕМО 3 (СР-3): unsubscribe + отказ после 10 сообщений")
    print("=" * 60)
    calculator_address = actorSystem.createActor(CalculatorAgent)
    time.sleep(0.3)
    switchable = actorSystem.createActor(SwitchableNumberAgent)
    time.sleep(0.5)

    for i in range(1, 13):
        actorSystem.tell(switchable, Message(
            MessageType.INITIALIZATION,
            {'init_value': i, 'calculator_address': calculator_address}))
        time.sleep(0.25)
    time.sleep(1.5)


def main():
    print("ЛР-2: каркас МАС (типизированные сообщения, подписки)...")
    actorSystem = ActorSystem()
    try:
        demo_base(actorSystem)
        demo_operations(actorSystem)
        demo_switchable(actorSystem)
    finally:
        actorSystem.shutdown()
    print("\n" + "=" * 60)
    print("Все демо завершены!")
    print("=" * 60)


if __name__ == '__main__':
    main()
