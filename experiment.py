"""ЛР4: три прогона на одинаковых данных с разными весами критериев."""

import csv
import json
from pathlib import Path

from main import plan_orders
from utils.config_utils import load_planning_config
from utils.excel_utils import get_excel_data
from utils.schedule_utils import save_schedule


def run_experiment(input_file='Исходные данные.xlsx', config_file='planning_config.json',
                   output_dir='Отчёты'):
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    couriers = get_excel_data(input_file, 'Курьеры')
    orders = get_excel_data(input_file, 'Заказы')
    with open(config_file, encoding='utf-8') as file:
        config = json.load(file)
    rows = []
    for profile in config['profiles']:
        _, criteria = load_planning_config(config_file, profile)
        weights = {item['name']: item['weight'] for item in criteria}
        # Каждый прогон создает новые сущности с пустыми расписаниями.
        scene, _ = plan_orders(couriers, orders, criteria)
        save_schedule(scene, output_dir / f'Расписание_ЛР4_{profile}.csv')
        assigned = [o for o in scene.get_entities_by_type('ORDER') if o.selected_variant]
        in_window = sum(o.time_from - 1e-9 <= o.selected_variant['time_to'] <= o.time_to + 1e-9
                        for o in assigned)
        row = {'Профиль': profile,
               'Вес получения': weights.get('start_efficiency', 0),
               'Вес доставки': weights.get('finish_efficiency', 0),
               'Вес стоимости': weights.get('price_efficiency', 0),
               'Вес точности получения': weights.get('pickup_accuracy_efficiency', 0),
               'Стоимость плана': round(sum(item.cost for courier in scene.get_entities_by_type('COURIER')
                                            for item in courier.schedule), 4),
               'Назначено': len(assigned), 'Доставлено в окне': in_window}
        rows.append(row)
        print(row)
    with (output_dir / 'Сравнение_ЛР4.csv').open('w', encoding='utf-8-sig', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]), delimiter=';')
        writer.writeheader()
        writer.writerows(rows)
    return rows


if __name__ == '__main__':
    root = Path(__file__).resolve().parent
    run_experiment(root / 'Исходные данные.xlsx', root / 'planning_config.json', root / 'Отчёты')
