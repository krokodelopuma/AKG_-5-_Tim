import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from PIL import Image, ImageTk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class ImageRGBAnalyzer:
    def __init__(self, parent):
        self.parent = parent
        self.frame = ttk.Frame(parent)
        self._build_ui()

    def _build_ui(self):
        frm = self.frame
        ttk.Label(frm, text='480x320').grid(row=0, column=0, columnspan=4, pady=6)

        # кнопки
        ttk.Button(frm, text='Choose Image A', command=self.load_a).grid(row=1, column=0, padx=4, pady=4)
        ttk.Button(frm, text='Choose Image B', command=self.load_b).grid(row=1, column=1, padx=4, pady=4)
        ttk.Button(frm, text='Analyze', command=self.analyze).grid(row=1, column=2, padx=4, pady=4)

        # Canvas для изображений
        self.canvas_a = tk.Canvas(frm, width=480, height=320, bg='gray')
        self.canvas_b = tk.Canvas(frm, width=480, height=320, bg='gray')
        self.canvas_a.grid(row=2, column=0, padx=4, pady=4)
        self.canvas_b.grid(row=2, column=1, padx=4, pady=4)

        # Метки для числовых средних
        self.label_avg_a = ttk.Label(frm, text='RGB A: N/A')
        self.label_avg_b = ttk.Label(frm, text='RGB B: N/A')
        self.label_avg_a.grid(row=3, column=0)
        self.label_avg_b.grid(row=3, column=1)

        # ссылки на изображения (для Tkinter)
        self.imgtk_a = None
        self.imgtk_b = None
        self.img_a = None
        self.img_b = None
        self.arr_a = None
        self.arr_b = None

        # контейнеры для гистограмм
        self.hist_frames = [ttk.Frame(frm) for _ in range(6)]
        for i, f in enumerate(self.hist_frames):
            f.grid(row=4, column=i%2, padx=4, pady=4)

    def load_a(self):
        path = filedialog.askopenfilename(title='Select Image A', filetypes=[('Image files', '*.png;*.jpg;*.jpeg;*.bmp;*.tif;*.tiff')])
        if path:
            self.img_a = Image.open(path).convert('RGB').resize((480,320), Image.Resampling.LANCZOS)
            self.imgtk_a = ImageTk.PhotoImage(self.img_a)
            self.canvas_a.delete('all')
            self.canvas_a.create_image(240,160, image=self.imgtk_a)
            self.arr_a = np.array(self.img_a)

    def load_b(self):
        path = filedialog.askopenfilename(title='Select Image B', filetypes=[('Image files', '*.png;*.jpg;*.jpeg;*.bmp;*.tif;*.tiff')])
        if path:
            self.img_b = Image.open(path).convert('RGB').resize((480,320), Image.Resampling.LANCZOS)
            self.imgtk_b = ImageTk.PhotoImage(self.img_b)
            self.canvas_b.delete('all')
            self.canvas_b.create_image(240,160, image=self.imgtk_b)
            self.arr_b = np.array(self.img_b)

    def analyze(self):
        if self.arr_a is None or self.arr_b is None:
            messagebox.showwarning('Missing images', 'Please load both images')
            return

        # Среднее RGB
        avg_a = np.mean(self.arr_a, axis=(0, 1))
        avg_b = np.mean(self.arr_b, axis=(0, 1))
        self.label_avg_a.config(text=f'Average RGB A: {avg_a[0]:.1f}, {avg_a[1]:.1f}, {avg_a[2]:.1f}')
        self.label_avg_b.config(text=f'Average RGB B: {avg_b[0]:.1f}, {avg_b[1]:.1f}, {avg_b[2]:.1f}')

        # Очистка предыдущих гистограмм
        for frame in self.hist_frames:
            for widget in frame.winfo_children():
                widget.destroy()

        # Отображение гистограмм 3 столбца (R,G,B) для каждой картинки
        for i, (arr, frame, avg) in enumerate(zip([self.arr_a, self.arr_b],
                                                  [self.hist_frames[0], self.hist_frames[1]],
                                                  [avg_a, avg_b])):
            plt.close('all')
            fig, ax = plt.subplots(figsize=(3, 2), dpi=100)
            colors = ['r', 'g', 'b']

            # Создание столбцов
            for c, col in enumerate(colors):
                height = np.mean(arr[:, :, c])
                ax.bar(c, height, color=col, alpha=0.7)

                ax.text(c, height + 5, f'{avg[c]:.1f}',
                        ha='center', va='bottom', fontsize=8, fontweight='bold')

            ax.set_xticks([0, 1, 2])
            ax.set_xticklabels(['R', 'G', 'B'])
            ax.set_ylim(0, max(avg_a.max(), avg_b.max()) + 20)
            ax.set_title(f'RGB Image {"A" if i == 0 else "B"}')

            canvas = FigureCanvasTkAgg(fig, master=frame)
            canvas.get_tk_widget().pack()
            canvas.draw()

class LauncherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('RGB Analyzer')
        self.geometry('1000x800')
        self.image_module = ImageRGBAnalyzer(self)
        self.image_module.frame.pack(fill='both', expand=True)

if __name__ == '__main__':
    app = LauncherApp()
    app.mainloop()
