
import numpy as np
import tkinter as tk
from tkinter import ttk

from transforms import PolyhedronTransforms, normalize
from view_and_spatial import SpatialTransforms

def to_h(point3):
    """Возвращает однородный 4x1 вектор из 3D точки (x, y, z)."""
    x, y, z = point3
    return np.array([x, y, z, 1.0], dtype=float)

def from_h(vec4):
    """Возвращает 3D точку из однородного вектора после перспективного деления."""
    w = vec4[3]
    if w == 0:
        raise ZeroDivisionError("Однородная координата w == 0 при дегомогенизации")
    return (vec4[:3] / w)

class Point:
    """Класс для представления точки в 3D пространстве."""
    def __init__(self, x, y, z):
        self.v = to_h((x, y, z))

    @property
    def xyz(self):
        return from_h(self.v)

    def as_array(self):
        return self.v.copy()

class PolygonFace:
    """Класс для представления грани многогранника."""
    def __init__(self, vertex_indices):
        self.indices = list(vertex_indices)

class Polyhedron(PolyhedronTransforms, SpatialTransforms):
    """Класс для представления многогранника."""
    def __init__(self, vertices, faces):
        """
        vertices: список вершин (кортежи (x,y,z))
        faces: список граней (списки индексов вершин)
        """
        self.V = np.array([to_h(p) for p in vertices], dtype=float).T  # 4xN (столбец = вершина)
        self.faces = [PolygonFace(f) for f in faces]

    # --- основные методы ---
    def copy(self):
        """Создает копию многогранника."""
        P = Polyhedron([(0,0,0)], [[]])
        P.V = self.V.copy()
        P.faces = [PolygonFace(f.indices.copy()) for f in self.faces]
        return P

    def center(self):
        """Вычисляет центр многогранника."""
        pts = self.V[:3, :] / self.V[3, :]
        return np.mean(pts, axis=1)

    def apply(self, M):
        """Применяет матричное преобразование 4x4."""
        self.V = M @ self.V
        return self

    def edges(self):
        """Вычисляет список ребер многогранника."""
        es = set()
        if self.faces and len(self.faces[0].indices)>0:
            # Строим ребра из граней
            for f in self.faces:
                idx = f.indices
                for i in range(len(idx)):
                    a = idx[i]
                    b = idx[(i+1) % len(idx)]
                    es.add(tuple(sorted((a,b))))
        else:
            # Резервный метод: соединение ближайших соседей
            pts = (self.V[:3,:] / self.V[3,:]).T
            n = len(pts)
            D = np.linalg.norm(pts[None,:,:]-pts[:,None,:], axis=-1)
            for i in range(n):
                neigh = list(np.argsort(D[i])[1:4])  # 3 ближайших соседа
                for j in neigh:
                    es.add(tuple(sorted((i,j))))
        return sorted(list(es))

    # --- проекция ---
    def projected(self, matrix4x4):
        """Возвращает 2D точки (x,y) после применения матрицы проекции."""
        Pv = matrix4x4 @ self.V
        # Перспективное деление
        Pv = Pv / Pv[3, :]
        # возвращаем только (x,y)
        return Pv[0, :], Pv[1, :]

def tetrahedron():
    """Создает правильный тетраэдр с центром в начале координат."""
    V = [(1, 1, 1),
         (1,-1,-1),
         (-1, 1,-1),
         (-1,-1, 1)]
    F = [
        [0,1,2],
        [0,3,1],
        [0,2,3],
        [1,3,2]
    ]
    return Polyhedron(V, F)

def hexahedron():
    """Правильный гексаэдр (куб) с центром в начале координат и ребром 2."""
    V = [
        (-1, -1, -1),  # 0
        ( 1, -1, -1),  # 1
        ( 1,  1, -1),  # 2
        (-1,  1, -1),  # 3
        (-1, -1,  1),  # 4
        ( 1, -1,  1),  # 5
        ( 1,  1,  1),  # 6
        (-1,  1,  1),  # 7
    ]
    # 6 квадратных граней (порядок вершин по контуру)
    F = [
        [0, 1, 2, 3],  # z = -1 (низ)
        [4, 5, 6, 7],  # z = +1 (верх)
        [0, 1, 5, 4],  # y = -1
        [1, 2, 6, 5],  # x = +1
        [2, 3, 7, 6],  # y = +1
        [3, 0, 4, 7],  # x = -1
    ]
    return Polyhedron(V, F)

def octahedron():
    """Правильный октаэдр с центром в начале координат и ребром √2."""
    V = [
        ( 1,  0,  0),  # 0
        (-1,  0,  0),  # 1
        ( 0,  1,  0),  # 2
        ( 0, -1,  0),  # 3
        ( 0,  0,  1),  # 4 (верх)
        ( 0,  0, -1),  # 5 (низ)
    ]
    # 8 треугольных граней
    F = [
        [4, 0, 2],
        [4, 2, 1],
        [4, 1, 3],
        [4, 3, 0],
        [5, 2, 0],
        [5, 1, 2],
        [5, 3, 1],
        [5, 0, 3],
    ]
    return Polyhedron(V, F)

