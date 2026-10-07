"""
Scene — тонкая обёртка вокруг списка полигонов + выделение.
Никакой геометрии — все алгоритмы берутся из polygons.py.
"""

from polygons import hit_test


class Scene:
    """Полигоны + выделение."""

    def __init__(self):
        self.polygons = []
        self.selected = None

    def all(self):
        return self.polygons

    def is_empty(self):
        return not self.polygons

    def has_selection(self):
        return self.selected is not None and self.selected in self.polygons

    def add(self, poly):
        self.polygons.append(poly)
        self.selected = poly
        return poly

    def clear(self):
        self.polygons.clear()
        self.selected = None

    def hit(self, p):
        """Верхний объект, содержащий точку p."""
        for poly in reversed(self.polygons):
            if hit_test(poly, p):
                return poly
        return None