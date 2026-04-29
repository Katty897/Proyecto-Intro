"""
Epic Adventure - main.py
Versión final: carga robusta de imágenes, placeholders automáticos,
redimensionado con Pillow si está disponible, recursividad en UI.
"""

import tkinter as tk
from tkinter import messagebox
import random
import os

# Intento de usar Pillow para redimensionar imágenes con calidad.
try:
    from PIL import Image, ImageTk, ImageDraw, ImageFont, UnidentifiedImageError
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

# ---------------------------
# Utilidades de ruta y archivos
# ---------------------------
def proyecto_path(*parts):
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, *parts)

def existe_archivo(ruta):
    return os.path.isfile(ruta)

# ---------------------------
# Resolución flexible de nombres de imagen
# ---------------------------
def posibles_extensiones(nombre_base):
    base, ext = os.path.splitext(nombre_base)
    if ext:
        yield nombre_base
    else:
        for e in (".png", ".PNG", ".jpg", ".jpeg", ".gif", ".webp"):
            yield base + e

def normalizar_nombre(n):
    yield n
    yield n.replace(" ", "_")
    yield n.replace(" ", "-")
    yield n.lower()
    yield n.upper()
    yield n.title()

def resolver_ruta_imagen(ruta_rel_o_abs):
    # Si es absoluta y existe
    if ruta_rel_o_abs and os.path.isabs(ruta_rel_o_abs) and existe_archivo(ruta_rel_o_abs):
        return ruta_rel_o_abs

    # Intentar ruta relativa directa
    if ruta_rel_o_abs:
        cand = proyecto_path(ruta_rel_o_abs)
        if existe_archivo(cand):
            return cand

    nombre = os.path.basename(ruta_rel_o_abs) if ruta_rel_o_abs else ""
    assets_dir = proyecto_path("assets")

    candidatos = []
    if ruta_rel_o_abs:
        candidatos.append(ruta_rel_o_abs)
        candidatos.append(proyecto_path(ruta_rel_o_abs))

    for nvar in normalizar_nombre(nombre):
        for variante in posibles_extensiones(nvar):
            candidatos.append(os.path.join(assets_dir, variante))
            candidatos.append(os.path.join(assets_dir, variante.lower()))
            candidatos.append(os.path.join(assets_dir, variante.upper()))

    try:
        for f in os.listdir(assets_dir):
            if nombre and nombre.lower().replace(" ", "") in f.lower().replace(" ", ""):
                candidatos.append(os.path.join(assets_dir, f))
    except Exception:
        pass

    for c in candidatos:
        if existe_archivo(c):
            print(f"[resolver_ruta_imagen] usando: {c}")
            return c

    print(f"[resolver_ruta_imagen] NO encontró imagen para: {ruta_rel_o_abs}")
    return None

# ---------------------------
# Placeholders automáticos
# ---------------------------
def asegurar_carpeta_placeholders():
    carpeta = proyecto_path("assets", "placeholders")
    os.makedirs(carpeta, exist_ok=True)
    return carpeta

def crear_placeholder(nombre, ancho=180, alto=180, color_bg="#DDDDDD", color_text="#222222"):
    carpeta = asegurar_carpeta_placeholders()
    base = os.path.splitext(os.path.basename(nombre))[0]
    ruta = os.path.join(carpeta, f"ph_{base}.png")
    if os.path.isfile(ruta):
        return ruta
    try:
        if PIL_AVAILABLE:
            img = Image.new("RGBA", (ancho, alto), color_bg)
            draw = ImageDraw.Draw(img)
            try:
                fnt = ImageFont.truetype("arial.ttf", 16)
            except Exception:
                fnt = ImageFont.load_default()
            texto = base[:14]
            w, h = draw.textsize(texto, font=fnt)
            draw.text(((ancho - w) / 2, (alto - h) / 2), texto, font=fnt, fill=color_text)
            img.save(ruta)
            return ruta
        else:
            # Crear archivo PNG mínimo si no hay Pillow
            with open(ruta, "wb") as f:
                f.write(b"")
            return ruta
    except Exception:
        with open(ruta, "wb") as f:
            f.write(b"")
        return ruta

