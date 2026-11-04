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


def save_schedule_to_excel(scene, filename):
    from openpyxl import Workbook
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = 'Расписание'
    sheet.append(['Курьер', 'Заказ', 'Действие', 'Начало', 'Конец', 'Откуда', 'Куда', 'Стоимость', 'Вариант'])
    for courier in scene.get_entities_by_type('COURIER'):
        for item in courier.schedule:
            sheet.append([courier.name, item.order.number, item.rec_type,
                          item.start_time, item.end_time, str(item.point_from), str(item.point_to),
                          item.cost, item.all_params['variant_name']])
    unassigned = workbook.create_sheet('Без исполнителя')
    unassigned.append(['Заказ', 'Наименование', 'Тип'])
    for order in scene.get_entities_by_type('ORDER'):
        if order.assigned_courier is None:
            unassigned.append([order.number, order.name, order.order_type])
    for ws in workbook:
        ws.freeze_panes = 'A2'
        for column in ws.columns:
            letter = column[0].column_letter
            ws.column_dimensions[letter].width = min(36, max(12, max(len(str(c.value or '')) for c in column)+2))
    workbook.save(filename)
