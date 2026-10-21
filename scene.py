"""Сцена сущностей виртуального мира."""

from collections import defaultdict


class Scene:
    def __init__(self):
        self.entities = defaultdict(list)

    def get_entities_by_type(self, entity_type):
        return self.entities.get(entity_type, [])

    def get_nearest_couriers(self, point, count):
        couriers = self.get_entities_by_type('COURIER')
        return sorted(couriers, key=lambda c: c.get_last_point().get_distance_to_other(point))[:count]
