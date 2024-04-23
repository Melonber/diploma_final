from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_timestamp
import requests
import time

# Создаем сессию Spark
spark = SparkSession.builder.getOrCreate()

# Определяем пороги для аномалий
minimum = 3
maximum = 50

# Путь к файлу с данными о загрузке CPU
file_path = "/Users/aydyn/Desktop/diplom/web_service/cpu_data.txt"

# URL FastAPI сервера для отправки аномалий
fastapi_url = "http://localhost:5000/api/cpu_anomalies"

# Инициализация глобального списка отправленных аномалий
sent_anomalies = []

# Начальная загрузка данных о загрузке CPU
df_previous = spark.read.option("header", "true") \
    .option("delimiter", ",") \
    .option("inferSchema", "true") \
    .csv(file_path)

# Преобразуем столбец `time` в тип `timestamp`
df_previous = df_previous.withColumn("time", to_timestamp(col("time"), "yyyy-MM-dd HH:mm:ss"))

# Отслеживание последней строки
last_index = df_previous.count()

# Функция для проверки данных и отправки новых аномалий
def check_for_anomalies():
    global last_index
    global sent_anomalies

    # Считываем текущие данные о загрузке CPU
    df_current = spark.read.option("header", "true") \
        .option("delimiter", ",") \
        .option("inferSchema", "true") \
        .csv(file_path)

    # Преобразуем столбец `time` в тип `timestamp`
    df_current = df_current.withColumn("time", to_timestamp(col("time"), "yyyy-MM-dd HH:mm:ss"))

    # Сравниваем количество строк в новом DataFrame
    current_count = df_current.count()

    # Если появились новые строки, проверяем их на аномалии
    if current_count > last_index:
        # Получаем новые данные о загрузке CPU
        new_data = df_current.filter((col("Cpu_data") < minimum) | (col("Cpu_data") > maximum)).tail(current_count - last_index)

        # Проверяем новые аномалии, только если они есть
        if new_data:
            anomalies_to_send = []

            for row in new_data:
                anomaly = {
                    "time": row["time"].strftime('%Y-%m-%d %H:%M:%S'),
                    "Cpu_data": row["Cpu_data"]
                }

                # Отправляем аномалию только если она еще не была отправлена
                if anomaly not in sent_anomalies:
                    anomalies_to_send.append(anomaly)
                    sent_anomalies.append(anomaly)  # Добавляем аномалию в список отправленных

            # Отправляем новые аномалии на FastAPI сервер
            if anomalies_to_send:
                response = requests.post(fastapi_url, json=anomalies_to_send)

                if response.status_code == 200:
                    print("Anomalies sent successfully.")
                else:
                    print(f"Failed to send anomalies. Status code: {response.status_code}")

        # Обновляем последний индекс
        last_index = current_count

while True:
    check_for_anomalies()
    time.sleep(5)
