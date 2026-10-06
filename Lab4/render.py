"""
Модуль 1 (продолжение) — визуализация сцены на Canvas.
Автор: Участник 1.

render.py не знает про окно, кнопки и события: принимает готовый canvas
и рисует то, что ему передали. ScreenMapping инкапсулирует переворот Y.

Полигоны используются «по утиной типизации» — достаточно, чтобы у poly
были .points и .centroid(). Поэтому render.py не импортирует polygons.py.
"""

import tkinter as tk

from geometry import Point


class ScreenMapping:
    """Мир (Y вверх) <-> экран (Y вниз)."""

    __slots__ = ("w", "h")

    def __init__(self, width, height):
        self.w = width
        self.h = height

    def to_world(self, sx, sy):
        return Point(sx, self.h - sy)

    def to_screen(self, p):
        return (p.x, self.h - p.y)


COLOR_DEFAULT   = "#1f77b4"
COLOR_SELECTED  = "#d62728"
COLOR_POINT_MSG = "#9467bd"
COLOR_ISEC      = "#d62728"
COLOR_SEG_FIX   = "#8c564b"
COLOR_SEG_DYN   = "#8c564b"

EDGE_COLORS = {"left":  "#2ca02c",
               "right": "#d62728",
               "on":    "#ff7f0e"}


def edge_color(res):
    return EDGE_COLORS.get(res, "#888888")


def draw_grid(canvas, mapping, step=50):
    w, h = int(mapping.w), int(mapping.h)
    for x in range(0, w + 1, step):
        canvas.create_line(x, 0, x, h, fill="#eeeeee")
    for y in range(0, h + 1, step):
        canvas.create_line(0, y, w, y, fill="#eeeeee")


def draw_polygon(canvas, poly, mapping, selected=False):
    """Универсально: точка / ребро / полигон (1 / 2 / N вершин)."""
    n = len(poly.points)
    if n == 0:
        return

    color = COLOR_SELECTED if selected else COLOR_DEFAULT
    pts = [mapping.to_screen(p) for p in poly.points]

    if n == 1:
        x, y = pts[0]
        canvas.create_oval(x - 5, y - 5, x + 5, y + 5,
                           outline=color, width=2)
    elif n == 2:
        canvas.create_line(*pts[0], *pts[1], fill=color, width=2)
    else:
        flat = [v for xy in pts for v in xy]
        canvas.create_polygon(flat, outline=color, fill="",
                              width=2, joinstyle=tk.ROUND)
        if selected:
            cx, cy = mapping.to_screen(poly.centroid())
            canvas.create_line(cx - 8, cy, cx + 8, cy, fill=color)
            canvas.create_line(cx, cy - 8, cx, cy + 8, fill=color)

    for (x, y) in pts:
        canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill=color, outline="")


def draw_pivot(canvas, p, mapping, color="#333333"):
    """Маркер опорной точки для отложенного клика."""
    x, y = mapping.to_screen(p)
    canvas.create_line(x - 10, y, x + 10, y, fill=color, width=2)
    canvas.create_line(x, y - 10, x, y + 10, fill=color, width=2)
    canvas.create_oval(x - 4, y - 4, x + 4, y + 4, outline=color, width=2)


def draw_marks(canvas, marks, mapping):
    """
    marks — словарь от текущего Tool:
        point_mark      : Point                        — «точка в полигоне»
        edge_mark       : (a, b, p, "left|right|on")   — положение точки
        fixed_segments  : [(a, b), ...]                — зафиксированные рёбра
        dynamic_segment : (a, b) | None                — строящееся ребро
        intersections   : [Point, ...]                 — найденные пересечения
    """
    if not marks:
        return

    p = marks.get("point_mark")
    if p is not None:
        x, y = mapping.to_screen(p)
        canvas.create_oval(x - 6, y - 6, x + 6, y + 6,
                           outline=COLOR_POINT_MSG, width=2)

    em = marks.get("edge_mark")
    if em is not None:
        a, b, p, res = em
        col = edge_color(res)
        x1, y1 = mapping.to_screen(a)
        x2, y2 = mapping.to_screen(b)
        canvas.create_line(x1, y1, x2, y2, fill=col, width=3)
        x, y = mapping.to_screen(p)
        canvas.create_oval(x - 6, y - 6, x + 6, y + 6, outline=col, width=2)
        canvas.create_text(x + 12, y - 12, text=res.upper(), fill=col,
                           font=("Segoe UI", 9, "bold"), anchor="w")

    for a, b in marks.get("fixed_segments", ()):
        x1, y1 = mapping.to_screen(a)
        x2, y2 = mapping.to_screen(b)
        canvas.create_line(x1, y1, x2, y2, fill=COLOR_SEG_FIX,
                           width=2, dash=(6, 3))

    ds = marks.get("dynamic_segment")
    if ds is not None:
        a, b = ds
        x1, y1 = mapping.to_screen(a)
        x2, y2 = mapping.to_screen(b)
        canvas.create_line(x1, y1, x2, y2, fill=COLOR_SEG_DYN, width=2)

    for q in marks.get("intersections", ()):
        qx, qy = mapping.to_screen(q)
        canvas.create_oval(qx - 5, qy - 5, qx + 5, qy + 5,
                           outline=COLOR_ISEC, width=2)
        canvas.create_text(qx + 10, qy + 10,
                           text=f"({q.x:.0f}; {q.y:.0f})",
                           fill=COLOR_ISEC, font=("Consolas", 8), anchor="nw")