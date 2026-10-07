import time
import operator
from thespian.actors import ActorSystem, Actor



class SimplestActor(Actor):
    """Простой актор, который в будущем станет агентом."""

    def __init__(self):
        super().__init__()
        print('Создан новый актор')
        self.messages = []
        self.child_addresses = []

    def receiveMessage(self, msg, sender):
        print(f'Актор с адресом {self.myAddress} получил {msg} от {sender}')
        self.messages.append(msg)
        for message in self.messages:
            print(f'Актор с адресом {self.myAddress} ранее получал сообщение {message}')
        # Ретрансляция ДО обработки CREATE_ACTOR (по методичке),
        # чтобы дочерний не получил саму команду создания.
        for child in self.child_addresses:
            print(f'Ретранслируем сообщение дочернему актору с адресом {child}')
            self.send(child, msg)
        if msg == 'CREATE_ACTOR':
            child_actor_address = self.createActor(SimplestActor)
            print(f'Создали нового актора, его адрес - {child_actor_address}')
            self.child_addresses.append(child_actor_address)


def test_simplest_actor():
    print("\n" + "=" * 60)
    print("ТЕСТ 1: SimplestActor (шаги 1-4)")
    print("=" * 60)
    actorSystem = ActorSystem()

    actorAddress1 = actorSystem.createActor(SimplestActor)
    time.sleep(0.5)

    # Шаг 2: сообщения произвольного типа
    actorSystem.tell(actorAddress1, "Первое сообщение")
    time.sleep(0.3)
    actorSystem.tell(actorAddress1, 132)
    time.sleep(0.3)
    actorSystem.tell(actorAddress1, [1, 3, 5])
    time.sleep(0.3)
    actorSystem.tell(actorAddress1, {'key': 'value'})
    time.sleep(0.5)

    # Шаг 4: порождение + ретрансляция
    actorSystem.tell(actorAddress1, 'CREATE_ACTOR')
    time.sleep(0.5)
    actorSystem.tell(actorAddress1, 'RETRANSLATED MESSAGE')
    time.sleep(1.0)

    actorSystem.shutdown()





class NumberActorForSum(Actor):
    def __init__(self):
        super().__init__()
        self.value = 0

    def receiveMessage(self, msg, sender):
        print(f'Актор числа с адресом {self.myAddress} получил {msg} от {sender}')
        if not isinstance(msg, dict):
            print(f'  Ожидался dict, игнорирую: {msg}')
            return
        self.value = msg.get('init_value')
        calculator_address = msg.get('calculator_address')
        self.send(calculator_address, self.value)


class CalculatorActorForSum(Actor):
    def __init__(self):
        super().__init__()
        self.values = []

    def receiveMessage(self, msg, sender):
        self.values.append(msg)
        total_sum = sum(self.values)
        print(f'Актор-калькулятор с адресом {self.myAddress} получил {msg} от {sender}, '
              f'итоговая сумма: {total_sum}')


def test_sum_actors():
    print("\n" + "=" * 60)
    print("ТЕСТ 2: Сумма чисел (NumberActor + CalculatorActor)")
    print("=" * 60)
    actorSystem = ActorSystem()

    calculator_address = actorSystem.createActor(CalculatorActorForSum)
    time.sleep(0.3)
    # Три ОТДЕЛЬНЫХ актора-числа, как на диаграмме последовательности
    number_1 = actorSystem.createActor(NumberActorForSum)
    number_2 = actorSystem.createActor(NumberActorForSum)
    number_3 = actorSystem.createActor(NumberActorForSum)
    time.sleep(0.5)

    actorSystem.tell(number_1, {'init_value': 1, 'calculator_address': calculator_address})
    time.sleep(0.5)
    actorSystem.tell(number_2, {'init_value': 2, 'calculator_address': calculator_address})
    time.sleep(0.5)
    actorSystem.tell(number_3, {'init_value': 3, 'calculator_address': calculator_address})
    time.sleep(1.5)  # дать калькулятору обработать до shutdown

    actorSystem.shutdown()





OPERATIONS = {
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '/': operator.truediv,
}


class NumberActor(Actor):
    """Актор-число: хранит значение и пересылает его в калькулятор."""

    def __init__(self):
        super().__init__()
        self.value = None

    def receiveMessage(self, msg, sender):
        if not isinstance(msg, dict) or 'value' not in msg:
            print(f'[NumberActor {self.myAddress}] получил странное сообщение: {msg}, игнорирую')
            return

        self.value = msg['value']
        calculator_address = msg['calculator_address']
        print(f'[NumberActor {self.myAddress}] получил значение {self.value}, '
              f'пересылаю в калькулятор {calculator_address}')
        self.send(calculator_address, {'value': self.value})


class CalculatorActor(Actor):
    """Актор-калькулятор: накапливает числа и оператор, затем вычисляет."""

    def __init__(self):
        super().__init__()
        self.numbers = []
        self.operator = None

    def receiveMessage(self, msg, sender):
        if not isinstance(msg, dict):
            print(f'[CalculatorActor {self.myAddress}] получил не-словарь: {msg}, игнорирую')
            return

        print(f'[CalculatorActor {self.myAddress}] получил сообщение: {msg}')

        if 'value' in msg:
            self.numbers.append(msg['value'])
        elif 'operator' in msg:
            self.operator = msg['operator']
        else:
            print('  Неизвестный тип сообщения, игнорирую.')
            return

        if self.operator is not None and len(self.numbers) >= 2:
            a = self.numbers[-2]
            b = self.numbers[-1]
            op = self.operator

            if op in OPERATIONS:
                if op == '/' and b == 0:
                    result = 'Ошибка: деление на ноль'
                else:
                    result = OPERATIONS[op](a, b)
            else:
                result = f'Неизвестная операция: {op}'

            print(f'Выражение: {a} {op} {b} = {result}')
            self.numbers = []
            self.operator = None


