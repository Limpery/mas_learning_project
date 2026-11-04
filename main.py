"""ЛР5: сравнение расписаний без конфликтов и с их разрешением."""

import logging
from pathlib import Path

from agents_dispatcher import AgentsDispatcher
from entities.courier_entity import CourierEntity
from entities.order_entity import OrderEntity
from scene import Scene
from utils.excel_utils import get_excel_data
from utils.schedule_utils import save_schedule
from utils.config_utils import load_planning_config


def plan_orders(courier_data, order_data, criteria, enable_conflicts=True,
                multiple=False, require_consent=True):
    scene = Scene()
    dispatcher = AgentsDispatcher(scene, criteria, enable_conflicts, multiple, require_consent)
    try:
        for row in courier_data:
            dispatcher.add_entity(CourierEntity({}, row, scene))
        for row in order_data:
            dispatcher.add_entity(OrderEntity({}, row, scene))
        stats = {'Сообщений': sum(dispatcher.message_counts.values()),
                 'Вытеснений': dispatcher.displacements, 'Отказов уступить': dispatcher.refusals,
                 'Глубина переговоров': dispatcher.max_depth,
                 'Максимум вытесненных за раз': dispatcher.max_group}
        return scene, stats
    finally:
        dispatcher.actor_system.shutdown()


def main(input_file='Исходные данные_конфликт.xlsx', output_dir='Отчёты',
         config_file='planning_config.json'):
    from experiment import run_experiment
    return run_experiment(input_file, config_file, output_dir)


if __name__ == '__main__':
    root = Path(__file__).resolve().parent
    logging.basicConfig(level=logging.INFO, format='%(message)s', force=True,
                        handlers=[logging.FileHandler(root / 'output_lab5.txt', encoding='utf-8', mode='w')])
    main(root / 'Исходные данные_конфликт.xlsx', root / 'Отчёты', root / 'planning_config.json')
