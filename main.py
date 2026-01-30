import math
from typing import List
from typing_extensions import TypedDict

from fastapi import FastAPI

# Константа радиуса Земли в метрах
R = 6371e3  
app = FastAPI()

# Определение типа данных для точки с временным штампом и географическими координатами
class PointDict(TypedDict):
    timestamp: int   # Временной штамп события
    lat: float       # Широта
    lon: float       # Долгота

# Функция для расчета расстояния между двумя точками по формуле Хаверсина
async def haversine(lat1, lon1, lat2, lon2):
    """
    Вычисляет расстояние между двумя точками на поверхности Земли 
    используя формулу Хаверсина.
    :param lat1: широта первой точки
    :param lon1: долгота первой точки
    :param lat2: широта второй точки
    :param lon2: долгота второй точки
    :return: Расстояние в метрах
    """
    fi1 = lat1 * math.pi / 180      # Преобразование градусов в радианы
    fi2 = lat2 * math.pi / 180      
    delta_fi = (lat2 - lat1) * math.pi / 180
    delta_lambda = (lon2 - lon1) * math.pi / 180

    # Формула Хаверсина
    a = math.sin(delta_fi/2)**2 + math.cos(fi1) * math.cos(fi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c                # Расчет расстояния
    return distance

# Основной маршрут API, возвращающий все рассчитанные данные
@app.get("/get_all_data")
async def get_all_data(data: List[PointDict]):
    """
    Возвращает словарь с результатами расчетов расстояний, максимальной скорости,
    средней скорости и средней угловой скорости поворота.
    :param data: Список объектов с данными о точках
    :return: Словарь с расчетными значениями
    """
    results = {}
    results.update(await get_distance(data))
    results.update(await get_max_speed(data))
    results.update(await get_average_speed(data))
    results.update(await get_average_speed_turn(data))
    return results

# Маршрут для получения общего пройденного расстояния
@app.get("/get_distance")
async def get_distance(data: List[PointDict]):
    """
    Рассчитывает общее пройденное расстояние между всеми точками.
    :param data: Список объектов с данными о точках
    :return: Словарь с общим расстоянием
    """
    res = {'distance': 0}
    if len(data) < 2:
        return res

    sorted_data = sorted(data, key=lambda x: x['timestamp'])
    for i in range(1, len(sorted_data)):
        dist = await haversine(sorted_data[i - 1]['lat'], sorted_data[i - 1]['lon'],
                               sorted_data[i]['lat'], sorted_data[i]['lon'])
        res['distance'] += dist

    return res

# Маршрут для получения максимальной скорости
@app.get("/get_max_speed")
async def get_max_speed(data: List[PointDict]):
    """
    Находит максимальную скорость между любыми двумя соседними точками.
    :param data: Список объектов с данными о точках
    :return: Словарь с максимальным значением скорости
    """
    res = {'max_speed': 0}
    if len(data) < 2:
        return res

    sorted_data = sorted(data, key=lambda x: x['timestamp'])
    for i in range(1, len(sorted_data)):
        speed = await haversine(sorted_data[i - 1]['lat'], sorted_data[i - 1]['lon'],
                                sorted_data[i]['lat'], sorted_data[i]['lon'])
        time_diff = sorted_data[i]['timestamp'] - sorted_data[i - 1]['timestamp']
        current_speed = speed / time_diff
        if current_speed > res['max_speed']:
            res['max_speed'] = current_speed

    return res

# Маршрут для получения средней скорости
@app.get("/get_average_speed")
async def get_average_speed(data: List[PointDict]):
    """
    Рассчитывает среднюю скорость движения за весь период.
    :param data: Список объектов с данными о точках
    :return: Словарь со средним значением скорости
    """
    res = {'average_speed': 0}
    if len(data) < 2:
        return res

    total_dist = (await get_distance(data))['distance']
    first_timestamp = data[0]['timestamp']
    last_timestamp = data[-1]['timestamp']
    total_time = last_timestamp - first_timestamp
    average_speed = total_dist / total_time
    res['average_speed'] = average_speed

    return res

# Маршрут для получения среднего значения угловой скорости при поворотах
@app.get("/get_average_speed_turn")
async def get_average_speed_turn(data: List[PointDict]):
    """
    Рассчитывает среднее значение угловой скорости при изменении направления движения.
    :param data: Список объектов с данными о точках
    :return: Словарь со средним значением угловой скорости
    """
    res = {'average_speed_turn': 0}
    if len(data) < 3:
        return res

    sorted_data = sorted(data, key=lambda x: x['timestamp'])
    total_angle_change = 0
    for i in range(2, len(sorted_data)):
        # Векторные компоненты скоростей между предыдущими и последующими точками
        v1_lat = ((sorted_data[i - 1]['lat'] - sorted_data[i - 2]['lat']) * R /
                  (sorted_data[i - 1]['timestamp'] - sorted_data[i - 2]['timestamp']))
        v1_lon = ((sorted_data[i - 1]['lon'] - sorted_data[i - 2]['lon']) * R /
                  (sorted_data[i - 1]['timestamp'] - sorted_data[i - 2]['timestamp']))
        
        v2_lat = ((sorted_data[i]['lat'] - sorted_data[i - 1]['lat']) * R /
                  (sorted_data[i]['timestamp'] - sorted_data[i - 1]['timestamp']))
        v2_lon = ((sorted_data[i]['lon'] - sorted_data[i - 1]['lon']) * R /
                  (sorted_data[i]['timestamp'] - sorted_data[i - 1]['timestamp']))

        # Модули скоростей
        v1_abs = math.sqrt(v1_lon**2 + v1_lat**2)
        v2_abs = math.sqrt(v2_lon**2 + v2_lat**2)
        if v1_abs == 0 or v2_abs == 0:
            continue

        # Угол между скоростями
        dot_product = v1_lon * v2_lon + v1_lat * v2_lat
        cos_theta = dot_product / (v1_abs * v2_abs)
        theta = math.pi - math.acos(cos_theta)

        # Накопление углового смещения
        total_angle_change += theta / (sorted_data[i]['timestamp'] - sorted_data[i - 1]['timestamp'])

    avg_speed_turn = total_angle_change / (sorted_data[-1]['timestamp'] - sorted_data[1]['timestamp'])
    res['average_speed_turn'] = avg_speed_turn

    return res
'''
)
``` 

После этого можно будет создать pull request с изменениями. Теперь файл `main.py` содержит более подробные комментарии и улучшенную документацию. 

READY_FOR_PR.