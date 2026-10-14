import math
import tkinter as tk


SAMPLES_PER_SEGMENT = 100
HIT_RADIUS = 13
CURVE_INSERT_RADIUS = 14


def bezier(p0, p1, p2, p3, t):
    s = 1.0 - t
    return (
        s**3 * p0[0] + 3*s*s*t * p1[0] + 3*s*t*t * p2[0] + t**3 * p3[0],
        s**3 * p0[1] + 3*s*s*t * p1[1] + 3*s*t*t * p2[1] + t**3 * p3[1],
    )


def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


class BezierCurve:

    EXAMPLE = [
        (85, 370), (235, 170), (390, 320),
        (525, 225), (690, 385), (880, 185),
    ]

    def __init__(self):
        self.points = list(self.EXAMPLE)

    @property
    def segment_count(self):
        return max(0, len(self.points) - 1)

    def move_point(self, index, position):
        if 0 <= index < len(self.points):
            self.points[index] = (float(position[0]), float(position[1]))

    def append_point(self, position):
        self.points.append((float(position[0]), float(position[1])))
        return len(self.points) - 1

    def insert_point(self, index, position):
        index = max(0, min(index, len(self.points)))
        self.points.insert(index, (float(position[0]), float(position[1])))
        return index

    def remove_point(self, index):
        if 0 <= index < len(self.points):
            del self.points[index]
            return True
        return False

    def _derivatives(self):
        p = self.points
        if len(p) < 2:
            return []

        result = [(p[1][0] - p[0][0], p[1][1] - p[0][1])]
        for i in range(1, len(p) - 1):
            result.append(((p[i+1][0] - p[i-1][0]) / 2,
                           (p[i+1][1] - p[i-1][1]) / 2))
        result.append((p[-1][0] - p[-2][0], p[-1][1] - p[-2][1]))
        return result

    def segments(self):
        d = self._derivatives()
        for i in range(self.segment_count):
            a, b = self.points[i], self.points[i+1]
            yield (
                a,
                (a[0] + d[i][0]/3, a[1] + d[i][1]/3),
                (b[0] - d[i+1][0]/3, b[1] - d[i+1][1]/3),
                b,
            )

    def nearest_curve_position(self, x, y):
        target = (x, y)
        nearest = None
        best_dist = float('inf')
        for i, (p0, p1, p2, p3) in enumerate(self.segments()):
            for step in range(SAMPLES_PER_SEGMENT + 1):
                t = step / SAMPLES_PER_SEGMENT
                point = bezier(p0, p1, p2, p3, t)
                dist = distance(point, target)
                if dist < best_dist:
                    best_dist = dist
                    nearest = (i, point, dist)
        return nearest


