import math
from typing import List
from typing_extensions import TypedDict

from fastapi import FastAPI

# Константа радиуса Земли в метрах
R = 6371e3  
app = FastAPI()

# Типизированный словарь для хранения информации о точке
class PointDict(TypedDict):
    timestamp: int   # Время отметки точки
    lat: float       # Широта
    lon: float       # Долгота

# Функция расчета расстояния между двумя точками по методу Хаверсину
async def haversine(lat1, lon1, lat2, lon2):
    """
    Вычисляет расстояние между двумя географическими координатами 
    используя формулу Хаверсину.
    """
    # Преобразование градусов в радианы
    fi1 = lat1 * math.pi / 180
    fi2 = lat2 * math.pi / 180
    delta_fi = (lat2 - lat1) * math.pi / 180
    delta_lambda = (lon2 - lon1) * math.pi / 180

    # Формула Хаверсину
    a = math.sin(delta_fi/2)**2 + math.cos(fi1) * math.cos(fi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    # Расстояние в метрах
    d = R * c
    return d

# Основной маршрут API, возвращает все данные сразу
@app.get("/get_all_data")
async def get_all_data(data: List[PointDict]):
    """
    Возвращает полный набор метрик: общее расстояние, максимальную скорость, среднюю скорость и среднюю угловую скорость поворота.
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
    Рассчитывает суммарное расстояние между всеми точками маршрута.
    """
    res = {'distance': 0}
    if len(data) < 2:
        return res

    # Сортируем точки по времени
    sorted_data = sorted(data, key=lambda x: x['timestamp'])
    for i in range(1, len(sorted_data)):
        # Суммируем расстояния между соседними точками
        res['distance'] += await haversine(sorted_data[i - 1]['lat'], sorted_data[i - 1]['lon'],
                                           sorted_data[i]['lat'], sorted_data[i]['lon'])
    return res

# Маршрут для максимальной скорости
@app.get("/get_max_speed")
async def get_max_speed(data: List[PointDict]):
    """
    Находит максимальную мгновенную скорость между любыми двумя последовательными точками.
    """
    res = {'max_speed': 0}
    if len(data) < 2:
        return res

    # Сортируем точки по времени
    sorted_data = sorted(data, key=lambda x: x['timestamp'])
    for i in range(1, len(sorted_data)):
        # Расчет расстояния и времени между точками
        distance = await haversine(sorted_data[i - 1]['lat'], sorted_data[i - 1]['lon'],
                                   sorted_data[i]['lat'], sorted_data[i]['lon'])
        time_diff = sorted_data[i]['timestamp'] - sorted_data[i - 1]['timestamp']
        speed = distance / time_diff
        
        # Обновляем максимум скорости
        if res['max_speed'] < speed:
            res['max_speed'] = speed
    return res

# Маршрут для средней скорости
@app.get("/get_average_speed")
async def get_average_speed(data: List[PointDict]):
    """
    Рассчитывает среднюю скорость за весь путь.
    """
    res = {'average_speed': 0}
    if len(data) < 2:
        return res

    # Сортируем точки по времени
    sorted_data = sorted(data, key=lambda x: x['timestamp'])
    total_distance = (await get_distance(data))['distance']
    total_time = sorted_data[-1]['timestamp'] - sorted_data[0]['timestamp']
    average_speed = total_distance / total_time
    res['average_speed'] = average_speed
    return res

# Маршрут для средней угловой скорости поворота
@app.get("/get_average_speed_turn")
async def get_average_speed_turn(data: List[PointDict]):
    """
    Рассчитывает среднюю угловую скорость поворота (изменение направления движения).
    """
    res = {'average_speed_turn': 0}
    if len(data) < 3:
        return res

    # Сортируем точки по времени
    sorted_data = sorted(data, key=lambda x: x['timestamp'])
    fi_sum = 0
    for i in range(2, len(sorted_data)):
        # Скорости по широте и долготе
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
        cos_angle = dot_product / (v1_abs * v2_abs)
        angle = math.pi - math.acos(cos_angle)

        # Накопление суммы углового отклонения
        fi_sum += angle / (sorted_data[i]['timestamp'] - sorted_data[i - 1]['timestamp'])

    # Средняя угловая скорость
    avg_speed_turn = fi_sum / (sorted_data[-1]['timestamp'] - sorted_data[1]['timestamp'])
    res['average_speed_turn'] = avg_speed_turn
    return res
 '''
,
    repo_full_name="Kokande/geoProjFastAPI"
)
``` 

После этого можно будет создать Pull Request для проверки изменений. Готово. 

READY_FOR_PR. 