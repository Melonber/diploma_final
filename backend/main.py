from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
from datetime import datetime
import time
import random
from urllib.parse import unquote
from identify_atack import check_request
import psutil
import json
from pydantic import BaseModel
from typing import Optional

# Создаем экземпляр приложения FastAPI
app = FastAPI()

# Добавляем CORS middleware для поддержки кросс-доменных запросов
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Класс модели для данных, которые получаем через POST-запрос
class PredictionData(BaseModel):
    prediction: str

# Переменная для хранения последнего предсказания
latest_prediction: Optional[str] = None
# Хранилище логов запросов
request_logs = []
suspect_log = []
request_time = []
anomalies = []
users_online_history = []
prediction_online = []
def log_request(req: Request):
    now = datetime.now().strftime("%d/%b/%Y %H:%M:%S")
    log_entry = f"{req.client.host} - - [{now}] \"{req.method} {req.url.path}?{req.url.query} HTTP/1.1\" 200"
    print(log_entry)
    request_logs.append(log_entry)

    # Запись лога в файл
    with open('/Users/aydyn/Desktop/diplom/web_service/logs.txt', 'a') as f:
        f.write(f'{log_entry}\n')

    # Проход по списку запросов и проверка на наличие URL-экранированных символов
    for log in request_logs:
        # Декодируем лог
        decoded_log = unquote(log)

        # Ищем начальную позицию "symbol=" и конечную позицию "HTTP/1.1"
        symbol_start = decoded_log.find('symbol=') + len('symbol=')
        http_start = decoded_log.find(' HTTP/1.1')

        # Если обе позиции найдены, извлекаем часть строки между ними
        if symbol_start != -1 and http_start != -1:
            symbol_value = decoded_log[symbol_start:http_start]

            # Добавляем найденное значение в suspect_log
            attack_type = check_request(symbol_value)
            print(attack_type)
            if attack_type != "normal_request":
                if (decoded_log + f' 💉 Type of attack: {attack_type} 💉') not in suspect_log:
                    suspect_log.append(decoded_log + f' 💉 Type of attack: {attack_type} 💉')
                    with open('/Users/aydyn/Desktop/diplom/web_service/suspect_logs/suspect_logs.txt', 'a') as f:
                        f.write(f'{decoded_log}\n')

# Обработчик маршрута для получения данных о криптовалютах
@app.get("/api/cryptos")
async def get_cryptos(request: Request, symbol: str = None):
    start_time = time.time()
    log_request(request)  # Логируем запрос

    if symbol:
        response = requests.get('https://api.coingecko.com/api/v3/coins/markets', params={
            'vs_currency': 'usd',
            'symbols': symbol.lower()
        })
        cryptos = response.json()
        end_time = time.time()
        request_time.append(round(end_time - start_time, 2))

        if cryptos:
            return JSONResponse(content=cryptos[0])
        else:
            return JSONResponse(content={"error": "Cryptocurrency not found"}, status_code=404)
    else:
        # Если символ не указан, возвращаем топ-20 криптовалют
        response = requests.get('https://api.coingecko.com/api/v3/coins/markets', params={
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': 20,
            'page': 1
        })
        end_time = time.time()
        request_time.append(round(end_time - start_time, 2))
        return JSONResponse(content=response.json())


# Обработчик маршрута для получения логов запросов
@app.get("/api/logs")
async def get_logs():
    return JSONResponse(content=request_logs)

# Обработчик маршрута для удаления логов запросов
@app.delete("/api/logs")
async def delete_logs():
    request_logs.clear()
    return JSONResponse(content={"message": "All logs have been deleted"})

# Обработчик маршрута для получения подозрительных логов запросов
@app.get("/api/suspectlogs")
async def get_suspect():
    return JSONResponse(content=suspect_log)

# Обработчик маршрута для получения времени отклика
@app.get("/api/time-response")
async def get_time():
    return JSONResponse(content=request_time)

# Генерация данных для графика
def generate_chart_data():
    now = datetime.now()
    data = {
        "time": now.strftime("%H:%M:%S"),
        "value": random.randint(500, 1000)
    }
    return data

# Обработчик маршрута для получения данных для графика
@app.get("/api/chart-data")
async def chart_data():
    data = generate_chart_data()
    return JSONResponse(content=data)

# Обработчик маршрута для получения данных о загрузке CPU
@app.get("/api/cpu")
async def get_cpu_data():
    cpu_usage = psutil.cpu_percent(interval=1)
    timestamp = datetime.now().strftime('%H:%M:%S')
    data = {
        'cpu_usage': [cpu_usage],
        'timestamps': [timestamp]
    }
    csv_line = f"{cpu_usage}, {timestamp}\n"
    # Открываем файл в режиме добавления и сохраняем строку CSV
    with open('/Users/aydyn/Desktop/diplom/web_service/cpu_data.txt', 'a') as f:
        f.write(csv_line)
    return JSONResponse(content=data)


@app.post("/api/cpu_anomalies")
async def receive_anomalies(request: Request):
    data = await request.json()
    # Сохраняем полученные аномалии в структуре данных или базе данных
    # Например, в список или другую структуру для дальнейшего использования
      # Это пример, используйте свою структуру данных

    anomalies.extend(data)

    # Сохраните данные в `anomalies` или используйте другую логику обработки данных
    return JSONResponse({"message": "Anomalies received successfully."})
@app.get("/api/cpu_anomalies")
async def get_anomalies():
    # Возвращаем текущие аномалии в JSON-формате
    return JSONResponse(content=anomalies)


@app.get("/api/users-online")
async def get_users_online():
    # Получаем текущее время в формате часов и минут
    current_time = datetime.now().strftime("%H:%M")

    # Генерируем случайное количество пользователей онлайн
    users_online = random.randint(1, 1000)

    # Формируем запись с текущим временем и количеством пользователей онлайн
    data = {
        "time": current_time,
        "users_online": users_online
    }

    # Добавляем новую запись в историю
    users_online_history.append(data)

    # Сохраняем запись в файл
    with open("/Users/aydyn/Desktop/diplom/web_service/online_users.txt", 'a') as file:
        file.write(f"{current_time}, {users_online}\n")

    # Возвращаем JSON-ответ с данными о времени и количестве пользователей онлайн
    return JSONResponse(content=data)


@app.get("/api/users-online-history")
async def get_users_online_history():
    # Возвращаем историю количества онлайн-пользователей
    return JSONResponse(content=users_online_history)


@app.post("/api/prediction_online")
async def receive_prediction(data: PredictionData):
    global latest_prediction
    # Получаем предсказание из данных POST-запроса
    latest_prediction = data.prediction

    # Записываем предсказание в текстовый файл
    with open("predictions.txt", "a") as file:
        file.write(f"{data.prediction}\n")

    # Возвращаем сообщение о том, что предсказание успешно получено
    return {"message": "Prediction received successfully."}


@app.get("/api/prediction_online")
async def get_latest_prediction():
    global latest_prediction
    # Возвращаем последнее предсказание
    if latest_prediction is not None:
        return {"latest_prediction": latest_prediction}
    else:
        # Если предсказание еще не было получено
        raise HTTPException(status_code=404, detail="No prediction available.")


if __name__ == '__main__':
    # Запускаем приложение FastAPI
    import uvicorn
    uvicorn.run(app, host="localhost", port=5000)
