"""Tkinter visualizer for Lab 8: back-face culling, Z-buffer, and camera."""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import numpy as np

try:
    from .task1 import (
        OBJModel, Polyhedron, Rx, Ry, Rz, S, T, cube, dodecahedron,
        icosahedron, octahedron, tetrahedron, uv_sphere,
        visible_faces_camera_space,
    )
    from .task2 import create_demo_scenes, render_scene, transform_object
    from .task3 import Camera, ortho_xy, perspective
except ImportError:
    from task1 import (
        OBJModel, Polyhedron, Rx, Ry, Rz, S, T, cube, dodecahedron,
        icosahedron, octahedron, tetrahedron, uv_sphere,
        visible_faces_camera_space,
    )
    from task2 import create_demo_scenes, render_scene, transform_object
    from task3 import Camera, ortho_xy, perspective


hexahedron = cube


def compute_visible_faces_camera_space(polyhedron, camera, ortho=False):
    """Compatibility helper used by the original standalone zbuffer.py demo."""
    camera_model, indices = visible_faces_camera_space(
        polyhedron, camera.get_view_matrix(), perspective=not ortho
    )
    return camera_model, [camera_model.faces[index] for index in indices]


def _draw_polyhedron(canvas, model, camera, projection="perspective", cull=True):
    canvas.delete("all")
    width = max(canvas.winfo_width(), 2)
    height = max(canvas.winfo_height(), 2)
    camera.aspect = width / height
    view = camera.get_view_matrix()
    camera_model = model.copy().apply(view)
    if cull:
        camera_model, face_indices = visible_faces_camera_space(
            model, view, perspective=(projection == "perspective")
        )
    else:
        face_indices = range(len(camera_model.faces))

    vertices = camera_model.V[:3, :] / camera_model.V[3, :]
    if projection == "perspective":
        clip = camera.get_projection_matrix() @ camera_model.V
        if np.any(clip[3, :] <= 1e-8):
            canvas.create_text(
                width / 2, height / 2, text="Модель пересекает плоскость камеры",
                fill="white",
            )
            return
        projected = clip[:2, :] / clip[3, :]
    else:
        projected = vertices[:2, :]
    scale = min(width, height) * 0.42
    screen_x = width / 2 + projected[0, :] * scale
    screen_y = height / 2 - projected[1, :] * scale

    sorted_faces = sorted(
        face_indices,
        key=lambda index: np.mean(vertices[2, camera_model.faces[index].indices]),
    )
    colors = ("#81a9e8", "#86c98a", "#edbc68", "#d987a7", "#83c6c4")
    for index in sorted_faces:
        face = camera_model.faces[index]
        polygon = []
        for vertex_index in face.indices:
            polygon.extend((float(screen_x[vertex_index]), float(screen_y[vertex_index])))
        canvas.create_polygon(
            *polygon, fill=colors[index % len(colors)], outline="#172033", width=1
        )
    canvas.create_text(
        12, 12, anchor=tk.NW,
        text=f"Граней показано: {len(sorted_faces)} / {len(model.faces)}",
        fill="white", font=("Segoe UI", 10, "bold"),
    )


def _show_rgb_image(canvas, rgb):
    height, width = rgb.shape[:2]
    ppm = f"P6 {width} {height} 255 ".encode("ascii") + rgb.tobytes()
    image = tk.PhotoImage(data=ppm, format="PPM")
    canvas.delete("all")
    canvas.create_image(0, 0, anchor=tk.NW, image=image)
    canvas.image = image


