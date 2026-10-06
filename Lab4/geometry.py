"""
Модуль 1 — базовая геометрия и аффинные преобразования.
Автор: Участник 1.

Любое преобразование — умножение точки в однородных координатах на матрицу 3x3:

    | x' |   | m00 m01 m02 |   | x |
    | y' | = | m10 m11 m12 | * | y |
    | 1  |   |  0   0   1  |   | 1 |

Мировая система координат «математическая»: ось Y направлена ВВЕРХ.
Переворот Y делается в render.py (ScreenMapping).
"""

import math

EPS = 1e-9


class Point:
    """Точка / радиус-вектор."""

    __slots__ = ("x", "y")

    def __init__(self, x=0.0, y=0.0):
        self.x = float(x)
        self.y = float(y)

    def __add__(self, o):  return Point(self.x + o.x, self.y + o.y)
    def __sub__(self, o):  return Point(self.x - o.x, self.y - o.y)
    def __mul__(self, k):  return Point(self.x * k, self.y * k)
    __rmul__ = __mul__

    def __eq__(self, o):
        return isinstance(o, Point) and self.dist(o) < EPS

    def __repr__(self):
        return f"Point({self.x:.3f}, {self.y:.3f})"

    def copy(self):
        return Point(self.x, self.y)

    def dist(self, o):
        return math.hypot(self.x - o.x, self.y - o.y)

    def as_tuple(self):
        return (self.x, self.y)


def cross(a, b, c):
    """(b-a) x (c-a). >0 — c слева от a->b, <0 — справа, 0 — коллинеарны."""
    return (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)


def point_on_segment(a, b, p, eps=EPS):
    """Лежит ли p на отрезке ab."""
    if abs(cross(a, b, p)) > eps:
        return False
    dot = (p.x - a.x) * (b.x - a.x) + (p.y - a.y) * (b.y - a.y)
    if dot < -eps:
        return False
    sq = (b.x - a.x) ** 2 + (b.y - a.y) ** 2
    return dot <= sq + eps


class Matrix3x3:
    """Однородная матрица аффинного преобразования плоскости."""

    __slots__ = ("m",)

    def __init__(self, rows=None):
        if rows is None:
            self.m = [[1.0, 0.0, 0.0],
                      [0.0, 1.0, 0.0],
                      [0.0, 0.0, 1.0]]
        else:
            self.m = [[float(v) for v in row] for row in rows]

    @staticmethod
    def identity():
        return Matrix3x3()

    @staticmethod
    def translation(dx, dy):
        """Сдвиг на (dx, dy)."""
        return Matrix3x3([[1, 0, dx],
                          [0, 1, dy],
                          [0, 0, 1]])

    @staticmethod
    def rotation(angle_deg):
        """Поворот на угол (в градусах) вокруг начала координат."""
        a = math.radians(angle_deg)
        c, s = math.cos(a), math.sin(a)
        return Matrix3x3([[c, -s, 0],
                          [s,  c, 0],
                          [0,  0, 1]])

    @staticmethod
    def scaling(sx, sy):
        """Масштаб относительно начала координат."""
        return Matrix3x3([[sx, 0, 0],
                          [0, sy, 0],
                          [0,  0, 1]])

    translate = translation

    @staticmethod
    def rotate_about(pivot, angle_deg):
        """Поворот на angle_deg вокруг точки pivot."""
        return (Matrix3x3.translation(pivot.x, pivot.y)
                * Matrix3x3.rotation(angle_deg)
                * Matrix3x3.translation(-pivot.x, -pivot.y))

    @staticmethod
    def scale_about(pivot, sx, sy):
        """Масштаб (sx, sy) относительно точки pivot."""
        return (Matrix3x3.translation(pivot.x, pivot.y)
                * Matrix3x3.scaling(sx, sy)
                * Matrix3x3.translation(-pivot.x, -pivot.y))

    def __mul__(self, other):
        if isinstance(other, Matrix3x3):
            r = [[0.0] * 3 for _ in range(3)]
            for i in range(3):
                for j in range(3):
                    r[i][j] = sum(self.m[i][k] * other.m[k][j]
                                  for k in range(3))
            return Matrix3x3(r)

        if isinstance(other, Point):
            x = self.m[0][0] * other.x + self.m[0][1] * other.y + self.m[0][2]
            y = self.m[1][0] * other.x + self.m[1][1] * other.y + self.m[1][2]
            w = self.m[2][0] * other.x + self.m[2][1] * other.y + self.m[2][2]
            if abs(w) < EPS:
                w = 1.0
            return Point(x / w, y / w)

        return NotImplemented

    def __repr__(self):
        return "Matrix3x3(" + ", ".join(str(r) for r in self.m) + ")"