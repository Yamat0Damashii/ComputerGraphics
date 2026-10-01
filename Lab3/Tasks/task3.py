import tkinter as tk
from PIL import Image, ImageDraw, ImageTk


class task3:
    """Градиентная заливка треугольника через растеризацию барицентрическими координатами."""

    def __init__(self, root: tk.Tk, parent):
        self.root = root
        self.parent = parent
        self.root.configure(bg=parent.back_ground)
        self.root.geometry("700x550+900+20")
        self.root.title("Task 3 - Gradient Triangle")

        # Цвета вершин треугольника: R, G, B
        self.colors = [(255, 0, 0), (0, 200, 0), (0, 0, 255)]

        self.vertices = []   # текущий набор точек (0..2), который копится до 3
        self.triangles = []  # список построенных треугольников

        self.canvas = tk.Canvas(self.root, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.reset_button = tk.Button(
            self.root, text="Reset", command=self.reset_canvas, bg="#555", fg="white"
        )
        self.reset_button.pack(pady=5)

        self.info_label = tk.Label(
            self.root,
            text="Кликните 3 точки — вершины треугольника (R, G, B)",
            bg=parent.back_ground, fg="white",
        )
        self.info_label.pack(pady=5)

        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Configure>", self.on_resize)

        self.image = None
        self.tk_image = None

        # первый render после того, как виджет получит реальный размер
        self.root.after(50, self.redraw)

    # ---------- события ----------

    def on_resize(self, event):
        self.redraw()

    def on_click(self, event):
        self.vertices.append((event.x, event.y))

        if len(self.vertices) == 3:
            self.triangles.append(tuple(self.vertices))
            self.vertices = []
            self.info_label.config(
                text="Треугольник построен. Кликните ещё 3 точки для нового."
            )
        else:
            self.info_label.config(
                text=f"Выбрано точек: {len(self.vertices)}/3 — продолжайте."
            )

        self.redraw()

    # ---------- отрисовка ----------

    def redraw(self):
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        if width <= 1 or height <= 1:
            return

        self.image = Image.new("RGB", (width, height), "white")
        for tri in self.triangles:
            self.rasterize_triangle(self.image, *tri)

        self.tk_image = ImageTk.PhotoImage(self.image)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)
        self.canvas.image = self.tk_image

        # маркеры вершин (и у завершённых треугольников, и у текущего)
        all_tris = list(self.triangles)
        if self.vertices:
            all_tris.append(tuple(self.vertices))
        for tri in all_tris:
            for i, (x, y) in enumerate(tri):
                color = "#%02x%02x%02x" % self.colors[i]
                r = 4
                self.canvas.create_oval(
                    x - r, y - r, x + r, y + r, fill=color, outline="black"
                )

    @staticmethod
    def _area2(ax, ay, bx, by, cx, cy):
        """Удвоенная знаковая площадь треугольника (a, b, c)."""
        return (bx - ax) * (cy - ay) - (cx - ax) * (by - ay)

    def rasterize_triangle(self, image, v1, v2, v3):
        """Заполняет треугольник v1,v2,v3 с градиентом по барицентрическим координатам."""
        x1, y1 = v1
        x2, y2 = v2
        x3, y3 = v3

        # Bounding box, обрезанный по границам картинки
        min_x = max(0, int(min(x1, x2, x3)))
        max_x = min(image.width - 1, int(max(x1, x2, x3)))
        min_y = max(0, int(min(y1, y2, y3)))
        max_y = min(image.height - 1, int(max(y1, y2, y3)))

        D = self._area2(x1, y1, x2, y2, x3, y3)
        if D == 0:
            return  # вырожденный треугольник

        c1, c2, c3 = self.colors
        draw = ImageDraw.Draw(image)

        for py in range(min_y, max_y + 1):
            for px in range(min_x, max_x + 1):
                # Барицентрические веса через отношения площадей
                alpha = self._area2(px, py, x2, y2, x3, y3) / D   # вес вершины 1
                beta  = self._area2(px, py, x3, y3, x1, y1) / D   # вес вершины 2
                gamma = self._area2(px, py, x1, y1, x2, y2) / D   # вес вершины 3

                if alpha >= 0 and beta >= 0 and gamma >= 0:
                    r = alpha * c1[0] + beta * c2[0] + gamma * c3[0]
                    g = alpha * c1[1] + beta * c2[1] + gamma * c3[1]
                    b = alpha * c1[2] + beta * c2[2] + gamma * c3[2]
                    draw.point((px, py), fill=(int(r), int(g), int(b)))

    # ---------- сброс ----------

    def reset_canvas(self):
        self.vertices = []
        self.triangles = []
        self.info_label.config(
            text="Кликните 3 точки — вершины треугольника (R, G, B)"
        )
        self.redraw()