import numpy as np
from tkinter import *
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


def compute_resolution(W_mm, H_mm, base_res=400):
    aspect = W_mm / H_mm
    Hres = base_res
    Wres = int(base_res * aspect)
    return Wres, Hres


def intersect_sphere(P, L, center, R):
    oc = P - center
    a = np.dot(L, L)
    b = 2 * np.dot(oc, L)
    c = np.dot(oc, oc) - R * R
    disc = b * b - 4 * a * c
    if disc < 0:
        return False
    t1 = (-b - np.sqrt(disc)) / (2 * a)
    t2 = (-b + np.sqrt(disc)) / (2 * a)
    return (t1 > 1e-3) or (t2 > 1e-3)


def generate_views_and_display():
    observer_dirs = [
        ("Вид XY (Z)", np.array([0, 0, 1]), np.array([0, 0, slider_zO.get()])),
        ("Вид XZ (Y)", np.array([0, 1, 0]), np.array([0, slider_zO.get(), 0])),
        ("Вид YZ (X)", np.array([1, 0, 0]), np.array([slider_zO.get(), 0, 0]))
    ]

    xC1, yC1, zC1, R1 = slider_xC1.get(), slider_yC1.get(), slider_zC1.get(), slider_R1.get()
    xC2, yC2, zC2, R2 = slider_xC2.get(), slider_yC2.get(), slider_zC2.get(), slider_R2.get()

    C1 = np.array([xC1, yC1, zC1])
    C2 = np.array([xC2, yC2, zC2])
    col1 = np.array([slider_Rs1.get(), slider_Gs1.get(), slider_Bs1.get()])
    col2 = np.array([slider_Rs2.get(), slider_Gs2.get(), slider_Bs2.get()])

    kd = slider_kd.get()
    ks = slider_ks.get()
    n = slider_n.get()

    lights = []
    for L in sources:
        Lpos = np.array([L["x"].get(), L["y"].get(), L["z"].get()])
        I0 = L["I0"].get()
        Lcol = np.array([L["r"].get(), L["g"].get(), L["b"].get()])
        lights.append({"pos": Lpos, "I0": I0, "col": Lcol})

    spheres = [
        {"C": C1, "R": R1, "col": col1},
        {"C": C2, "R": R2, "col": col2}
    ]

    fig, axs = plt.subplots(2, 2, figsize=(10, 10))

    for i in range(2):
        for j in range(2):
            axs[i, j].clear()


    views_data = []
    for idx, (name, dir_vec, O) in enumerate(observer_dirs):
        if idx == 0:
            grid_pos = (1, 0)
        elif idx == 1:
            grid_pos = (0, 1)
        else:
            grid_pos = (1, 1)

        if idx == 0:
            xs = [s["C"][0] - s["R"] for s in spheres] + [s["C"][0] + s["R"] for s in spheres]
            ys = [s["C"][1] - s["R"] for s in spheres] + [s["C"][1] + s["R"] for s in spheres]
        elif idx == 1:
            xs = [s["C"][0] - s["R"] for s in spheres] + [s["C"][0] + s["R"] for s in spheres]
            ys = [s["C"][2] - s["R"] for s in spheres] + [s["C"][2] + s["R"] for s in spheres]
        else:
            xs = [s["C"][1] - s["R"] for s in spheres] + [s["C"][1] + s["R"] for s in spheres]
            ys = [s["C"][2] - s["R"] for s in spheres] + [s["C"][2] + s["R"] for s in spheres]

        Wmm = max(xs) - min(xs) + 50
        Hmm = max(ys) - min(ys) + 50
        Wres, Hres = compute_resolution(Wmm, Hmm)

        X, Y = np.meshgrid(np.linspace(min(xs) - 25, max(xs) + 25, Wres),
                           np.linspace(min(ys) - 25, max(ys) + 25, Hres))
        img = np.zeros((Hres, Wres, 3), dtype=float)
        zbuf = np.full((Hres, Wres), -np.inf)

        for i in range(Hres):
            for j in range(Wres):
                px, py = X[i, j], Y[i, j]
                best_depth = -np.inf
                best_sphere = None
                best_P = None
                for s in spheres:
                    if idx == 0:
                        dx, dy = px - s["C"][0], py - s["C"][1]
                    elif idx == 1:
                        dx, dy = px - s["C"][0], py - s["C"][2]
                    else:
                        dx, dy = px - s["C"][1], py - s["C"][2]
                    if dx * dx + dy * dy <= s["R"] ** 2:
                        dz = np.sqrt(s["R"] ** 2 - dx * dx - dy * dy)
                        if idx == 0:
                            depth = s["C"][2] + dz
                            P = np.array([px, py, s["C"][2] + dz])
                        elif idx == 1:
                            depth = s["C"][1] + dz
                            P = np.array([px, s["C"][1] + dz, py])
                        else:
                            depth = s["C"][0] + dz
                            P = np.array([s["C"][0] + dz, px, py])
                        if depth > best_depth:
                            best_depth = depth
                            best_sphere = s
                            best_P = P
                if best_sphere is None:
                    continue
                C = best_sphere["C"]
                col = best_sphere["col"]
                P = best_P
                N = (P - C) / np.linalg.norm(P - C)
                V = (O - P) / np.linalg.norm(O - P)
                total = np.zeros(3)
                for L in lights:
                    Lvec = L["pos"] - P
                    Ldir = Lvec / np.linalg.norm(Lvec)
                    shadow = False
                    for other in spheres:
                        if other is best_sphere:
                            continue
                        if intersect_sphere(P, Ldir, other["C"], other["R"]):
                            shadow = True
                            break
                    if shadow:
                        continue
                    Hvec = (V + Ldir) / np.linalg.norm(V + Ldir)
                    diff = kd * max(0, np.dot(N, Ldir))
                    if diff > 0:
                        spec = ks * max(0, np.dot(N, Hvec)) ** n
                    else:
                        spec = 0
                    total += L["I0"] * L["col"] * col * (diff + spec)

                img[i, j] = total
                zbuf[i, j] = best_depth

        maxv = np.max(img)
        if maxv > 0:
            img_norm = (img / maxv * 255).astype(np.uint8)
        else:
            img_norm = img.astype(np.uint8)

        out_im = Image.fromarray(img_norm)
        out_im.save(f"lab5_result_{name.replace(' ', '_').replace('(', '').replace(')', '')}.png")

        ax = axs[grid_pos]
        ax.imshow(img_norm)
        ax.set_title(name)
        ax.axis('off')

        views_data.append((grid_pos, name, img_norm))

    axs[0, 0].axis('off')

    plt.tight_layout()

    if hasattr(generate_views_and_display, 'result_window') and generate_views_and_display.result_window.winfo_exists():
        generate_views_and_display.result_window.destroy()

    generate_views_and_display.result_window = Toplevel(root)
    generate_views_and_display.result_window.title("3 вида сфер - Z, Y, X")

    canvas = FigureCanvasTkAgg(fig, master=generate_views_and_display.result_window)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=BOTH, expand=True)

    Button(generate_views_and_display.result_window, text="Закрыть",
           command=generate_views_and_display.result_window.destroy).pack()


