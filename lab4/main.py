import numpy as np
from tkinter import *
from PIL import Image, ImageTk

def compute_resolution(W_mm, H_mm, base_res=100):
    aspect = W_mm / H_mm
    Hres = base_res
    Wres = int(base_res * aspect)
    return Wres, Hres

def generate_image():
    xC = float(slider_xC.get())
    yC = float(slider_yC.get())
    zC = float(slider_zC.get())
    R  = float(slider_R.get())
    zO = float(slider_zO.get())

    kd = float(slider_kd.get())
    ks = float(slider_ks.get())
    n  = float(slider_n.get())

    W_mm = float(slider_W.get())
    H_mm = float(slider_H.get())

    margin = 50
    if W_mm/2 < abs(xC) + R:
        W_mm = 2*(abs(xC)+R+margin)
        slider_W.set(W_mm)
    if H_mm/2 < abs(yC) + R:
        H_mm = 2*(abs(yC)+R+margin)
        slider_H.set(H_mm)

    Wres, Hres = compute_resolution(W_mm, H_mm)

    x = np.linspace(-W_mm/2, W_mm/2, Wres)
    y = np.linspace(-H_mm/2, H_mm/2, Hres)
    X, Y = np.meshgrid(x, y)
    brightness = np.zeros_like(X)

    O = np.array([0,0,zO])

    lights = []
    for s in sources:
        lights.append({'pos': np.array([s['x'].get(), s['y'].get(), s['z'].get()]),
                       'I0': s['I0'].get()})

    for i in range(Hres):
        for j in range(Wres):
            px, py = X[i,j], Y[i,j]
            dx, dy = px - xC, py - yC
            if dx**2 + dy**2 <= R**2:
                pz = zC + np.sqrt(R**2 - dx**2 - dy**2)
                P = np.array([px, py, pz])
                N = (P - np.array([xC, yC, zC])) / np.linalg.norm(P - np.array([xC, yC, zC]))
                V = O - P
                V /= np.linalg.norm(V)
                I = 0
                for L in lights:
                    L_vec = L['pos'] - P
                    L_vec /= np.linalg.norm(L_vec)
                    H_vec = (L_vec + V)/np.linalg.norm(L_vec + V)
                    I_diff = kd * L['I0'] * max(0, np.dot(N,L_vec))
                    I_spec = ks * L['I0'] * max(0, np.dot(N,H_vec))**n
                    I =I + I_diff + I_spec
                    if (j == 42):
                        if (i == 53):
                            print(f"{I:.0f}", f"+{i:.0f}", f"+{j:.0f}", end=' ')
                        if (i == 54):
                            print(f"{I:.0f}", f"+{i:.0f}", f"+{j:.0f}", end=' ')
                        if (i == 55):
                            print(f"{I:.0f}", f"+{i:.0f}", f"+{j:.0f}", end=' ')

                brightness[i,j] = I
        print()


    brightness_norm = (brightness / np.max(brightness) * 255).astype(np.uint8)
    img = Image.fromarray(brightness_norm)
    img.save("sphere_brightness.png")
    img_tk = ImageTk.PhotoImage(img)
    label_img.config(image=img_tk)
    label_img.image = img_tk

    # --- Расчет яркости контрольных точек ---
    points = [
        (xC, yC, zC + R),  # Верхняя точка
        (xC + R, yC, zC),  # Экватор по X
        (xC, yC + R, zC)  # Экватор по Y
    ]

    values = []
    for px, py, pz in points:
        # Вектор от центра сферы к точке
        P = np.array([px, py, pz])
        N = (P - np.array([xC, yC, zC])) / np.linalg.norm(P - np.array([xC, yC, zC]))
        V = np.array([0, 0, zO]) - P
        V /= np.linalg.norm(V)
        I = 0
        for light in lights:
            L = light['pos'] - P
            L /= np.linalg.norm(L)
            H_vec = (L + V) / np.linalg.norm(L + V)
            I_diff = kd * light['I0'] * max(0, np.dot(N, L))
            I_spec = ks * light['I0'] * max(0, np.dot(N, H_vec)) ** n
            I += I_diff + I_spec
        values.append(I)

    print(f"Z ({points[0][0]}, {points[0][1]}, {points[0][2]}) = {values[0]:.3f}")
    print(f"X ({points[1][0]}, {points[1][1]}, {points[1][2]}) = {values[1]:.3f}")
    print(f"Y ({points[2][0]}, {points[2][1]}, {points[2][2]}) = {values[2]:.3f}")
    print(f"Max = {np.max(brightness):.3f}")
    print(f"Min = {np.min(brightness):.3f}")

