"""СР3: 50 заказов, 20 курьеров, опрос всех и трех ближайших."""

import csv
import random
from pathlib import Path

from main import plan_orders
from message import MessageType


def make_experiment_data():
    rng = random.Random(3)
    couriers = [
        {'Табельный номер': i, 'ФИО': f'Курьер {i}',
         'Координата начального положения x': rng.randint(0, 100),
         'Координата начального положения y': rng.randint(0, 100),
         'Типы доставляемых заказов': 'Посылка', 'Стоимость выхода на работу': 0,
         'Цена работы за единицу времени': 1, 'Скорость': 10,
         'Объем ранца': 10, 'Грузоподъемность': 10}
        for i in range(1, 21)]
    orders = [
        {'Номер': i, 'Наименование': f'Заказ {i}', 'Масса': 1, 'Объем': 1, 'Стоимость': 100,
         'Координата получения x': rng.randint(0, 100),
         'Координата получения y': rng.randint(0, 100),
         'Координата доставки x': rng.randint(0, 100),
         'Координата доставки y': rng.randint(0, 100),
         'Время получения заказа': 0, 'Время доставки заказа': 10000, 'Тип заказа': 'Посылка'}
        for i in range(1, 51)]
    return couriers, orders


def run_experiment(filename='Отчёты/Эксперимент_ЛР3.csv'):
    couriers, orders = make_experiment_data()
    rows = []
    for count in (None, 3):
        scene, counters = plan_orders(couriers, orders, count)
        row = {'Режим': 'Все 20 курьеров' if count is None else '3 ближайших',
               'Заказов': len(orders), 'Курьеров': len(couriers)}
        row.update({kind.value: counters.get(kind.value, 0) for kind in MessageType
                    if kind != MessageType.INIT_MESSAGE})
        row['Всего сообщений'] = sum(counters.values())
        row['Назначено заказов'] = sum(o.assigned_courier is not None
                                      for o in scene.get_entities_by_type('ORDER'))
        rows.append(row)
        print(row)
    with open(filename, 'w', encoding='utf-8-sig', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]), delimiter=';')
        writer.writeheader()
        writer.writerows(rows)
    return rows


if __name__ == '__main__':
    run_experiment(Path(__file__).resolve().parent / 'Отчёты/Эксперимент_ЛР3.csv')
