import logging
import math

from agent_base import AgentBase
from message import Message, MessageType


class CourierAgent(AgentBase):
    def __init__(self):
        super().__init__()
        self.subscribe(MessageType.RELEASE_ORDER, self.handle_release_order)
        self.subscribe(MessageType.PARAMETERS_CHANGED, self.handle_parameters_changed)
        self.subscribe(MessageType.PRICE_REQUEST, self.handle_price_request)
        self.subscribe(MessageType.PLANNING_REQUEST, self.handle_planning_request)

    def handle_price_request(self, message, sender):
        self.dispatcher.negotiating_couriers.add(self.entity.uri)
        body = message.msg_body
        context = body.get('context')
        schedule = context.schedules[self.entity] if context else self.entity.schedule
        variants = self.entity.get_variants(body['order'], schedule,
                                            self.dispatcher.enable_conflicts,
                                            self.dispatcher.multiple,
                                            body.get('ancestors', ()))
        self.send(sender, Message(MessageType.PRICE_RESPONSE, variants))

    def add_order(self, params, context):
        schedule = context.schedules[self.entity]
        # Сохраняем весь черновик, включая записи других курьеров.
        old_state = context.snapshot()
        variants = self.entity.get_variants(params['order'], schedule,
                                            self.dispatcher.enable_conflicts,
                                            self.dispatcher.multiple)
        current = next((v for v in variants if v['variant_name'] == params['variant_name']
                        and v['removed_orders'] == params['removed_orders']
                        and v['point_from'] == params['point_from']
                        and all(math.isclose(v[k], params[k], abs_tol=1e-9)
                                for k in ('time_from', 'time_to', 'price'))), None)
        if current is None:
            return False
        result = self.entity.preview(params, schedule)
        if result is None:
            context.restore(old_state)
            return False
        context.schedules[self.entity] = result
        context.placements[params['order']] = params
        for victim in params['removed_orders']:
            context.evicted.append((victim, self.entity))
        logging.info('%s: размещен %s для заказа %s; вытеснение %s', self.name,
                     params['variant_name'], params['order'].number,
                     [o.number for o in params['removed_orders']])
        return True

    def handle_planning_request(self, message, sender):
        self.dispatcher.negotiating_couriers.add(self.entity.uri)
        body = message.msg_body
        accepted = self.add_order(body['variant'], body['context'])
        self.send(sender, Message(MessageType.PLANNING_RESPONSE, accepted))

    def notify_available(self):
        for order in self.scene.get_entities_by_type('ORDER'):
            if order.order_type in self.entity.types and order.assigned_courier is None:
                self.send(self.dispatcher.reference_book.get_address(order),
                          Message(MessageType.NEW_COURIER, self.entity))

    def handle_init_message(self, message, sender):
        super().handle_init_message(message, sender)
        for order in self.scene.get_entities_by_type('ORDER'):
            if order.order_type in self.entity.types:
                self.send(self.dispatcher.reference_book.get_address(order),
                          Message(MessageType.NEW_COURIER, self.entity))

    def notify_removed_orders(self, orders):
        for order in orders:
            if not order.is_deleting:
                self.send(self.dispatcher.reference_book.get_address(order),
                          Message(MessageType.REMOVE_ORDER, {'courier': self.entity, 'relocated': False}))

    def handle_release_order(self, message, sender):
        self.dispatcher.maintenance_couriers.add(self.entity.uri)
        order = message.msg_body['order']
        affected = self.entity.release_order(order)
        if message.msg_body['replan']:
            affected.insert(0, order)
        self.notify_removed_orders(affected)
        self.notify_available()

    def handle_parameters_changed(self, message, sender):
        orders = list(dict.fromkeys(r.order for r in self.entity.schedule))
        if orders:
            self.dispatcher.maintenance_couriers.add(self.entity.uri)
        self.entity.schedule.clear()
        self.notify_removed_orders(orders)
        self.notify_available()

    def handle_delete_message(self):
        super().handle_delete_message()
        if self.dispatcher.closing:
            return
        if self.entity.schedule:
            self.dispatcher.maintenance_couriers.add(self.entity.uri)
        self.entity.schedule.clear()
        for order in self.scene.get_entities_by_type('ORDER'):
            self.send(self.dispatcher.reference_book.get_address(order),
                      Message(MessageType.DELETED_COURIER, self.entity))
