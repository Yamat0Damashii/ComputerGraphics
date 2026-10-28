import tkinter as tk
from typing import Sequence


Point = tuple[float, float]
EPSILON = 1e-9


def cross_product(first: Point, second: Point, point: Point) -> float:
	return (second[0] - first[0]) * (point[1] - first[1]) - (
		second[1] - first[1]
	) * (point[0] - first[0])


def polygon_signed_area(polygon: Sequence[Point]) -> float:
	area = 0.0
	for index, point in enumerate(polygon):
		next_point = polygon[(index + 1) % len(polygon)]
		area += point[0] * next_point[1] - next_point[0] * point[1]
	return area / 2


def is_convex_polygon(polygon: Sequence[Point]) -> bool:
	if len(polygon) < 3 or abs(polygon_signed_area(polygon)) <= EPSILON:
		return False

	turn_direction = 0
	for index in range(len(polygon)):
		first = polygon[index]
		second = polygon[(index + 1) % len(polygon)]
		third = polygon[(index + 2) % len(polygon)]
		turn = cross_product(first, second, third)
		if abs(turn) <= EPSILON:
			continue

		direction = 1 if turn > 0 else -1
		if turn_direction and direction != turn_direction:
			return False
		turn_direction = direction

	return turn_direction != 0


def point_inside(point: Point, polygon: Sequence[Point]) -> bool:
	return all(
		cross_product(polygon[index], polygon[(index + 1) % len(polygon)], point)
		>= -EPSILON
		for index in range(len(polygon))
	)


def segment_intersection(
	first_start: Point, first_end: Point, second_start: Point, second_end: Point
) -> tuple[Point, float, float] | None:
	first_direction = (
		first_end[0] - first_start[0],
		first_end[1] - first_start[1],
	)
	second_direction = (
		second_end[0] - second_start[0],
		second_end[1] - second_start[1],
	)
	denominator = (
		first_direction[0] * second_direction[1]
		- first_direction[1] * second_direction[0]
	)
	if abs(denominator) <= EPSILON:
		return None

	distance = (second_start[0] - first_start[0], second_start[1] - first_start[1])
	first_position = (
		distance[0] * second_direction[1] - distance[1] * second_direction[0]
	) / denominator
	second_position = (
		distance[0] * first_direction[1] - distance[1] * first_direction[0]
	) / denominator
	if not (-EPSILON <= first_position <= 1 + EPSILON):
		return None
	if not (-EPSILON <= second_position <= 1 + EPSILON):
		return None

	point = (
		first_start[0] + first_position * first_direction[0],
		first_start[1] + first_position * first_direction[1],
	)
	return point, first_position, second_position


def polygon_chain(
	polygon: Sequence[Point], start: tuple[Point, int, float], end: tuple[Point, int, float]
) -> list[Point]:
	points = []
	start_index = (start[1] + 1) % len(polygon)
	end_index = (end[1] + 1) % len(polygon)
	wrap_same_edge = start[1] == end[1] and end[2] < start[2]
	index = start_index

	while index != end_index or wrap_same_edge:
		points.append(polygon[index])
		index = (index + 1) % len(polygon)
		if wrap_same_edge and index == end_index:
			wrap_same_edge = False

	points.append(end[0])
	return points


