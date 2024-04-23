from flask import Flask, request, jsonify
import time

app = Flask(__name__)

# Простое хранилище данных о запросах
requests_log = []

@app.route('/')
def home():
    start_time = time.time()
    # Имитация обработки запроса
    time.sleep(1)  # Удалите или измените это в зависимости от ваших нужд
    response_time = time.time() - start_time
    requests_log.append(response_time)
    return "Welcome to the Test Site!"

@app.route('/stats')
def stats():
    # Возвращаем статистику запросов
    return jsonify({
        'total_requests': len(requests_log),
        'average_response_time': sum(requests_log) / len(requests_log) if requests_log else 0
    })

if __name__ == '__main__':
    app.run(debug=True, port=8000)
