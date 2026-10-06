"""
Модуль 3 (продолжение) — сборка GUI на tkinter.
Автор: Участник 3.

Здесь только окно, панель, привязка событий, диалоги параметров.
Геометрия — в tools.py/polygons.py, отрисовка — в render.py.
"""

import tkinter as tk
from tkinter import simpledialog, messagebox

from geometry import Matrix3x3
from scene import Scene
from render import (ScreenMapping, draw_grid, draw_polygon,
                    draw_marks, draw_pivot)
from tools import (PolygonTool, SelectTool, PointTestTool,
                   EdgeTestTool, IntersectTool)


W, H = 940, 620

TOOL_FACTORY = {
    "polygon":   PolygonTool,
    "select":    SelectTool,
    "point":     PointTestTool,
    "edge":      EdgeTestTool,
    "intersect": IntersectTool,
}

HINTS = {
    "polygon":   "ЛКМ — вершина, ПКМ — завершить полигон",
    "select":    "ЛКМ — выбрать полигон",
    "point":     "ЛКМ — проверить точку на принадлежность полигонам",
    "edge":      "ЛКМ — классифицировать точку относительно ближайшего ребра",
    "intersect": "ЛКМ — первая точка, движение мыши, ЛКМ — вторая точка",
}

BUTTONS_TOOLS = (
    ("Полигон",           "polygon"),
    ("Точка → полигон",   "point"),
    ("Точка → ребро",     "edge"),
    ("Пересечение рёбер", "intersect"),
    ("Выбрать полигон",   "select"),
)


