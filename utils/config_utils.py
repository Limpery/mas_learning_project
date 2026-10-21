import json
import math


def load_planning_config(filename='planning_config.json', profile=None):
    with open(filename, encoding='utf-8') as file:
        config = json.load(file)
    profile = profile or config['default_profile']
    weights = config['profiles'][profile]
    criteria = [{**item, 'weight': weights[item['name']]} for item in config['criteria']]
    if not criteria or len({c['name'] for c in criteria}) != len(criteria):
        raise ValueError('Критерии должны быть непустыми и иметь уникальные имена')
    if any(c['direction'] not in ('increasing', 'decreasing') for c in criteria):
        raise ValueError('Неизвестное направление нормировки')
    if any(not math.isfinite(c['weight']) or c['weight'] < 0 for c in criteria):
        raise ValueError('Веса должны быть конечными неотрицательными числами')
    if not math.isclose(sum(c['weight'] for c in criteria), 1.0, abs_tol=1e-9):
        raise ValueError('Сумма весов должна быть равна единице')
    return profile, criteria
