import os
import tkinter as tk

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


class Task2:
	def __init__(self, root: tk.Tk, parent):
		self.root = root
		self.parent = parent
		self.root.configure(bg=parent.back_ground)
		self.root.geometry("230x80+500+20")
		self.root.title("task2")

		self.start_button = tk.Button(
			root,
			text="start",
			command=self.start,
			width=20,
			bg="#555",
			fg="white",
		)
		self.root.grid_columnconfigure(0, weight=1)
		self.start_button.grid(
			row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew"
		)
		self.delete_button = None

	def start(self):
		image = Image.open(self.parent.path_entry.get()).convert("RGB")
		image_array = np.array(image)

		red, green, blue = (
			image_array[:, :, 0],
			image_array[:, :, 1],
			image_array[:, :, 2],
		)
		channels = (
			("R", red, 0, "red"),
			("G", green, 1, "green"),
			("B", blue, 2, "blue"),
		)

		output_dir = os.path.join(self.parent.output_path, "task2")
		os.makedirs(output_dir, exist_ok=True)

		fig, axes = plt.subplots(1, 3, figsize=(18, 5))
		for axis, (name, channel, channel_index, color) in zip(axes, channels):
			channel_image = np.zeros_like(image_array)
			channel_image[:, :, channel_index] = channel
			output_path = os.path.join(output_dir, f"{name}_channel.jpg")
			Image.fromarray(channel_image).save(output_path)

			histogram = np.bincount(channel.ravel(), minlength=256)
			axis.bar(range(256), histogram, color=color, alpha=0.6)
			axis.set_title(f"Histogram for {name}-channel")
			axis.set_xlabel("Intensity")
			axis.set_ylabel("Pixels")
			axis.set_xlim(0, 255)

		fig.tight_layout()
		plt.show()

		if self.delete_button is None:
			self.delete_button = tk.Button(
				self.root,
				text="Удалить файлы",
				command=self.delete_files,
				width=20,
				bg="#555",
				fg="white",
			)
			self.delete_button.grid(
				row=2, column=0, columnspan=2, padx=10, pady=5, sticky="nsew"
			)

	def delete_files(self):
		output_dir = os.path.join(self.parent.output_path, "task2")
		for name in ("R", "G", "B"):
			output_path = os.path.join(output_dir, f"{name}_channel.jpg")
			if os.path.exists(output_path):
				os.remove(output_path)

		if self.delete_button is not None:
			self.delete_button.destroy()
			self.delete_button = None