from entities.base_entity import BaseEntity
from point import Point


class OrderEntity(BaseEntity):
    def __init__(self, onto_desc, init_dict_data, scene=None):
        super().__init__(onto_desc, scene)
        self.number = init_dict_data['Номер']
        self.name = init_dict_data['Наименование']
        self.weight = float(init_dict_data['Масса'])
        self.volume = float(init_dict_data['Объем'])
        self.price = float(init_dict_data['Стоимость'])
        self.point_from = Point(float(init_dict_data['Координата получения x']),
                                float(init_dict_data['Координата получения y']))
        self.point_to = Point(float(init_dict_data['Координата доставки x']),
                              float(init_dict_data['Координата доставки y']))
        self.time_from = float(init_dict_data['Время получения заказа'])
        self.time_to = float(init_dict_data['Время доставки заказа'])
        self.order_type = init_dict_data['Тип заказа']
        self.uri = 'Order' + str(self.number)
        self.assigned_courier = None

    def get_type(self):
        return 'ORDER'
