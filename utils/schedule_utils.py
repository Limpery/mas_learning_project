import csv


def save_schedule(scene, filename):
    with open(filename, 'w', encoding='utf-8-sig', newline='') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow(['Курьер', 'Заказ', 'Действие', 'Начало', 'Конец', 'Откуда', 'Куда', 'Стоимость', 'Вариант'])
        for courier in scene.get_entities_by_type('COURIER'):
            for item in courier.schedule:
                writer.writerow([courier.name, item.order.number, item.rec_type,
                                 round(item.start_time, 4), round(item.end_time, 4),
                                 item.point_from, item.point_to, round(item.cost, 4),
                                 item.all_params['variant_name']])