class Lab8App:
    """Application with one demonstration tab for each Lab 8 task."""

    def __init__(self, root):
        self.root = root
        root.title("Лабораторная работа №8 — компьютерная графика")
        root.geometry("1250x820")
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.task1_frame = ttk.Frame(self.notebook, padding=8)
        self.task2_frame = ttk.Frame(self.notebook, padding=8)
        self.task3_frame = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(self.task1_frame, text="1. Отсечение граней")
        self.notebook.add(self.task2_frame, text="2. Z-буфер")
        self.notebook.add(self.task3_frame, text="3. Камера")
        self._build_task1()
        self._build_task2()
        self._build_task3()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(150, self._redraw_all)

    def _build_task1(self):
        controls = ttk.Frame(self.task1_frame)
        controls.pack(side=tk.TOP, fill=tk.X, pady=(0, 8))
        self.culling_model_var = tk.StringVar(value="Куб")
        ttk.Label(controls, text="Объект").pack(side=tk.LEFT)
        ttk.Combobox(
            controls, textvariable=self.culling_model_var,
            values=("Куб", "Шар", "OBJ файл"), state="readonly", width=12,
        ).pack(side=tk.LEFT, padx=(4, 8))
        ttk.Button(controls, text="Показать", command=self._select_culling_model).pack(
            side=tk.LEFT, padx=(0, 10)
        )
        ttk.Button(controls, text="Загрузить OBJ", command=self._load_culling_obj).pack(
            side=tk.LEFT, padx=(0, 12)
        )
        self.culling_enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            controls, text="Отсечение нелицевых граней",
            variable=self.culling_enabled, command=self._redraw_task1,
        ).pack(side=tk.LEFT, padx=4)
        self.culling_projection = tk.StringVar(value="parallel")
        ttk.Radiobutton(
            controls, text="Параллельная", value="parallel",
            variable=self.culling_projection, command=self._redraw_task1,
        ).pack(side=tk.LEFT, padx=3)
        ttk.Radiobutton(
            controls, text="Перспективная", value="perspective",
            variable=self.culling_projection, command=self._redraw_task1,
        ).pack(side=tk.LEFT, padx=3)

        orbit = ttk.Frame(self.task1_frame)
        orbit.pack(side=tk.TOP, fill=tk.X, pady=(0, 6))
        ttk.Label(orbit, text="Направление обзора:").pack(side=tk.LEFT)
        self.culling_theta = tk.DoubleVar(value=35)
        self.culling_phi = tk.DoubleVar(value=20)
        ttk.Label(orbit, text="Азимут").pack(side=tk.LEFT, padx=(8, 2))
        ttk.Scale(
            orbit, from_=-180, to=180, variable=self.culling_theta,
            command=lambda _value: self._redraw_task1(),
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        ttk.Label(orbit, text="Высота").pack(side=tk.LEFT, padx=(8, 2))
        ttk.Scale(
            orbit, from_=-75, to=75, variable=self.culling_phi,
            command=lambda _value: self._redraw_task1(),
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        ttk.Button(orbit, text="Повернуть объект", command=self._rotate_culling_model).pack(
            side=tk.LEFT, padx=(8, 4)
        )
        self.culling_animation = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            orbit, text="Вращать автоматически", variable=self.culling_animation,
            command=self._toggle_culling_animation,
        ).pack(side=tk.LEFT)
        self.culling_canvas = tk.Canvas(self.task1_frame, bg="#20242c", highlightthickness=0)
        self.culling_canvas.pack(fill=tk.BOTH, expand=True)
        self.culling_canvas.bind("<Configure>", lambda _event: self._redraw_task1())
        self.culling_model = cube()
        self.culling_initial = self.culling_model.copy()
        self._culling_after_id = None

    def _build_task2(self):
        controls = ttk.Frame(self.task2_frame)
        controls.pack(side=tk.TOP, fill=tk.X, pady=(0, 8))
        ttk.Label(controls, text="Сцена").pack(side=tk.LEFT)
        self.scenes = create_demo_scenes()
        self.scene_var = tk.StringVar(value=self.scenes[0].name)
        ttk.Combobox(
            controls, textvariable=self.scene_var,
            values=tuple(scene.name for scene in self.scenes),
            state="readonly", width=25,
        ).pack(side=tk.LEFT, padx=(4, 12))
        ttk.Button(controls, text="Показать сцену", command=self._change_scene).pack(
            side=tk.LEFT, padx=(0, 10)
        )
        ttk.Label(controls, text="Объект").pack(side=tk.LEFT)
        self.object_var = tk.StringVar(value="1")
        self.object_choice = ttk.Combobox(
            controls, textvariable=self.object_var, state="readonly", width=5
        )
        self.object_choice.pack(side=tk.LEFT, padx=(4, 12))
        self.zbuffer_enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            controls, text="Включить Z-буфер",
            variable=self.zbuffer_enabled, command=self._redraw_task2,
        ).pack(side=tk.LEFT, padx=4)
        self.zbuffer_culling = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            controls, text="Отсечение нелицевых граней",
            variable=self.zbuffer_culling, command=self._redraw_task2,
        ).pack(side=tk.LEFT, padx=4)

        transform = ttk.Frame(self.task2_frame)
        transform.pack(side=tk.TOP, fill=tk.X, pady=(0, 8))
        for axis in ("x", "y", "z"):
            ttk.Button(
                transform, text=f"Поворот {axis.upper()}",
                command=lambda selected_axis=axis: self._transform_task2(selected_axis),
            ).pack(side=tk.LEFT, padx=2)
        ttk.Button(
            transform, text="Увеличить", command=lambda: self._scale_task2(1.15)
        ).pack(side=tk.LEFT, padx=(10, 2))
        ttk.Button(
            transform, text="Уменьшить", command=lambda: self._scale_task2(1 / 1.15)
        ).pack(side=tk.LEFT, padx=2)
        ttk.Button(transform, text="Сбросить сцену", command=self._reset_scene).pack(
            side=tk.LEFT, padx=(10, 2)
        )
        self.zbuffer_canvas = tk.Canvas(self.task2_frame, bg="#14171e", highlightthickness=0)
        self.zbuffer_canvas.pack(fill=tk.BOTH, expand=True)
        self.zbuffer_canvas.bind("<Configure>", lambda _event: self._redraw_task2())
        self.zbuffer_camera = Camera(
            position=self.scenes[0].camera_position, target=self.scenes[0].camera_target
        )
        self._update_object_choices()

    def _build_task3(self):
        controls = ttk.Frame(self.task3_frame)
        controls.pack(side=tk.TOP, fill=tk.X, pady=(0, 8))
        ttk.Label(controls, text="Камера вращается вокруг неподвижного куба").pack(
            side=tk.LEFT, padx=(0, 12)
        )
        ttk.Button(controls, text="◀", command=lambda: self._orbit_task3(-10, 0)).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(controls, text="▶", command=lambda: self._orbit_task3(10, 0)).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(controls, text="Вверх", command=lambda: self._orbit_task3(0, 8)).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(controls, text="Вниз", command=lambda: self._orbit_task3(0, -8)).pack(
            side=tk.LEFT, padx=2
        )
        ttk.Button(controls, text="Ближе", command=lambda: self._zoom_task3(0.5)).pack(
            side=tk.LEFT, padx=(12, 2)
        )
        ttk.Button(controls, text="Дальше", command=lambda: self._zoom_task3(-0.5)).pack(
            side=tk.LEFT, padx=2
        )
        self.camera_animation = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            controls, text="Автовращение камеры", variable=self.camera_animation,
            command=self._toggle_camera_animation,
        ).pack(side=tk.LEFT, padx=(12, 2))
        self.camera_canvas = tk.Canvas(self.task3_frame, bg="#14171e", highlightthickness=0)
        self.camera_canvas.pack(fill=tk.BOTH, expand=True)
        self.camera_canvas.bind("<Configure>", lambda _event: self._redraw_task3())
        self.static_camera_model = cube()
        self.task3_camera = Camera(position=(4.5, 2.8, 6.5), target=(0, 0, 0), fov=50)
        self._camera_after_id = None

    def _select_culling_model(self):
        selection = self.culling_model_var.get()
        if selection == "Куб":
            model = cube()
        elif selection == "Шар":
            model = uv_sphere()
        else:
            return
        self.culling_model = model
        self.culling_initial = model.copy()
        self._redraw_task1()

    def _load_culling_obj(self):
        filename = filedialog.askopenfilename(
            title="Выберите OBJ-файл",
            filetypes=(("OBJ files", "*.obj"), ("All files", "*.*")),
        )
        if not filename:
            return
        obj = OBJModel()
        if not obj.load_from_file(filename):
            messagebox.showerror("Ошибка OBJ", obj.last_error or "Не удалось загрузить файл")
            return
        self.culling_model = obj.polyhedron
        self.culling_initial = obj.polyhedron.copy()
        self.culling_model_var.set("OBJ файл")
        self._redraw_task1()

    def _redraw_task1(self):
        if not hasattr(self, "culling_canvas"):
            return
        theta, phi = np.radians([self.culling_theta.get(), self.culling_phi.get()])
        radius = max(4.0, float(np.linalg.norm(self.culling_model.center())) + 4)
        position = radius * np.array([
            np.cos(phi) * np.sin(theta), np.sin(phi), np.cos(phi) * np.cos(theta),
        ])
        camera = Camera(position=position, target=self.culling_model.center())
        _draw_polyhedron(
            self.culling_canvas, self.culling_model, camera,
            self.culling_projection.get(), self.culling_enabled.get(),
        )

    def _rotate_culling_model(self):
        self.culling_model.rotate_around_axis_through_center("y", 12)
        self._redraw_task1()

    def _toggle_culling_animation(self):
        if self.culling_animation.get():
            self._animate_culling_model()
        elif self._culling_after_id is not None:
            self.root.after_cancel(self._culling_after_id)
            self._culling_after_id = None

    def _animate_culling_model(self):
        if not self.culling_animation.get():
            self._culling_after_id = None
            return
        self.culling_model.rotate_around_axis_through_center("y", 2)
        self._redraw_task1()
        self._culling_after_id = self.root.after(40, self._animate_culling_model)

    def _update_object_choices(self):
        scene = next(scene for scene in self.scenes if scene.name == self.scene_var.get())
        self.object_choice.configure(values=tuple(str(i + 1) for i in range(len(scene.objects))))
        self.object_var.set("1")

    def _change_scene(self):
        scene = next(scene for scene in self.scenes if scene.name == self.scene_var.get())
        self.zbuffer_camera.reset(position=scene.camera_position, target=scene.camera_target)
        self._update_object_choices()
        self._redraw_task2()

    def _reset_scene(self):
        selected_name = self.scene_var.get()
        self.scenes = create_demo_scenes()
        self.scene_var.set(selected_name)
        self._change_scene()

    def _selected_scene_object(self):
        scene = next(scene for scene in self.scenes if scene.name == self.scene_var.get())
        index = max(0, min(int(self.object_var.get()) - 1, len(scene.objects) - 1))
        return scene.objects[index][0]

    def _transform_task2(self, axis):
        transform_object(self._selected_scene_object(), "rotate", axis, 12)
        self._redraw_task2()

    def _scale_task2(self, factor):
        transform_object(self._selected_scene_object(), "scale", value=factor)
        self._redraw_task2()

    def _redraw_task2(self):
        if not hasattr(self, "zbuffer_canvas"):
            return
        width = max(2, min(self.zbuffer_canvas.winfo_width(), 800))
        height = max(2, min(self.zbuffer_canvas.winfo_height(), 600))
        scene = next(scene for scene in self.scenes if scene.name == self.scene_var.get())
        try:
            image, _depth = render_scene(
                scene.objects, self.zbuffer_camera, width, height,
                cull_backfaces=self.zbuffer_culling.get(),
                enable_zbuffer=self.zbuffer_enabled.get(),
            )
        except (ValueError, ZeroDivisionError, FloatingPointError) as error:
            messagebox.showerror("Ошибка рендеринга Z-буфера", str(error))
            return
        _show_rgb_image(self.zbuffer_canvas, image)

    def _redraw_task3(self):
        if not hasattr(self, "camera_canvas"):
            return
        width = max(2, min(self.camera_canvas.winfo_width(), 800))
        height = max(2, min(self.camera_canvas.winfo_height(), 600))
        try:
            image, _depth = render_scene(
                [(self.static_camera_model, (110, 175, 245))],
                self.task3_camera, width, height, cull_backfaces=True,
            )
        except (ValueError, ZeroDivisionError, FloatingPointError) as error:
            messagebox.showerror("Ошибка камеры", str(error))
            return
        _show_rgb_image(self.camera_canvas, image)
        position = self.task3_camera.position
        self.camera_canvas.create_text(
            12, 12, anchor=tk.NW, fill="white",
            text=f"Положение камеры: ({position[0]:.2f}, {position[1]:.2f}, {position[2]:.2f})",
        )

    def _orbit_task3(self, theta, phi):
        self.task3_camera.orbit_rotate(theta, phi)
        self._redraw_task3()

    def _zoom_task3(self, delta):
        self.task3_camera.zoom(delta)
        self._redraw_task3()

    def _toggle_camera_animation(self):
        if self.camera_animation.get():
            self._animate_camera()
        elif self._camera_after_id is not None:
            self.root.after_cancel(self._camera_after_id)
            self._camera_after_id = None

    def _animate_camera(self):
        if not self.camera_animation.get():
            self._camera_after_id = None
            return
        self.task3_camera.orbit_rotate(2, 0)
        self._redraw_task3()
        self._camera_after_id = self.root.after(40, self._animate_camera)

    def _redraw_all(self):
        self._redraw_task1()
        self._redraw_task2()
        self._redraw_task3()

    def close(self):
        for after_id in (self._culling_after_id, self._camera_after_id):
            if after_id is not None:
                self.root.after_cancel(after_id)
        self.root.destroy()


def main():
    root = tk.Tk()
    Lab8App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
