import pandas as pd


def get_excel_data(filename, sheet_name):
    return list(pd.read_excel(filename, sheet_name=sheet_name).to_dict('index').values())
