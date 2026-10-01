import tkinter as tk

from Tasks.task2 import task2
from Tasks.task3 import task3


class Lab3:
    def __init__(self, root: tk.Tk):
        self.back_ground = "#333"

        self.root = root
        self.root.title("Lab3")
        self.root.configure(bg=self.back_ground)
        self.root.geometry("300x160+1+1")

        # task2
        self.task2_button = tk.Button(
            root,
            text="task2",
            command=self.task2,
            bg="#555",
            fg="white",
            width=100,
        )
        self.task2_button.pack(pady=5, padx=5)

        self.task3_button = tk.Button(
            root,
            text="task3",
            command=self.task3,
            bg="#555",
            fg="white",
            width=100,
        )
        self.task3_button.pack(pady=5, padx=5)

    def task2(self):
        child = tk.Toplevel()
        task2_window = task2(root=child, parent=self)

    def task3(self):                           # <-- ДОБАВЛЕНО
        child = tk.Toplevel()
        task3_window = task3(root=child, parent=self)


if __name__ == "__main__":
    root = tk.Tk()
    app = Lab3(root)
    root.mainloop()