
import numpy as np
from math import cos, sin, radians
import tkinter as tk
from tkinter import ttk

def normalize(v):
    """Нормализует вектор."""
    n = np.linalg.norm(v)
    if n == 0:
        return v
    return v / n

def T(dx, dy, dz):
    """Матрица переноса (смещения)."""
    M = np.eye(4)
    M[:3, 3] = [dx, dy, dz]
    return M

def S(sx, sy, sz):
    """Матрица масштабирования."""
    M = np.eye(4)
    M[0,0], M[1,1], M[2,2] = sx, sy, sz
    return M

def Rx(angle_deg):
    """Матрица поворота вокруг оси X."""
    a = radians(angle_deg)
    ca, sa = cos(a), sin(a)
    M = np.eye(4)
    M[1,1], M[1,2] = ca, -sa
    M[2,1], M[2,2] = sa,  ca
    return M

def Ry(angle_deg):
    """Матрица поворота вокруг оси Y."""
    a = radians(angle_deg)
    ca, sa = cos(a), sin(a)
    M = np.eye(4)
    M[0,0], M[0,2] =  ca, sa
    M[2,0], M[2,2] = -sa, ca
    return M

def Rz(angle_deg):
    """Матрица поворота вокруг оси Z."""
    a = radians(angle_deg)
    ca, sa = cos(a), sin(a)
    M = np.eye(4)
    M[0,0], M[0,1] = ca, -sa
    M[1,0], M[1,1] = sa,  ca
    return M

def reflect(plane: str):
    """Отражение относительно координатной плоскости: 'xy', 'yz', или 'xz'."""
    plane = plane.lower()
    if plane == "xy":
        return S(1, 1, -1)
    if plane == "yz":
        return S(-1, 1, 1)
    if plane == "xz":
        return S(1, -1, 1)
    raise ValueError("Плоскость должна быть: 'xy', 'yz', 'xz'")



class PolyhedronTransforms:
    """Базовые преобразования Polyhedron через его apply()."""

    def translate(self, dx, dy, dz):
        """Перенос (смещение)."""
        return self.apply(T(dx, dy, dz))

    def scale(self, sx, sy, sz):
        """Масштабирование."""
        return self.apply(S(sx, sy, sz))


    def rotate_x(self, angle_deg):
        """Поворот вокруг оси X."""
        return self.apply(Rx(angle_deg))

    def rotate_y(self, angle_deg):
        """Поворот вокруг оси Y."""
        return self.apply(Ry(angle_deg))

    def rotate_z(self, angle_deg):
        """Поворот вокруг оси Z."""
        return self.apply(Rz(angle_deg))

    def reflect(self, plane: str):
        """Отражение относительно координатной плоскости."""
        return self.apply(reflect(plane))



