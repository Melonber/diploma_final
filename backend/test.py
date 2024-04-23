import matplotlib.pyplot as plt
import numpy as np

# Создаем окно графика
plt.ion()

# Инициализируем пустой график
fig, ax = plt.subplots()
x = np.arange(0, 10, 0.1)  # Создаем массив значений по x
y = np.zeros_like(x)  # Инициализируем массив нулями по y
line, = ax.plot(x, y)  # Создаем линию графика

# Основной цикл для обновления графика
for i in range(100):
    y = np.sin(x + i * 0.1)  # Генерируем новые данные (например, синусоида с постоянным сдвигом)

    # Обновляем данные на графике
    line.set_ydata(y)

    # Перерисовываем график
    fig.canvas.draw()

    # Добавляем небольшую задержку для эффекта анимации
    plt.pause(0.1)

# Чтобы окно графика не закрывалось сразу после завершения анимации, добавим ожидание ввода
plt.ioff()
plt.show()
