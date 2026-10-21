import logging

from agent_base import AgentBase
from message import Message, MessageType


class OrderAgent(AgentBase):
    def __init__(self):
        super().__init__()
        self.possible_variants = []
        self.unchecked_couriers = []
        self.selected_variant = None
        self.subscribe(MessageType.PRICE_RESPONSE, self.handle_price_response)
        self.subscribe(MessageType.PLANNING_RESPONSE, self.handle_planning_response)

    def handle_init_message(self, message, sender):
        super().handle_init_message(message, sender)
        self.send_params_request()

    def send_params_request(self):
        self.possible_variants = []
        couriers = []
        for courier in self.scene.get_entities_by_type('COURIER'):
            if self.entity.order_type not in courier.types:
                logging.info('%s: курьер %s исключен по типу груза %s',
                             self.name, courier.name, self.entity.order_type)
                continue
            couriers.append(courier)
        self.unchecked_couriers = [self.dispatcher.reference_book.get_address(c) for c in couriers]
        if not self.unchecked_couriers:
            logging.info('%s: нет курьеров', self.name)
        for address in self.unchecked_couriers[:]:
            self.send(address, Message(MessageType.PRICE_REQUEST, self.entity))

    def handle_price_response(self, message, sender):
        self.possible_variants.extend(message.msg_body)
        self.unchecked_couriers.remove(sender)
        if not self.unchecked_couriers:
            self.run_planning()

    def evaluate_variants(self):
        if not self.possible_variants:
            return
        for variant in self.possible_variants:
            variant['total_efficiency'] = 0.0
        for criterion in self.dispatcher.criteria:
            values = [v[criterion['field']] for v in self.possible_variants]
            normalize = (self.get_decreasing_kpi_value if criterion['direction'] == 'decreasing'
                         else self.get_increasing_kpi_value)
            for variant in self.possible_variants:
                score = normalize(variant[criterion['field']], min(values), max(values))
                variant[criterion['name']] = score
                variant['total_efficiency'] += criterion['weight'] * score
        for variant in self.possible_variants:
            logging.info('%s: %s', self.name,
                         {**variant, 'courier': variant['courier'].name,
                          'order': variant['order'].number})

    def run_planning(self):
        if not self.possible_variants:
            logging.info('%s: подходящий вариант отсутствует', self.name)
            return
        self.evaluate_variants()
        # Стабильная сортировка сохраняет порядок предложений при равных оценках.
        self.possible_variants.sort(key=lambda v: v['total_efficiency'], reverse=True)
        self.selected_variant = self.possible_variants.pop(0)
        address = self.dispatcher.reference_book.get_address(self.selected_variant['courier'])
        self.send(address, Message(MessageType.PLANNING_REQUEST, self.selected_variant))

    def handle_planning_response(self, message, sender):
        if message.msg_body:
            self.entity.assigned_courier = self.selected_variant['courier']
            self.entity.selected_variant = self.selected_variant
        elif self.possible_variants:
            self.run_planning()
        else:
            # Все ранее предложенные варианты заняты: запрашиваем актуальные.
            self.send_params_request()
