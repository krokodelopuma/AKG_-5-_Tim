import numpy as np
import matplotlib.pyplot as plt
from tkinter import *
from tkinter import ttk
from PIL import Image
import os
from math import sqrt, isnan

circle_center = (0.0, 0.0)

def resolut(W_mm, H_mm, base_res=400):
    aspect = W_mm / H_mm
    Hres = base_res
    Wres = int(base_res * aspect)
    return Wres, Hres

def compute(W_mm, H_mm, xL, yL, zL, I0, Wres, Hres):
    x = np.linspace(-W_mm/2, W_mm/2, Wres)
    y = np.linspace(H_mm/2, -H_mm/2, Hres)
    X, Y = np.meshgrid(x, y)
    dx = X - xL
    dy = Y - yL
    R = np.sqrt(dx**2 + dy**2 + zL**2)
    cos_a = zL / R
    E = np.zeros_like(R)
    valid = cos_a > 0
    E[valid] = I0 * cos_a[valid]**2 / (R[valid]**2)
    return X, Y, E


def run_calc():
    W_mm = s_W.get()
    H_mm = s_H.get()
    xL = s_xL.get()
    yL = s_yL.get()
    zL = s_zL.get()
    I0 = s_I0.get()
    rc = s_rc.get()

    Wres, Hres = resolut(W_mm, H_mm)

    print(f"Используемое разрешение: {Wres} × {Hres} пикселей")

    xc, yc = circle_center
    X, Y, E = compute(W_mm, H_mm, xL, yL, zL, I0, Wres, Hres)

    # маска
    dist_to_center = np.sqrt((X - xc)**2 + (Y - yc)**2)
    mask_circle = dist_to_center <= rc

    E_circle = E[mask_circle]
    Emax, Emin, Eavg = np.max(E_circle), np.min(E_circle), np.mean(E_circle)

    E_masked = E.copy()
    E_masked[~mask_circle] = 0

    # нормировка
    E_max = np.max(E_masked)
    if E_max <= 0 or np.isnan(E_max):
        E_max = 1e-12
    E_norm = E_masked / E_max
    img = (E_norm * 255).astype(np.uint8)

    os.makedirs("illum_calc_results", exist_ok=True)
    Image.fromarray(img).save("illum_calc_results/illumination_gui.png")

    points = {
        "center": (0.0, 0.0),
        "X_plus": (rc, 0.0),
        "X_minus": (-rc, 0.0),
        "Y_plus": (0.0, rc),
        "Y_minus": (0.0, -rc),
    }

    results = []
    for name, (px, py) in points.items():
        r = np.sqrt((px - xL)**2 + (py - yL)**2 + zL**2)
        cos_a = zL / r
        E_val = 0 if cos_a <= 0 else I0 * cos_a**2 / r**2
        results.append((name, px, py, E_val))

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    ax1, ax2 = axes

    ax1.imshow(img, origin="upper",
               extent=[-W_mm/2, W_mm/2, -H_mm/2, H_mm/2])
    circ = plt.Circle((xc, yc), rc, fill=False, color="red", linestyle="--")
    ax1.add_patch(circ)
    ax1.set_title("Распределение освещенности")
    ax1.set_xlabel("x, мм")
    ax1.set_ylabel("y, мм")

    iy0 = np.argmin(np.abs(np.linspace(H_mm/2, -H_mm/2, Hres)))
    E_line = E_masked[iy0, :]
    x = np.linspace(-W_mm/2, W_mm/2, Wres)
    ax2.plot(x, E_line)
    ax2.set_title("Сечение вдоль y=0")
    ax2.set_xlabel("x, мм")
    ax2.set_ylabel("E, Вт/м²")
    ax2.grid(True)
    plt.tight_layout()
    plt.savefig("illum_calc_results/illumination_gui_full.png")
    plt.show()

    print(f"Статистика в пределах круга r = {rc} мм")
    print(f"Максимум: {Emax:.6e}")
    print(f"Минимум:  {Emin:.6e}")
    print(f"Среднее:  {Eavg:.6e}\n")
    print("Контрольные точки:")
    for name, px, py, E_val in results:
        print(f"{name:8s}: (x={px:7.2f}, y={py:7.2f}) E = {E_val:.6e}")


root = Tk()
root.title("Расчет освещенности от точечного источника")

mainframe = ttk.Frame(root, padding="10")
mainframe.grid(row=0, column=0, sticky=(N, W, E, S))

def add_slider(label, from_, to_, row, init, step=10):
    ttk.Label(mainframe, text=label).grid(row=row, column=0, sticky=W)
    s = Scale(mainframe, from_=from_, to=to_, orient=HORIZONTAL,
              length=300, resolution=step)
    s.set(init)
    s.grid(row=row, column=1, sticky=(W, E))
    return s

s_W  = add_slider("Ширина области W (мм)", 100, 10000, 0, 500)
s_H  = add_slider("Высота области H (мм)", 100, 10000, 1, 300)
s_xL = add_slider("xL (мм)", -10000, 10000, 2, 0)
s_yL = add_slider("yL (мм)", -10000, 10000, 3, 0)
s_zL = add_slider("zL (мм)", 100, 10000, 4, 800)
s_I0 = add_slider("I0 (Вт/ср)", 0.01, 10000, 5, 100, step=1)
s_rc = add_slider("Радиус круга r (мм)", 10, 500, 6, 80, step=5)

ttk.Button(mainframe, text="Рассчитать", command=run_calc)\
    .grid(row=7, column=0, columnspan=2, pady=10)

Label(mainframe, text="Центр круга: (x=0, y=0)").grid(row=8, column=0, columnspan=2)

root.mainloop()
