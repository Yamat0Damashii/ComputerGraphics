import os
import tkinter as tk
from tkinter import filedialog, messagebox

from Tasks.task2 import Task2


class MainWindow:
	def __init__(self, root: tk.Tk):
		self.root = root
		self.back_ground = "#2b2b2b"
		self.output_path = os.path.join(os.getcwd(), "output")

		self.root.title("Computer Graphics Lab 2")
		self.root.geometry("620x220")
		self.root.configure(bg=self.back_ground)
		self.root.columnconfigure(1, weight=1)

		label_options = {"bg": self.back_ground, "fg": "white"}
		entry_options = {"bg": "white", "fg": "black"}

		tk.Label(root, text="Путь к изображению", **label_options).grid(
			row=0, column=0, padx=10, pady=10, sticky="w"
		)
		self.path_entry = tk.Entry(root, **entry_options)
		self.path_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
		tk.Button(root, text="Выбрать", command=self.choose_image).grid(
			row=0, column=2, padx=10, pady=10
		)

		tk.Label(root, text="Папка для результатов", **label_options).grid(
			row=1, column=0, padx=10, pady=10, sticky="w"
		)
		self.output_entry = tk.Entry(root, **entry_options)
		self.output_entry.insert(0, self.output_path)
		self.output_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
		tk.Button(root, text="Выбрать", command=self.choose_output).grid(
			row=1, column=2, padx=10, pady=10
		)

		tk.Button(root, text="Запустить задание 2", command=self.run_task2).grid(
			row=2, column=0, columnspan=3, padx=10, pady=20, sticky="ew"
		)

	def choose_image(self):
		path = filedialog.askopenfilename(
			title="Выберите изображение",
			filetypes=[
				("Изображения", "*.png *.jpg *.jpeg *.bmp *.tiff"),
				("Все файлы", "*.*"),
			],
		)
		if path:
			self.path_entry.delete(0, tk.END)
			self.path_entry.insert(0, path)

	def choose_output(self):
		path = filedialog.askdirectory(title="Выберите папку для результатов")
		if path:
			self.output_entry.delete(0, tk.END)
			self.output_entry.insert(0, path)

	def run_task2(self):
		image_path = self.path_entry.get().strip()
		output_path = self.output_entry.get().strip()
		if not image_path or not os.path.isfile(image_path):
			messagebox.showerror("Ошибка", "Выберите существующее изображение.")
			return
		if not output_path:
			messagebox.showerror("Ошибка", "Укажите папку для результатов.")
			return

		self.output_path = output_path
		os.makedirs(self.output_path, exist_ok=True)
		task_window = tk.Toplevel(self.root)
		Task2(task_window, self)


if __name__ == "__main__":
	root = tk.Tk()
	MainWindow(root)
	root.mainloop()
