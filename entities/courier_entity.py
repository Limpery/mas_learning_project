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
        self.types = [item.strip() for item in init_dict_data['Типы доставляемых заказов'].split(';')]
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

    def get_conflicts(self, start_time, end_time):
        # Полуоткрытые интервалы: касание границ конфликтом не считается.
        if start_time >= end_time:
            return []
        return [item for item in self.schedule
                if item.start_time < item.end_time
                and item.start_time < end_time and start_time < item.end_time]

    def get_variants(self, order):
        if (order.order_type not in self.types or order.weight > self.max_mass
                or order.volume > self.max_volume or self.velocity <= 0):
            return []
        start = self.get_last_time()
        arrival = start + self.get_last_point().get_distance_to_other(order.point_from) / self.velocity
        pickup = max(arrival, order.time_from)
        end = pickup + order.point_from.get_distance_to_other(order.point_to) / self.velocity
        return [{'courier': self, 'order': order, 'time_from': start, 'time_to': end,
                 'arrival': arrival, 'pickup': pickup, 'price': (end - start) * self.rate,
                 'point_from': self.get_last_point(), 'variant_name': 'asap'}]

    def add_order_to_schedule(self, order, start_time, end_time, price, params):
        # Пересчитываем предложение: после ответа другому заказу оно могло устареть.
        variants = self.get_variants(order)
        if not variants:
            return False
        current = variants[0]
        if (self.get_conflicts(start_time, end_time)
                or params['point_from'] != current['point_from']
                or any(not math.isclose(params[key], current[key], abs_tol=1e-9)
                       for key in ('time_from', 'time_to', 'price', 'arrival', 'pickup'))):
            return False
        arrival, pickup = params['arrival'], params['pickup']
        self.schedule.extend([
            ScheduleItem(order, 'Движение за грузом', start_time, arrival,
                         self.get_last_point(), order.point_from, (arrival - start_time) * self.rate, params),
            ScheduleItem(order, 'Ожидание', arrival, pickup,
                         order.point_from, order.point_from, (pickup - arrival) * self.rate, params),
            ScheduleItem(order, 'Движение с грузом', pickup, end_time,
                         order.point_from, order.point_to, (end_time - pickup) * self.rate, params),
        ])
        return True
