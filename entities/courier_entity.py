import logging
import math

from entities.base_entity import BaseEntity
from point import Point
from schedule_item import ScheduleItem


class CourierEntity(BaseEntity):
    def __init__(self, onto_desc, init_dict_data, scene=None):
        super().__init__(onto_desc, scene)
        self.number = init_dict_data['Табельный номер']
        self.name = init_dict_data['ФИО']
        self.point = Point(float(init_dict_data['Координата начального положения x']),
                           float(init_dict_data['Координата начального положения y']))
        self.types = [s.strip() for s in init_dict_data['Типы доставляемых заказов'].split(';')]
        self.start_cost = float(init_dict_data['Стоимость выхода на работу'])
        self.rate = float(init_dict_data['Цена работы за единицу времени'])
        self.velocity = float(init_dict_data['Скорость'])
        self.max_volume = float(init_dict_data['Объем ранца'])
        self.max_mass = float(init_dict_data['Грузоподъемность'])
        self.schedule = []
        self.uri = 'Courier' + str(self.number)

    def get_type(self):
        return 'COURIER'

    def get_last_point(self):
        return self.schedule[-1].point_to if self.schedule else self.point

    def get_last_time(self):
        return self.schedule[-1].end_time if self.schedule else 0.0

    def get_all_order_records(self, order, schedule=None):
        schedule = self.schedule if schedule is None else schedule
        return [item for item in schedule if item.order is order]

    def get_conflicts(self, start_time, end_time, schedule=None):
        schedule = self.schedule if schedule is None else schedule
        if start_time >= end_time:
            return []
        return [item for item in schedule if item.rec_type != 'Ожидание'
                and item.start_time < item.end_time
                and item.start_time < end_time and start_time < item.end_time]

    def get_conflicted_tasks(self, records, schedule=None):
        tasks = {}
        for record in records:
            if record.order in tasks:
                continue
            items = self.get_all_order_records(record.order, schedule)
            tasks[record.order] = {'start': min(i.start_time for i in items),
                                   'end': max(i.end_time for i in items),
                                   'cost': sum(i.cost for i in items)}
        return tasks

    def make_variant(self, order, start, point, name, removed=()):
        to_order = point.get_distance_to_other(order.point_from) / self.velocity
        with_order = order.point_from.get_distance_to_other(order.point_to) / self.velocity
        pickup = start + to_order
        return {'courier': self, 'order': order, 'time_from': start,
                'time_to': pickup + with_order, 'arrival': pickup, 'pickup': pickup,
                'price': (to_order + with_order) * self.rate, 'point_from': point,
                'variant_name': name, 'pickup_deviation': abs(pickup - order.time_from),
                'removed_orders': tuple(removed)}

    def records_for(self, variant):
        order = variant['order']
        start, pickup, end = (variant[k] for k in ('time_from', 'pickup', 'time_to'))
        return [ScheduleItem(order, 'Движение за грузом', start, pickup,
                             variant['point_from'], order.point_from, (pickup-start)*self.rate, variant),
                ScheduleItem(order, 'Ожидание', pickup, pickup,
                             order.point_from, order.point_from, 0.0, variant),
                ScheduleItem(order, 'Движение с грузом', pickup, end,
                             order.point_from, order.point_to, (end-pickup)*self.rate, variant)]

    def preview(self, variant, schedule):
        removed = variant['removed_orders']
        remaining = [r for r in schedule if r.order not in removed]
        if self.get_conflicts(variant['time_from'], variant['time_to'], remaining):
            return None
        result = sorted(remaining + self.records_for(variant), key=lambda r: r.start_time)
        # Проверяем также координаты: отсутствие пересечений само по себе недостаточно.
        point, time = self.point, 0.0
        for item in result:
            if item.start_time < time - 1e-9 or item.point_from != point:
                return None
            point, time = item.point_to, item.end_time
        return result

    def get_variants(self, order, schedule=None, conflicts=False, multiple=True, ancestors=()):
        schedule = self.schedule if schedule is None else schedule
        if (order.order_type not in self.types or order.weight > self.max_mass
                or order.volume > self.max_volume or self.velocity <= 0):
            return []
        last_point = schedule[-1].point_to if schedule else self.point
        last_time = schedule[-1].end_time if schedule else 0.0
        variants = [self.make_variant(order, last_time, last_point, 'asap')]
        time_to_order = last_point.get_distance_to_other(order.point_from) / self.velocity
        jit_start = order.time_from - time_to_order
        jit = self.make_variant(order, jit_start, last_point, 'jit_pickup')
        if jit_start > 0 and self.preview(jit, schedule) is not None:
            variants.append(jit)
        if not schedule:
            duration = variants[0]['time_to'] - variants[0]['time_from']
            departure = order.time_to - duration
            if departure > 0:
                variants.append(self.make_variant(order, departure, last_point, 'jit_delivery'))
        # Свободные интервалы, в том числе появившиеся после удаления заказа.
        point, start = self.point, 0.0
        for existing_order in dict.fromkeys(r.order for r in schedule):
            records = self.get_all_order_records(existing_order, schedule)
            first, last = records[0], records[-1]
            if first.start_time > start + 1e-9:
                gap_variant = self.make_variant(order, start, point, 'gap')
                if gap_variant['time_to'] <= first.start_time + 1e-9 and self.preview(gap_variant, schedule) is not None:
                    variants.append(gap_variant)
            point, start = last.point_to, last.end_time
        if not conflicts or jit_start <= 0:
            return variants
        records = self.get_conflicts(jit_start, jit['time_to'], schedule)
        tasks = self.get_conflicted_tasks(records, schedule)
        logging.info('%s: конфликтующие заказы %s', self.name,
                     {o.number: summary for o, summary in tasks.items()})
        cheaper = sorted((o for o in tasks if o.price < order.price and o not in ancestors),
                         key=lambda o: (o.price, str(o.number)))
        if not cheaper:
            return variants
        groups = [(cheaper[0],)]
        if multiple and len(cheaper) > 1 and len(cheaper) == len(tasks):
            groups.append(tuple(cheaper))
        for removed in groups:
            first = min((r for o in removed for r in self.get_all_order_records(o, schedule)),
                        key=lambda r: r.start_time)
            variant = self.make_variant(order, first.start_time, first.point_from, 'conflict', removed)
            if self.preview(variant, schedule) is not None:
                logging.info('%s: вариант conflict, вытеснение %s', self.name, [o.number for o in removed])
                variants.append(variant)
        return variants

    def add_order_to_schedule(self, order, start_time, end_time, price, params):
        result = self.preview(params, self.schedule)
        if result is None:
            return False
        self.schedule = result
        return True

    def release_order(self, order):
        remaining = [r for r in self.schedule if r.order is not order]
        point = self.point
        kept = []
        affected = []
        broken = False
        for item in remaining:
            broken = broken or item.point_from != point
            if broken:
                if item.order not in affected:
                    affected.append(item.order)
            else:
                kept.append(item)
                point = item.point_to
        self.schedule = kept
        return affected
