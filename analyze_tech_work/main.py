from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import LinearRegression
from pyspark.sql.functions import col, mean
from pyspark.sql.window import Window
import time
import requests


def send_prediction_to_api(prediction):
    # URL API для отправки POST-запроса
    api_url = "http://localhost:5000/api/prediction_online"

    # Подготовка данных для отправки в POST-запросе
    data = {
        "prediction": "high" if prediction >= threshold else "low"
    }

    # Отправка POST-запроса на API
    response = requests.post(api_url, json=data)

    # Проверка успешности запроса
    if response.status_code == 200:
        print(f"Предсказание {data['prediction']} успешно отправлено на API.")
    else:
        print(f"Ошибка при отправке предсказания: {response.status_code} - {response.text}")


# Основной цикл программы
while True:
    # Создание Spark-сессии
    spark = SparkSession.builder \
        .appName("OnlinePrediction") \
        .getOrCreate()

    # Определение пути к файлу данных
    input_path = "/Users/aydyn/Desktop/diplom/web_service/online_users.txt"

    # Чтение данных из файла
    data_stream = spark.read.option("header", "true") \
        .option("delimiter", ",") \
        .option("inferSchema", "true") \
        .csv(input_path)

    # Убедитесь, что столбец времени представлен в формате timestamp
    data_stream = data_stream.withColumn("time", col("time").cast("timestamp"))

    # Создание окна времени длиной 5 минут
    time_window = Window.orderBy(col('time').cast('long')).rangeBetween(-300, -1)

    # Рассчитайте среднюю активность за предыдущие 5 минут
    data_stream = data_stream.withColumn(
        'avg_activity_last_5_minutes',
        mean(col('online')).over(time_window)
    )

    # Создание окна для расчета средней активности в следующие 5 минут
    future_window = Window.orderBy(col('time').cast('long')).rangeBetween(0, 300)

    # Рассчитайте среднюю активность в следующие 5 минут
    data_stream = data_stream.withColumn(
        'avg_activity_next_5_minutes',
        mean(col('online')).over(future_window)
    )

    # Удаление строк с `null` значениями в данных
    data_stream = data_stream.dropna(subset=['avg_activity_last_5_minutes', 'avg_activity_next_5_minutes'])

    # Разделение данных на тренировочный и тестовый наборы
    (trainingData, testData) = data_stream.randomSplit([0.8, 0.2], seed=42)

    # Преобразование данных в векторные столбцы
    assembler = VectorAssembler(inputCols=['avg_activity_last_5_minutes'], outputCol='features')
    trainingData = assembler.transform(trainingData)
    testData = assembler.transform(testData)

    # Создание и обучение модели линейной регрессии для предсказания средней активности в следующие 5 минут
    lr = LinearRegression(featuresCol='features', labelCol='avg_activity_next_5_minutes')
    lr_model = lr.fit(trainingData)

    # Использование модели для предсказания на тестовом наборе
    predictions = lr_model.transform(testData)

    # Установите порог для определения низкой активности. Например, 30.0
    threshold = 30.0

    # Получение последнего предсказанного значения
    latest_prediction = predictions.orderBy(col("time").desc()).first()

    # Определение уровня активности
    if latest_prediction["prediction"] < threshold:
        prediction_result = "low"
    else:
        prediction_result = "high"

    # Вывод сообщения о низкой или высокой активности
    print(f"В ближайшие 5 минут ожидается {prediction_result} активность.")

    # Отправка предсказания на API
    send_prediction_to_api(latest_prediction["prediction"])

    # Закрытие Spark-сессии
    spark.stop()

    # Задержка на 5 минут перед следующей итерацией
    time.sleep(300)
