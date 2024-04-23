from pyspark.sql import SparkSession
from pyspark.sql.functions import col, regexp_extract, desc
import time
# Создаем сессию Spark
spark = SparkSession.builder \
    .appName("CryptoRequestAnalyzer") \
    .getOrCreate()

while True:
    time.sleep(10)
    # Путь к файлу логов
    log_file_path = "/Users/aydyn/Desktop/diplom/web_service/logs.txt"

    # Читаем данные из файла в формате текстовых строк
    logs_df = spark.read.text(log_file_path)

    # Регулярное выражение для извлечения криптовалютного запроса из строки лога
    regex_pattern = r'GET /api/cryptos\?symbol=([a-zA-Z0-9]+)'

    # Извлекаем символ криптовалюты из строки лога
    logs_df = logs_df.withColumn("crypto_symbol", regexp_extract(col("value"), regex_pattern, 1))

    # Фильтруем строки, чтобы оставались только те, которые содержат запросы по криптовалюте
    crypto_requests_df = logs_df.filter(logs_df.crypto_symbol != "")

    # Группируем по символу криптовалюты и подсчитываем количество запросов для каждого символа
    crypto_requests_count_df = crypto_requests_df.groupBy("crypto_symbol").count()

    # Находим самый частый запрос по криптовалюте
    most_frequent_request = crypto_requests_count_df.orderBy(desc("count")).first()

    # Выводим результат
    print(f"The most popular crypto request is: {most_frequent_request['crypto_symbol']} with {most_frequent_request['count']} requests.")


