from collections import Counter

from thespian.actors import ActorSystem

from courier_agent import CourierAgent
from message import Message, MessageType
from order_agent import OrderAgent
from reference_book import ReferenceBook


TYPES_AGENTS = {'ORDER': OrderAgent, 'COURIER': CourierAgent}


class AgentsDispatcher:
    def __init__(self, scene, nearest_count=None):
        # Учебная сцена передается по ссылке в одном процессе.
        self.actor_system = ActorSystem('simpleSystemBase', logDefs=False)
        self.reference_book = ReferenceBook()
        self.scene = scene
        self.nearest_count = nearest_count
        self.message_counts = Counter()

    def add_entity(self, entity):
        agent_type = TYPES_AGENTS.get(entity.get_type())
        if agent_type is None:
            return False
        self.scene.entities[entity.get_type()].append(entity)
        self.create_agent(agent_type, entity)
        return True

    def create_agent(self, agent_class, entity):
        address = self.actor_system.createActor(agent_class)
        self.reference_book.add_agent(entity, address)
        init_data = {'dispatcher': self, 'scene': self.scene, 'entity': entity}
        self.actor_system.tell(address, Message(MessageType.INIT_MESSAGE, init_data))