def convex_polygon_intersection(
	subject: Sequence[Point], clip: Sequence[Point]
) -> list[Point]:
	if not is_convex_polygon(subject) or not is_convex_polygon(clip):
		raise ValueError("Оба многоугольника должны быть выпуклыми и иметь площадь.")

	first_polygon = list(subject)
	second_polygon = list(clip)
	if polygon_signed_area(first_polygon) < 0:
		first_polygon.reverse()
	if polygon_signed_area(second_polygon) < 0:
		second_polygon.reverse()

	# Каждая запись хранит пересечение и его положение на обеих границах полигона.
	crossings = []
	for first_edge, first_start in enumerate(first_polygon):
		first_end = first_polygon[(first_edge + 1) % len(first_polygon)]
		for second_edge, second_start in enumerate(second_polygon):
			second_end = second_polygon[(second_edge + 1) % len(second_polygon)]
			intersection = segment_intersection(
				first_start, first_end, second_start, second_end
			)
			if intersection is None:
				continue

			point, first_position, second_position = intersection
			if any(
				abs(point[0] - crossing[0][0]) <= EPSILON
				and abs(point[1] - crossing[0][1]) <= EPSILON
				for crossing in crossings
			):
				continue

			first_direction = (
				first_end[0] - first_start[0], first_end[1] - first_start[1]
			)
			second_direction = (
				second_end[0] - second_start[0], second_end[1] - second_start[1]
			)
			turn = (
				second_direction[0] * first_direction[1]
				- second_direction[1] * first_direction[0]
			)
			crossings.append(
				(
					point,
					(first_edge, first_position),
					(second_edge, second_position),
					turn > EPSILON,
				)
			)

	if not crossings:
		if all(point_inside(point, second_polygon) for point in first_polygon):
			return first_polygon
		if all(point_inside(point, first_polygon) for point in second_polygon):
			return second_polygon
		return []

	first_order = sorted(range(len(crossings)), key=lambda index: crossings[index][1])
	second_order = sorted(range(len(crossings)), key=lambda index: crossings[index][2])
	start = next(
		(index for index, crossing in enumerate(crossings) if crossing[3]), None
	)
	if start is None:
		return []

	first_next = {
		first_order[index]: first_order[(index + 1) % len(first_order)]
		for index in range(len(first_order))
	}
	second_next = {
		second_order[index]: second_order[(index + 1) % len(second_order)]
		for index in range(len(second_order))
	}
	result = []
	current = start
	follow_first = True

	for _ in range(len(crossings) * 2):
		next_crossing = (
			first_next[current] if follow_first else second_next[current]
		)
		polygon = first_polygon if follow_first else second_polygon
		start_key = crossings[current][1 if follow_first else 2]
		end_key = crossings[next_crossing][1 if follow_first else 2]
		start_point = (crossings[current][0], start_key[0], start_key[1])
		end_point = (crossings[next_crossing][0], end_key[0], end_key[1])
		result.extend(polygon_chain(polygon, start_point, end_point))
		current = next_crossing
		follow_first = not follow_first
		if current == start and follow_first:
			break

	cleaned = []
	for point in result:
		if not cleaned or (
			abs(point[0] - cleaned[-1][0]) > EPSILON
			or abs(point[1] - cleaned[-1][1]) > EPSILON
		):
			cleaned.append(point)
	if len(cleaned) > 1 and (
		abs(cleaned[0][0] - cleaned[-1][0]) <= EPSILON
		and abs(cleaned[0][1] - cleaned[-1][1]) <= EPSILON
	):
		cleaned.pop()

	if len(cleaned) < 3 or abs(polygon_signed_area(cleaned)) <= EPSILON:
		return []
	return cleaned


