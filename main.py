import math
import logging
from typing import List
from typing_extensions import TypedDict

from fastapi import FastAPI

R = 6371e3  # Радиус Земли в метрах

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class PointDict(TypedDict):
    timestamp: int
    lat: float
    lon: float

async def haversine(lat1, lon1, lat2, lon2):
    logger.debug("Calculating Haversine distance between points.")
    fi1 = lat1 * math.pi / 180
    fi2 = lat2 * math.pi / 180
    delta_fi = (lat2 - lat1) * math.pi / 180
    delta_lambda = (lon2 - lon1) * math.pi / 180

    a = math.sin(delta_fi/2)**2 + math.cos(fi1) * math.cos(fi2) * \\
        math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    d = R * c
    return d

@app.get("/get_all_data")
async def get_all_data(data: List[PointDict]):
    try:
        results = {
            **(await get_distance(data)),
            **(await get_max_speed(data)),
            **(await get_average_speed(data)),
            **(await get_average_speed_turn(data))
        }
        logger.info("Successfully calculated all metrics.")
        return results
    except Exception as e:
        logger.error(f"Error calculating all metrics: {e}")
        raise

@app.get("/get_distance")
async def get_distance(data: List[PointDict]):
    logger.info("Starting calculation of total distance.")
    res = {'distance': 0}
    if len(data) < 2:
        logger.warning("Insufficient data points to calculate distance.")
        return res

    data = sorted(data, key=lambda x: x['timestamp'])
    for i in range(1, len(data)):
        dist = await haversine(data[i - 1]['lat'], data[i - 1]['lon'],
                               data[i]['lat'], data[i]['lon'])
        res['distance'] += dist
        logger.debug(f"Added segment distance: {dist:.2f}m")

    logger.info(f"Total distance calculated: {res['distance']:.2f}m")
    return res

@app.get("/get_max_speed")
async def get_max_speed(data: List[PointDict]):
    logger.info("Starting calculation of maximum speed.")
    res = {'max_speed': 0}
    if len(data) < 2:
        logger.warning("Insufficient data points to calculate max speed.")
        return res

    data = sorted(data, key=lambda x: x['timestamp'])
    for i in range(1, len(data)):
        s = await haversine(data[i - 1]['lat'], data[i - 1]['lon'],
                            data[i]['lat'], data[i]['lon'])
        t = data[i]['timestamp'] - data[i - 1]['timestamp']
        current_speed = s / t
        if res['max_speed'] < current_speed:
            res['max_speed'] = current_speed
            logger.debug(f"Updated max speed: {current_speed:.2f}m/s")

    logger.info(f"Maximum speed found: {res['max_speed']:.2f}m/s")
    return res

@app.get("/get_average_speed")
async def get_average_speed(data: List[PointDict]):
    logger.info("Starting calculation of average speed.")
    res = {'average_speed': 0}
    if len(data) < 2:
        logger.warning("Insufficient data points to calculate avg speed.")
        return res

    data = sorted(data, key=lambda x: x['timestamp'])
    total_dist = (await get_distance(data))['distance']
    total_time = data[-1]['timestamp'] - data[0]['timestamp']
    res['average_speed'] = total_dist / total_time

    logger.info(f"Average speed calculated: {res['average_speed']:.2f}m/s")
    return res

@app.get("/get_average_speed_turn")
async def get_average_speed_turn(data: List[PointDict]):
    logger.info("Starting calculation of average turn speed.")
    res = {'average_speed_turn': 0}
    if len(data) < 3:
        logger.warning("Insufficient data points to calculate avg turn speed.")
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
        v2lon = ((data[i]['lon'] - data[i - 1]['lon']) * R/
                 (data[i]['timestamp'] - data[i - 1]['timestamp']))

        v1abs = math.sqrt(v1lon**2 + v1lat**2)
        v2abs = math.sqrt(v2lon**2 + v2lat**2)
        if v1abs == 0 or v2abs == 0:
            continue

        angle = math.pi - math.acos((v1lon * v2lon + v1lat * v2lat) /
                                    (v1abs * v2abs))

        fi += angle / (data[i]['timestamp'] - data[i - 1]['timestamp'])

    res['average_speed_turn'] = fi / (data[-1]['timestamp'] - data[1]['timestamp'])
    logger.info(f"Average turn speed calculated: {res['average_speed_turn']:.2f}rads/s")
    return res
"""
Расстояние Хаверсина в метрах
"""
@app.get("/get_distance")
async def get_distance(data: List[PointDict]):
    res = {'distance': 0}
    if len(data) < 2:
        return res

    data = list(sorted(data, key=lambda x: x['timestamp']))
    for i in range(1, len(data)):
        res['distance'] += await haversine(data[i - 1]['lat'], data[i - 1]['lon'],
                                           data[i]['lat'], data[i]['lon'])

    return res


"""
Максимальная скорость среди всех последовательных пар точек
"""
@app.get("/get_max_speed")
async def get_max_speed(data: List[PointDict]):
    res = {'max_speed': 0}
    if len(data) < 2:
        return res

    data = list(sorted(data, key=lambda x: x['timestamp']))
    for i in range(1, len(data)):
        s = await haversine(data[i - 1]['lat'], data[i - 1]['lon'],
                            data[i]['lat'], data[i]['lon'])
        t = data[i]['timestamp'] - data[i - 1]['timestamp']
        if res['max_speed'] < s / t:
            res['max_speed'] = s / t
    return res


"""
Средняя скорость s/t
"""
@app.get("/get_average_speed")
async def get_average_speed(data: List[PointDict]):
    res = {'average_speed': 0}
    if len(data) < 2:
        return res

    data = list(sorted(data, key=lambda x: x['timestamp']))
    s = (await get_distance(data))['distance']
    t = data[-1]['timestamp'] - data[0]['timestamp']
    res['average_speed'] = s / t

    return res


"""
Средняя скорость в повороте - скорость изменения угла вектора скорости
"""
@app.get("/get_average_speed_turn")
async def get_average_speed_turn(data: List[PointDict]):
    res = {'average_speed_turn': 0}
    if len(data) < 3:
        return res

    data = list(sorted(data, key=lambda x: x['timestamp']))
    fi = 0
    for i in range(2, len(data)):
        v1lat = ((data[i - 1]['lat'] - data[i - 2]['lat']) * R /
                 (data[i - 1]['timestamp'] - data[i - 2]['timestamp']))
        v1lon = ((data[i - 1]['lon'] - data[i - 2]['lon']) * R /
                 (data[i - 1]['timestamp'] - data[i - 2]['timestamp']))
        v2lat = ((data[i]['lat'] - data[i - 1]['lat']) * R /
                 (data[i]['timestamp'] - data[i - 1]['timestamp']))
        v2lon = ((data[i]['lon'] - data[i - 1]['lon']) * R/
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
""",
    repo_full_name="Kokande/geoProjFastAPI"
}