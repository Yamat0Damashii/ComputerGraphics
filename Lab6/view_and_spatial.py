
from __future__ import annotations

from math import cos, sin, radians
from typing import TYPE_CHECKING
import numpy as np
import tkinter as tk
from tkinter import ttk

from transforms import T, S, Rx, Ry, Rz, normalize

if TYPE_CHECKING:
    from geometry import Polyhedron

def rodrigues_axis_angle(axis, angle_deg):
    """Поворот 3x3 вокруг единичной оси на угол в градусах."""
    axis = normalize(np.asarray(axis, dtype=float))
    a = radians(angle_deg)
    c, s = cos(a), sin(a)
    K = np.array([[0, -axis[2], axis[1]],
                  [axis[2], 0, -axis[0]],
                  [-axis[1], axis[0], 0]], dtype=float)
    R = np.eye(3)*c + (1-c)*np.outer(axis, axis) + s*K
    return R

def R_around_line(p1, p2, angle_deg):
    """Матрица поворота 4x4 вокруг произвольной 3D линии p1->p2 на угол."""
    p1 = np.asarray(p1, dtype=float)
    p2 = np.asarray(p2, dtype=float)
    axis = p2 - p1
    R3 = rodrigues_axis_angle(axis, angle_deg)  # 3x3
    M = np.eye(4)
    M[:3,:3] = R3
    return T(*p1) @ M @ T(*(-p1))


class SpatialTransforms:
    """Перенесённые методы модели для центра и произвольной прямой."""

    def scale_about_center(self, s):
        c = self.center()
        return self.apply(T(*c) @ S(s, s, s) @ T(*(-c)))

    def rotate_around_axis_through_center(self, axis: str, angle_deg):
        axis = axis.lower()
        c = self.center()
        R = {'x': Rx, 'y': Ry, 'z': Rz}[axis](angle_deg)
        return self.apply(T(*c) @ R @ T(*(-c)))

    def rotate_around_line(self, p1, p2, angle_deg):
        """Поворот вокруг произвольной линии."""
        return self.apply(R_around_line(p1, p2, angle_deg))


def perspective(f=1.5):
    """
    Простая матрица перспективной проекции.
    Камера в начале координат смотрит вдоль +Z; точки сцены должны иметь z > 0.
    """
    M = np.eye(4)
    M[3,3] = 0.0
    M[3,2] = 1.0 / f  # w' = z/f  -> x' = x / (z/f) = f*x/z
    return M

def ortho_xy():
    """Ортографическая проекция на плоскость XY (отбрасывание Z)."""
    M = np.eye(4)
    M[2,2] = 0.0
    return M

def isometric_projection_matrix():
    """Аксонометрическая (изометрическая) проекция = поворот + ортографическая проекция."""
    # Классическая изометрия: поворот вокруг Z на 45°, затем вокруг X на ~35.264°
    alpha = 35.264389682754654
    beta = 45.0
    R = Rx(alpha) @ Rz(beta)
    return ortho_xy() @ R

def project_points(P: Polyhedron, proj_mode: str, f: float = 1.8):
    """Возвращает 2D проекцию вершин и список рёбер.

    proj_mode: 'perspective' или 'axonometric'/'isometric'
    """
    Q = P.copy()
    if proj_mode == 'perspective':
        # Стандартная перспектива: камера в начале координат, смотрит вдоль +Z; сместим модель на z=5
        Q = Q.translate(0, 0, 5.0)
        M = perspective(f)
    else:
        # Стандартная изометрическая (аксонометрическая) матрица
        M = isometric_projection_matrix()
    x, y = Q.projected(M)
    edges = Q.edges()
    return (x, y, edges)

def to_pixels(x, y, width, height, scale=120.0):
    """Перевод модельных координат в пиксели с фиксированным масштабом и центрированием."""
    x = np.asarray(x)
    y = np.asarray(y)
    cx = width * 0.5
    cy = height * 0.5
    Xs = cx + scale * x
    Ys = cy - scale * y  # переворот оси Y
    return Xs, Ys