class TransformControls:
    """Базовые поля и обработчики; вызывает сборку пространственных элементов UI."""

    def build_transform_controls(self, root):
        # Панель преобразований
        controls = ttk.LabelFrame(root, text='Преобразования')
        controls.pack(side=tk.TOP, fill=tk.X, padx=8, pady=(0,8))

        # Смещение
        trf1 = ttk.Frame(controls)
        trf1.pack(side=tk.TOP, fill=tk.X, pady=4)
        ttk.Label(trf1, text='Смещение: dx').pack(side=tk.LEFT)
        self.dx_entry = ttk.Entry(trf1, width=6)
        self.dx_entry.insert(0, '0')
        self.dx_entry.pack(side=tk.LEFT, padx=(4,8))
        ttk.Label(trf1, text='dy').pack(side=tk.LEFT)
        self.dy_entry = ttk.Entry(trf1, width=6)
        self.dy_entry.insert(0, '0')
        self.dy_entry.pack(side=tk.LEFT, padx=(4,8))
        ttk.Label(trf1, text='dz').pack(side=tk.LEFT)
        self.dz_entry = ttk.Entry(trf1, width=6)
        self.dz_entry.insert(0, '0')
        self.dz_entry.pack(side=tk.LEFT, padx=(4,8))
        ttk.Button(trf1, text='Применить', command=self.apply_translate).pack(side=tk.LEFT, padx=6)

        # Поворот
        trf2 = ttk.Frame(controls)
        trf2.pack(side=tk.TOP, fill=tk.X, pady=4)
        ttk.Label(trf2, text='Поворот: ось').pack(side=tk.LEFT)
        self.rot_axis_var = tk.StringVar(value='x')
        self.rot_axis = ttk.Combobox(trf2, textvariable=self.rot_axis_var, values=['x','y','z'], state='readonly', width=4)
        self.rot_axis.pack(side=tk.LEFT, padx=(4,8))
        ttk.Label(trf2, text='угол (°)').pack(side=tk.LEFT)
        self.angle_entry = ttk.Entry(trf2, width=8)
        self.angle_entry.insert(0, '30')
        self.angle_entry.pack(side=tk.LEFT, padx=(4,8))
        ttk.Button(trf2, text='Повернуть', command=self.apply_rotate).pack(side=tk.LEFT, padx=6)
        self.build_center_rotation_control(trf2)

        # Масштаб
        trf3 = ttk.Frame(controls)
        trf3.pack(side=tk.TOP, fill=tk.X, pady=4)
        ttk.Label(trf3, text='Масштаб: sx').pack(side=tk.LEFT)
        self.sx_entry = ttk.Entry(trf3, width=6)
        self.sx_entry.insert(0, '1')
        self.sx_entry.pack(side=tk.LEFT, padx=(4,8))
        ttk.Label(trf3, text='sy').pack(side=tk.LEFT)
        self.sy_entry = ttk.Entry(trf3, width=6)
        self.sy_entry.insert(0, '1')
        self.sy_entry.pack(side=tk.LEFT, padx=(4,8))
        ttk.Label(trf3, text='sz').pack(side=tk.LEFT)
        self.sz_entry = ttk.Entry(trf3, width=6)
        self.sz_entry.insert(0, '1')
        self.sz_entry.pack(side=tk.LEFT, padx=(4,8))
        ttk.Button(trf3, text='Масштаб', command=self.apply_scale).pack(side=tk.LEFT, padx=6)

        self.build_center_scale_controls(trf3)

        self.build_line_rotation_controls(controls)

        # Отражение
        trf4 = ttk.Frame(controls)
        trf4.pack(side=tk.TOP, fill=tk.X, pady=4)
        ttk.Label(trf4, text='Отражение: плоскость').pack(side=tk.LEFT)
        self.refl_plane_var = tk.StringVar(value='xy')
        self.refl_plane = ttk.Combobox(trf4, textvariable=self.refl_plane_var, values=['xy','yz','xz'], state='readonly', width=6)
        self.refl_plane.pack(side=tk.LEFT, padx=(6,10))
        ttk.Button(trf4, text='Отразить', command=self.apply_reflect).pack(side=tk.LEFT, padx=6)

    def _parse_float(self, widget, default=0.0):
        try:
            return float(widget.get())
        except Exception:
            return default

    def apply_translate(self):
        dx = self._parse_float(self.dx_entry, 0.0)
        dy = self._parse_float(self.dy_entry, 0.0)
        dz = self._parse_float(self.dz_entry, 0.0)
        self.model.translate(dx, dy, dz)
        self.redraw()

    def apply_rotate(self):
        axis = (self.rot_axis_var.get() or 'x').lower()
        angle = self._parse_float(self.angle_entry, 0.0)
        # Поворот вокруг оси, проходящей через начало координат
        if axis == 'x':
            self.model.rotate_x(angle)
        elif axis == 'y':
            self.model.rotate_y(angle)
        else:
            self.model.rotate_z(angle)
        self.redraw()


    def apply_scale(self):
        sx = self._parse_float(self.sx_entry, 1.0)
        sy = self._parse_float(self.sy_entry, 1.0)
        sz = self._parse_float(self.sz_entry, 1.0)
        # Анизотропный масштаб вокруг начала координат
        self.model.scale(sx, sy, sz)
        self.redraw()


    def apply_reflect(self):
        plane = (self.refl_plane_var.get() or 'xy').lower()
        if plane not in ('xy','yz','xz'):
            plane = 'xy'
        self.model.reflect(plane)
        self.redraw()

