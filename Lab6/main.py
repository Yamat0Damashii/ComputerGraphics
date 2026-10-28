
import tkinter as tk
from tkinter import ttk

from geometry import GeometryControls
from transforms import TransformControls
from view_and_spatial import ViewControls


class App(GeometryControls, TransformControls, ViewControls):
    """Соединяет три части интерфейса и общую модель."""

    def __init__(self, root):
        self.root = root
        self.root.title('Правильные многогранники — Tkinter')

        top = ttk.Frame(root)
        top.pack(side=tk.TOP, fill=tk.X, padx=8, pady=8)

        self.build_geometry_controls(top)
        self.build_projection_controls(top)
        self.build_transform_controls(root)
        self.build_canvas(root)


def main():
    root = tk.Tk()
    app = App(root)
    root.mainloop()


if __name__ == '__main__':
    main()