class PolygonIntersectionApp:
	def __init__(self, root: tk.Tk):
		self.root = root
		self.root.title("Пересечение выпуклых полигонов")
		self.root.geometry("1000x720")
		self.root.minsize(700, 500)
		self.root.configure(bg="#333")

		self.polygons: dict[str, list[Point]] = {"A": [], "B": []}
		self.completed: set[str] = set()
		self.intersection: list[Point] = []
		self.active_polygon = "A"
		self.preview_point: Point | None = None

		self.controls = tk.Frame(self.root, bg="#333")
		self.controls.pack(fill="x", padx=8, pady=8)

		self.button_a = tk.Button(
			self.controls,
			text="Полигон A",
			command=lambda: self.select_polygon("A"),
			bg="#3478a8",
			fg="white",
		)
		self.button_a.pack(side="left", padx=3)
		self.button_b = tk.Button(
			self.controls,
			text="Полигон B",
			command=lambda: self.select_polygon("B"),
			bg="#a8642f",
			fg="white",
		)
		self.button_b.pack(side="left", padx=3)

		tk.Button(
			self.controls,
			text="Завершить полигон",
			command=self.finish_polygon,
			bg="#555",
			fg="white",
		).pack(side="left", padx=3)
		tk.Button(
			self.controls,
			text="Отменить вершину",
			command=self.undo_vertex,
			bg="#555",
			fg="white",
		).pack(side="left", padx=3)
		tk.Button(
			self.controls,
			text="Найти пересечение",
			command=self.calculate_intersection,
			bg="#28794e",
			fg="white",
		).pack(side="left", padx=3)
		tk.Button(
			self.controls,
			text="Сбросить",
			command=self.reset,
			bg="#555",
			fg="white",
		).pack(side="right", padx=3)

		self.status = tk.StringVar(
			value="Выбран полигон A. Щёлкайте по холсту, чтобы добавить вершины."
		)
		tk.Label(
			self.root,
			textvariable=self.status,
			bg="#333",
			fg="white",
			anchor="w",
		).pack(fill="x", padx=12, pady=(0, 6))

		self.canvas = tk.Canvas(self.root, bg="white", highlightthickness=0)
		self.canvas.pack(fill="both", expand=True, padx=10, pady=(0, 10))
		self.canvas.bind("<Button-1>", self.on_canvas_click)
		self.canvas.bind("<Motion>", self.on_canvas_motion)

		self.update_controls()
		self.draw_scene()

	def update_controls(self) -> None:
		self.button_a.configure(
			relief="sunken" if self.active_polygon == "A" else "raised",
			state="disabled" if "A" in self.completed else "normal",
		)
		self.button_b.configure(
			relief="sunken" if self.active_polygon == "B" else "raised",
			state="disabled" if "B" in self.completed else "normal",
		)

	def select_polygon(self, name: str) -> None:
		if name in self.completed:
			return
		self.active_polygon = name
		self.status.set(
			f"Выбран полигон {name}. Щёлкайте по холсту, чтобы добавить вершины."
		)
		self.update_controls()

	def on_canvas_click(self, event: tk.Event) -> None:
		if self.active_polygon in self.completed:
			self.status.set("Этот полигон уже завершён. Выберите другой или сбросьте построение.")
			return

		point = (float(event.x), float(event.y))
		vertices = self.polygons[self.active_polygon]
		if vertices and abs(vertices[-1][0] - point[0]) <= EPSILON and abs(
			vertices[-1][1] - point[1]
		) <= EPSILON:
			return

		vertices.append(point)
		self.intersection = []
		self.draw_scene()

	def on_canvas_motion(self, event: tk.Event) -> None:
		self.preview_point = (float(event.x), float(event.y))
		self.draw_scene()

	def finish_polygon(self) -> None:
		vertices = self.polygons[self.active_polygon]
		if not is_convex_polygon(vertices):
			self.status.set(
				f"Полигон {self.active_polygon}: нужно минимум 3 вершины, "
				"ненулевой площади и выпуклый контур."
			)
			return

		self.completed.add(self.active_polygon)
		self.intersection = []
		self.status.set(
			f"Полигон {self.active_polygon} завершён. "
			"Выберите второй полигон или нажмите «Найти пересечение»."
		)
		self.update_controls()
		self.draw_scene()

	def undo_vertex(self) -> None:
		if self.active_polygon in self.completed:
			self.status.set("Завершённый полигон нельзя редактировать. Нажмите «Сбросить».")
			return
		vertices = self.polygons[self.active_polygon]
		if vertices:
			vertices.pop()
			self.intersection = []
			self.draw_scene()

	def calculate_intersection(self) -> None:
		if len(self.completed) != 2:
			self.status.set("Сначала завершите оба выпуклых полигона.")
			return

		self.intersection = convex_polygon_intersection(
			self.polygons["A"], self.polygons["B"]
		)
		self.draw_scene()
		if self.intersection:
			area = abs(polygon_signed_area(self.intersection))
			self.status.set(
				f"Пересечение выделено зелёным. Площадь: {area:.1f} кв. пикс."
			)
		else:
			self.status.set("Пересечение с ненулевой площадью не найдено.")

	def reset(self) -> None:
		self.polygons = {"A": [], "B": []}
		self.completed.clear()
		self.intersection = []
		self.active_polygon = "A"
		self.status.set("Построение сброшено. Выбран полигон A.")
		self.update_controls()
		self.draw_scene()

	def draw_polygon(self, name: str, color: str) -> None:
		vertices = self.polygons[name]
		if not vertices:
			return

		coordinates = [coordinate for point in vertices for coordinate in point]
		if name in self.completed:
			self.canvas.create_polygon(
				*coordinates,
				fill=color,
				stipple="gray50",
				outline=color,
				width=2,
			)
		elif len(vertices) > 1:
			self.canvas.create_line(*coordinates, fill=color, width=2)
			if name == self.active_polygon and self.preview_point is not None:
				self.canvas.create_line(
					*vertices[-1], *self.preview_point, fill=color, dash=(4, 3)
				)

		for x, y in vertices:
			self.canvas.create_oval(
				x - 4, y - 4, x + 4, y + 4, fill=color, outline="white"
			)

	def draw_scene(self) -> None:
		self.canvas.delete("all")
		self.draw_polygon("A", "#3478a8")
		self.draw_polygon("B", "#a8642f")

		if self.intersection:
			coordinates = [
				coordinate
				for point in self.intersection
				for coordinate in point
			]
			self.canvas.create_polygon(
				*coordinates,
				fill="#32a852",
				stipple="gray50",
				outline="#168238",
				width=3,
			)
			for x, y in self.intersection:
				self.canvas.create_oval(
					x - 4, y - 4, x + 4, y + 4, fill="#168238", outline="white"
				)


if __name__ == "__main__":
	root = tk.Tk()
	app = PolygonIntersectionApp(root)
	root.mainloop()
