ORDER_FIELDS = [('Номер', int), ('Наименование', str), ('Масса', float), ('Объем', float),
                ('Стоимость', float), ('Координата получения x', float), ('Координата получения y', float),
                ('Координата доставки x', float), ('Координата доставки y', float),
                ('Время получения заказа', float), ('Время доставки заказа', float), ('Тип заказа', str)]
COURIER_FIELDS = [('Табельный номер', int), ('ФИО', str), ('Координата начального положения x', float),
                  ('Координата начального положения y', float), ('Типы доставляемых заказов', str),
                  ('Стоимость выхода на работу', float), ('Цена работы за единицу времени', float),
                  ('Скорость', float), ('Объем ранца', float), ('Грузоподъемность', float)]


def read_entity_type():
    value = input('Тип: C/С — курьер, O/О — заказ: ').strip().upper()
    if value in ('C', 'С'):
        return 'COURIER'
    if value in ('O', 'О'):
        return 'ORDER'
    raise ValueError('Неизвестный тип сущности')


def read_add_event():
    kind = read_entity_type()
    fields = COURIER_FIELDS if kind == 'COURIER' else ORDER_FIELDS
    data = {key: convert(input(key + ': ').strip()) for key, convert in fields}
    if kind == 'COURIER' and data['Скорость'] <= 0:
        raise ValueError('Скорость должна быть положительной')
    return {'action': 'add', 'entity_type': kind, 'data': data}


def show_entities(scene):
    for kind in ('COURIER', 'ORDER'):
        for entity in scene.get_entities_by_type(kind):
            if kind == 'ORDER':
                courier = entity.assigned_courier
                print('Заказ:', entity.name, 'Курьер:', courier.name if courier else 'не назначен')
            else:
                print('Курьер:', entity.name, 'Скорость:', entity.velocity,
                      'Типы:', ';'.join(entity.types))
