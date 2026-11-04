"""Самостоятельная работа ЛР6: 50 заказов, 10 курьеров и 10 событий."""

import csv
import logging
import random
from pathlib import Path
from time import perf_counter

from main import create_world
from scenarios import make_courier, make_order
from utils.config_utils import load_planning_config
from utils.metrics import plan_quality


def experiment_data():
    rng = random.Random(6)
    couriers = [make_courier(i, types='Обычный;Срочный', velocity=rng.uniform(8, 12),
                             rate=rng.uniform(1, 2)) for i in range(1, 11)]
    orders = []
    for i in range(1, 51):
        row = make_order(i, pickup_x=rng.randint(1, 30), pickup_time=rng.randint(0, 20),
                         delivery_time=rng.randint(30, 70))
        row['Координата получения y'] = rng.randint(0, 20)
        orders.append(row)
    events = [
        {'action': 'add', 'entity_type': 'ORDER', 'data': make_order(51)},
        {'action': 'add', 'entity_type': 'ORDER', 'data': make_order(52, order_type='Срочный')},
        {'action': 'add', 'entity_type': 'COURIER',
         'data': make_courier(11, types='Обычный;Срочный', velocity=12, rate=0.8)},
        {'action': 'change', 'entity_type': 'ORDER', 'name': 'Заказ 5', 'changes': {'time_from': 10, 'time_to': 12}},
        {'action': 'change', 'entity_type': 'COURIER', 'name': 'Курьер 2', 'changes': {'velocity': 4}},
        {'action': 'remove', 'entity_type': 'ORDER', 'name': 'Заказ 7'},
        {'action': 'remove', 'entity_type': 'COURIER', 'name': 'Курьер 1'},
        {'action': 'add', 'entity_type': 'ORDER', 'data': make_order(53)},
        {'action': 'change', 'entity_type': 'ORDER', 'name': 'Заказ 15', 'changes': {'time_from': 5, 'time_to': 10}},
        {'action': 'remove', 'entity_type': 'COURIER', 'name': 'Курьер 3'},
    ]
    return couriers, orders, events


def change_input(couriers, orders, event):
    rows = couriers if event['entity_type'] == 'COURIER' else orders
    if event['action'] == 'add':
        rows.append(dict(event['data']))
        return
    name_key = 'ФИО' if event['entity_type'] == 'COURIER' else 'Наименование'
    row = next(r for r in rows if r[name_key] == event['name'])
    if event['action'] == 'remove':
        rows.remove(row)
    else:
        keys = {'velocity': 'Скорость', 'time_from': 'Время получения заказа', 'time_to': 'Время доставки заказа'}
        row.update({keys[k]: value for k, value in event['changes'].items()})


def run_experiment(config_file='planning_config.json', output_dir='Отчёты'):
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    _, criteria = load_planning_config(config_file)
    rows = []
    logger = logging.getLogger()
    old_level = logger.level
    logger.setLevel(logging.WARNING)
    try:
        for mode in ('Адаптивный', 'Полный пересчет'):
            couriers, orders, events = experiment_data()
            scene = dispatcher = None
            total_time = 0.0
            if mode == 'Адаптивный':
                scene, dispatcher = create_world(couriers, orders, criteria)
            try:
                for index, event in enumerate(events, 1):
                    start = perf_counter()
                    if mode == 'Адаптивный':
                        metrics = dispatcher.apply_event(event)
                    else:
                        change_input(couriers, orders, event)
                        scene, dispatcher = create_world(couriers, orders, criteria)
                        metrics = {'Заказов в переговорах': len(dispatcher.negotiating_orders),
                                   'Курьеров в переговорах': len(dispatcher.negotiating_couriers)}
                    elapsed = perf_counter() - start
                    total_time += elapsed
                    rows.append({'Режим': mode, 'Событие': index, 'Действие': event['action'],
                                 'Тип': event['entity_type'], 'Время мс': round(elapsed * 1000, 4),
                                 'Накопленное время мс': round(total_time * 1000, 4),
                                 'Заказов в переговорах': metrics['Заказов в переговорах'],
                                 'Курьеров в переговорах': metrics['Курьеров в переговорах'],
                                 **plan_quality(scene)})
                    if mode == 'Полный пересчет':
                        dispatcher.close()
                        dispatcher = None
            finally:
                if dispatcher is not None:
                    dispatcher.close()
    finally:
        logger.setLevel(old_level)
    with (output_dir / 'Эксперимент_ЛР6.csv').open('w', encoding='utf-8-sig', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]), delimiter=';')
        writer.writeheader()
        writer.writerows(rows)
    final = [r for r in rows if r['Событие'] == 10]
    with (output_dir / 'Сравнение_ЛР6.csv').open('w', encoding='utf-8-sig', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=list(final[0]), delimiter=';')
        writer.writeheader()
        writer.writerows(final)
    draw_comparison(rows, output_dir / 'Сравнение_ЛР6.png')
    for row in final:
        print(row)
    return rows


def draw_comparison(rows, filename):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    figure = plt.figure(figsize=(7.5, 6.4))
    grid = figure.add_gridspec(2, 2)
    axes = [figure.add_subplot(grid[0, :]), figure.add_subplot(grid[1, 0]),
            figure.add_subplot(grid[1, 1])]
    for mode in ('Адаптивный', 'Полный пересчет'):
        data = [r for r in rows if r['Режим'] == mode]
        axes[0].plot([r['Событие'] for r in data], [r['Накопленное время мс'] for r in data], marker='o', label=mode)
    axes[0].set(xlabel='Номер события', ylabel='Накопленное время, мс', title='Время обработки 10 событий')
    final = [r for r in rows if r['Событие'] == 10]
    labels = ['Адаптивный', 'Полный\nпересчет']
    axes[1].bar(labels, [r['Стоимость'] for r in final], color=['#377ca8', '#d48b37'])
    axes[1].set(ylabel='Условные единицы', title='Итоговая стоимость')
    axes[2].bar(labels, [r['В окне'] for r in final], color=['#377ca8', '#d48b37'])
    axes[2].set(ylabel='Количество заказов', title='Доставки в окне')
    axes[0].legend(fontsize=8)
    for axis in axes:
        axis.spines[['top', 'right']].set_visible(False)
    figure.tight_layout()
    figure.savefig(filename, dpi=160)
    plt.close(figure)


if __name__ == '__main__':
    root = Path(__file__).resolve().parent
    run_experiment(root / 'planning_config.json', root / 'Отчёты')