def icosahedron():
    """Икосаэдр, построенный с цилиндра.
    Полюса: (0,0,±sqrt(5)/2); кольца радиуса 1 на z=±1/2, нижнее смещено на 36°.
    Возвращает Polyhedron с явными 20 треугольными гранями.
    """
    def deg(a): return np.deg2rad(a)

    z_top, z_bot = +0.5, -0.5
    r = 1.0
    z_pole = np.sqrt(5.0) / 2.0

    V = []
    # верхняя вершина
    V.append((0.0, 0.0, +z_pole))

    # 1..5 — верхнее кольцо (углы 0,72,144,216,288)
    for k in range(5):
        ang = deg(72*k)
        V.append((r*np.cos(ang), r*np.sin(ang), z_top))

    # 6..10 — нижнее кольцо (углы 36,108,180,252,324)
    for k in range(5):
        ang = deg(36 + 72*k)
        V.append((r*np.cos(ang), r*np.sin(ang), z_bot))

    # нижняя вершина
    V.append((0.0, 0.0, -z_pole))

    F = []

    # Верхняя «шапка»: 5 треугольников (0, Ti, Ti+1)
    for i in range(5):
        F.append([0, 1+i, 1+((i+1) % 5)])

    # Средняя зона: 10 треугольников (по 2 на «сектор»).
    # Важный момент: у вершины верхнего кольца Ti ближайшие нижние — Bi и B(i-1).
    for i in range(5):
        Ti = 1 + i  # Текущая вершина верхнего кольца (1-5)
        Tip1 = 1 + ((i + 1) % 5)  # Следующая вершина верхнего кольца
        Bi = 6 + i  # Соответствующая вершина нижнего кольца (6-10)
        Bim1 = 6 + ((i - 1) % 5)  # Предыдущая вершина нижнего кольца

        # «верхний» из пары (Ti, Bi, B(i-1))
        F.append([Ti, Bi, Bim1])  # Треугольник, соединяющий верхнюю вершину с двумя нижними
        # «нижний» из пары (Bi, Tip1, Ti)
        F.append([Bi, Tip1, Ti])  # Треугольник, соединяющий нижнюю вершину с двумя верхними

    # Нижняя «шапка»: 5 треугольников (11, Bj+1, Bj)
    for j in range(5):
        Bj   = 6 + j
        Bjp1 = 6 + ((j+1) % 5)
        F.append([11, Bjp1, Bj])

    return Polyhedron(V, F)


def dodecahedron():
    """Додекаэдр как дуал к идущему выше 'цилиндрическому' икосаэдру:
    вершины = центры тяжести треугольных граней икосаэдра,
    грани = пятиугольники, по одному на каждую вершину икосаэдра.
    """
    I = icosahedron()
    # координаты вершин икосаэдра (N x 3)
    V = (I.V[:3, :] / I.V[3, :]).T  # Нормализация: делим x,y,z на w, транспонируем в N×3
    faces_I = [f.indices for f in I.faces]  # Извлекаем списки индексов для всех граней

    # 20 вершин додекаэдра: центроиды треугольников
    D_vertices = [tuple(np.mean(V[idxs], axis=0)) for idxs in faces_I]

    # каждой вершине икосаэдра ставим в соответствие номера граней в которых она используется
    incident = [[] for _ in range(len(V))]
    for fi, tri in enumerate(faces_I):
        for vid in tri:
            incident[vid].append(fi)

    # Построим 12 пятиугольных граней додекаэдра.
    D_faces = []
    for vid, fids in enumerate(incident):
        if len(fids) != 5:
            # на всякий случай пропустим аномалии (их быть не должно)
            continue
        p = V[vid]              # точка-центр «звезды» (вершины икосаэдра)
        n = normalize(p)        # используем направление p как «нормаль» локальной плоскости
        # ортонормированный базис {e1,e2} в плоскости, перпендикулярной n
        tmp = np.array([1.0, 0.0, 0.0]) if abs(n[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
        e1 = normalize(np.cross(n, tmp))
        e2 = np.cross(n, e1)

        # отсортируем прилегающие центроиды по углу в этой плоскости
        ang_with_id = []
        for fid in fids:
            c = np.mean(V[faces_I[fid]], axis=0)
            d = c - p
            ang = np.arctan2(np.dot(d, e2), np.dot(d, e1))
            ang_with_id.append((ang, fid))
        ang_with_id.sort()#массив отсортированных по полярному углу точек, чтобы точки брались по кругу

        D_faces.append([fid for ang, fid in ang_with_id]) #добавляем грань

    return Polyhedron(D_vertices, D_faces)

POLY_BUILDERS = {
    'Тетраэдр': tetrahedron,
    'Гексаэдр (куб)': hexahedron,
    'Октаэдр': octahedron,
    'Икосаэдр': icosahedron,
    'Додекаэдр': dodecahedron,
}

def make_poly(name: str) -> Polyhedron:
    """Создаёт выбранный многогранник без дополнительных поворотов/масштабов."""
    builder = POLY_BUILDERS.get(name)
    if builder is None:
        builder = hexahedron
    return builder()

class GeometryControls:
    """Часть App: текущая модель, выбор многогранника и сброс."""

    def build_geometry_controls(self, top):
        self.poly_var = tk.StringVar(value='Гексаэдр (куб)')
        # Текущая модель многогранника
        self.model: Polyhedron = make_poly(self.poly_var.get())

        ttk.Label(top, text='Многогранник:').pack(side=tk.LEFT)
        self.poly_box = ttk.Combobox(
            top,
            textvariable=self.poly_var,
            values=list(POLY_BUILDERS.keys()),
            state='readonly',
            width=18,
        )
        self.poly_box.pack(side=tk.LEFT, padx=(6, 12))
        self.poly_box.bind('<<ComboboxSelected>>', lambda e: self.rebuild_model())

        ttk.Button(top, text='Сброс', command=self.rebuild_model).pack(side=tk.RIGHT)

    def get_poly(self) -> Polyhedron:
        return self.model

    def rebuild_model(self):
        self.model = make_poly(self.poly_var.get())
        self.redraw()