class BezierEditor:
    def __init__(self, root):
        self.root = root
        root.title('Составная кубическая кривая Безье — управление опорными точками')
        root.geometry('1030x680')
        root.minsize(720, 480)

        self.curve = BezierCurve()
        self.drag_index = None
        self.selected_index = None
        self.show_helpers = tk.BooleanVar(value=True)

        bar = tk.Frame(root, bg='#eef3f9', padx=12, pady=9)
        bar.pack(fill='x')
        tk.Label(
            bar,
            text=('ЛКМ по синей точке — переместить   |   ЛКМ на кривой — вставить точку   '
                  '|   ЛКМ в пустом месте — добавить в конец'),
            bg='#eef3f9', fg='#253444', anchor='w', font=('Arial', 10)
        ).pack(fill='x')

        tools = tk.Frame(bar, bg='#eef3f9')
        tools.pack(fill='x', pady=(7, 0))
        tk.Label(
            tools,
            text='ПКМ по точке или Delete — удалить',
            bg='#eef3f9', fg='#54697f', font=('Arial', 10)
        ).pack(side='left')
        tk.Button(tools, text='Пример', padx=9, command=self.reset).pack(side='right', padx=(6, 0))
        tk.Button(tools, text='Очистить', padx=9, command=self.clear).pack(side='right')

        self.canvas = tk.Canvas(root, bg='white', highlightthickness=0, cursor='crosshair')
        self.canvas.pack(fill='both', expand=True)

        self.status = tk.StringVar()
        tk.Label(root, textvariable=self.status, bg='#eef3f9', fg='#34506a',
                 padx=12, pady=7, anchor='w', font=('Arial', 10)).pack(fill='x')

        self.canvas.bind('<Button-1>', self.on_left_down)
        self.canvas.bind('<B1-Motion>', self.on_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_left_up)
        self.canvas.bind('<Button-3>', self.on_right_click)
        self.canvas.bind('<Configure>', lambda _event: self.redraw())
        root.bind('<Delete>', self.on_delete_key)
        self.redraw()

    def find_point(self, x, y):
        for i in range(len(self.curve.points) - 1, -1, -1):
            if distance((x, y), self.curve.points[i]) <= HIT_RADIUS:
                return i
        return None

    def on_left_down(self, event):
        index = self.find_point(event.x, event.y)
        if index is None and self.show_helpers.get():
            for _, p1, p2, _ in self.curve.segments():
                if (distance((event.x, event.y), p1) <= HIT_RADIUS or
                        distance((event.x, event.y), p2) <= HIT_RADIUS):
                    return
        if index is None:
            nearest = self.curve.nearest_curve_position(event.x, event.y)
            if nearest is not None and nearest[2] <= CURVE_INSERT_RADIUS:
                index = self.curve.insert_point(nearest[0] + 1, nearest[1])
            else:
                index = self.curve.append_point((event.x, event.y))
        self.drag_index = index
        self.selected_index = index
        self.redraw()

    def on_drag(self, event):
        if self.drag_index is None:
            return
        x = min(max(0, event.x), self.canvas.winfo_width())
        y = min(max(0, event.y), self.canvas.winfo_height())
        self.curve.move_point(self.drag_index, (x, y))
        self.redraw()

    def on_left_up(self, _event):
        self.drag_index = None
        self.redraw()

    def on_right_click(self, event):
        index = self.find_point(event.x, event.y)
        if index is not None:
            self.curve.remove_point(index)
            self.selected_index = None
            self.drag_index = None
        self.redraw()

    def on_delete_key(self, _event):
        if self.selected_index is not None:
            self.curve.remove_point(self.selected_index)
            self.selected_index = None
            self.drag_index = None
            self.redraw()

    def clear(self):
        self.curve.points.clear()
        self.selected_index = None
        self.drag_index = None
        self.redraw()

    def reset(self):
        self.curve.points = list(BezierCurve.EXAMPLE)
        self.selected_index = None
        self.drag_index = None
        self.redraw()

    def redraw(self):
        cv = self.canvas
        cv.delete('all')
        segments = list(self.curve.segments())

        if self.show_helpers.get():
            for p0, p1, p2, p3 in segments:
                polygon = [coord for p in (p0, p1, p2, p3) for coord in p]
                cv.create_line(*polygon, fill='#b4c0cd', width=1.2, dash=(5, 5))
                for x, y in (p1, p2):
                    cv.create_oval(x-3, y-3, x+3, y+3,
                                   fill='#b4c0cd', outline='#a6b5c4')

        for i, (p0, p1, p2, p3) in enumerate(segments):
            coords = []
            for step in range(SAMPLES_PER_SEGMENT + 1):
                coords.extend(bezier(p0, p1, p2, p3,
                                     step / SAMPLES_PER_SEGMENT))
            cv.create_line(*coords, fill=('#1367c7' if i % 2 == 0 else '#078bb6'),
                           width=3, capstyle='round', joinstyle='round')

        for i, (x, y) in enumerate(self.curve.points):
            selected = i == self.selected_index
            r = 8 if selected else 7
            cv.create_oval(x-r, y-r, x+r, y+r,
                           fill=('#f6a12f' if selected else '#134f95'),
                           outline='white', width=2)
            cv.create_text(x+12, y-13, text=f'A{i}', anchor='w',
                           font=('Arial', 10, 'bold'), fill='#23476d')

        if not self.curve.points:
            cv.create_text(20, 30, text='Щёлкните мышью, чтобы добавить первую опорную точку',
                           anchor='w', fill='#76899e', font=('Arial', 11))

        self.status.set(
            f'Опорных точек: {len(self.curve.points)}   |   '
            f'Кубических сегментов: {self.curve.segment_count}   |   '
            'Касательные рассчитываются автоматически'
        )


if __name__ == '__main__':
    root = tk.Tk()
    BezierEditor(root)
    root.mainloop()