def test_calculator():
    print("\n" + "=" * 60)
    print("ТЕСТ 3: Калькулятор (+, -, *, /)")
    print("=" * 60)
    actorSystem = ActorSystem('simpleSystemBase')

    calculator = actorSystem.createActor(CalculatorActor)
    number_agent_1 = actorSystem.createActor(NumberActor)
    number_agent_2 = actorSystem.createActor(NumberActor)
    time.sleep(0.5)

    print('\n--- Тест 1: 2 * 5 ---')
    actorSystem.tell(number_agent_1, {'value': 2, 'calculator_address': calculator})
    actorSystem.tell(number_agent_2, {'value': 5, 'calculator_address': calculator})
    actorSystem.tell(calculator, {'operator': '*'})
    time.sleep(1)

    print('\n--- Тест 2: 10 + 7 ---')
    actorSystem.tell(calculator, {'operator': '+'})
    actorSystem.tell(number_agent_1, {'value': 10, 'calculator_address': calculator})
    actorSystem.tell(number_agent_2, {'value': 7, 'calculator_address': calculator})
    time.sleep(1)

    print('\n--- Тест 3: 20 - 8 ---')
    actorSystem.tell(number_agent_1, {'value': 20, 'calculator_address': calculator})
    actorSystem.tell(calculator, {'operator': '-'})
    actorSystem.tell(number_agent_2, {'value': 8, 'calculator_address': calculator})
    time.sleep(1)

    print('\n--- Тест 4: 15 / 3 ---')
    actorSystem.tell(number_agent_1, {'value': 15, 'calculator_address': calculator})
    actorSystem.tell(number_agent_2, {'value': 3, 'calculator_address': calculator})
    actorSystem.tell(calculator, {'operator': '/'})
    time.sleep(1)

    actorSystem.shutdown()





class TimerActor(Actor):
    """Простой актор-таймер со счётчиком."""

    def __init__(self):
        super().__init__()
        print('Создан новый таймер актор')
        self.counter = 0

    def receiveMessage(self, msg, sender):
        self.counter += 1
        print(f'Таймер актор {self.myAddress} получил "{msg}", счётчик = {self.counter}')
        self.send(sender, self.counter)


def test_timer_actor():
    print("\n" + "=" * 60)
    print("ТЕСТ 4: TimerActor (ask)")
    print("=" * 60)
    actorSystem = ActorSystem()

    timerAddress1 = actorSystem.createActor(TimerActor)
    timerAddress2 = actorSystem.createActor(TimerActor)
    time.sleep(0.5)

    for i in range(1, 4):
        resp = actorSystem.ask(timerAddress1, f'привет {i}')
        print(f'   Ответ от timerAddress1: {resp}')

    for i in range(1, 3):
        resp = actorSystem.ask(timerAddress2, f'здравствуй {i}')
        print(f'   Ответ от timerAddress2: {resp}')

    resp = actorSystem.ask(timerAddress1, 'привет 4', timeout=1)
    print(f'   Ответ от timerAddress1 (привет 4): {resp}')

    actorSystem.shutdown()





class ChainActor(Actor):
    """Актор в цепочке: передаёт сообщение следующему, последний возвращает результат."""

    def __init__(self):
        super().__init__()
        self.next_actor = None
        self.is_last = False
        self.is_first = False
        self.first_actor = None

    def receiveMessage(self, msg, sender):
        if not isinstance(msg, dict) and not isinstance(msg, str):
            return

        if isinstance(msg, dict) and 'next' in msg:
            self.next_actor = msg['next']
            self.is_last = msg.get('is_last', False)
            self.is_first = msg.get('is_first', False)
            self.first_actor = msg.get('first_actor')
            return

        if self.is_first and isinstance(msg, dict) and 'result' in msg:
            elapsed = time.perf_counter() - self.start_time
            print(f'Результат: {msg["result"]}, переходов: {msg["hops"]}, '
                  f'время: {elapsed * 1000:.2f} мс')
            return

        if msg == 'start':
            self.start_time = time.perf_counter()
            self.send(self.next_actor, {'data': 'Hello', 'hops': 1})
            return

        if not self.is_last:
            self.send(self.next_actor, {'data': msg['data'], 'hops': msg['hops'] + 1})
            return

        if self.is_last:
            self.send(self.first_actor, {'result': msg['data'], 'hops': msg['hops'] + 1})
            return


def test_chain_actor():
    print("\n" + "=" * 60)
    print("ТЕСТ 5: ChainActor (цепочка из 5 акторов)")
    print("=" * 60)
    actorSystem = ActorSystem('simpleSystemBase')

    actors = [actorSystem.createActor(ChainActor) for _ in range(5)]
    time.sleep(0.5)

    for i in range(5):
        next_idx = (i + 1) % 5
        actorSystem.tell(actors[i], {
            'next': actors[next_idx],
            'is_last': i == 4,
            'is_first': i == 0,
            'first_actor': actors[0]
        })
    time.sleep(1.0)  # дождаться конфигурации до 'start'

    actorSystem.tell(actors[0], 'start')
    time.sleep(1.5)

    actorSystem.shutdown()


def main():
    print("Запуск всех тестов акторов Thespian (main2)...")

    test_simplest_actor()
    test_sum_actors()
    test_calculator()
    test_timer_actor()
    test_chain_actor()

    print("\n" + "=" * 60)
    print("Все тесты завершены!")
    print("=" * 60)


if __name__ == '__main__':
    main()