class App:
    def __init__(self, root):
        self.root = root
        root.title("Полигоны: аффинные преобразования и геометрия")
        root.resizable(False, False)

        self.scene = Scene()
        self.mapping = ScreenMapping(W, H)

        self.mode = "polygon"
        self.tool = TOOL_FACTORY[self.mode](self.scene)
        self.pending_pivot_mode = None
        self.pending_pivot_mark = None

        self._build_ui()
        self._bind()
        self.set_mode("polygon")

    # ---------- UI ----------
    def _build_ui(self):
        panel = tk.Frame(self.root, width=230, bg="#e8e8e8")
        panel.pack(side=tk.LEFT, fill=tk.Y)
        panel.pack_propagate(False)

        tk.Label(panel, text="ИНСТРУМЕНТЫ", bg="#e8e8e8",
                 font=("Segoe UI", 11, "bold")).pack(pady=(12, 6))

        self.mode_buttons = {}
        for text, mode in BUTTONS_TOOLS:
            b = tk.Button(panel, text=text, anchor="w", relief=tk.RIDGE,
                          bg="#f0f0f0",
                          command=lambda m=mode: self.set_mode(m))
            b.pack(fill=tk.X, padx=8, pady=2)
            self.mode_buttons[mode] = b

        tk.Label(panel, text="ПРЕОБРАЗОВАНИЯ", bg="#e8e8e8",
                 font=("Segoe UI", 10, "bold")).pack(pady=(16, 4))

        for text, cmd in (("Смещение dx, dy",       self.op_translate),
                          ("Поворот вокруг точки",  self.op_rotate_point),
                          ("Поворот вокруг центра", self.op_rotate_center),
                          ("Масштаб отн. точки",    self.op_scale_point),
                          ("Масштаб отн. центра",   self.op_scale_center)):
            tk.Button(panel, text=text, anchor="w", relief=tk.RIDGE,
                      command=cmd).pack(fill=tk.X, padx=8, pady=2)

        tk.Label(panel, text="", bg="#e8e8e8").pack(pady=4)
        tk.Button(panel, text="Очистить сцену", anchor="w",
                  relief=tk.RIDGE, fg="#a00", command=self.op_clear
                  ).pack(fill=tk.X, padx=8, pady=2)

        tk.Label(panel, bg="#e8e8e8", justify="left", wraplength=210,
                 fg="#555", font=("Segoe UI", 8),
                 text=("ЛКМ — основное действие\n"
                       "ПКМ — завершить полигон\n"
                       "Esc — отмена текущего действия")
                 ).pack(side=tk.BOTTOM, pady=10)

        right = tk.Frame(self.root)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(right, width=W, height=H, bg="white",
                                highlightthickness=1,
                                highlightbackground="#999")
        self.canvas.pack()

        self.status = tk.Label(right, text="", anchor="w", bg="#f0f0f0",
                               font=("Consolas", 9), padx=6)
        self.status.pack(fill=tk.X)

    def _bind(self):
        c = self.canvas
        c.bind("<Button-1>", self.on_left)
        c.bind("<Button-3>", self.on_right)
        c.bind("<Motion>",   self.on_motion)
        self.root.bind("<Escape>", lambda e: self.cancel())

    def set_status(self, text):
        if text:
            self.status.config(text=text)

    # ---------- режимы ----------
    def set_mode(self, mode):
        self.mode = mode
        self.tool = TOOL_FACTORY[mode](self.scene)
        self.pending_pivot_mode = None
        self.pending_pivot_mark = None

        for m, b in self.mode_buttons.items():
            active = (m == mode)
            b.config(relief=tk.SUNKEN if active else tk.RIDGE,
                     bg="#cfe3ff" if active else "#f0f0f0")

        self.set_status(HINTS.get(mode, ""))
        self.redraw()

    # ---------- события мыши ----------
    def on_left(self, event):
        p = self.mapping.to_world(event.x, event.y)

        if self.pending_pivot_mode == "rotate":
            self._do_rotate_about(p)
            return
        if self.pending_pivot_mode == "scale":
            self._do_scale_about(p)
            return

        self.set_status(self.tool.on_click(p))
        self.redraw()

    def on_right(self, event):
        p = self.mapping.to_world(event.x, event.y)
        self.set_status(self.tool.on_right_click(p))
        self.redraw()

    def on_motion(self, event):
        p = self.mapping.to_world(event.x, event.y)
        self.set_status(self.tool.on_move(p))
        self.redraw()

    def cancel(self):
        self.tool.cancel()
        self.pending_pivot_mode = None
        self.pending_pivot_mark = None
        self.set_status("Действие отменено")
        self.redraw()

    # ---------- преобразования ----------
    def _require_selection(self):
        if not self.scene.has_selection():
            messagebox.showinfo(
                "Нет полигона",
                "Сначала создайте или выберите полигон\n"
                "(инструмент «Выбрать полигон»).")
            return None
        return self.scene.selected

    def _apply_rotation(self, pivot, angle_deg):
        self.scene.selected.apply_matrix(
            Matrix3x3.rotate_about(pivot, angle_deg))
        self.set_status(
            f"Поворот на {angle_deg}° вокруг ({pivot.x:.0f}; {pivot.y:.0f})")
        self.redraw()

    def _apply_scaling(self, pivot, k):
        self.scene.selected.apply_matrix(
            Matrix3x3.scale_about(pivot, k, k))
        self.set_status(
            f"Масштаб x{k} относительно ({pivot.x:.0f}; {pivot.y:.0f})")
        self.redraw()

    def op_translate(self):
        if self._require_selection() is None:
            return
        dx = self._ask_number("Смещение по X (dx):", "60")
        if dx is None: return
        dy = self._ask_number("Смещение по Y (dy):", "0")
        if dy is None: return

        self.scene.selected.apply_matrix(Matrix3x3.translation(dx, dy))
        self.set_status(f"Смещение на ({dx}; {dy})")
        self.redraw()

    def op_rotate_point(self):
        if self._require_selection() is None:
            return
        self.pending_pivot_mode = "rotate"
        self.set_status("Кликните точку — центр поворота")

    def op_rotate_center(self):
        poly = self._require_selection()
        if poly is None:
            return
        ang = self._ask_number("Угол поворота (градусы):", "30")
        if ang is None:
            return
        self._apply_rotation(poly.centroid(), ang)

    def op_scale_point(self):
        if self._require_selection() is None:
            return
        self.pending_pivot_mode = "scale"
        self.set_status("Кликните точку — центр масштабирования")

    def op_scale_center(self):
        poly = self._require_selection()
        if poly is None:
            return
        k = self._ask_number("Коэффициент масштабирования:", "1.5")
        if k is None:
            return
        self._apply_scaling(poly.centroid(), k)

    def _do_rotate_about(self, pivot):
        ang = self._ask_number("Угол поворота (градусы):", "30")
        self.pending_pivot_mode = None
        self.pending_pivot_mark = None
        if ang is None:
            self.redraw(); return
        self._apply_rotation(pivot, ang)

    def _do_scale_about(self, pivot):
        k = self._ask_number("Коэффициент масштабирования:", "1.5")
        self.pending_pivot_mode = None
        self.pending_pivot_mark = None
        if k is None:
            self.redraw(); return
        self._apply_scaling(pivot, k)

    def _ask_number(self, prompt, default):
        s = simpledialog.askstring("Параметр", prompt,
                                   initialvalue=default, parent=self.root)
        if s is None:
            return None
        try:
            return float(s.replace(",", "."))
        except ValueError:
            messagebox.showerror("Ошибка",
                                 "Введите число, например 30 или 1.5")
            return None

    # ---------- очистка ----------
    def op_clear(self):
        self.scene.clear()
        self.tool = TOOL_FACTORY[self.mode](self.scene)
        self.pending_pivot_mode = None
        self.pending_pivot_mark = None
        self.set_status("Сцена очищена")
        self.redraw()

    # ---------- отрисовка ----------
    def redraw(self):
        c = self.canvas
        c.delete("all")
        draw_grid(c, self.mapping)

        for poly in self.scene.all():
            draw_polygon(c, poly, self.mapping,
                         selected=(poly is self.scene.selected))

        cur = self.tool.current_polygon()
        if cur is not None:
            draw_polygon(c, cur, self.mapping, selected=True)

        if self.pending_pivot_mark is not None:
            draw_pivot(c, self.pending_pivot_mark, self.mapping)

        draw_marks(c, self.tool.marks(), self.mapping)


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()