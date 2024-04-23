from pyspark.sql import SparkSession
from pyspark.sql.functions import split, col, concat_ws, expr

# Создание Spark-сессии
spark = SparkSession.builder \
    .appName("Suspect Request Tracking") \
    .getOrCreate()

# Определяем путь к директории, содержащей suspect_logs.txt
log_dir_path = "/Users/aydyn/Desktop/diplom/web_service/suspect_logs"

# Интервал обработки
processing_interval = "5 seconds"

# Чтение данных из директории с использованием structured streaming
stream_df = spark.readStream \
    .format("text") \
    .option("path", log_dir_path) \
    .option("maxFilesPerTrigger", 1)  # Чтение одного файла за раз
    .load()

# Разделение строк данных на отдельные поля
stream_df = stream_df.withColumn("parts", split(col("value"), " "))

# Извлечение необходимых полей из массива частей строки
stream_df = stream_df.withColumn("ip_address", col("parts").getItem(0)) \
    .withColumn("timestamp", concat_ws(' ', col("parts")[3], col("parts")[4])) \
    .withColumn("request", concat_ws(' ', col("parts")[5], col("parts")[6], col("parts")[7], col("parts")[8])) \
    .withColumn("status_code", col("parts").getItem(9).cast("int"))

# Реакция на каждую новую запись: вывод ее на консоль
stream_query = stream_df.writeStream \
    .outputMode("append") \
    .format("console") \
    .trigger(processingTime=processing_interval) \
    .start()

# Ожидание завершения потоковой обработки
stream_query.awaitTermination()
