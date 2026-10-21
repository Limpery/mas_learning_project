import logging

from agent_base import AgentBase
from message import Message, MessageType


class CourierAgent(AgentBase):
    def __init__(self):
        super().__init__()
        self.subscribe(MessageType.PRICE_REQUEST, self.handle_price_request)
        self.subscribe(MessageType.PLANNING_REQUEST, self.handle_planning_request)

    def handle_price_request(self, message, sender):
        order = message.msg_body
        if order.weight > self.entity.max_mass or order.volume > self.entity.max_volume:
            logging.info('%s: заказ %s исключен по массе или объему', self.name, order.number)
            variants = []
        else:
            variants = self.entity.get_variants(order)
        logging.info('%s: варианты %s', self.name,
                     [(v['time_from'], v['time_to'], v['price']) for v in variants])
        self.send(sender, Message(MessageType.PRICE_RESPONSE, variants))

    def handle_planning_request(self, message, sender):
        params = message.msg_body
        accepted = self.entity.add_order_to_schedule(
            params['order'], params['time_from'], params['time_to'], params['price'], params)
        logging.info('%s: %s, заказ %s', self.name,
                     'Принято' if accepted else 'Отказ, вариант уже невыполним', params['order'].number)
        self.send(sender, Message(MessageType.PLANNING_RESPONSE, accepted))
