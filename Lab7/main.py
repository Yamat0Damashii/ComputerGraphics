"""Tkinter visualizer for the three Lab 7 assignments."""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

try:
    from .task1 import OBJModel, Polyhedron
    from .task2 import SurfaceOfRevolution
    from .task3 import FunctionSurface, compile_function
except ImportError:
    from task1 import OBJModel, Polyhedron
    from task2 import SurfaceOfRevolution
    from task3 import FunctionSurface, compile_function


class ModelViewer:
    """GUI for loading OBJ files and creating the task 2 and 3 models."""

    def __init__(self, root):
        self.root = root
        self.root.title("Лабораторная работа №7 — 3D модели")
        self.root.geometry("1200x800")
        self.current_model = None
        self.initial_model = None
        self._setup_ui()
        self._set_model(FunctionSurface.create_surface(
            compile_function("math.sin(x) * math.cos(y)"),
            (-3, 3), (-3, 3), 25, 25,
        ))

    def _setup_ui(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        controls = ttk.Frame(main_frame, width=330)
        controls.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        controls.pack_propagate(False)

        obj_frame = ttk.LabelFrame(controls, text="Задание 1 — OBJ-модель", padding=8)
        obj_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(obj_frame, text="Загрузить OBJ", command=self.load_obj).pack(fill=tk.X)
        ttk.Button(obj_frame, text="Сохранить текущую модель", command=self.save_obj).pack(
            fill=tk.X, pady=(5, 0)
        )

        revolution_frame = ttk.LabelFrame(
            controls, text="Задание 2 — Фигура вращения", padding=8
        )
        revolution_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(revolution_frame, text="Профиль: радиус, высота (по точке на строку)").pack(
            anchor=tk.W
        )
        self.profile_text = tk.Text(revolution_frame, height=5, width=34)
        self.profile_text.pack(fill=tk.X, pady=(4, 5))
        self.profile_text.insert(tk.END, "0, 0\n1, 0\n1, 2\n0, 2")
        revolution_options = ttk.Frame(revolution_frame)
        revolution_options.pack(fill=tk.X)
        ttk.Label(revolution_options, text="Ось").pack(side=tk.LEFT)
        self.axis_var = tk.StringVar(value="y")
        ttk.Combobox(
            revolution_options, textvariable=self.axis_var, values=("x", "y", "z"),
            state="readonly", width=4,
        ).pack(side=tk.LEFT, padx=(4, 10))
        ttk.Label(revolution_options, text="Сегменты").pack(side=tk.LEFT)
        self.segments_var = tk.StringVar(value="36")
        ttk.Entry(revolution_options, textvariable=self.segments_var, width=6).pack(
            side=tk.LEFT, padx=(4, 0)
        )
        ttk.Button(
            revolution_frame, text="Построить фигуру", command=self.create_revolution
        ).pack(fill=tk.X, pady=(6, 0))

        surface_frame = ttk.LabelFrame(
            controls, text="Задание 3 — Поверхность z = f(x, y)", padding=8
        )
        surface_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(surface_frame, text="Функция (например, math.sin(x)*math.cos(y))").pack(
            anchor=tk.W
        )
        self.function_var = tk.StringVar(value="math.sin(x) * math.cos(y)")
        ttk.Entry(surface_frame, textvariable=self.function_var).pack(fill=tk.X, pady=(4, 6))

        ranges = ttk.Frame(surface_frame)
        ranges.pack(fill=tk.X)
        self.range_vars = {
            "x_min": tk.StringVar(value="-3"),
            "x_max": tk.StringVar(value="3"),
            "y_min": tk.StringVar(value="-3"),
            "y_max": tk.StringVar(value="3"),
        }
        for row, axis in enumerate(("x", "y")):
            ttk.Label(ranges, text=f"{axis.upper()} min/max").grid(
                row=row, column=0, sticky=tk.W, pady=2
            )
            for col, suffix in enumerate(("min", "max"), start=1):
                ttk.Entry(
                    ranges, textvariable=self.range_vars[f"{axis}_{suffix}"], width=7
                ).grid(row=row, column=col, padx=3, pady=2)

        steps = ttk.Frame(surface_frame)
        steps.pack(fill=tk.X, pady=(4, 0))
        ttk.Label(steps, text="Шаги X").pack(side=tk.LEFT)
        self.x_steps_var = tk.StringVar(value="25")
        ttk.Entry(steps, textvariable=self.x_steps_var, width=6).pack(
            side=tk.LEFT, padx=(4, 10)
        )
        ttk.Label(steps, text="Y").pack(side=tk.LEFT)
        self.y_steps_var = tk.StringVar(value="25")
        ttk.Entry(steps, textvariable=self.y_steps_var, width=6).pack(
            side=tk.LEFT, padx=(4, 0)
        )
        ttk.Button(
            surface_frame, text="Построить поверхность", command=self.create_surface
        ).pack(fill=tk.X, pady=(6, 0))

        transform_frame = ttk.LabelFrame(controls, text="Преобразования", padding=8)
        transform_frame.pack(fill=tk.X)
        for axis in ("x", "y", "z"):
            ttk.Button(
                transform_frame, text=f"Поворот {axis.upper()} +10°",
                command=lambda selected_axis=axis: self.rotate_model(selected_axis, 10),
            ).pack(fill=tk.X, pady=2)
        scale_buttons = ttk.Frame(transform_frame)
        scale_buttons.pack(fill=tk.X, pady=(4, 0))
        ttk.Button(
            scale_buttons, text="Увеличить", command=lambda: self.scale_model(1.2)
        ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2))
        ttk.Button(
            scale_buttons, text="Уменьшить", command=lambda: self.scale_model(1 / 1.2)
        ).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(2, 0))
        ttk.Button(transform_frame, text="Сбросить модель", command=self.reset_model).pack(
            fill=tk.X, pady=(5, 0)
        )

        display = ttk.Frame(main_frame)
        display.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.figure = Figure(figsize=(8, 6))
        self.axes = self.figure.add_subplot(111, projection="3d")
        self.canvas = FigureCanvasTkAgg(self.figure, master=display)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _set_model(self, model):
        self.current_model = model
        self.initial_model = model.copy()
        self.plot_model()

    def plot_model(self):
        self.axes.clear()
        if self.current_model is None or self.current_model.V.shape[1] == 0:
            self.axes.text2D(0.5, 0.5, "Создайте или загрузите модель", ha="center")
            self.canvas.draw_idle()
            return

        vertices = (self.current_model.V[:3, :] / self.current_model.V[3, :]).T
        for first, second in self.current_model.edges():
            points = vertices[[first, second]]
            self.axes.plot(points[:, 0], points[:, 1], points[:, 2], color="navy", linewidth=0.8)
        minimum = vertices.min(axis=0)
        maximum = vertices.max(axis=0)
        center = (minimum + maximum) / 2
        radius = max(float((maximum - minimum).max()) / 2, 0.5)
        self.axes.set_xlim(center[0] - radius, center[0] + radius)
        self.axes.set_ylim(center[1] - radius, center[1] + radius)
        self.axes.set_zlim(center[2] - radius, center[2] + radius)
        self.axes.set_box_aspect((1, 1, 1))
        self.axes.set_xlabel("X")
        self.axes.set_ylabel("Y")
        self.axes.set_zlabel("Z")
        self.axes.set_title(
            f"Вершины: {self.current_model.V.shape[1]}, грани: {len(self.current_model.faces)}"
        )
        self.canvas.draw_idle()

    def load_obj(self):
        filename = filedialog.askopenfilename(
            title="Выберите OBJ-файл",
            filetypes=(("OBJ files", "*.obj"), ("All files", "*.*")),
        )
        if not filename:
            return
        model = OBJModel()
        if not model.load_from_file(filename):
            messagebox.showerror("Ошибка загрузки OBJ", model.last_error or "Неизвестная ошибка")
            return
        self._set_model(model.polyhedron)

    def save_obj(self):
        if self.current_model is None:
            messagebox.showwarning("Нет модели", "Сначала создайте или загрузите модель")
            return
        filename = filedialog.asksaveasfilename(
            title="Сохранить OBJ-файл",
            defaultextension=".obj",
            filetypes=(("OBJ files", "*.obj"), ("All files", "*.*")),
        )
        if not filename:
            return
        model = OBJModel(self.current_model)
        if not model.save_to_file(filename):
            messagebox.showerror("Ошибка сохранения OBJ", model.last_error or "Неизвестная ошибка")

    def create_revolution(self):
        try:
            profile = []
            for line_number, line in enumerate(
                self.profile_text.get("1.0", tk.END).splitlines(), start=1
            ):
                if not line.strip():
                    continue
                values = line.replace(",", " ").split()
                if len(values) != 2:
                    raise ValueError(f"Строка профиля {line_number}: укажите радиус и высоту")
                profile.append((float(values[0]), float(values[1])))
            model = SurfaceOfRevolution.create_from_profile(
                profile, self.axis_var.get(), int(self.segments_var.get())
            )
        except (ValueError, OverflowError) as error:
            messagebox.showerror("Ошибка построения фигуры", str(error))
            return
        self._set_model(model)

    def create_surface(self):
        try:
            function = compile_function(self.function_var.get())
            ranges = {
                name: float(variable.get()) for name, variable in self.range_vars.items()
            }
            model = FunctionSurface.create_surface(
                function,
                (ranges["x_min"], ranges["x_max"]),
                (ranges["y_min"], ranges["y_max"]),
                int(self.x_steps_var.get()),
                int(self.y_steps_var.get()),
            )
        except (ValueError, ArithmeticError, OverflowError) as error:
            messagebox.showerror("Ошибка построения поверхности", str(error))
            return
        self._set_model(model)

    def rotate_model(self, axis, angle):
        if self.current_model is None:
            return
        self.current_model.rotate_around_axis_through_center(axis, angle)
        self.plot_model()

    def scale_model(self, factor):
        if self.current_model is None:
            return
        self.current_model.scale_about_center(factor)
        self.plot_model()

    def reset_model(self):
        if self.initial_model is not None:
            self.current_model = self.initial_model.copy()
            self.plot_model()


def main():
    root = tk.Tk()
    ModelViewer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
