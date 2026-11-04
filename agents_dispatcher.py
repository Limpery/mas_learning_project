import logging
import math
from collections import Counter, deque

from thespian.actors import ActorExitRequest, ActorSystem

from courier_agent import CourierAgent
from entities.courier_entity import CourierEntity
from entities.order_entity import OrderEntity
from message import Message, MessageType
from order_agent import OrderAgent
from reference_book import ReferenceBook


TYPES_AGENTS = {'ORDER': OrderAgent, 'COURIER': CourierAgent}


class AgentsDispatcher:
    def __init__(self, scene, criteria, enable_conflicts=True, multiple=False, require_consent=True):
        self.actor_system = ActorSystem('simpleSystemBase', logDefs=False)
        self.reference_book = ReferenceBook()
        self.scene = scene
        self.criteria = criteria
        self.enable_conflicts = enable_conflicts
        self.multiple = multiple
        self.require_consent = require_consent
        self.displacements = self.refusals = self.max_depth = self.max_group = 0
        self.message_counts = Counter()
        self.planning_queue = deque()
        self.active_order = None
        self.closing = False
        self.negotiating_orders = set()
        self.negotiating_couriers = set()
        self.notified_agents = set()
        self.maintenance_couriers = set()

    def add_entity(self, entity):
        agent_type = TYPES_AGENTS.get(entity.get_type())
        if agent_type is None:
            return False
        existing = self.scene.get_entities_by_type(entity.get_type())
        if any(e.number == entity.number or e.name == entity.name for e in existing):
            raise ValueError('Номер и имя сущности должны быть уникальны в своем типе')
        self.scene.entities[entity.get_type()].append(entity)
        address = self.actor_system.createActor(agent_type)
        self.reference_book.add_agent(entity, address)
        self.actor_system.tell(address, Message(MessageType.INIT_MESSAGE,
                               {'dispatcher': self, 'scene': self.scene, 'entity': entity}))
        return True

    def get_entity(self, entity_type, entity_name):
        return next((e for e in self.scene.get_entities_by_type(entity_type)
                     if e.name == entity_name), None)

    def remove_entity(self, entity_type, entity_name):
        entity = self.get_entity(entity_type, entity_name)
        if entity is None:
            return False
        address = self.reference_book.get_address(entity)
        if address is None:
            return False
        # Исключаем из подбора до рассылки уведомлений из обработчика удаления.
        entity.is_deleting = True
        self.planning_queue = deque(e for e in self.planning_queue if e is not entity)
        self.actor_system.tell(address, ActorExitRequest())
        self.scene.entities[entity_type].remove(entity)
        self.reference_book.remove_agent(entity)
        return True

    def update_entity(self, entity_type, entity_name, changes):
        entity = self.get_entity(entity_type, entity_name)
        if entity is None:
            return False
        allowed = {'ORDER': {'time_from', 'time_to'}, 'COURIER': {'velocity'}}[entity_type]
        if not changes or not set(changes) <= allowed:
            raise ValueError('Для заказа изменяется окно, для курьера — скорость')
        values = {key: float(value) for key, value in changes.items()}
        if any(not math.isfinite(v) or v < 0 for v in values.values()):
            raise ValueError('Параметры должны быть конечными неотрицательными числами')
        if entity_type == 'COURIER' and values['velocity'] <= 0:
            raise ValueError('Скорость должна быть положительной')
        if entity_type == 'ORDER' and values.get('time_from', entity.time_from) > values.get('time_to', entity.time_to):
            raise ValueError('Начало окна не может быть позже конца')
        for key, value in values.items():
            setattr(entity, key, value)
        self.actor_system.tell(self.reference_book.get_address(entity),
                               Message(MessageType.PARAMETERS_CHANGED, values))
        return True

    def request_planning(self, entity, sending_agent):
        if self.closing or entity.is_deleting:
            return
        if entity is not self.active_order and entity not in self.planning_queue:
            self.planning_queue.append(entity)
        self._start_next(sending_agent)

    def _start_next(self, sending_agent):
        if self.active_order is not None or not self.planning_queue:
            return
        self.active_order = self.planning_queue.popleft()
        sending_agent.send(self.reference_book.get_address(self.active_order),
                           Message(MessageType.START_PLANNING))

    def finish_planning(self, entity, sending_agent):
        if self.active_order is entity:
            self.active_order = None
        self._start_next(sending_agent)

    def apply_event(self, event):
        self.negotiating_orders.clear()
        self.negotiating_couriers.clear()
        self.notified_agents.clear()
        self.maintenance_couriers.clear()
        before = sum(self.message_counts.values())
        kind = event['entity_type']
        logging.info('СОБЫТИЕ: %s', event)
        if event['action'] == 'add':
            cls = CourierEntity if kind == 'COURIER' else OrderEntity
            success = self.add_entity(cls({}, event['data'], self.scene))
        elif event['action'] == 'remove':
            success = self.remove_entity(kind, event['name'])
        elif event['action'] == 'change':
            success = self.update_entity(kind, event['name'], event['changes'])
        else:
            raise ValueError('Неизвестное событие')
        return {'Успех': success, 'Заказов в переговорах': len(self.negotiating_orders),
                'Курьеров в переговорах': len(self.negotiating_couriers),
                'Агентов в перестройке': len(self.negotiating_orders | self.negotiating_couriers | self.maintenance_couriers),
                'Агентов получили сообщение': len(self.notified_agents),
                'Сообщений': sum(self.message_counts.values()) - before}

    def close(self):
        self.closing = True
        self.actor_system.shutdown()
