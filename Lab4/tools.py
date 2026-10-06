"""
Модуль 2 (продолжение) — инструменты. Без tkinter.
Автор: Участник 2.

Каждый Tool предоставляет:
    on_click(p)        -> str | None  — ЛКМ
    on_right_click(p)  -> str | None  — ПКМ
    on_move(p)         -> str | None  — движение мыши
    cancel()
    marks()            -> dict        — что нарисовать
    current_polygon()  -> Polygon | None

Работает со «сценой» через all(), add(), hit() и атрибут selected.
"""

from geometry import Point
from polygons import (Polygon, classify_point_edge, point_in_polygon,
                      is_convex, segment_polygons_intersections,
                      nearest_edge)


class Tool:
    def __init__(self, scene):
        self.scene = scene

    def on_click(self, p):       return None
    def on_right_click(self, p): return None
    def on_move(self, p):        return None
    def cancel(self):            pass
    def marks(self):             return {}
    def current_polygon(self):   return None


class PolygonTool(Tool):
    """ЛКМ — вершина, ПКМ — завершить."""

    def __init__(self, scene):
        super().__init__(scene)
        self.current = None

    def on_click(self, p):
        if self.current is None:
            self.current = Polygon()
        self.current.add_point(p)
        return f"Вершин: {len(self.current)}  (ПКМ — завершить)"

    def on_right_click(self, p):
        if self.current is None or len(self.current) == 0:
            return None
        self.scene.add(self.current)
        self.scene.selected = self.current
        n = len(self.current)
        kind = {1: "точка", 2: "ребро"}.get(n, "полигон")
        self.current = None
        return f"Добавлен {kind} из {n} вершин"

    def cancel(self):
        self.current = None

    def current_polygon(self):
        return self.current


class SelectTool(Tool):
    """ЛКМ — выбрать полигон."""

    def on_click(self, p):
        hit = self.scene.hit(p)
        if hit is not None:
            self.scene.selected = hit
            return f"Выбран полигон из {len(hit)} вершин"
        return "Объект не найден"


class PointTestTool(Tool):
    """ЛКМ — проверить точку на принадлежность полигонам."""

    def __init__(self, scene):
        super().__init__(scene)
        self.point_mark = None

    def on_click(self, p):
        self.point_mark = p
        results = []
        for i, poly in enumerate(self.scene.all()):
            if len(poly) < 3:
                continue
            kind = "выпуклый" if is_convex(poly) else "невыпуклый"
            inside = point_in_polygon(poly, p)
            results.append(f"#{i+1} ({kind}): "
                           f"{'ВНУТРИ' if inside else 'СНАРУЖИ'}")
        if not results:
            return "Нет полигонов с 3+ вершинами"
        return f"Точка ({p.x:.0f}; {p.y:.0f})  →  " + " | ".join(results)

    def cancel(self):
        self.point_mark = None

    def marks(self):
        return {"point_mark": self.point_mark}


class EdgeTestTool(Tool):
    """ЛКМ — положение точки относительно ближайшего ребра."""

    def __init__(self, scene):
        super().__init__(scene)
        self.edge_mark = None

    def on_click(self, p):
        best = nearest_edge(self.scene.all(), p)
        if best is None:
            self.edge_mark = None
            return "Нет рёбер на сцене"
        a, b = best
        res = classify_point_edge(a, b, p)
        self.edge_mark = (a, b, p, res)
        label = {"left":  "СЛЕВА",
                 "right": "СПРАВА",
                 "on":    "НА ПРЯМОЙ"}[res]
        return (f"Точка ({p.x:.0f}; {p.y:.0f}) — {label}  "
                f"[({a.x:.0f};{a.y:.0f}) → ({b.x:.0f};{b.y:.0f})]")

    def cancel(self):
        self.edge_mark = None

    def marks(self):
        return {"edge_mark": self.edge_mark}


class IntersectTool(Tool):
    """ЛКМ #1 — начало ребра, движение мыши — динамика, ЛКМ #2 — фиксация."""

    def __init__(self, scene):
        super().__init__(scene)
        self.first = None
        self.fixed = []
        self.dynamic = None
        self.intersections = []

    def on_click(self, p):
        if self.first is None:
            self.first = p
            self.dynamic = (p, p)
            self.intersections = []
            return "Первая точка задана, ведите мышь"
        self.fixed.append((self.first, p))
        self.first = None
        self.dynamic = None
        self.intersections = []
        return "Ребро зафиксировано, ЛКМ — новое ребро"

    def on_move(self, p):
        if self.first is None:
            return None
        self.dynamic = (self.first, p)
        self.intersections = segment_polygons_intersections(
            self.scene.all(), self.first, p)
        if not self.intersections:
            return None
        return f"Пересечений: {len(self.intersections)}"

    def cancel(self):
        self.first = None
        self.dynamic = None
        self.intersections = []

    def marks(self):
        return {
            "fixed_segments":  list(self.fixed),
            "dynamic_segment": self.dynamic,
            "intersections":   list(self.intersections),
        }