"""Черновики расписаний: принятие всех перестановок или полный откат."""


class PlanningTransaction:
    def __init__(self, scene):
        self.schedules = {c: list(c.schedule) for c in scene.get_entities_by_type('COURIER')}
        self.placements = {}
        self.evicted = []

    def snapshot(self):
        return ({c: list(s) for c, s in self.schedules.items()},
                dict(self.placements), list(self.evicted))

    def restore(self, snapshot):
        self.schedules, self.placements, self.evicted = snapshot

    def commit(self):
        for courier, schedule in self.schedules.items():
            courier.schedule = schedule
        for order, variant in self.placements.items():
            order.assigned_courier = variant['courier']
            order.selected_variant = variant
