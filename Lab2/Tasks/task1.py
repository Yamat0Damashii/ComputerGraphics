import os
import tkinter as tk

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


class Task1:
    def __init__(self, root: tk.Tk, parent):
        self.root = root
        self.parent = parent
        self.root.configure(bg=parent.back_ground)
        self.root.geometry("260x80+500+20")
        self.root.title("task1")

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
        image_array = np.array(image).astype(np.float32)

        red = image_array[:, :, 0]
        green = image_array[:, :, 1]
        blue = image_array[:, :, 2]

        # Вариант 1 — PAL/NTSC
        gray_1 = 0.299 * red + 0.587 * green + 0.114 * blue
        # Вариант 2 — HDTV / sRGB
        gray_2 = 0.2126 * red + 0.7152 * green + 0.0722 * blue

        gray_1 = np.clip(gray_1, 0, 255).astype(np.uint8)
        gray_2 = np.clip(gray_2, 0, 255).astype(np.uint8)

        diff = np.abs(
            gray_1.astype(np.int16) - gray_2.astype(np.int16)
        ).astype(np.uint8)

        output_dir = os.path.join(self.parent.output_path, "task1")
        os.makedirs(output_dir, exist_ok=True)

        Image.fromarray(gray_1).save(
            os.path.join(output_dir, "gray_formula_1.jpg")
        )
        Image.fromarray(gray_2).save(
            os.path.join(output_dir, "gray_formula_2.jpg")
        )
        Image.fromarray(diff).save(
            os.path.join(output_dir, "gray_difference.jpg")
        )

        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        hist_1 = np.bincount(gray_1.ravel(), minlength=256)
        hist_2 = np.bincount(gray_2.ravel(), minlength=256)

        axes[0].bar(range(256), hist_1, color="gray", alpha=0.7)
        axes[0].set_title("Histogram: formula 1 (PAL/NTSC)")
        axes[0].set_xlabel("Intensity")
        axes[0].set_ylabel("Pixels")
        axes[0].set_xlim(0, 255)

        axes[1].bar(range(256), hist_2, color="gray", alpha=0.7)
        axes[1].set_title("Histogram: formula 2 (HDTV)")
        axes[1].set_xlabel("Intensity")
        axes[1].set_ylabel("Pixels")
        axes[1].set_xlim(0, 255)

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
        output_dir = os.path.join(self.parent.output_path, "task1")
        for name in (
            "gray_formula_1.jpg",
            "gray_formula_2.jpg",
            "gray_difference.jpg",
        ):
            output_path = os.path.join(output_dir, name)
            if os.path.exists(output_path):
                os.remove(output_path)

        if self.delete_button is not None:
            self.delete_button.destroy()
            self.delete_button = None