"""
Полигон трактуется расширенно:
    1 вершина  — точка,
    2 вершины  — ребро (отрезок),
    3+ вершин  — замкнутый полигон.
"""

from geometry import Point, Matrix3x3, cross, point_on_segment, EPS


class Polygon:
    """Полигон: точка / ребро / замкнутая ломаная."""

    def __init__(self, points=None):
        self.points = [p.copy() for p in points] if points else []

    def add_point(self, p):
        self.points.append(p.copy())

    def clear(self):
        self.points.clear()

    def __len__(self):
        return len(self.points)

    def is_empty(self):   return len(self.points) == 0
    def is_point(self):   return len(self.points) == 1
    def is_segment(self): return len(self.points) == 2
    def is_polygon(self): return len(self.points) >= 3

    def centroid(self):
        """Точка / середина отрезка / центроид площади."""
        n = len(self.points)
        if n == 0:
            return Point()
        if n == 1:
            return self.points[0].copy()
        if n == 2:
            a, b = self.points
            return Point((a.x + b.x) / 2.0, (a.y + b.y) / 2.0)

        a2 = cx = cy = 0.0
        for i in range(n):
            x0, y0 = self.points[i].x, self.points[i].y
            x1, y1 = self.points[(i + 1) % n].x, self.points[(i + 1) % n].y
            f = x0 * y1 - x1 * y0
            a2 += f
            cx += (x0 + x1) * f
            cy += (y0 + y1) * f

        if abs(a2) < EPS:
            return Point(sum(p.x for p in self.points) / n,
                         sum(p.y for p in self.points) / n)

        a2 *= 0.5
        return Point(cx / (6.0 * a2), cy / (6.0 * a2))

    def edges(self):
        """Пара точек на каждое ребро. Для 3+ вершин контур замыкается."""
        n = len(self.points)
        if n < 2:
            return []
        if n == 2:
            return [(self.points[0], self.points[1])]
        return [(self.points[i], self.points[(i + 1) % n]) for i in range(n)]

    def apply_matrix(self, m):
        """Единственная точка применения матрицы (m — Matrix3x3)."""
        self.points = [m * p for p in self.points]
        return self


def classify_point_edge(a, b, p):
    """'left' / 'right' / 'on' — положение p относительно ребра a->b."""
    s = cross(a, b, p)
    if abs(s) < EPS:
        return "on"
    return "left" if s > 0 else "right"


def point_in_polygon(poly, p):
    """Принадлежность точки полигону (выпуклому и невыпуклому)."""
    pts = poly.points
    n = len(pts)
    if n < 3:
        return False

    for a, b in poly.edges():
        if point_on_segment(a, b, p):
            return True

    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = pts[i].x, pts[i].y
        xj, yj = pts[j].x, pts[j].y
        if (yi > p.y) != (yj > p.y):
            x_hit = xi + (p.y - yi) * (xj - xi) / (yj - yi)
            if p.x < x_hit:
                inside = not inside
        j = i
    return inside


def is_convex(poly):
    """True, если знак cross для всех троек подряд идущих вершин одинаков."""
    pts = poly.points
    n = len(pts)
    if n < 3:
        return False

    sign = 0
    for i in range(n):
        s = cross(pts[i], pts[(i + 1) % n], pts[(i + 2) % n])
        if abs(s) < EPS:
            continue
        cur = 1 if s > 0 else -1
        if sign == 0:
            sign = cur
        elif sign != cur:
            return False
    return True


def segment_intersection(a1, a2, b1, b2):
    """Точка пересечения отрезков или None (через определители)."""
    d1x, d1y = a2.x - a1.x, a2.y - a1.y
    d2x, d2y = b2.x - b1.x, b2.y - b1.y

    denom = d1x * d2y - d1y * d2x
    if abs(denom) < EPS:
        return None

    ex, ey = b1.x - a1.x, b1.y - a1.y
    t = (ex * d2y - ey * d2x) / denom
    u = (ex * d1y - ey * d1x) / denom

    if -EPS <= t <= 1.0 + EPS and -EPS <= u <= 1.0 + EPS:
        return Point(a1.x + t * d1x, a1.y + t * d1y)
    return None


def segment_polygons_intersections(polygons, a, b):
    """Все точки пересечения отрезка ab с рёбрами всех полигонов."""
    res = []
    for poly in polygons:
        for (c, d) in poly.edges():
            pt = segment_intersection(a, b, c, d)
            if pt is not None and not any(pt.dist(q) < 1e-6 for q in res):
                res.append(pt)
    return res


def dist_to_segment(p, a, b):
    """Расстояние от точки до отрезка ab."""
    dx, dy = b.x - a.x, b.y - a.y
    sq = dx * dx + dy * dy
    if sq < 1e-12:
        return p.dist(a)
    t = ((p.x - a.x) * dx + (p.y - a.y) * dy) / sq
    t = max(0.0, min(1.0, t))
    return p.dist(Point(a.x + t * dx, a.y + t * dy))


def hit_test(poly, p, vertex_tol=10.0, edge_tol=6.0):
    """Попадание мышью по объекту: точка / ребро / полигон."""
    n = len(poly)
    if n == 0:
        return False
    if n == 1:
        return poly.points[0].dist(p) < vertex_tol
    if n == 2:
        a, b = poly.points
        return dist_to_segment(p, a, b) < edge_tol
    return point_in_polygon(poly, p)


def nearest_edge(polygons, p):
    """Ближайшее к p ребро среди всех полигонов или None."""
    best, best_d = None, float("inf")
    for poly in polygons:
        for (a, b) in poly.edges():
            d = dist_to_segment(p, a, b)
            if d < best_d:
                best_d, best = d, (a, b)
    return best