def add_light():
    frame = Frame(lights_frame)
    frame.pack(pady=2)
    x = DoubleVar(value=200)
    y = DoubleVar(value=200)
    z = DoubleVar(value=800)
    I0 = DoubleVar(value=1000)
    sources.append({'frame': frame, 'x': x, 'y': y, 'z': z, 'I0': I0})
    Label(frame, text="x").pack(side=LEFT)
    Entry(frame, textvariable=x, width=5).pack(side=LEFT)
    Label(frame, text="y").pack(side=LEFT)
    Entry(frame, textvariable=y, width=5).pack(side=LEFT)
    Label(frame, text="z").pack(side=LEFT)
    Entry(frame, textvariable=z, width=5).pack(side=LEFT)
    Label(frame, text="I0").pack(side=LEFT)
    Entry(frame, textvariable=I0, width=5).pack(side=LEFT)

root = Tk()
root.title("глаз проктол")

slider_xC = Scale(root, from_=-1000, to=1000, orient=HORIZONTAL, label="xC"); slider_xC.set(0); slider_xC.grid(row=0,column=0)
slider_yC = Scale(root, from_=-1000, to=1000, orient=HORIZONTAL, label="yC"); slider_yC.set(0); slider_yC.grid(row=0,column=1)
slider_zC = Scale(root, from_=100, to=2000, orient=HORIZONTAL, label="zC"); slider_zC.set(500); slider_zC.grid(row=0,column=2)
slider_R = Scale(root, from_=10, to=500, orient=HORIZONTAL, label="R"); slider_R.set(100); slider_R.grid(row=0,column=3)

slider_zO = Scale(root, from_=100, to=2000, orient=HORIZONTAL, label="zO (наблюдатель)"); slider_zO.set(1000); slider_zO.grid(row=1,column=0,columnspan=2)

slider_kd = Scale(root, from_=0, to=1, resolution=0.01, orient=HORIZONTAL, label="kd"); slider_kd.set(0.7); slider_kd.grid(row=2,column=0)
slider_ks = Scale(root, from_=0, to=1, resolution=0.01, orient=HORIZONTAL, label="ks"); slider_ks.set(0.5); slider_ks.grid(row=2,column=1)
slider_n  = Scale(root, from_=1, to=100, orient=HORIZONTAL, label="n"); slider_n.set(20); slider_n.grid(row=2,column=2)

slider_W = Scale(root, from_=100, to=10000, orient=HORIZONTAL, label="W (мм)"); slider_W.set(500); slider_W.grid(row=3,column=0)
slider_H = Scale(root, from_=100, to=10000, orient=HORIZONTAL, label="H (мм)"); slider_H.set(500); slider_H.grid(row=3,column=1)

sources = []
lights_frame = Frame(root)
lights_frame.grid(row=4,column=0,columnspan=4)
Button(root, text="Добавить источник света", command=add_light).grid(row=5,column=0,columnspan=4)
add_light()

Button(root, text="Сгенерировать изображение", command=generate_image).grid(row=6,column=0,columnspan=4)

label_img = Label(root)
label_img.grid(row=7,column=0,columnspan=4)

label_values = Label(root, text="", justify=LEFT, font=("Arial", 10))
label_values.grid(row=8,column=0,columnspan=4)

root.mainloop()
