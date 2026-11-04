import logging


class ReferenceBook:
    def __init__(self):
        self.agents_entities = {}

    def add_agent(self, entity, agent_address):
        self.agents_entities[entity] = agent_address

    def get_address(self, entity):
        address = self.agents_entities.get(entity)
        if address is None:
            logging.error('Агент %s отсутствует в адресной книге', entity.uri)
        return address

    def remove_agent(self, entity):
        self.agents_entities.pop(entity, None)
