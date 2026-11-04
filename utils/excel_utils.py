from openpyxl import load_workbook


def get_excel_data(filename, sheet_name):
    workbook = load_workbook(filename, read_only=True, data_only=True)
    try:
        rows = workbook[sheet_name].iter_rows(values_only=True)
        columns = next(rows)
        return [dict(zip(columns, row)) for row in rows if any(v is not None for v in row)]
    finally:
        workbook.close()
