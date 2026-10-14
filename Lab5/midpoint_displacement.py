import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
import random

class MountainGenerator:
    def __init__(self):
        # Настройка окна и места для слайдеров
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        plt.subplots_adjust(bottom=0.35)
        self.ax.set_title("Midpoint Displacement: Двумерная визуализация горного массива")
        self.ax.set_xlabel("Расстояние (X)")
        self.ax.set_ylabel("Высота (Y)")

        # Начальные параметры
        self.n_iter = 8          # Количество итераций (детализация)
        self.roughness = 0.6     # Шероховатость (как быстро падает случайность)
        self.max_disp = 1.0      # Максимальное начальное смещение
        self.seed = 42           # Зерно рандома для воспроизводимости

        # --- Создание слайдеров ---
        color_ax = 'lightgoldenrodyellow'

        ax_iter = plt.axes([0.2, 0.22, 0.65, 0.03], facecolor=color_ax)
        self.s_iter = Slider(ax_iter, 'Итерации', 1, 12, valinit=self.n_iter, valstep=1)

        ax_rough = plt.axes([0.2, 0.17, 0.65, 0.03], facecolor=color_ax)
        self.s_rough = Slider(ax_rough, 'Шероховатость', 0.1, 0.95, valinit=self.roughness, valstep=0.05)

        ax_disp = plt.axes([0.2, 0.12, 0.65, 0.03], facecolor=color_ax)
        self.s_disp = Slider(ax_disp, 'Макс. смещение', 0.1, 3.0, valinit=self.max_disp, valstep=0.1)

        ax_step = plt.axes([0.2, 0.07, 0.65, 0.03], facecolor=color_ax)
        self.s_step = Slider(ax_step, 'Текущий шаг алгоритма', 0, self.n_iter, valinit=self.n_iter, valstep=1)

        # Кнопка перегенерации
        ax_button = plt.axes([0.78, 0.02, 0.14, 0.04])
        self.b_regenerate = Button(ax_button, 'Новый рельеф', color=color_ax, hovercolor='0.975')

        # Привязка обработчиков событий
        self.s_iter.on_changed(self.update_params)
        self.s_rough.on_changed(self.update_params)
        self.s_disp.on_changed(self.update_params)
        self.s_step.on_changed(self.update_step)
        self.b_regenerate.on_clicked(self.regenerate)

        self.steps = []
        self.generate_and_plot()

    def generate(self):
        """Генерация ломаной методом midpoint displacement"""
        random.seed(self.seed)

        # Начальная ломаная (две точки)
        points = [(0.0, 0.0), (1.0, 0.0)]
        steps = [points]
        disp = self.max_disp

        # Итеративное разбиение
        for _ in range(self.n_iter):
            new_points = [points[0]]
            for i in range(len(points) - 1):
                x1, y1 = points[i]
                x2, y2 = points[i+1]

                # Находим середину
                mx = (x1 + x2) / 2
                # Добавляем случайное смещение по Y
                my = (y1 + y2) / 2 + random.uniform(-disp, disp)

                new_points.append((mx, my))
                new_points.append((x2, y2))

            points = new_points
            steps.append(points)
            # Уменьшаем диапазон случайности (шероховатость)
            disp *= self.roughness

        self.steps = steps

        # Обновляем лимиты слайдера шагов
        self.s_step.valmax = self.n_iter
        self.s_step.ax.set_xlim(0, self.n_iter)
        if self.s_step.val > self.n_iter:
            self.s_step.set_val(self.n_iter)

    def plot(self):
        """Отрисовка последовательных шагов"""
        self.ax.clear()
        self.ax.set_title("Midpoint Displacement: Двумерная визуализация горного массива")
        self.ax.set_xlabel("Расстояние")
        self.ax.set_ylabel("Высота")

        current_step = int(self.s_step.val)

        # Рисуем все шаги до текущего, чтобы была видна эволюция
        for i in range(current_step + 1):
            x = [p[0] for p in self.steps[i]]
            y = [p[1] for p in self.steps[i]]

            # Градиент цвета: от светло-зеленого (начало) к темно-зеленому (конец)
            color = plt.cm.Greens(0.3 + 0.7 * (i / max(1, current_step)))
            alpha = 0.4 + 0.6 * (i / max(1, current_step))

            # Последний шаг рисуем более жирной линией
            lw = 2.0 if i == current_step else 1.0
            self.ax.plot(x, y, color=color, alpha=alpha, linewidth=lw)

        # Фиксируем оси, чтобы при изменении параметров график не "прыгал"
        self.ax.set_ylim(-self.max_disp * 1.5, self.max_disp * 1.5)
        self.ax.set_xlim(-0.05, 1.05)
        self.fig.canvas.draw_idle()

    def update_params(self, val):
        """Обновление параметров и пересчет"""
        self.n_iter = int(self.s_iter.val)
        self.roughness = self.s_rough.val
        self.max_disp = self.s_disp.val
        self.generate()
        self.plot()

    def update_step(self, val):
        """Обновление только текущего шага просмотра"""
        self.plot()

    def regenerate(self, event):
        """Генерация нового случайного рельефа"""
        self.seed = random.randint(0, 100000)
        self.generate()
        self.plot()

    def generate_and_plot(self):
        self.generate()
        self.plot()

if __name__ == '__main__':
    app = MountainGenerator()
    plt.show()