class ViewControls:
    """Пространственные элементы управления и отображение; используют self.model."""

    def build_center_rotation_control(self, trf2):
        ttk.Button(trf2, text='Повернуть (через центр)', command=self.apply_rotate_center).pack(side=tk.LEFT, padx=6)

    def build_center_scale_controls(self, trf3):
        # Равномерный масштаб вокруг центра (одно число)
        ttk.Label(trf3, text=' s').pack(side=tk.LEFT, padx=(12,2))
        self.s_uniform_entry = ttk.Entry(trf3, width=6)
        self.s_uniform_entry.insert(0, '1')
        self.s_uniform_entry.pack(side=tk.LEFT, padx=(2,6))
        ttk.Button(trf3, text='Масштаб (через центр)', command=self.apply_scale_center).pack(side=tk.LEFT, padx=6)

    def build_line_rotation_controls(self, controls):
        # Вращение вокруг произвольной прямой (p1 -> p2)
        trf5 = ttk.Frame(controls)
        trf5.pack(side=tk.TOP, fill=tk.X, pady=4)
        ttk.Label(trf5, text='Поворот вокруг прямой:').pack(side=tk.LEFT)
        ttk.Label(trf5, text='p1(x,y,z)').pack(side=tk.LEFT, padx=(8,2))
        self.p1x_entry = ttk.Entry(trf5, width=5); self.p1x_entry.insert(0,'0'); self.p1x_entry.pack(side=tk.LEFT)
        self.p1y_entry = ttk.Entry(trf5, width=5); self.p1y_entry.insert(0,'0'); self.p1y_entry.pack(side=tk.LEFT)
        self.p1z_entry = ttk.Entry(trf5, width=5); self.p1z_entry.insert(0,'0'); self.p1z_entry.pack(side=tk.LEFT)
        ttk.Label(trf5, text='p2(x,y,z)').pack(side=tk.LEFT, padx=(8,2))
        self.p2x_entry = ttk.Entry(trf5, width=5); self.p2x_entry.insert(0,'0'); self.p2x_entry.pack(side=tk.LEFT)
        self.p2y_entry = ttk.Entry(trf5, width=5); self.p2y_entry.insert(0,'1'); self.p2y_entry.pack(side=tk.LEFT)
        self.p2z_entry = ttk.Entry(trf5, width=5); self.p2z_entry.insert(0,'0'); self.p2z_entry.pack(side=tk.LEFT)
        ttk.Label(trf5, text='угол (°)').pack(side=tk.LEFT, padx=(8,2))
        self.angle_line_entry = ttk.Entry(trf5, width=7); self.angle_line_entry.insert(0,'30'); self.angle_line_entry.pack(side=tk.LEFT)
        ttk.Button(trf5, text='Повернуть (линия)', command=self.apply_rotate_line).pack(side=tk.LEFT, padx=6)

    def apply_rotate_center(self):
        """Явное вращение вокруг прямой через центр модели, параллельной выбранной оси."""
        axis = (self.rot_axis_var.get() or 'x').lower()
        angle = self._parse_float(self.angle_entry, 0.0)
        self.model.rotate_around_axis_through_center(axis, angle)
        self.redraw()

    def apply_scale_center(self):
        # Равномерный масштаб вокруг центра модели (одно число)
        s = self._parse_float(self.s_uniform_entry, 1.0)
        self.model.scale_about_center(s)
        self.redraw()

    def apply_rotate_line(self):
        # Чтение точек p1, p2 и угла
        x1 = self._parse_float(self.p1x_entry, 0.0)
        y1 = self._parse_float(self.p1y_entry, 0.0)
        z1 = self._parse_float(self.p1z_entry, 0.0)
        x2 = self._parse_float(self.p2x_entry, 0.0)
        y2 = self._parse_float(self.p2y_entry, 1.0)
        z2 = self._parse_float(self.p2z_entry, 0.0)
        angle = self._parse_float(self.angle_line_entry, 0.0)
        p1 = (x1, y1, z1)
        p2 = (x2, y2, z2)
        # Проверка на нулевую ось
        if np.linalg.norm(np.asarray(p2, float) - np.asarray(p1, float)) < 1e-12:
            # Ничего не делаем, если ось нулевая
            return
        self.model.rotate_around_line(p1, p2, angle)
        self.redraw()

    def build_projection_controls(self, top):
        self.proj_var = tk.StringVar(value='perspective')  # 'perspective' | 'isometric'

        ttk.Label(top, text='Проекция:').pack(side=tk.LEFT)
        self.rb_persp = ttk.Radiobutton(
            top, text='Перспективная', value='perspective', variable=self.proj_var,
            command=self.redraw
        )
        self.rb_iso = ttk.Radiobutton(
            top, text='Аксонометрическая', value='isometric', variable=self.proj_var,
            command=self.redraw
        )
        self.rb_persp.pack(side=tk.LEFT, padx=(6, 6))
        self.rb_iso.pack(side=tk.LEFT)

    def build_canvas(self, root):
        self.canvas = tk.Canvas(root, bg='white', width=800, height=600)
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.canvas.bind('<Configure>', lambda e: self.redraw())

        self.redraw()

    def redraw(self):
        self.canvas.delete('all')
        W = self.canvas.winfo_width()
        H = self.canvas.winfo_height()
        if W < 10 or H < 10:
            return

        P = self.get_poly()
        mode = self.proj_var.get()
        x, y, edges = project_points(P, mode)
        # Фиксированный небольшой размер фигур
        Xs, Ys = to_pixels(x, y, W, H, scale=120.0)

        # Рисуем рёбра
        for a, b in edges:
            self.canvas.create_line(float(Xs[a]), float(Ys[a]), float(Xs[b]), float(Ys[b]), fill='#1f77b4')
