import math
from typing import List
from typing_extensions import TypedDict

from fastapi import FastAPI

R = 6371e3  # Радиус Земли в метрах
app = FastAPI()


class PointDict(TypedDict):
    timestamp: int
    lat: float
    lon: float


async def haversine(lat1, lon1, lat2, lon2):
    """Вычисляет расстояние между двумя точками по формуле Хаверсина."""
    fi1 = lat1 * math.pi / 180
    fi2 = lat2 * math.pi / 180
    delta_fi = (lat2 - lat1) * math.pi / 180
    delta_lambda = (lon2 - lon1) * math.pi / 180

    a = math.sin(delta_fi/2)**2 + math.cos(fi1) * math.cos(fi2) * \\
        math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    d = R * c
    return d


@app.get(
    "/get_all_data",
    description="Возвращает все данные о расстоянии, максимальной скорости, средней скорости и средней скорости поворота."
)
async def get_all_data(data: List[PointDict]):
    return {
        **(await get_distance(data)),
        **(await get_max_speed(data)),
        **(await get_average_speed(data)),
        **(await get_average_speed_turn(data))
    }


@app.get(
    "/get_distance",
    description="Рассчитывает общее пройденное расстояние между всеми точками данных."
)
async def get_distance(data: List[PointDict]):
    """
    Расстояние Хаверсина в метрах.
    Возвращает объект с полем distance — общим расстоянием между всеми точками.
    """
    res = {'distance': 0}
    if len(data) < 2:
        return res

    data = sorted(data, key=lambda x: x['timestamp'])
    for i in range(1, len(data)):
        res['distance'] += await haversine(data[i - 1]['lat'], data[i - 1]['lon'],
                                           data[i]['lat'], data[i]['lon'])

    return res


@app.get(
    "/get_max_speed",
    description="Находит максимальную скорость среди всех последовательных пар точек."
)
async def get_max_speed(data: List[PointDict]):
    """
    Максимальная скорость среди всех последовательных пар точек.
    Возвращает объект с полем max_speed — наибольшей скоростью.
    """
    res = {'max_speed': 0}
    if len(data) < 2:
        return res

    data = sorted(data, key=lambda x: x['timestamp'])
    for i in range(1, len(data)):
        s = await haversine(data[i - 1]['lat'], data[i - 1]['lon'],
                            data[i]['lat'], data[i]['lon'])
        t = data[i]['timestamp'] - data[i - 1]['timestamp']
        speed = s / t
        if res['max_speed'] < speed:
            res['max_speed'] = speed
    return res


@app.get(
    "/get_average_speed",
    description="Рассчитывает среднюю скорость движения."
)
async def get_average_speed(data: List[PointDict]):
    """
    Средняя скорость s/t.
    Возвращает объект с полем average_speed — средним значением скорости.
    """
    res = {'average_speed': 0}
    if len(data) < 2:
        return res

    data = sorted(data, key=lambda x: x['timestamp'])
    total_distance = (await get_distance(data))['distance']
    time_difference = data[-1]['timestamp'] - data[0]['timestamp']
    res['average_speed'] = total_distance / time_difference

    return res


@app.get(
    "/get_average_speed_turn",
    description="Рассчитывает среднюю скорость изменения направления движения."
)
async def get_average_speed_turn(data: List[PointDict]):
    """
    Средняя скорость в повороте - скорость изменения угла вектора скорости.
    Возвращает объект с полем average_speed_turn — средним изменением угла за единицу времени.
    """
    res = {'average_speed_turn': 0}
    if len(data) < 3:
        return res

    data = sorted(data, key=lambda x: x['timestamp'])
    fi = 0
    for i in range(2, len(data)):
        v1lat = ((data[i - 1]['lat'] - data[i - 2]['lat']) * R /
                 (data[i - 1]['timestamp'] - data[i - 2]['timestamp']))
        v1lon = ((data[i - 1]['lon'] - data[i - 2]['lon']) * R /
                 (data[i - 1]['timestamp'] - data[i - 2]['timestamp']))
        v2lat = ((data[i]['lat'] - data[i - 1]['lat']) * R /
                 (data[i]['timestamp'] - data[i - 1]['timestamp']))
        v2lon = ((data[i]['lon'] - data[i - 1]['lon']) * R /
                 (data[i]['timestamp'] - data[i - 1]['timestamp']))

        v1abs = math.sqrt(v1lon**2 + v1lat**2)
        v2abs = math.sqrt(v2lon**2 + v2lat**2)
        if v1abs == 0 or v2abs == 0:
            continue

        angle = math.pi - math.acos((v1lon * v2lon + v1lat * v2lat) /
                                    (v1abs * v2abs))

        fi += angle / (data[i]['timestamp'] - data[i - 1]['timestamp'])

    res['average_speed_turn'] = fi / (data[-1]['timestamp'] - data[1]['timestamp'])
    return res