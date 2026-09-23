from thespian.actors import *
 
class SimplestActor(Actor):
    """Простой актор, который в будущем станет агентом"""
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
        for child in self.child_addresses:
            print(f'Ретранслируем сообщение дочернему актору с адресом {child}')
            self.send(child, msg)
        if msg == 'CREATE_ACTOR':
            child_actor_address = self.createActor(SimplestActor)
            print(f'Создали нового актора, его адрес - {child_actor_address}')
            self.child_addresses.append(child_actor_address)





# class NumberActor(Actor):
#     def __init__(self):
#         super().__init__()
#         self.value = 0
 
#     def receiveMessage(self, msg, sender):
#         print(f'Актор числа с адресом {self.myAddress} получил {msg} от {sender}')
#         # Ожидаем словарь со значением числа и адресом актора-калькулятора
#         self.value = msg.get('init_value')
#         calculator_address = msg.get('calculator_address')
#         self.send(calculator_address, self.value)
 
# class CalculatorActor(Actor):
#     def __init__(self):
#         super().__init__()
#         self.values = []
 
#     def receiveMessage(self, msg, sender):
#         self.values.append(msg)
#         total_sum = sum(self.values)
#         print(f'Актор-калькулятор с адресом {self.myAddress} получил {msg} от {sender}, '
#               f'итоговая сумма: {total_sum}')


# Самостоятельная работа

class NumberActor(Actor):
    def __init__(self):
        super().__init__()
        self.value = 0
 
    def receiveMessage(self, msg, sender):
        print(f'Актор числа с адресом {self.myAddress} получил {msg} от {sender}')
        # Ожидаем словарь со значением числа и адресом актора-калькулятора
        self.value = msg.get('init_value')
        calculator_address = msg.get('calculator_address')
        operator = msg.get('operator')
        self.send(calculator_address, self.value)
 
class CalculatorActor(Actor):
    def __init__(self):
        super().__init__()
        self.values = []
 
    def receiveMessage(self, msg, sender):
        self.values.append(msg)
        operator = '+'
        if len(self.values) < 2:
            result = sum(self.values)
        else:
            result = eval(f"{self.values[-2]} {operator} {self.values[-1]}")
        print(f'Актор-калькулятор с адресом {self.myAddress} получил {msg} от {sender}, '
              f'результат выражения: {result}')



if __name__ == "__main__":
    # Создаем систему акторов, внутри которой они будут жить
    actorSystem = ActorSystem()
    # Создаем экземпляр созданного нами класса и сохраняем его адрес
    actorAddress1 = actorSystem.createActor(SimplestActor)
    # Отправляем по сохраненному адресу сообщение
    # actorSystem.tell(actorAddress1, "Первое сообщение")
    # actorSystem.tell(actorAddress1, 132)
    # actorSystem.tell(actorAddress1, [1, 3, 5])
    # actorSystem.tell(actorAddress1, {'key': 'value'})
    
    
    # actorSystem.tell(actorAddress1, 'CREATE_ACTOR')
    # actorSystem.tell(actorAddress1, 'RETRANSLATED MESSAGE')
    
    # calculator_address = actorSystem.createActor(CalculatorActor)
    # number_agent_1 = actorSystem.createActor(NumberActor)
    # init_message_1 = {'init_value': 1, 'calculator_address': calculator_address}
    # actorSystem.tell(number_agent_1, init_message_1)
    
    
    # init_message_2 = {'init_value': 2, 'calculator_address': calculator_address}
    # actorSystem.tell(number_agent_1, init_message_2)
    # init_message_3 = {'init_value': 3, 'calculator_address': calculator_address}
    # actorSystem.tell(number_agent_1, init_message_3)
    
    
    calculator_address = actorSystem.createActor(CalculatorActor)
    number_agent_1 = actorSystem.createActor(NumberActor)
    init_message_1 = {'init_value': 1, 'calculator_address': calculator_address, 'operator': '+'}
    actorSystem.tell(number_agent_1, init_message_1)
    init_message_2 = {'init_value': 5, 'calculator_address': calculator_address, 'operator': '*'}
    actorSystem.tell(number_agent_1, init_message_1)
