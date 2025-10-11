import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageTk, ImageEnhance, ImageOps, ImageFilter
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class ImageEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Image Editor")
        self.root.geometry("1000x700")
        self.original_image = None
        self.processed_image = None

        self.create_ui()

    def create_ui(self):
        frame_top = ttk.Frame(self.root)
        frame_top.pack(pady=10)

        ttk.Button(frame_top, text="Open Image", command=self.load_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_top, text="Save Image", command=self.save_image).pack(side=tk.LEFT, padx=5)

        # инверсия и оттенки серого
        self.gray_var = tk.BooleanVar()
        self.invert_var = tk.BooleanVar()
        ttk.Checkbutton(frame_top, text="Grayscale", variable=self.gray_var, command=self.apply_filters).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(frame_top, text="Invert", variable=self.invert_var, command=self.apply_filters).pack(side=tk.LEFT, padx=5)

        # слайдеры
        frame_sliders = ttk.Frame(self.root)
        frame_sliders.pack(pady=10)

        ttk.Label(frame_sliders, text="Brightness").grid(row=0, column=0)
        self.brightness = tk.DoubleVar(value=1.0)
        ttk.Scale(frame_sliders, from_=0.2, to=2.0, orient="horizontal",
                  variable=self.brightness, command=self.on_slider_change).grid(row=0, column=1, padx=5)

        ttk.Label(frame_sliders, text="Contrast").grid(row=1, column=0)
        self.contrast = tk.DoubleVar(value=1.0)
        ttk.Scale(frame_sliders, from_=0.2, to=2.0, orient="horizontal",
                  variable=self.contrast, command=self.on_slider_change).grid(row=1, column=1, padx=5)

        ttk.Label(frame_sliders, text="Blur").grid(row=2, column=0)
        self.blur = tk.DoubleVar(value=0.0)
        ttk.Scale(frame_sliders, from_=0, to=5, orient="horizontal",
                  variable=self.blur, command=self.on_slider_change).grid(row=2, column=1, padx=5)

        # Область изображений
        frame_imgs = ttk.Frame(self.root)
        frame_imgs.pack(pady=10)

        self.canvas_orig = tk.Canvas(frame_imgs, width=480, height=320, bg='gray')
        self.canvas_orig.pack(side=tk.LEFT, padx=10)
        self.canvas_proc = tk.Canvas(frame_imgs, width=480, height=320, bg='gray')
        self.canvas_proc.pack(side=tk.LEFT, padx=10)

        # Гистограммы
        self.hist_frame = ttk.Frame(self.root)
        self.hist_frame.pack(pady=10)

    def load_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.png *.bmp")])
        if not path:
            return
        self.original_image = Image.open(path).convert("RGB").resize((480, 320), Image.Resampling.LANCZOS)
        self.processed_image = self.original_image.copy()
        self.update_display()

    def save_image(self):
        if self.processed_image is None:
            return
        path = filedialog.asksaveasfilename(defaultextension=".png",
                                            filetypes=[("PNG Files", "*.png"), ("JPEG Files", "*.jpg")])
        if path:
            self.processed_image.save(path)

    def on_slider_change(self, event=None):
        # применяем фильтры через 300 мс после последнего движения (чтобы успело построить)
        if hasattr(self, 'update_job'):
            self.root.after_cancel(self.update_job)
        self.update_job = self.root.after(300, self.apply_filters)

    def apply_filters(self):
        if self.original_image is None:
            return

        img = self.original_image.copy()

        # применяем фильтры
        img = ImageEnhance.Brightness(img).enhance(self.brightness.get())
        img = ImageEnhance.Contrast(img).enhance(self.contrast.get())

        if self.blur.get() > 0:
            img = img.filter(ImageFilter.GaussianBlur(radius=self.blur.get()))

        if self.gray_var.get():
            img = ImageOps.grayscale(img).convert("RGB")

        if self.invert_var.get():
            img = ImageOps.invert(img)

        self.processed_image = img
        self.update_display(show_hist=True)

    def update_display(self, show_hist=True):
        if self.original_image:
            self.tk_orig = ImageTk.PhotoImage(self.original_image)
            self.canvas_orig.delete("all")
            self.canvas_orig.create_image(240, 160, image=self.tk_orig)

        if self.processed_image:
            self.tk_proc = ImageTk.PhotoImage(self.processed_image)
            self.canvas_proc.delete("all")
            self.canvas_proc.create_image(240, 160, image=self.tk_proc)

        if show_hist:
            self.update_histograms()

    def update_histograms(self):
        for widget in self.hist_frame.winfo_children():
            widget.destroy()

        if self.original_image is None or self.processed_image is None:
            return

        plt.close('all')
        fig, axs = plt.subplots(1, 2, figsize=(8, 3), dpi=100)
        colors = ['r', 'g', 'b']

        arr_orig = np.array(self.original_image)
        arr_proc = np.array(self.processed_image)

        for i, col in enumerate(colors):
            axs[0].hist(arr_orig[:, :, i].flatten(), bins=256, color=col, alpha=0.5)
            axs[1].hist(arr_proc[:, :, i].flatten(), bins=256, color=col, alpha=0.5)

        axs[0].set_title("Original RGB Histogram")
        axs[1].set_title("Processed RGB Histogram")

        for ax in axs:
            ax.set_xlim(0, 255)
            ax.set_xlabel("")
            ax.set_ylabel("")

        canvas = FigureCanvasTkAgg(fig, master=self.hist_frame)
        canvas.get_tk_widget().pack()
        canvas.draw()
        plt.close(fig)

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageEditor(root)
    root.mainloop()
