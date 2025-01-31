import csv
import requests
data = []
with open('task_18.csv', 'rt') as f:
    reader = csv.DictReader(f)
    for line in reader:
        data.append(line)
"""data2 = [
            {
                'timestamp': 124142,
                'lat': 9.1472222222222222222222222222222,
                'lon': },
            {
                'timestamp': 124322,
                'lat': ,
                'lon':
            }
]"""
re = requests.get("http://localhost:8000/get_all_data", json=data)
print(re.content)