def add_light():
    fr = Frame(lights_frame)
    fr.pack(pady=1)
    x = DoubleVar(value=300);
    y = DoubleVar(value=0);
    z = DoubleVar(value=800)
    I0 = DoubleVar(value=1000);
    r = DoubleVar(value=1);
    g = DoubleVar(value=1);
    b = DoubleVar(value=1)
    Entry(fr, textvariable=x, width=5).pack(side=LEFT)
    Entry(fr, textvariable=y, width=5).pack(side=LEFT)
    Entry(fr, textvariable=z, width=5).pack(side=LEFT)
    Entry(fr, textvariable=I0, width=5).pack(side=LEFT)
    Entry(fr, textvariable=r, width=3).pack(side=LEFT)
    Entry(fr, textvariable=g, width=3).pack(side=LEFT)
    Entry(fr, textvariable=b, width=3).pack(side=LEFT)
    sources.append({"x": x, "y": y, "z": z, "I0": I0, "r": r, "g": g, "b": b})


root = Tk();
root.title("ЛР-5 - Управление параметрами")

control_frame = Frame(root)
control_frame.pack(pady=10)

sphere1_frame = LabelFrame(control_frame, text="Сфера 1", padx=5, pady=5)
sphere1_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

slider_xC1 = Scale(sphere1_frame, from_=-1000, to=1000, orient=HORIZONTAL, label="xC1");
slider_xC1.set(-150);
slider_xC1.pack()
slider_yC1 = Scale(sphere1_frame, from_=-1000, to=1000, orient=HORIZONTAL, label="yC1");
slider_yC1.set(0);
slider_yC1.pack()
slider_zC1 = Scale(sphere1_frame, from_=100, to=2000, orient=HORIZONTAL, label="zC1");
slider_zC1.set(500);
slider_zC1.pack()
slider_R1 = Scale(sphere1_frame, from_=20, to=500, orient=HORIZONTAL, label="R1");
slider_R1.set(150);
slider_R1.pack()