# ---------------------------
# Carga y redimensionado robusto
# ---------------------------
def cargar_imagen_redimensionada(ruta_original, ancho=160, alto=160):
    if not ruta_original:
        ph = crear_placeholder("missing", ancho, alto)
        return cargar_imagen_redimensionada(ph, ancho, alto)

    ruta = resolver_ruta_imagen(ruta_original)
    if not ruta:
        ph = crear_placeholder(ruta_original, ancho, alto)
        ruta = ph

    # Intento con Pillow
    if PIL_AVAILABLE:
        try:
            img = Image.open(ruta)
            img = img.convert("RGBA")
            img = img.resize((ancho, alto), Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"[cargar_imagen_redimensionada] Pillow fallo para {ruta}: {e}")

    # Fallback con tk.PhotoImage
    try:
        tkimg = tk.PhotoImage(file=ruta)
        w = tkimg.width()
        h = tkimg.height()
        if w > ancho or h > alto:
            fx = max(1, int(w / ancho))
            fy = max(1, int(h / alto))
            factor = max(fx, fy)
            tkimg = tkimg.subsample(factor, factor)
        return tkimg
    except Exception as e:
        print(f"[cargar_imagen_redimensionada] PhotoImage fallo para {ruta}: {e}")

    # Crear placeholder final y recargar
    ph = crear_placeholder(os.path.basename(ruta_original), ancho, alto)
    try:
        if PIL_AVAILABLE:
            img = Image.open(ph).convert("RGBA")
            img = img.resize((ancho, alto), Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        else:
            return tk.PhotoImage(file=ph)
    except Exception as e:
        print(f"[cargar_imagen_redimensionada] Falla final cargando placeholder {ph}: {e}")
        return None

# ============================================================
# CARGA DE PERSONAJES (RECURSIVO)
# ============================================================
def cargar_personajes(ruta="personajes.txt"):
    ruta_abs = proyecto_path(ruta)
    try:
        with open(ruta_abs, "r", encoding="utf-8") as f:
            lineas = [l.strip() for l in f.readlines() if l.strip() and not l.strip().startswith("#")]
    except FileNotFoundError:
        lineas = []
    def procesar(lista, idx=0, resultado=None):
        if resultado is None:
            resultado = []
        if idx >= len(lista):
            return resultado
        partes = lista[idx].split(",")
        if len(partes) >= 7:
            imagen_rel = partes[6].strip()
            p = {
                "nombre": partes[0].strip(),
                "pelicula": partes[1].strip(),
                "rol": partes[2].strip(),
                "vida_max": int(partes[3]),
                "vida": int(partes[3]),
                "ataque": int(partes[4]),
                "defensa": int(partes[5]),
                "imagen_ruta": imagen_rel,
                "ko": False,
            }
            resultado.append(p)
        return procesar(lista, idx + 1, resultado)
    return procesar(lineas)

# ============================================================
# LÓGICA DE COMBATE (RECURSIVO)
# ============================================================
def calcular_danio(atk, def_):
    return max(atk - def_, 1)

def todos_ko(lista, index=0):
    if index >= len(lista):
        return True
    if not lista[index]["ko"]:
        return False
    return todos_ko(lista, index + 1)

def siguiente_vivo(lista, index=0):
    if index >= len(lista):
        return None
    if not lista[index]["ko"]:
        return lista[index]
    return siguiente_vivo(lista, index + 1)

def obtener_seleccionados(vars_lista, personajes, index=0, resultado=None):
    if resultado is None:
        resultado = []
    if index >= len(vars_lista):
        return resultado
    if vars_lista[index].get():
        resultado.append(personajes[index])
    return obtener_seleccionados(vars_lista, personajes, index + 1, resultado)

def restaurar_vida(p):
    p["vida"] = p["vida_max"]
    p["ko"] = False
    return p

def copiar_personaje(p):
    return {k: v for k, v in p.items()}

# ============================================================
# APLICACIÓN PRINCIPAL
# ============================================================
class EpicAdventureApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Epic Adventure ✨ Imaginary Battle")
        self.root.geometry("920x660")
        self.root.resizable(False, False)

        self.todos_personajes = cargar_personajes()
        self.nombre_jugador = ""
        self.equipo_jugador = []
        self.equipo_hueco = []
        self.personaje_jugador_activo = None
        self.personaje_hueco_activo = None

        self.contenedor = tk.Frame(self.root, bg="#F8F8FF")
        self.contenedor.pack(fill="both", expand=True)

        self.imagenes_cache = {}

        self.ruta_fondo = None
        for nombre in ("assets/fondo_batalla.png", "assets/fondo_pantalla.png", "assets/fondo.png"):
            r = proyecto_path(nombre)
            if existe_archivo(r):
                self.ruta_fondo = r
                break

        self.mostrar_pantalla_inicio()

    # Crear checkbuttons recursivamente
    def crear_checkbuttons_rec(self, parent, personajes, vars_list, idx=0):
        if idx >= len(personajes):
            return
        var = tk.BooleanVar()
        vars_list.append(var)
        p = personajes[idx]
        texto = f"{p['nombre']} ({p['rol']})  HP:{p['vida_max']} ATK:{p['ataque']} DEF:{p['defensa']}"
        cb = tk.Checkbutton(parent, text=texto, variable=var, anchor="w", justify="left")
        cb.pack(fill="x", padx=12, pady=2)
        return self.crear_checkbuttons_rec(parent, personajes, vars_list, idx + 1)

    def mostrar_pantalla_inicio(self):
        for w in self.contenedor.winfo_children():
            w.destroy()
        tk.Label(self.contenedor, text="✨ EPIC ADVENTURE ✨", font=("Georgia", 22, "bold"), fg="#6A1B4D", bg=self.contenedor.cget("bg")).pack(pady=12)
        tk.Label(self.contenedor, text="Ingresa tu nombre:", font=("Helvetica", 11), bg=self.contenedor.cget("bg")).pack()
        self.entry_nombre = tk.Entry(self.contenedor, font=("Helvetica", 12))
        self.entry_nombre.pack(pady=6)
        tk.Label(self.contenedor, text="Elige exactamente 3 personajes:", font=("Helvetica", 11), bg=self.contenedor.cget("bg")).pack(pady=(8,0))
        frame_list = tk.Frame(self.contenedor, bg=self.contenedor.cget("bg"))
        frame_list.pack(fill="both", expand=False, padx=10, pady=6)
        self.vars_personajes = []
        self.crear_checkbuttons_rec(frame_list, self.todos_personajes, self.vars_personajes, 0)
        tk.Button(self.contenedor, text="INICIAR", command=self.iniciar_juego, bg="#E85D9A", fg="white").pack(pady=12)

    def iniciar_juego(self):
        nombre = self.entry_nombre.get().strip()
        if not nombre:
            messagebox.showerror("Error", "Debes ingresar tu nombre")
            return
        seleccionados = obtener_seleccionados(self.vars_personajes, self.todos_personajes)
        if len(seleccionados) != 3:
            messagebox.showerror("Error", f"Debes elegir exactamente 3 personajes (seleccionaste {len(seleccionados)})")
            return
        self.nombre_jugador = nombre
        self.equipo_jugador = [copiar_personaje(p) for p in seleccionados]
        self.preparar_batalla()

    def preparar_batalla(self):
        def filtrar(lista, idx=0, resultado=None):
            if resultado is None:
                resultado = []
            if idx >= len(lista):
                return resultado
            if lista[idx]["nombre"] not in [e["nombre"] for e in self.equipo_jugador]:
                resultado.append(lista[idx])
            return filtrar(lista, idx + 1, resultado)
        disponibles = filtrar(self.todos_personajes)
        if len(disponibles) < 3:
            disponibles = [copiar_personaje(p) for p in self.todos_personajes]
        seleccion = random.sample(disponibles, 3)
        self.equipo_hueco = [copiar_personaje(p) for p in seleccion]
        self.personaje_jugador_activo = self.equipo_jugador[0]
        self.personaje_hueco_activo = self.equipo_hueco[0]
        self.mostrar_batalla()

    def mostrar_batalla(self):
        for w in self.contenedor.winfo_children():
            w.destroy()
        canvas = tk.Canvas(self.contenedor, width=920, height=560)
        canvas.pack(fill="both", expand=False)
        if self.ruta_fondo:
            img_fondo = cargar_imagen_redimensionada(self.ruta_fondo, ancho=920, alto=560)
            if img_fondo:
                canvas.create_image(0, 0, anchor="nw", image=img_fondo)
                self.imagenes_cache["fondo"] = img_fondo
            else:
                canvas.configure(bg="#BEEAF5")
        else:
            canvas.configure(bg="#BEEAF5")
        pj = self.personaje_jugador_activo
        img_j = cargar_imagen_redimensionada(pj.get("imagen_ruta"), ancho=180, alto=180)
        if img_j:
            canvas.create_image(200, 320, image=img_j)
            self.imagenes_cache["img_j"] = img_j
        else:
            canvas.create_rectangle(110, 230, 290, 410, fill="#7FB3D5", outline="#2E86C1")
            canvas.create_text(200, 420, text=pj["nombre"], font=("Helvetica", 10, "bold"))
        canvas.create_text(200, 460, text=f"HP: {pj['vida']}/{pj['vida_max']}", font=("Helvetica", 11, "bold"), fill="#0B5345")
        canvas.create_text(200, 485, text=f"ATK: {pj['ataque']}   DEF: {pj['defensa']}", font=("Helvetica", 10), fill="#0B5345")
        ph = self.personaje_hueco_activo
        img_h = cargar_imagen_redimensionada(ph.get("imagen_ruta"), ancho=160, alto=160)
        if img_h:
            canvas.create_image(700, 200, image=img_h)
            self.imagenes_cache["img_h"] = img_h
        else:
            canvas.create_rectangle(620, 120, 780, 280, fill="#F1948A", outline="#C0392B")
            canvas.create_text(700, 300, text=ph["nombre"], font=("Helvetica", 10, "bold"))
        canvas.create_text(700, 330, text=f"HP: {ph['vida']}/{ph['vida_max']}", font=("Helvetica", 11, "bold"), fill="#641E16")
        canvas.create_text(700, 355, text=f"ATK: {ph['ataque']}   DEF: {ph['defensa']}", font=("Helvetica", 10), fill="#641E16")
        frame_bot = tk.Frame(self.contenedor, bg=self.contenedor.cget("bg"))
        frame_bot.pack(fill="x", pady=6)
        self.label_log = tk.Label(frame_bot, text="¿Qué hará tu personaje?", font=("Helvetica", 10), bg=self.contenedor.cget("bg"))
        self.label_log.pack(side="left", padx=12)
        tk.Button(frame_bot, text="🔄 CAMBIAR", command=self.mostrar_cambio_personaje, bg="#5EBF8A", fg="white").pack(side="right", padx=8)
        tk.Button(frame_bot, text="⚔ ATACAR", command=self.turno_jugador, bg="#E85D9A", fg="white").pack(side="right", padx=8)
        def mostrar_equipo_rec(lista, idx=0, titulo=None):
            if idx == 0 and titulo:
                tk.Label(self.contenedor, text=titulo, font=("Helvetica", 10, "bold"), bg=self.contenedor.cget("bg")).pack(anchor="w", padx=12)
            if idx >= len(lista):
                return
            p = lista[idx]
            estado = "KO" if p["ko"] else f"{p['vida']}/{p['vida_max']}"
            texto = f"  {p['nombre']}  —  HP: {estado}   ATK: {p['ataque']}   DEF: {p['defensa']}"
            tk.Label(self.contenedor, text=texto, font=("Helvetica", 9), bg=self.contenedor.cget("bg")).pack(anchor="w", padx=12)
            return mostrar_equipo_rec(lista, idx + 1)
        mostrar_equipo_rec(self.equipo_jugador, 0, titulo="Tu equipo:")
        mostrar_equipo_rec(self.equipo_hueco, 0, titulo="Equipo enemigo:")

    def turno_jugador(self):
        pj = self.personaje_jugador_activo
        ph = self.personaje_hueco_activo
        danio = calcular_danio(pj["ataque"], ph["defensa"])
        ph["vida"] -= danio
        log = f"{pj['nombre']} atacó a {ph['nombre']} causando {danio} de daño."
        if ph["vida"] <= 0:
            ph["vida"] = 0
            ph["ko"] = True
            log += f" {ph['nombre']} fue derrotada y capturada."
            nueva = restaurar_vida(copiar_personaje(ph))
            self.equipo_jugador.append(nueva)
            if todos_ko(self.equipo_hueco):
                messagebox.showinfo("Victoria", "Has derrotado al Hollow en esta tierra.")
                self.mostrar_pantalla_inicio()
                return
            self.personaje_hueco_activo = siguiente_vivo(self.equipo_hueco)
        else:
            log += self.turno_hueco()
        self.actualizar_log(log)
        self.mostrar_batalla()

    def turno_hueco(self):
        pj = self.personaje_jugador_activo
        ph = self.personaje_hueco_activo
        accion = random.choices(["atacar", "cambiar"], weights=[70, 30])[0]
        if accion == "cambiar":
            vivos = [p for p in self.equipo_hueco if not p["ko"]]
            opciones = [p for p in vivos if p["nombre"] != ph["nombre"]]
            if opciones:
                elegido = random.choice(opciones)
                self.personaje_hueco_activo = elegido
                return f" La Hueca cambió a {elegido['nombre']}."
        danio = calcular_danio(ph["ataque"], pj["defensa"])
        pj["vida"] -= danio
        texto = f" {ph['nombre']} atacó a {pj['nombre']} causando {danio} de daño."
        if pj["vida"] <= 0:
            pj["vida"] = 0
            pj["ko"] = True
            texto += f" {pj['nombre']} fue derrotada."
            nueva = restaurar_vida(copiar_personaje(pj))
            self.equipo_hueco.append(nueva)
            if todos_ko(self.equipo_jugador):
                messagebox.showinfo("Derrota", "Todos tus personajes están KO. Fin del juego.")
                self.mostrar_pantalla_inicio()
                return ""
            self.personaje_jugador_activo = siguiente_vivo(self.equipo_jugador)
        return texto

    def actualizar_log(self, texto):
        try:
            self.label_log.config(text=texto)
            self.label_log.update()
        except Exception:
            pass

    def mostrar_cambio_personaje(self):
        vivos = [p for p in self.equipo_jugador if not p["ko"] and p["nombre"] != self.personaje_jugador_activo["nombre"]]
        if not vivos:
            messagebox.showinfo("Sin opciones", "No tienes otras opciones disponibles.")
            return
        v = tk.Toplevel(self.root)
        v.title("Cambiar personaje")
        v.geometry("340x300")
        tk.Label(v, text="Elige tu nueva personaje:", font=("Helvetica", 11)).pack(pady=8)
        def crear_botones_rec(lista, idx=0):
            if idx >= len(lista):
                return
            p = lista[idx]
            txt = f"{p['nombre']}  HP:{p['vida']}/{p['vida_max']}"
            tk.Button(v, text=txt, command=lambda x=p: seleccionar(x), bg="#F0F0F0").pack(fill="x", padx=12, pady=6)
            return crear_botones_rec(lista, idx + 1)
        def seleccionar(p):
            self.personaje_jugador_activo = p
            v.destroy()
            self.mostrar_batalla()
        crear_botones_rec(vivos, 0)

# ============================================================
# EJECUCIÓN
# ============================================================
if __name__ == "__main__":
    root = tk.Tk()
    app = EpicAdventureApp(root)
    root.mainloop()
