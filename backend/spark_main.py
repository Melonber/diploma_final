from pyspark import SparkContext
from pyspark.streaming import StreamingContext
from collections import Counter
from threading import Timer
import matplotlib.pyplot as plt

# Создаем контекст Spark и Streaming
sc = SparkContext(appName="CryptoLogAnalysis")
ssc = StreamingContext(sc, 1)  # Интервал в 1 секунду

# Чтение данных из файла logs.txt
lines = ssc.textFileStream("logs.txt")

# Фильтрация строк и подсчет количества запросов для каждой криптовалюты
def process_line(line):
    # Найдем запрос криптовалюты в строке
    start_idx = line.find("/api/cryptos?symbol=")
    if start_idx != -1:
        end_idx = line.find(" ", start_idx)
        symbol = line[start_idx + len("/api/cryptos?symbol="):end_idx]
        return symbol
    return None

# Применение функции к каждой строке
symbols = lines.map(process_line).filter(lambda x: x is not None)

# Подсчет количества запросов для каждой криптовалюты
counts = Counter()

def update_counts(rdd):
    for symbol in rdd.collect():
        counts[symbol] += 1

# Применение функции для обновления счетчиков к каждой партии RDD
symbols.foreachRDD(update_counts)

# Функция для обновления графика в основном потоке
def update_graph():
    plt.clf()
    plt.bar(counts.keys(), counts.values())
    plt.xlabel('Криптовалюты')
    plt.ylabel('Количество запросов')
    plt.title('Популярность криптовалют в реальном времени')
    plt.pause(1)  # Обновление каждые 1 секунду

# Таймер для периодического обновления графиков в основном потоке
def timer_update():
    update_graph()
    Timer(1, timer_update).start()

# Запуск таймера обновления графиков
timer_update()

# Запуск стриминга
ssc.start()
ssc.awaitTermination()
