def plan_quality(scene):
    orders = scene.get_entities_by_type('ORDER')
    couriers = scene.get_entities_by_type('COURIER')
    assigned = [o for o in orders if o.selected_variant]
    return {'Заказов': len(orders), 'Назначено': len(assigned),
            'В окне': sum(o.time_from - 1e-9 <= o.selected_variant['time_to'] <= o.time_to + 1e-9
                         for o in assigned),
            'Стоимость': round(sum(r.cost for c in couriers for r in c.schedule), 4),
            'Завершение плана': round(max((r.end_time for c in couriers for r in c.schedule), default=0), 4)}


def assignment_signatures(scene):
    return {o.number: (o.assigned_courier.number, o.selected_variant['time_from'],
                       o.selected_variant['time_to'], o.selected_variant['price'])
            if o.selected_variant else None for o in scene.get_entities_by_type('ORDER')}
