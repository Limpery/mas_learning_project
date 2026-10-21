"""ЛР4. Запуск: python main.py. Сравнение весов: python experiment.py."""

import logging
from pathlib import Path

from agents_dispatcher import AgentsDispatcher
from entities.courier_entity import CourierEntity
from entities.order_entity import OrderEntity
from scene import Scene
from utils.excel_utils import get_excel_data
from utils.schedule_utils import save_schedule
from utils.config_utils import load_planning_config


def plan_orders(courier_data, order_data, criteria):
    scene = Scene()
    dispatcher = AgentsDispatcher(scene, criteria)
    try:
        # Курьеры должны быть в сцене до начала переговоров заказов.
        for row in courier_data:
            dispatcher.add_entity(CourierEntity({}, row, scene))
        for row in order_data:
            dispatcher.add_entity(OrderEntity({}, row, scene))
        return scene, dict(dispatcher.message_counts)
    finally:
        dispatcher.actor_system.shutdown()


def main(input_file='Исходные данные.xlsx', output_file='Отчёты/Расписание_ЛР4.csv',
         config_file='planning_config.json', profile=None):
    profile, criteria = load_planning_config(config_file, profile)
    scene, counts = plan_orders(get_excel_data(input_file, 'Курьеры'),
                               get_excel_data(input_file, 'Заказы'), criteria)
    save_schedule(scene, output_file)
    for order in scene.get_entities_by_type('ORDER'):
        courier = order.assigned_courier
        variant = order.selected_variant
        details = (f", {variant['variant_name']}, цена {variant['price']:.4f}, "
                   f"оценка {variant['total_efficiency']:.4f}" if variant else '')
        print(f'Заказ {order.number}: {courier.name if courier else "не назначен"}{details}')
    print('Профиль:', profile)
    print('Сообщений переговоров:', sum(counts.values()))
    print('Расписание:', output_file)
    return scene, counts


if __name__ == '__main__':
    root = Path(__file__).resolve().parent
    logging.basicConfig(level=logging.INFO, format='%(message)s', force=True,
                        handlers=[logging.FileHandler(root / 'output_lab4.txt', encoding='utf-8', mode='w')])
    main(root / 'Исходные данные.xlsx', root / 'Отчёты/Расписание_ЛР4.csv',
         root / 'planning_config.json')
