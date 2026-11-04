"""Два прогона ЛР5 и небольшие демонстрации самостоятельной работы."""

import csv
import json
from pathlib import Path

from main import plan_orders
from utils.config_utils import load_planning_config
from utils.excel_utils import get_excel_data
from utils.schedule_utils import save_schedule


def run_experiment(input_file='Исходные данные_конфликт.xlsx', config_file='planning_config.json',
                   output_dir='Отчёты'):
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    couriers = get_excel_data(input_file, 'Курьеры')
    orders = get_excel_data(input_file, 'Заказы')
    _, criteria = load_planning_config(config_file)
    rows = []
    for enabled, name in ((False, 'До'), (True, 'После')):
        scene, stats = plan_orders(couriers, orders, criteria, enable_conflicts=enabled)
        save_schedule(scene, output_dir / f'Расписание_ЛР5_{name}.csv')
        assigned = [o for o in scene.get_entities_by_type('ORDER') if o.selected_variant]
        row = {'Режим': name,
               'Стоимость': round(sum(r.cost for c in scene.get_entities_by_type('COURIER')
                                       for r in c.schedule), 4),
               'Назначено': len(assigned),
               'В окне': sum(o.time_from-1e-9 <= o.selected_variant['time_to'] <= o.time_to+1e-9
                            for o in assigned), **stats}
        rows.append(row)
        print(row)
    with (output_dir / 'Сравнение_ЛР5.csv').open('w', encoding='utf-8-sig', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]), delimiter=';')
        writer.writeheader()
        writer.writerows(rows)
    return rows


def run_demonstrations(input_file='Исходные данные_конфликт.xlsx', config_file='planning_config.json'):
    couriers = get_excel_data(input_file, 'Курьеры')
    orders = get_excel_data(input_file, 'Заказы')
    _, criteria = load_planning_config(config_file)
    cases = {}
    # Два заказа с одинаковым маршрутом: новый занимает интервалы обоих.
    multiple = [dict(row) for row in orders]
    for row in multiple:
        row['Координата получения x'] = 0
        row['Координата доставки x'] = 10
        row['Время доставки заказа'] = 30
    multiple[0]['Стоимость'] = 10
    multiple[1]['Стоимость'] = 20
    multiple[2]['Время получения заказа'] = 3
    _, cases['Несколько заказов'] = plan_orders(couriers, multiple, criteria, multiple=True)
    # Второй заказ нельзя перепланировать до его срока — уступка отклоняется.
    refusal = [dict(row) for row in orders]
    refusal[1]['Время доставки заказа'] = 5
    _, cases['Отказ уступить'] = plan_orders(couriers, refusal, criteria)
    # Корневой заказ вытесняет первый; тот находит место второго, второй переезжает в хвост.
    recursive = [dict(row) for row in orders]
    for row, values in zip(recursive, ((200,100,50,35,100), (100,50,0,31,100), (300,0,50,5,25))):
        price, pickup_x, delivery_x, pickup_time, delivery_time = values
        row.update({'Стоимость':price, 'Координата получения x':pickup_x,
                    'Координата доставки x':delivery_x, 'Время получения заказа':pickup_time,
                    'Время доставки заказа':delivery_time})
    _, cases['Рекурсивные переговоры'] = plan_orders(couriers, recursive, criteria)
    for name, stats in cases.items():
        print(name, stats)
    result_file = Path(input_file).resolve().parent / 'Отчёты/Самостоятельная_ЛР5.json'
    result_file.parent.mkdir(exist_ok=True)
    result_file.write_text(json.dumps(cases, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return cases


if __name__ == '__main__':
    root = Path(__file__).resolve().parent
    run_experiment(root / 'Исходные данные_конфликт.xlsx', root / 'planning_config.json', root / 'Отчёты')
    run_demonstrations(root / 'Исходные данные_конфликт.xlsx', root / 'planning_config.json')