color1_frame = LabelFrame(sphere1_frame, text="Цвет сферы 1", padx=5, pady=5)
color1_frame.pack(pady=5)
slider_Rs1 = Scale(color1_frame, from_=0, to=1, resolution=0.01, orient=HORIZONTAL, label="R");
slider_Rs1.set(1);
slider_Rs1.pack()
slider_Gs1 = Scale(color1_frame, from_=0, to=1, resolution=0.01, orient=HORIZONTAL, label="G");
slider_Gs1.set(0.2);
slider_Gs1.pack()
slider_Bs1 = Scale(color1_frame, from_=0, to=1, resolution=0.01, orient=HORIZONTAL, label="B");
slider_Bs1.set(0.2);
slider_Bs1.pack()

sphere2_frame = LabelFrame(control_frame, text="Сфера 2", padx=5, pady=5)
sphere2_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

slider_xC2 = Scale(sphere2_frame, from_=-1000, to=1000, orient=HORIZONTAL, label="xC2");
slider_xC2.set(150);
slider_xC2.pack()
slider_yC2 = Scale(sphere2_frame, from_=-1000, to=1000, orient=HORIZONTAL, label="yC2");
slider_yC2.set(0);
slider_yC2.pack()
slider_zC2 = Scale(sphere2_frame, from_=100, to=2000, orient=HORIZONTAL, label="zC2");
slider_zC2.set(500);
slider_zC2.pack()
slider_R2 = Scale(sphere2_frame, from_=20, to=500, orient=HORIZONTAL, label="R2");
slider_R2.set(150);
slider_R2.pack()

color2_frame = LabelFrame(sphere2_frame, text="Цвет сферы 2", padx=5, pady=5)
color2_frame.pack(pady=5)
slider_Rs2 = Scale(color2_frame, from_=0, to=1, resolution=0.01, orient=HORIZONTAL, label="R");
slider_Rs2.set(0.2);
slider_Rs2.pack()
slider_Gs2 = Scale(color2_frame, from_=0, to=1, resolution=0.01, orient=HORIZONTAL, label="G");
slider_Gs2.set(0.2);
slider_Gs2.pack()
slider_Bs2 = Scale(color2_frame, from_=0, to=1, resolution=0.01, orient=HORIZONTAL, label="B");
slider_Bs2.set(1);
slider_Bs2.pack()

observer_frame = LabelFrame(control_frame, text="Наблюдатель и освещение", padx=5, pady=5)
observer_frame.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")

slider_zO = Scale(observer_frame, from_=200, to=3000, orient=HORIZONTAL, label="z наблюдателя");
slider_zO.set(1500);
slider_zO.pack()
slider_kd = Scale(observer_frame, from_=0, to=1, resolution=0.01, orient=HORIZONTAL, label="Коэф. диффуз. (kd)");
slider_kd.set(0.7);
slider_kd.pack()
slider_ks = Scale(observer_frame, from_=0, to=1, resolution=0.01, orient=HORIZONTAL, label="Коэф. зерк. (ks)");
slider_ks.set(0.5);
slider_ks.pack()
slider_n = Scale(observer_frame, from_=1, to=200, orient=HORIZONTAL, label="Экспонента (n)");
slider_n.set(50);
slider_n.pack()

lights_frame = LabelFrame(control_frame, text="Источники света", padx=5, pady=5)
lights_frame.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky="ew")

sources = []
Button(control_frame, text="Добавить источник света", command=add_light).grid(row=2, column=0, columnspan=3, pady=5)
add_light()

Button(control_frame, text="Сгенерировать 3 вида", command=generate_views_and_display,
       bg="lightblue", font=("Arial", 12)).grid(row=3, column=0, columnspan=3, pady=10)

root.mainloop()