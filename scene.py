"""Сцена сущностей виртуального мира."""

from collections import defaultdict


class Scene:
    def __init__(self):
        self.entities = defaultdict(list)

    def get_entities_by_type(self, entity_type):
        return self.entities.get(entity_type, [])
