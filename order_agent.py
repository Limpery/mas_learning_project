import logging

from agent_base import AgentBase
from message import Message, MessageType
from transaction import PlanningTransaction


class OrderAgent(AgentBase):
    def __init__(self):
        super().__init__()
        self.possible_variants = []
        self.unchecked_couriers = []
        self.selected_variant = None
        self.context = None
        self.parent = None
        self.ancestors = ()
        self.pending_victims = []
        self.subscribe(MessageType.NEW_COURIER, self.handle_new_resource_message)
        self.subscribe(MessageType.DELETED_COURIER, self.handle_delete_courier_message)
        self.subscribe(MessageType.PARAMETERS_CHANGED, self.handle_parameters_changed)
        self.subscribe(MessageType.START_PLANNING, self.handle_start_planning)
        self.subscribe(MessageType.PRICE_RESPONSE, self.handle_price_response)
        self.subscribe(MessageType.PLANNING_RESPONSE, self.handle_planning_response)
        self.subscribe(MessageType.REMOVE_ORDER, self.handle_remove_message)
        self.subscribe(MessageType.CONSENT_REQUEST, self.handle_consent_request)
        self.subscribe(MessageType.CONSENT_RESPONSE, self.handle_consent_response)

    def handle_init_message(self, message, sender):
        super().handle_init_message(message, sender)
        self.restart_planning()

    def send_params_request(self):
        self.dispatcher.negotiating_orders.add(self.entity.uri)
        self.possible_variants = []
        couriers = [c for c in self.scene.get_entities_by_type('COURIER')
                    if self.entity.order_type in c.types]
        self.unchecked_couriers = [self.dispatcher.reference_book.get_address(c) for c in couriers]
        logging.info('%s: новый опрос, глубина переговоров %s', self.name, len(self.ancestors))
        self.dispatcher.max_depth = max(self.dispatcher.max_depth, len(self.ancestors))
        if not self.unchecked_couriers:
            self.finish(False)
        for address in self.unchecked_couriers[:]:
            self.send(address, Message(MessageType.PRICE_REQUEST,
                      {'order': self.entity, 'context': self.context, 'ancestors': self.ancestors}))

    def handle_price_response(self, message, sender):
        variants = message.msg_body
        if self.parent is not None:
            # Согласие возможно, только если найден переезд не позднее желаемой доставки.
            variants = [v for v in variants if v['time_to'] <= self.entity.time_to + 1e-9]
        self.possible_variants.extend(variants)
        self.unchecked_couriers.remove(sender)
        if not self.unchecked_couriers:
            self.evaluate_variants()
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
                value = normalize(variant[criterion['field']], min(values), max(values))
                variant[criterion['name']] = value
                variant['total_efficiency'] += criterion['weight'] * value
        self.possible_variants.sort(key=lambda v: v['total_efficiency'], reverse=True)

    def run_planning(self):
        if not self.possible_variants:
            self.finish(False)
            return
        if self.context is None:
            self.context = PlanningTransaction(self.scene)
        self.attempt_snapshot = self.context.snapshot()
        self.selected_variant = self.possible_variants.pop(0)
        address = self.dispatcher.reference_book.get_address(self.selected_variant['courier'])
        self.send(address, Message(MessageType.PLANNING_REQUEST,
                  {'variant': self.selected_variant, 'context': self.context}))

    def retry(self):
        self.context.restore(self.attempt_snapshot)
        logging.info('%s: откат неудачной попытки', self.name)
        self.run_planning()

    def handle_planning_response(self, message, sender):
        if not message.msg_body:
            self.retry()
            return
        victims = self.selected_variant['removed_orders']
        if victims and self.dispatcher.require_consent:
            # Сначала более дорогие: каждый рекурсивный шаг допускает только меньшую цену.
            self.pending_victims = sorted(victims, key=lambda o: (-o.price, str(o.number)))
            self.request_next_consent()
        else:
            self.finish(True)

    def request_next_consent(self):
        if not self.pending_victims:
            self.finish(True)
            return
        victim = self.pending_victims.pop(0)
        logging.info('%s: запрос согласия заказа %s', self.name, victim.number)
        self.send(self.dispatcher.reference_book.get_address(victim),
                  Message(MessageType.CONSENT_REQUEST,
                          {'context': self.context, 'ancestors': self.ancestors + (self.entity,)}))

    def handle_consent_request(self, message, sender):
        self.parent = sender
        self.context = message.msg_body['context']
        self.ancestors = message.msg_body['ancestors']
        self.send_params_request()

    def handle_consent_response(self, message, sender):
        if message.msg_body:
            self.request_next_consent()
        else:
            self.dispatcher.refusals += 1
            self.retry()

    def finish(self, success):
        if self.parent is not None:
            logging.info('%s: согласие=%s; текущее место до фиксации сохранено', self.name, success)
            parent = self.parent
            self.parent = None
            self.ancestors = ()
            self.send(parent, Message(MessageType.CONSENT_RESPONSE, success))
            self.context = None
            return
        if success:
            context = self.context
            context.commit()
            self.dispatcher.max_group = max(self.dispatcher.max_group,
                max((len(v['removed_orders']) for v in context.placements.values()), default=0))
            for victim, courier in context.evicted:
                logging.info('REMOVE_ORDER: заказ %s вытеснен с %s', victim.number, courier.name)
                self.dispatcher.displacements += 1
                self.send(self.dispatcher.reference_book.get_address(victim),
                          Message(MessageType.REMOVE_ORDER,
                                  {'courier': courier, 'relocated': victim in context.placements}))
        else:
            logging.info('%s: подходящее размещение отсутствует', self.name)
        self.context = None
        self.dispatcher.finish_planning(self.entity, self)

    def handle_remove_message(self, message, sender):
        logging.info('%s: REMOVE_ORDER от курьера %s', self.name, message.msg_body['courier'].name)
        self.possible_variants.clear()
        self.context = None
        if not message.msg_body['relocated']:
            self.entity.assigned_courier = None
            self.entity.selected_variant = None
            self.restart_planning()

    def restart_planning(self):
        if self.entity.is_deleting:
            return
        self.possible_variants.clear()
        self.context = None
        self.selected_variant = None
        self.parent = None
        self.ancestors = ()
        self.dispatcher.request_planning(self.entity, self)

    def handle_start_planning(self, message, sender):
        self.send_params_request()

    def handle_new_resource_message(self, message, sender):
        if self.entity.assigned_courier is None:
            self.restart_planning()

    def handle_delete_courier_message(self, message, sender):
        if self.entity.assigned_courier is not message.msg_body:
            return
        self.entity.assigned_courier = None
        self.entity.selected_variant = None
        self.restart_planning()

    def handle_parameters_changed(self, message, sender):
        courier = self.entity.assigned_courier
        if courier is None:
            self.restart_planning()
        else:
            self.send(self.dispatcher.reference_book.get_address(courier),
                      Message(MessageType.RELEASE_ORDER, {'order': self.entity, 'replan': True}))

    def handle_delete_message(self):
        super().handle_delete_message()
        if self.dispatcher.closing:
            return
        courier = self.entity.assigned_courier
        if courier is not None and not courier.is_deleting:
            self.send(self.dispatcher.reference_book.get_address(courier),
                      Message(MessageType.RELEASE_ORDER, {'order': self.entity, 'replan': False}))
        self.entity.assigned_courier = None
        self.entity.selected_variant = None
