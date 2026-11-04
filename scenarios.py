"""Протоколы трех событий ЛР6 и примеры самостоятельной работы."""

import csv
import json
import logging
from pathlib import Path

from main import create_world
from utils.config_utils import load_planning_config
from utils.excel_utils import get_excel_data
from utils.metrics import assignment_signatures, plan_quality
from utils.schedule_utils import save_schedule, save_schedule_to_excel


def make_order(number, name=None, order_type='Обычный', pickup_x=5, delivery_x=0,
               pickup_time=0, delivery_time=50):
    return {'Номер': number, 'Наименование': name or f'Заказ {number}', 'Масса': 1,
            'Объем': 1, 'Стоимость': 100, 'Координата получения x': pickup_x,
            'Координата получения y': 0, 'Координата доставки x': delivery_x,
            'Координата доставки y': 0, 'Время получения заказа': pickup_time,
            'Время доставки заказа': delivery_time, 'Тип заказа': order_type}


def make_courier(number, name=None, types='Обычный', velocity=5, rate=1):
    return {'Табельный номер': number, 'ФИО': name or f'Курьер {number}',
            'Координата начального положения x': 0, 'Координата начального положения y': 0,
            'Типы доставляемых заказов': types, 'Стоимость выхода на работу': 0,
            'Цена работы за единицу времени': rate, 'Скорость': velocity,
            'Объем ранца': 10, 'Грузоподъемность': 10}


def run_scenarios(input_file='Исходные данные_ЛР6.xlsx', config_file='planning_config.json',
                  output_dir='Отчёты'):
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    _, criteria = load_planning_config(config_file)
    scene, dispatcher = create_world(get_excel_data(input_file, 'Курьеры'),
                                     get_excel_data(input_file, 'Заказы'), criteria)
    events = [
        ('01_Новый_заказ', {'action': 'add', 'entity_type': 'ORDER',
                          'data': make_order(4, 'Новый обычный')}),
        ('02_Срочный_без_курьера', {'action': 'add', 'entity_type': 'ORDER',
                                 'data': make_order(5, 'Срочный заказ', 'Срочный')}),
        ('03_Новый_курьер', {'action': 'add', 'entity_type': 'COURIER',
                           'data': make_courier(3, 'Курьер В', 'Обычный;Срочный', rate=0.5)}),
        ('04_Удаление_курьера', {'action': 'remove', 'entity_type': 'COURIER', 'name': 'Курьер А'}),
    ]
    protocol = []
    try:
        for label, event in events:
            before = assignment_signatures(scene)
            save_schedule(scene, output_dir / f'ЛР6_{label}_до.csv')
            metrics = dispatcher.apply_event(event)
            after = assignment_signatures(scene)
            row = {'Сценарий': label, **metrics, **plan_quality(scene),
                   'Неизменных назначений': sum(before[n] == after[n] for n in before.keys() & after.keys())}
            protocol.append(row)
            save_schedule(scene, output_dir / f'ЛР6_{label}_после.csv')
            print(row)
        save_schedule_to_excel(scene, output_dir.parent / 'Результаты.xlsx')
    finally:
        dispatcher.close()
    with (output_dir / 'Протокол_событий_ЛР6.csv').open('w', encoding='utf-8-sig', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=list(protocol[0]), delimiter=';')
        writer.writeheader()
        writer.writerows(protocol)
    return protocol


def run_independent(config_file='planning_config.json', output_dir='Отчёты'):
    _, criteria = load_planning_config(config_file)
    output_dir = Path(output_dir)
    scene, dispatcher = create_world([make_courier(1)], [make_order(i) for i in (1, 2, 3)], criteria)
    results = {}
    try:
        old_third = assignment_signatures(scene)[3]
        save_schedule(scene, output_dir / 'ЛР6_Удаление_заказа_до.csv')
        results['Удаление заказа'] = dispatcher.apply_event(
            {'action': 'remove', 'entity_type': 'ORDER', 'name': 'Заказ 2'})
        save_schedule(scene, output_dir / 'ЛР6_Удаление_заказа_после.csv')
        dispatcher.apply_event({'action': 'add', 'entity_type': 'ORDER', 'data': make_order(4, 'Замена')})
        order = dispatcher.get_entity('ORDER', 'Замена')
        results['Освободившийся интервал'] = {
            'Вариант': order.selected_variant['variant_name'],
            'Начало': order.selected_variant['time_from'], 'Конец': order.selected_variant['time_to'],
            'Соседний заказ сохранен': assignment_signatures(scene)[3] == old_third}
        save_schedule(scene, output_dir / 'ЛР6_Свободный_интервал_занят.csv')
        save_schedule(scene, output_dir / 'ЛР6_Изменение_окна_до.csv')
        results['Изменение окна'] = dispatcher.apply_event(
            {'action': 'change', 'entity_type': 'ORDER', 'name': 'Заказ 1',
             'changes': {'time_from': 10, 'time_to': 12}})
        save_schedule(scene, output_dir / 'ЛР6_Изменение_окна_после.csv')
        results['Изменение окна']['Показатели'] = plan_quality(scene)
        save_schedule(scene, output_dir / 'ЛР6_Изменение_скорости_до.csv')
        results['Изменение скорости'] = dispatcher.apply_event(
            {'action': 'change', 'entity_type': 'COURIER', 'name': 'Курьер 1', 'changes': {'velocity': 2.5}})
        results['Изменение скорости']['Показатели'] = plan_quality(scene)
        save_schedule(scene, output_dir / 'ЛР6_Изменение_скорости_после.csv')
    finally:
        dispatcher.close()
    (output_dir / 'Самостоятельная_ЛР6.json').write_text(json.dumps(results, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    for name, result in results.items():
        print(name, result)
    return results


if __name__ == '__main__':
    root = Path(__file__).resolve().parent
    logging.basicConfig(level=logging.INFO, format='%(message)s', force=True,
                        handlers=[logging.FileHandler(root / 'output_lab6.txt', encoding='utf-8', mode='w')])
    run_scenarios(root / 'Исходные данные_ЛР6.xlsx', root / 'planning_config.json', root / 'Отчёты')
    run_independent(root / 'planning_config.json', root / 'Отчёты')
