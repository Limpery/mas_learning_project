"""ЛР6. python main.py — цикл событий; python scenarios.py — протоколы; python experiment.py — сравнение."""

import logging
from pathlib import Path

from agents_dispatcher import AgentsDispatcher
from entities.courier_entity import CourierEntity
from entities.order_entity import OrderEntity
from scene import Scene
from utils.config_utils import load_planning_config
from utils.excel_utils import get_excel_data
from utils.schedule_utils import save_schedule_to_excel


def create_world(courier_data, order_data, criteria):
    scene = Scene()
    dispatcher = AgentsDispatcher(scene, criteria)
    try:
        for row in courier_data:
            dispatcher.add_entity(CourierEntity({}, row, scene))
        for row in order_data:
            dispatcher.add_entity(OrderEntity({}, row, scene))
    except Exception:
        dispatcher.close()
        raise
    return scene, dispatcher


def main(input_file='Исходные данные_ЛР6.xlsx', config_file='planning_config.json',
         output_file='Результаты.xlsx'):
    from utils.console_utils import read_add_event, read_entity_type, show_entities
    _, criteria = load_planning_config(config_file)
    scene, dispatcher = create_world(get_excel_data(input_file, 'Курьеры'),
                                     get_excel_data(input_file, 'Заказы'), criteria)
    try:
        save_schedule_to_excel(scene, output_file)
        while True:
            print('A — добавить, D — удалить, L — список, C — изменить параметры, Q — выход')
            try:
                command = input(': ').strip().upper()
                if command == 'Q':
                    break
                if command == 'L':
                    show_entities(scene)
                    continue
                if command == 'A':
                    event = read_add_event()
                elif command in ('D', 'C'):
                    kind = read_entity_type()
                    name = input('Имя сущности: ').strip()
                    event = {'action': 'remove', 'entity_type': kind, 'name': name}
                    if command == 'C':
                        changes = ({'velocity': float(input('Новая скорость: '))} if kind == 'COURIER'
                                   else {'time_from': float(input('Время получения: ')),
                                         'time_to': float(input('Время доставки: '))})
                        event.update(action='change', changes=changes)
                else:
                    print('Неизвестная команда')
                    continue
                result = dispatcher.apply_event(event)
                print(result)
                if result['Успех']:
                    save_schedule_to_excel(scene, output_file)
            except EOFError:
                break
            except (ValueError, KeyError) as error:
                print('Не удалось применить событие:', error)
    finally:
        dispatcher.close()


if __name__ == '__main__':
    root = Path(__file__).resolve().parent
    logging.basicConfig(level=logging.INFO, format='%(message)s', force=True,
                        handlers=[logging.FileHandler(root / 'output_lab6.txt', encoding='utf-8', mode='w')])
    main(root / 'Исходные данные_ЛР6.xlsx', root / 'planning_config.json', root / 'Результаты.xlsx')
