"""Interactive demonstrations for the Lab 9 shading and texturing tasks."""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import numpy as np

try:
    from .task1 import cube, octahedron, tetrahedron
    from .task2 import render_gouraud, render_phong_toon
    from .task3 import (
        create_checkerboard_texture,
        create_gradient_texture,
        load_obj,
        load_texture,
        render_textured,
    )
except ImportError:
    from task1 import cube, octahedron, tetrahedron
    from task2 import render_gouraud, render_phong_toon
    from task3 import (
        create_checkerboard_texture,
        create_gradient_texture,
        load_obj,
        load_texture,
        render_textured,
    )


MODEL_BUILDERS = {
    "Тетраэдр": tetrahedron,
    "Куб": cube,
    "Октаэдр": octahedron,
}


class Lab9App:
    def __init__(self, root):
        self.root = root
        root.title("Лабораторная работа №9 — освещение и текстуры")
        root.geometry("1100x780")
        self.model_name = tk.StringVar(value="Куб")
        self.mode = tk.StringVar(value="Гуро — Ламберт")
        self.texture_name = tk.StringVar(value="Шахматная доска")
        self.light_values = [tk.StringVar(value=value) for value in ("2", "3", "4")]
        self.color_values = [tk.StringVar(value=value) for value in ("0.2", "0.55", "0.95")]
        self.textures = {
            "Шахматная доска": create_checkerboard_texture(),
            "Градиент": create_gradient_texture(),
        }
        self.model = cube()
        self.initial_model = self.model.copy()
        self._build_ui()
        self.root.after(100, self.redraw)

    def _build_ui(self):
        controls = ttk.Frame(self.root, padding=8)
        controls.pack(side=tk.TOP, fill=tk.X)

        row = ttk.Frame(controls)
        row.pack(fill=tk.X, pady=3)
        ttk.Label(row, text="Многогранник").pack(side=tk.LEFT)
        ttk.Combobox(
            row, textvariable=self.model_name, values=tuple(MODEL_BUILDERS),
            state="readonly", width=13,
        ).pack(side=tk.LEFT, padx=(4, 12))
        ttk.Button(row, text="Показать", command=self.select_model).pack(side=tk.LEFT, padx=2)
        ttk.Button(row, text="Загрузить OBJ", command=self.open_obj).pack(side=tk.LEFT, padx=2)
        ttk.Label(row, text="Затенение").pack(side=tk.LEFT, padx=(12, 4))
        mode_box = ttk.Combobox(
            row, textvariable=self.mode,
            values=("Гуро — Ламберт", "Фонг — toon", "Текстура"),
            state="readonly", width=20,
        )
        mode_box.pack(side=tk.LEFT)
        mode_box.bind("<<ComboboxSelected>>", lambda _event: self.redraw())

        row = ttk.Frame(controls)
        row.pack(fill=tk.X, pady=3)
        ttk.Label(row, text="Положение света x,y,z").pack(side=tk.LEFT)
        for value in self.light_values:
            ttk.Entry(row, textvariable=value, width=6).pack(side=tk.LEFT, padx=2)
        ttk.Label(row, text="Цвет объекта RGB (0–1)").pack(side=tk.LEFT, padx=(10, 4))
        for value in self.color_values:
            ttk.Entry(row, textvariable=value, width=6).pack(side=tk.LEFT, padx=2)
        ttk.Button(row, text="Применить", command=self.redraw).pack(side=tk.LEFT, padx=6)
        ttk.Label(row, text="Текстура").pack(side=tk.LEFT, padx=(8, 3))
        self.texture_box = ttk.Combobox(
            row, textvariable=self.texture_name, values=tuple(self.textures),
            state="readonly", width=17,
        )
        self.texture_box.pack(side=tk.LEFT)
        self.texture_box.bind("<<ComboboxSelected>>", lambda _event: self.redraw())
        ttk.Button(row, text="Загрузить изображение", command=self.open_texture).pack(
            side=tk.LEFT, padx=4
        )

        transform = ttk.LabelFrame(self.root, text="Аффинные преобразования", padding=6)
        transform.pack(side=tk.TOP, fill=tk.X, padx=8, pady=(0, 6))
        for axis in ("x", "y", "z"):
            ttk.Button(
                transform, text=f"Поворот {axis.upper()}",
                command=lambda selected=axis: self.rotate(selected),
            ).pack(side=tk.LEFT, padx=2)
        ttk.Button(transform, text="Увеличить", command=lambda: self.scale(1.15)).pack(
            side=tk.LEFT, padx=(10, 2)
        )
        ttk.Button(transform, text="Уменьшить", command=lambda: self.scale(1 / 1.15)).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Label(transform, text="Перенос dx,dy,dz").pack(side=tk.LEFT, padx=(10, 3))
        self.translation_values = [
            tk.StringVar(value=value) for value in ("0", "0", "0")
        ]
        for value in self.translation_values:
            ttk.Entry(transform, textvariable=value, width=6).pack(side=tk.LEFT, padx=2)
        ttk.Button(transform, text="Перенести", command=self.translate).pack(side=tk.LEFT, padx=3)
        ttk.Button(transform, text="Сбросить", command=self.reset_model).pack(
            side=tk.RIGHT, padx=2
        )

        self.canvas = tk.Canvas(self.root, bg="#171a21", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        self.canvas.bind("<Configure>", lambda _event: self.redraw())

    def _light_position(self):
        position = np.asarray([float(value.get()) for value in self.light_values])
        if not np.all(np.isfinite(position)):
            raise ValueError("Координаты источника света должны быть конечными числами")
        return position

    def _material_color(self):
        color = np.asarray([float(value.get()) for value in self.color_values])
        if not np.all(np.isfinite(color)) or np.any(color < 0) or np.any(color > 1):
            raise ValueError("Компоненты цвета должны быть в диапазоне от 0 до 1")
        return color

    def select_model(self):
        builder = MODEL_BUILDERS.get(self.model_name.get())
        if builder is None:
            return
        self.model = builder()
        self.initial_model = self.model.copy()
        self.redraw()

    def reset_model(self):
        self.model = self.initial_model.copy()
        self.redraw()

    def rotate(self, axis):
        self.model.rotate(axis, 15)
        self.redraw()

    def scale(self, factor):
        self.model.scale(factor)
        self.redraw()

    def translate(self):
        try:
            dx, dy, dz = (float(value.get()) for value in self.translation_values)
            self.model.translate(dx, dy, dz)
            self.redraw()
        except ValueError as error:
            messagebox.showerror("Некорректное преобразование", str(error))

    def open_obj(self):
        filename = filedialog.askopenfilename(
            title="Открыть OBJ-модель",
            filetypes=(("OBJ-файлы", "*.obj"), ("Все файлы", "*.*")),
        )
        if not filename:
            return
        try:
            self.model = load_obj(filename)
            self.initial_model = self.model.copy()
            self.model_name.set("OBJ-модель")
            self.redraw()
        except (OSError, ValueError) as error:
            messagebox.showerror("Ошибка OBJ", str(error))

    def open_texture(self):
        filename = filedialog.askopenfilename(
            title="Загрузить текстуру",
            filetypes=(("Изображения", "*.png *.jpg *.jpeg *.bmp *.gif"), ("Все файлы", "*.*")),
        )
        if not filename:
            return
        try:
            name = "Загруженная текстура"
            self.textures[name] = load_texture(filename)
            self.texture_name.set(name)
            self._refresh_texture_options()
            self.redraw()
        except (OSError, RuntimeError, ValueError) as error:
            messagebox.showerror("Ошибка текстуры", str(error))

    def _refresh_texture_options(self):
        self.texture_box.configure(values=tuple(self.textures))

    def redraw(self):
        if not hasattr(self, "canvas"):
            return
        width = min(max(self.canvas.winfo_width(), 2), 800)
        height = min(max(self.canvas.winfo_height(), 2), 600)
        try:
            light = self._light_position()
            material = self._material_color()
            arguments = {
                "camera_position": (3, 2.5, 5),
                "camera_target": (0, 0, 0),
            }
            if self.mode.get() == "Гуро — Ламберт":
                image, _depth = render_gouraud(
                    self.model, width, height, light_position=light,
                    material_color=material, **arguments,
                )
            elif self.mode.get() == "Фонг — toon":
                image, _depth = render_phong_toon(
                    self.model, width, height, light_position=light,
                    material_color=material, **arguments,
                )
            else:
                image, _depth = render_textured(
                    self.model, self.textures[self.texture_name.get()],
                    width, height, light_position=light, **arguments,
                )
        except (ValueError, FloatingPointError) as error:
            messagebox.showerror("Ошибка рендеринга", str(error))
            return
        ppm = f"P6 {width} {height} 255 ".encode("ascii") + image.tobytes()
        photo = tk.PhotoImage(data=ppm, format="PPM")
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        self.canvas.image = photo


def main():
    root = tk.Tk()
    Lab9App(root)
    root.mainloop()


if __name__ == "__main__":
    main()