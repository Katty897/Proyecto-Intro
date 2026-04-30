"""
Epic Adventure - main.py  v4.0
"""

import tkinter as tk
from tkinter import messagebox
import random
import os

try:
    from PIL import Image, ImageTk, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

# ── Música ──────────────────────────────────────────────────────────────────
# Se usa 'subprocess' + 'threading' para reproducir música SIN pygame.
# Esto funciona en Windows, macOS y Linux sin instalar librerías extra.
#
# Estrategia:
#   • Windows  → el comando nativo 'start' abre el reproductor del SO
#   • macOS    → 'afplay' es un reproductor de audio nativo
#   • Linux    → se intenta 'mpg123', 'vlc' o 'ffplay' (el que esté disponible)
#
# El proceso de reproducción se guarda en self._proc_musica para poder
# detenerlo cuando el jugador presione "Detener música".
import threading
import subprocess
import sys as _sys

# Detectamos el sistema operativo una sola vez
PLATAFORMA = _sys.platform   # 'win32', 'darwin' o 'linux'

def _reproducir_archivo(ruta):
    """
    Abre el archivo de audio en un proceso independiente del SO.
    Devuelve el objeto Popen para poder terminarlo después,
    o None si no se pudo iniciar la reproducción.
    """
    try:
        if PLATAFORMA == "win32":
            # En Windows usamos PowerShell con Windows Media Player
            # -NoProfile acelera el arranque; Start-Process abre en segundo plano
            proc = subprocess.Popen(
                ["powershell", "-NoProfile", "-Command",
                 f'(New-Object Media.SoundPlayer "{ruta}").PlayLooping()'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        elif PLATAFORMA == "darwin":
            # macOS incluye 'afplay' de serie (reproduce mp3/wav/aiff)
            proc = subprocess.Popen(
                ["afplay", ruta],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            # Linux: probamos reproductores en orden de preferencia
            for cmd in [["mpg123", "-q", ruta],
                        ["ffplay", "-nodisp", "-autoexit", ruta],
                        ["vlc", "--intf", "dummy", ruta]]:
                try:
                    proc = subprocess.Popen(
                        cmd,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    return proc
                except FileNotFoundError:
                    continue
            return None   # ningún reproductor encontrado
        return proc
    except Exception:
        return None

# ─────────────────────────────────────────────
# RUTAS
# ─────────────────────────────────────────────
def proyecto_path(*parts):
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, *parts)

def existe_archivo(ruta):
    return os.path.isfile(ruta)

# ─────────────────────────────────────────────
# RESOLUCIÓN DE IMÁGENES
# ─────────────────────────────────────────────
def resolver_ruta_imagen(ruta):
    if not ruta:
        return None
    if os.path.isabs(ruta) and existe_archivo(ruta):
        return ruta
    cand = proyecto_path(ruta)
    if existe_archivo(cand):
        return cand
    nombre = os.path.basename(ruta)
    assets = proyecto_path("assets")
    candidatos = [ruta, cand]
    variaciones = [nombre, nombre.replace(" ","_"), nombre.replace(" ","-"),
                   nombre.lower(), nombre.upper(), nombre.title()]
    extensiones = (".png",".PNG",".jpg",".jpeg",".gif",".webp")
    for nv in variaciones:
        base_nv, ext_nv = os.path.splitext(nv)
        exts = [ext_nv] if ext_nv else list(extensiones)
        for e in exts:
            candidatos += [os.path.join(assets, base_nv+e),
                           os.path.join(assets, (base_nv+e).lower())]
    try:
        for f in os.listdir(assets):
            if nombre and nombre.lower().replace(" ","") in f.lower().replace(" ",""):
                candidatos.append(os.path.join(assets, f))
    except Exception:
        pass
    for c in candidatos:
        if existe_archivo(c):
            return c
    return None

def crear_placeholder(nombre, ancho=180, alto=180):
    carpeta = proyecto_path("assets", "placeholders")
    os.makedirs(carpeta, exist_ok=True)
    base = os.path.splitext(os.path.basename(nombre or "missing"))[0]
    ruta = os.path.join(carpeta, f"ph_{base}.png")
    if os.path.isfile(ruta):
        return ruta
    try:
        if PIL_AVAILABLE:
            img = Image.new("RGBA", (ancho, alto), "#334455")
            draw = ImageDraw.Draw(img)
            fnt = ImageFont.load_default()
            draw.text((8, alto//2 - 8), base[:16], font=fnt, fill="#AACCEE")
            img.save(ruta)
        else:
            open(ruta, "wb").close()
    except Exception:
        try: open(ruta, "wb").close()
        except Exception: pass
    return ruta

def cargar_imagen(ruta_original, ancho=160, alto=160):
    ruta = resolver_ruta_imagen(ruta_original)
    if not ruta:
        ruta = crear_placeholder(ruta_original or "missing", ancho, alto)
    if PIL_AVAILABLE:
        try:
            img = Image.open(ruta).convert("RGBA").resize((ancho, alto), Image.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception:
            pass
    try:
        tkimg = tk.PhotoImage(file=ruta)
        w, h = tkimg.width(), tkimg.height()
        if w > ancho or h > alto:
            factor = max(max(1, w//ancho), max(1, h//alto))
            tkimg = tkimg.subsample(factor, factor)
        return tkimg
    except Exception:
        pass
    return None

# ─────────────────────────────────────────────
# CARGA DE PERSONAJES
# ─────────────────────────────────────────────
def cargar_personajes(ruta="personajes.txt"):
    ruta_abs = proyecto_path(ruta)
    try:
        with open(ruta_abs, "r", encoding="utf-8") as f:
            lineas = [l.strip() for l in f if l.strip() and not l.strip().startswith("#")]
    except FileNotFoundError:
        lineas = []

    def procesar(lista, idx=0, res=None):
        if res is None: res = []
        if idx >= len(lista): return res
        p = lista[idx].split(",")
        if len(p) >= 7:
            res.append({
                "nombre":      p[0].strip(),
                "pelicula":    p[1].strip(),
                "rol":         p[2].strip(),
                "vida_max":    int(p[3]),
                "vida":        int(p[3]),
                "ataque":      int(p[4]),
                "defensa":     int(p[5]),
                "imagen_ruta": p[6].strip(),
                "ko": False,
            })
        return procesar(lista, idx+1, res)
    return procesar(lineas)

# ─────────────────────────────────────────────
# LÓGICA DE COMBATE
# ─────────────────────────────────────────────
PROB_CRITICO = 0.05   # 5 %

def calcular_danio(atk, def_, critico=False):
    base = max(atk - def_, 1)
    return base * 2 if critico else base

def tirar_critico():
    return random.random() < PROB_CRITICO

def todos_ko(lista, i=0):
    if i >= len(lista): return True
    if not lista[i]["ko"]: return False
    return todos_ko(lista, i+1)

def siguiente_vivo(lista, i=0):
    if i >= len(lista): return None
    if not lista[i]["ko"]: return lista[i]
    return siguiente_vivo(lista, i+1)

def obtener_seleccionados(vars_lista, personajes, i=0, res=None):
    if res is None: res = []
    if i >= len(vars_lista): return res
    if vars_lista[i].get(): res.append(personajes[i])
    return obtener_seleccionados(vars_lista, personajes, i+1, res)

def restaurar_vida(p):
    p["vida"] = p["vida_max"]
    p["ko"] = False
    return p

def copiar_personaje(p):
    return dict(p)

# ─────────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────────
AVATARES_JUGADOR = [
    {"nombre": "Neirity",   "emoji": "🌊", "desc": "Guerrera de Avatar"},
    {"nombre": "Hermione",  "emoji": "📚", "desc": "Maga de Harry Potter"},
    {"nombre": "Tris",      "emoji": "🔥", "desc": "Divergente valiente"},
]
AVATARES_HOLLOW = [
    {"nombre": "Hollow Rojo",   "emoji": "👹"},
    {"nombre": "Hollow Oscuro", "emoji": "💀"},
    {"nombre": "Hollow Araña",  "emoji": "🕷️"},
    {"nombre": "Hollow Sombra", "emoji": "👾"},
    {"nombre": "Hollow Escorpión","emoji": "🦂"},
]
UBICACIONES_MAPA = [
    {"nombre": "Abnegación",           "emoji": "🕊️", "desc": "El sector del sacrificio y la humildad — Divergente."},
    {"nombre": "Distrito 12",          "emoji": "🔥", "desc": "El hogar de los mineros, tierra de Katniss — Los Juegos del Hambre."},
    {"nombre": "Gryffindor",           "emoji": "🦁", "desc": "La torre del valor y la lealtad — Hogwarts."},
    {"nombre": "El Castillo de Walt D","emoji": "🏰", "desc": "El castillo mágico donde los sueños se hacen realidad."},
    {"nombre": "Casa de Mike",         "emoji": "🏠", "desc": "El refugio del barrio donde todo comenzó — Stranger Things."},
]

# ═══════════════════════════════════════════════════
# APP
# ═══════════════════════════════════════════════════
class EpicAdventureApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Epic Adventure - Imaginary Battle")
        self.root.geometry("960x720")
        self.root.resizable(False, False)

        self.todos_personajes = cargar_personajes()

        self.nombre_jugador  = ""
        self.avatar_jugador  = None
        self.avatar_hollow   = None
        self.equipo_jugador  = []
        self.equipo_hueco    = []
        self.pj_activo       = None
        self.ph_activo       = None
        self.puntaje_jugador = 0
        self.puntaje_hueco   = 0
        self.ubicacion_actual = 0
        self.ubicaciones_completadas = set()
        self.cache_imgs = {}
        self.vars_personajes = []   # se recrea en mostrar_inicio

        # ── Música ─────────────────────────────────────────────────────────────
        # Estado del sistema de música:
        #   musica_activa  → True si hay música sonando en este momento
        #   musica_canciones → lista de nombres "legibles" de las canciones
        #   musica_archivos  → nombres de archivo correspondientes (en carpeta music/)
        #   musica_idx       → índice de la canción que se reproducirá la próxima vez
        #   _proc_musica     → referencia al proceso del reproductor del SO;
        #                      se usa para poder detenerlo con .terminate()
        self.musica_activa    = False
        self.musica_canciones = [
            "Sorry",            # canción 0
            "What Do You Mean", # canción 1
            "Company",          # canción 2
        ]
        self.musica_archivos  = [
            "sorry.mp3",
            "what_do_you_mean.mp3",
            "company.mp3",
        ]
        self.musica_idx   = 0    # próxima canción a reproducir (rota en ciclo)
        self._proc_musica = None # proceso activo del reproductor (None si no hay)

        self.ruta_fondo = None
        for f in ("assets/fondo_batalla.png","assets/fondo_pantalla.png","assets/fondo.png"):
            r = proyecto_path(f)
            if existe_archivo(r):
                self.ruta_fondo = r
                break

        self.contenedor = tk.Frame(self.root, bg="#F8F8FF")
        self.contenedor.pack(fill="both", expand=True)
        self.mostrar_inicio()

    # ══════════════════════════════════════════
    # PANTALLA INICIO
    # ══════════════════════════════════════════
    def mostrar_inicio(self):
        for w in self.contenedor.winfo_children():
            w.destroy()
        self.vars_personajes = []
        self.contenedor.configure(bg="#F8F8FF")
        BG = "#F8F8FF"

        # ── Barra superior fija ──
        barra = tk.Frame(self.contenedor, bg="#6A1B4D")
        barra.pack(fill="x", side="top")
        tk.Label(barra, text="✨ EPIC ADVENTURE ✨", font=("Georgia",16,"bold"),
                 fg="white", bg="#6A1B4D").pack(side="left", padx=12, pady=6)
        tk.Button(barra, text="ℹ About", font=("Helvetica",10,"bold"),
                  bg="#E85D9A", fg="white", relief="flat",
                  command=self.mostrar_about).pack(side="right", padx=12, pady=6)

        # ── Scroll externo (toda la página) ──
        page_cv   = tk.Canvas(self.contenedor, bg=BG, highlightthickness=0)
        page_sb   = tk.Scrollbar(self.contenedor, orient="vertical", command=page_cv.yview)
        page_cv.configure(yscrollcommand=page_sb.set)
        page_sb.pack(side="right", fill="y")
        page_cv.pack(side="left", fill="both", expand=True)

        page_inner = tk.Frame(page_cv, bg=BG)
        page_win   = page_cv.create_window((0,0), window=page_inner, anchor="nw")

        def _page_resize(e):  page_cv.itemconfig(page_win, width=e.width)
        def _page_scroll(e):  page_cv.configure(scrollregion=page_cv.bbox("all"))
        page_cv.bind("<Configure>", _page_resize)
        page_inner.bind("<Configure>", _page_scroll)

        # Rueda de ratón en la zona exterior
        def _page_wheel(e):
            page_cv.yview_scroll(int(-1*(e.delta/120)), "units")
        page_cv.bind_all("<MouseWheel>", _page_wheel)

        # ── Nombre ──
        tk.Label(page_inner, text="Ingresa tu nombre (solo letras):",
                 font=("Helvetica",11), bg=BG).pack(pady=(16,0))
        self.entry_nombre = tk.Entry(page_inner, font=("Helvetica",12), width=28)
        self.entry_nombre.pack(pady=6)

        # ── Avatar jugador ──
        tk.Label(page_inner, text="Elige tu Avatar (cosmético, no pelea):",
                 font=("Helvetica",11,"bold"), bg=BG).pack(pady=(10,0))
        self.var_avatar = tk.IntVar(value=0)
        fa = tk.Frame(page_inner, bg=BG)
        fa.pack(pady=4, anchor="w", padx=40)
        for i, av in enumerate(AVATARES_JUGADOR):
            tk.Radiobutton(
                fa,
                text=f"{av['emoji']}  {av['nombre']} — {av['desc']}",
                variable=self.var_avatar, value=i,
                font=("Helvetica",10), bg=BG, anchor="w"
            ).pack(fill="x", pady=2)

        # ── Separador ──
        tk.Frame(page_inner, bg="#CCCCCC", height=1).pack(fill="x", padx=20, pady=8)

        # ── Título de la lista de personajes ──
        tk.Label(page_inner, text="Elige exactamente 3 personajes de combate:",
                 font=("Helvetica",11,"bold"), bg=BG).pack(pady=(4,0))
        tk.Label(page_inner,
                 text="(Desplázate con la rueda del ratón dentro del recuadro)",
                 font=("Helvetica",9,"italic"), fg="#888888", bg=BG).pack(pady=(0,4))

        # ── Lista scrollable con canvas INTERNO de altura fija ──
        #    El truco: canvas con height fijo + frame interior que crece libremente.
        #    Los checkbuttons viven en frame_checks (dentro del canvas), NO en un
        #    canvas anidado, para que los BooleanVar funcionen correctamente.
        lista_frame = tk.Frame(page_inner, bg="#E8E8F0", bd=2, relief="sunken")
        lista_frame.pack(fill="x", padx=30, pady=4)

        lista_cv = tk.Canvas(lista_frame, bg="#F8F8FF", highlightthickness=0, height=260)
        lista_sb = tk.Scrollbar(lista_frame, orient="vertical", command=lista_cv.yview)
        lista_cv.configure(yscrollcommand=lista_sb.set)
        lista_sb.pack(side="right", fill="y")
        lista_cv.pack(side="left", fill="both", expand=True)

        # frame_checks es el contenedor real de los Checkbutton
        frame_checks = tk.Frame(lista_cv, bg="#F8F8FF")
        fc_win = lista_cv.create_window((0,0), window=frame_checks, anchor="nw")

        def _fc_resize(e): lista_cv.itemconfig(fc_win, width=e.width)
        def _fc_scroll(e): lista_cv.configure(scrollregion=lista_cv.bbox("all"))
        lista_cv.bind("<Configure>", _fc_resize)
        frame_checks.bind("<Configure>", _fc_scroll)

        # Cuando el ratón está SOBRE la lista, la rueda controla SOLO esa lista
        def _lista_wheel(e):
            lista_cv.yview_scroll(int(-1*(e.delta/120)), "units")
            return "break"   # evita que el evento suba a la página
        lista_cv.bind("<Enter>", lambda e: lista_cv.bind_all("<MouseWheel>", _lista_wheel))
        lista_cv.bind("<Leave>", lambda e: lista_cv.bind_all("<MouseWheel>", _page_wheel))

        # Crear los checkbuttons DIRECTAMENTE en frame_checks (no recursivo sobre canvas)
        for p in self.todos_personajes:
            var = tk.BooleanVar(value=False)
            self.vars_personajes.append(var)
            txt = f"  {p['nombre']}  ({p['rol']})   HP:{p['vida_max']}  ATK:{p['ataque']}  DEF:{p['defensa']}"
            cb = tk.Checkbutton(
                frame_checks, text=txt, variable=var,
                anchor="w", font=("Helvetica",10), bg="#F8F8FF",
                activebackground="#E0E0FF", selectcolor="#CCDDFF"
            )
            cb.pack(fill="x", padx=8, pady=3)

        # ── Botón INICIAR ──
        tk.Button(page_inner, text="▶  INICIAR JUEGO", command=self.iniciar_juego,
                  bg="#E85D9A", fg="white", font=("Helvetica",13,"bold"),
                  padx=24, pady=8).pack(pady=20)

    # ══════════════════════════════════════════
    # ABOUT
    # ══════════════════════════════════════════
    def mostrar_about(self):
        v = tk.Toplevel(self.root)
        v.title("Acerca del Proyecto")
        v.geometry("500x440")
        v.resizable(False, False)
        v.configure(bg="#F8F8FF")
        tk.Label(v, text="✨ EPIC ADVENTURE ✨", font=("Georgia",18,"bold"),
                 fg="#6A1B4D", bg="#F8F8FF").pack(pady=14)
        info = (
            "Proyecto: Epic Adventure — Imaginary Battle\n\n"
            "Juego de combate por turnos inspirado en Bleach.\n"
            "Elige 3 personajes, explora el mapa y derrota Hollows\n"
            "para capturar sus guerreros y expandir tu equipo.\n\n"
            "Mecánicas:\n"
            "  • Daño = ATK atacante − DEF defensor  (mínimo 1)\n"
            "  • Golpe crítico (5% prob.) = daño × 2, se muestra en pantalla\n"
            "  • Al hacer KO al enemigo lo capturas (vida reiniciada)\n"
            "  • Si tu personaje cae en KO, el Hollow lo captura\n"
            "  • Ganas la batalla cuando el Hollow no tiene personajes\n"
            "  • Ganas el juego al completar las 5 zonas del mapa\n"
            "  • Pierdes si te quedas sin personajes vivos\n"
            "  • Mapa: 5 ubicaciones, solo puedes ir a adyacentes\n"
            "  • Puntaje: +1 por cada personaje capturado\n\n"
            "Versión: 4.0   |   Python & Tkinter"
        )
        tk.Label(v, text=info, font=("Helvetica",10), bg="#F8F8FF",
                 justify="left", wraplength=460).pack(padx=20)
        tk.Button(v, text="Cerrar", command=v.destroy,
                  bg="#E85D9A", fg="white", font=("Helvetica",10)).pack(pady=12)

    # ══════════════════════════════════════════
    # INICIAR JUEGO
    # ══════════════════════════════════════════
    def iniciar_juego(self):
        """
        Valida los datos ingresados en la pantalla de inicio y arranca la partida.

        Pasos de validación (en orden):
          1. El nombre no puede estar vacío.
          2. El nombre solo puede contener letras y espacios (sin números ni símbolos).
          3. Deben seleccionarse EXACTAMENTE 3 personajes de combate.

        Si todo es válido, guarda el estado inicial en los atributos de la clase:
          • nombre_jugador, avatar_jugador → identidad visual del jugador
          • equipo_jugador                 → copia de los 3 personajes elegidos
          • puntaje_jugador/hueco          → reiniciados a 0
          • ubicacion_actual               → empieza en el índice 0 del mapa
          • ubicaciones_completadas        → conjunto vacío (ninguna zona ganada)

        Luego llama a mostrar_mapa() para ir directamente al mapa.
        """
        nombre = self.entry_nombre.get().strip()
        if not nombre:
            messagebox.showerror("Error","Debes ingresar tu nombre.")
            return
        if not all(c.isalpha() or c == " " for c in nombre):
            messagebox.showerror("Error","El nombre solo puede contener letras (sin números ni símbolos).")
            return

        sel = obtener_seleccionados(self.vars_personajes, self.todos_personajes)
        if len(sel) != 3:
            messagebox.showerror("Error", f"Debes elegir exactamente 3 personajes (tienes {len(sel)}).")
            return

        self.nombre_jugador  = nombre
        self.avatar_jugador  = AVATARES_JUGADOR[self.var_avatar.get()]
        self.equipo_jugador  = [copiar_personaje(p) for p in sel]
        self.puntaje_jugador = 0
        self.puntaje_hueco   = 0
        self.ubicacion_actual = 0
        self.ubicaciones_completadas = set()
        self.mostrar_mapa()

    # ══════════════════════════════════════════
    # MAPA
    # ══════════════════════════════════════════
    def mostrar_mapa(self):
        """
        Dibuja la pantalla principal del MAPA DE EXPLORACIÓN.

        Esta es la pantalla central del juego entre batallas. Muestra:
          • Cabecera con título, botón de música y datos del jugador
          • Lista de las 5 ubicaciones con colores según su estado:
              ─ Verde/activa   → ubicación donde está el jugador ahora
              ─ Azul clara     → adyacente (se puede mover a ella)
              ─ Gris oscuro    → completada (Hollow ya derrotado)
              ─ Apagada        → no accesible todavía
          • Botón "Moverme aquí" en ubicaciones adyacentes
          • Botón "Combatir Hollow" en la ubicación actual
          • Botón para volver al menú principal

        Lógica de adyacencia:
          Las ubicaciones son una lista lineal (0..4). Solo se puede ir
          a la ubicación anterior o siguiente (|idx_destino - idx_actual| == 1).
          Esto obliga al jugador a recorrer el mapa en orden, no saltar.

        El botón de música se crea aquí y queda guardado en self.btn_musica
        para poder actualizarlo desde _toggle_musica sin redibujar todo.
        """
        for w in self.contenedor.winfo_children(): w.destroy()
        BG = "#1A1A2E"
        self.contenedor.configure(bg=BG)

        # ── Cabecera con botón de música ──
        header = tk.Frame(self.contenedor, bg=BG)
        header.pack(fill="x", padx=20, pady=(10,0))

        tk.Label(header, text="🗺️  MAPA DE EXPLORACIÓN",
                 font=("Georgia",16,"bold"), fg="#E0C97F", bg=BG).pack(side="left")

        # Botón música (derecha del título)
        cancion_actual = self.musica_canciones[self.musica_idx]
        icono_musica  = "⏹ Detener música" if self.musica_activa else "🎵 Reproducir música"
        color_musica  = "#CC4488" if self.musica_activa else "#5588CC"
        self.btn_musica = tk.Button(
            header,
            text=icono_musica,
            font=("Helvetica",10,"bold"),
            bg=color_musica, fg="white",
            relief="flat", padx=10, pady=4,
            command=self._toggle_musica
        )
        self.btn_musica.pack(side="right")

        # Etiqueta canción
        self.lbl_cancion = tk.Label(
            self.contenedor,
            text=f"🎵 Justin Bieber — {cancion_actual}" if self.musica_activa else "",
            font=("Helvetica",9,"italic"), fg="#AA88CC", bg=BG
        )
        self.lbl_cancion.pack()

        av = self.avatar_jugador
        vivos = len([p for p in self.equipo_jugador if not p["ko"]])
        completadas = len(self.ubicaciones_completadas)
        tk.Label(self.contenedor,
                 text=f"{av['emoji']} {self.nombre_jugador}   |   Puntaje: {self.puntaje_jugador}"
                      f"   |   Personajes vivos: {vivos}"
                      f"   |   Zonas: {completadas}/{len(UBICACIONES_MAPA)}",
                 font=("Helvetica",10), fg="#AAAACC", bg=BG).pack()
        tk.Label(self.contenedor,
                 text="Solo puedes moverte a ubicaciones adyacentes (arriba/abajo en la lista).",
                 font=("Helvetica",9), fg="#666688", bg=BG).pack(pady=(2,8))

        frame_mapa = tk.Frame(self.contenedor, bg=BG)
        frame_mapa.pack(pady=4, fill="x")
        self._dibujar_ubicaciones(frame_mapa, 0)

        tk.Button(self.contenedor, text="↩ Menú Principal",
                  command=self._confirmar_salir,
                  bg="#444", fg="white", font=("Helvetica",9)).pack(pady=14)

    def _toggle_musica(self):
        """
        Alterna entre REPRODUCIR y DETENER la música de Justin Bieber.

        Lógica principal:
        ─────────────────
        1. Si la música ESTÁ activa  →  terminamos el proceso del reproductor
           y marcamos musica_activa = False.

        2. Si la música NO está activa  →  buscamos el archivo .mp3 de la
           canción actual (índice musica_idx), lanzamos el reproductor en un
           hilo separado para no bloquear la UI, y avanzamos el índice para
           que la próxima vez que el jugador presione el botón suene otra canción.

        El reproductor corre en subprocess (ver función _reproducir_archivo).
        Guardamos la referencia en self._proc_musica para poder hacer .terminate().

        Después de cambiar el estado, actualizamos el texto y color del botón
        sin necesidad de redibujar toda la pantalla del mapa.
        """

        if self.musica_activa:
            # ── DETENER MÚSICA ────────────────────────────────────────────────
            # Terminamos el proceso del reproductor si sigue corriendo
            if self._proc_musica is not None:
                try:
                    self._proc_musica.terminate()   # envía señal de cierre al proceso
                except Exception:
                    pass   # ya terminó solo, no pasa nada
            self._proc_musica = None
            self.musica_activa = False

        else:
            # ── REPRODUCIR MÚSICA ─────────────────────────────────────────────
            # Construimos la ruta completa al archivo de la canción actual
            ruta = proyecto_path("music", self.musica_archivos[self.musica_idx])

            # Verificamos que el archivo exista antes de intentar reproducirlo
            if not existe_archivo(ruta):
                messagebox.showwarning(
                    "Archivo no encontrado",
                    f"No se encontró el archivo de música:\n{ruta}\n\n"
                    "Crea la carpeta 'music/' junto a main.py y agrega:\n"
                    "  sorry.mp3\n"
                    "  what_do_you_mean.mp3\n"
                    "  company.mp3\n\n"
                    "Puedes descargar MP3 legalmente desde sitios autorizados."
                )
                return

            # Lanzamos la reproducción en un hilo para no congelar la UI.
            # _reproducir_archivo devuelve el Popen; lo guardamos en self._proc_musica.
            def _iniciar():
                proc = _reproducir_archivo(ruta)
                self._proc_musica = proc   # guardamos referencia para poder detenerlo

            hilo = threading.Thread(target=_iniciar, daemon=True)
            hilo.start()

            self.musica_activa = True
            # Avanzamos al siguiente índice en ciclo (0→1→2→0→…)
            self.musica_idx = (self.musica_idx + 1) % len(self.musica_canciones)

        # ── Actualizar el botón y la etiqueta de canción en pantalla ──────────
        # Hacemos esto sin redibujar todo el mapa para que sea instantáneo.
        try:
            cancion_mostrar = self.musica_canciones[
                (self.musica_idx - 1) % len(self.musica_canciones)
                if self.musica_activa else self.musica_idx
            ]
            self.btn_musica.config(
                text  = "⏹ Detener música" if self.musica_activa else "🎵 Reproducir música",
                bg    = "#CC4488"          if self.musica_activa else "#5588CC"
            )
            self.lbl_cancion.config(
                text = f"🎵 Justin Bieber — {cancion_mostrar}" if self.musica_activa else ""
            )
        except Exception:
            pass   # los widgets pueden no existir si se cambió de pantalla

    def _dibujar_ubicaciones(self, parent, idx):
        """
        Dibuja recursivamente cada tarjeta de ubicación en el mapa.

        Parámetros:
          parent → frame padre donde se insertan las tarjetas
          idx    → índice de la ubicación actual a dibujar (0..4)

        La función se llama a sí misma con idx+1 hasta agotar la lista.
        Esto es recursión de cola: procesa una ubicación y luego la siguiente.

        Para cada ubicación determina su estado visual:
          ✔ Completada  → fondo muy oscuro, texto gris (ya no es relevante)
          ► Actual      → fondo azul medio, texto dorado (aquí está el jugador)
          → Adyacente   → fondo azul oscuro, texto claro (accesible)
            No accesible → fondo casi negro, texto apagado

        Botones que aparecen (solo en ubicaciones no completadas):
          • "Moverme aquí"    → solo en ubicaciones adyacentes
          • "Combatir Hollow" → solo en la ubicación actual

        El emoji y la descripción de cada lugar vienen de UBICACIONES_MAPA.
        """
        loc = UBICACIONES_MAPA[idx]
        es_actual    = (idx == self.ubicacion_actual)
        es_adyacente = (abs(idx - self.ubicacion_actual) == 1)
        completada   = idx in self.ubicaciones_completadas

        if completada:
            cbg, cfg = "#111111", "#3A3A3A"
        elif es_actual:
            cbg, cfg = "#2E4057", "#E0C97F"
        elif es_adyacente:
            cbg, cfg = "#1E3A5F", "#CCCCFF"
        else:
            cbg, cfg = "#16213E", "#666688"

        fila = tk.Frame(parent, bg="#1A1A2E")
        fila.pack(fill="x", padx=40, pady=3)
        card = tk.Frame(fila, bg=cbg, bd=2, relief="groove")
        card.pack(fill="x")

        if completada:
            nombre_txt = f"  ✔  {loc['nombre']}  ── COMPLETADO"
            fuente_n   = ("Helvetica",11)
        elif es_actual:
            nombre_txt = f"► {loc['emoji']}  {loc['nombre']}"
            fuente_n   = ("Helvetica",12,"bold")
        else:
            nombre_txt = f"   {loc['emoji']}  {loc['nombre']}"
            fuente_n   = ("Helvetica",11)

        tk.Label(card, text=nombre_txt, font=fuente_n,
                 fg=cfg, bg=cbg, width=30, anchor="w").pack(side="left", padx=10, pady=6)
        tk.Label(card, text=loc["desc"], font=("Helvetica",9),
                 fg=cfg, bg=cbg).pack(side="left", padx=6)

        btn_box = tk.Frame(card, bg=cbg)
        btn_box.pack(side="right", padx=10)
        if not completada:
            if es_adyacente:
                tk.Button(btn_box, text="Moverme aquí",
                          command=lambda i=idx: self._mover_a(i),
                          bg="#5EBF8A", fg="white", font=("Helvetica",9)).pack(pady=4)
            elif es_actual:
                tk.Button(btn_box, text="⚔  Combatir Hollow",
                          command=self.preparar_batalla,
                          bg="#E85D9A", fg="white", font=("Helvetica",9,"bold")).pack(pady=4)

        self._dibujar_ubicaciones(parent, idx+1)

    def _mover_a(self, idx):
        self.ubicacion_actual = idx
        self.mostrar_mapa()

    def _confirmar_salir(self):
        if messagebox.askyesno("Salir","¿Regresar al menú? Se perderá el progreso."):
            self.contenedor.configure(bg="#F8F8FF")
            self.mostrar_inicio()

    # ══════════════════════════════════════════
    # PREPARAR BATALLA
    # ══════════════════════════════════════════
    def preparar_batalla(self):
        """
        Prepara e inicia un combate en la ubicación actual del mapa.

        Proceso:
          1. Filtra los personajes disponibles: excluye a los que ya están
             en el equipo del jugador (no pueden estar en los dos lados).
          2. Si hay menos de 3 disponibles, avisa al jugador y aborta.
          3. Elige aleatoriamente 3 personajes para el equipo Hollow
             (sin repetir, usando random.sample).
          4. Asigna un avatar Hollow aleatorio (cosmético, no afecta combate).
          5. Reinicia el puntaje del Hollow a 0 para esta batalla.
          6. Establece el personaje activo del jugador (el primero que no esté en KO)
             y el primer personaje del equipo Hollow.
          7. Llama a mostrar_batalla() para arrancar el combate.

        Nota: los personajes se copian con copiar_personaje() para no modificar
        los datos originales de self.todos_personajes.
        """

        disponibles = [p for p in self.todos_personajes
                       if p["nombre"] not in nombres_jugador]

        if len(disponibles) < 3:
            messagebox.showwarning("Aviso",
                "No hay suficientes personajes distintos para el Hollow.\n"
                "Vuelve al menú y elige otros personajes.")
            return

        self.equipo_hueco    = [copiar_personaje(p) for p in random.sample(disponibles, 3)]
        self.avatar_hollow   = random.choice(AVATARES_HOLLOW)
        self.puntaje_hueco   = 0
        self.pj_activo       = siguiente_vivo(self.equipo_jugador)
        self.ph_activo       = self.equipo_hueco[0]
        self.contenedor.configure(bg="#1C1C2E")
        self.mostrar_batalla()

    # ══════════════════════════════════════════
    # PANTALLA BATALLA
    # ══════════════════════════════════════════
    def mostrar_batalla(self, mensaje_critico=None):
        """
        Dibuja (o redibuja) la PANTALLA DE COMBATE completa.

        Se llama al inicio de cada turno y también después de cualquier acción
        para reflejar los cambios de HP, KO, capturas, etc.

        Estructura visual de la pantalla:
        ──────────────────────────────────
        ┌─────────────────────────────────────────────────────┐
        │  [Avatar jugador]    PUNTAJE    [Avatar Hollow]     │
        │                                                     │
        │   [Imagen PJ]          VS          [Imagen Hollow]  │
        │   [HP Bar PJ]                      [HP Bar Hollow]  │
        │   [Nombre / Stats]                 [Nombre / Stats] │
        │                  ⚡ CRÍTICO ⚡  (si aplica)         │
        ├─────────────────────────────────────────────────────┤
        │  [Log del turno]    [🗺 Mapa] [🔄 Cambiar] [⚔ Atacar]│
        ├─────────────────────────────────────────────────────┤
        │  Tu equipo:   PJ1  PJ2  PJ3  |  Equipo Hollow:  …  │
        └─────────────────────────────────────────────────────┘

        Parámetro:
          mensaje_critico → si es True, dibuja el texto "⚡ ¡CRÍTICO! ⚡"
                            en grande sobre el canvas (lo usa _mostrar_critico_y_continuar).

        Las imágenes de los personajes se cargan y cachean en self.cache_imgs
        para que Tkinter no las descarte (las PhotoImage se eliminan del GC
        si no tienen una referencia fuerte).
        """
        # Limpiamos todos los widgets anteriores de la pantalla de batalla
        for w in self.contenedor.winfo_children(): w.destroy()
        BG = "#1C1C2E"
        self.contenedor.configure(bg=BG)
        self.cache_imgs = {}   # vaciar caché de imágenes del turno anterior

        # ── Canvas principal ──
        cv = tk.Canvas(self.contenedor, width=960, height=440,
                       bg="#1C2C3C", highlightthickness=0)
        cv.pack()

        if self.ruta_fondo:
            img_f = cargar_imagen(self.ruta_fondo, 960, 440)
            if img_f:
                cv.create_image(0, 0, anchor="nw", image=img_f)
                self.cache_imgs["fondo"] = img_f

        loc = UBICACIONES_MAPA[self.ubicacion_actual]

        # ── PUNTAJE ──
        cv.create_rectangle(180, 0, 780, 28, fill="#000000", outline="")
        cv.create_text(480, 14,
                       text=f"🏆 {self.nombre_jugador}: {self.puntaje_jugador}"
                            f"   ⚔   Hollow: {self.puntaje_hueco}"
                            f"   |   {loc['emoji']} {loc['nombre']}",
                       font=("Helvetica",10,"bold"), fill="#FFD700")

        # ── LADO JUGADOR ──
        av_j = self.avatar_jugador
        pj   = self.pj_activo

        # Avatar cosmético
        cv.create_rectangle(4, 4, 90, 54, fill="#003322", outline="#00FF88")
        cv.create_text(47, 20, text=av_j["emoji"], font=("Helvetica",20))
        cv.create_text(47, 42, text=av_j["nombre"], font=("Helvetica",7), fill="#00FF88")

        # Imagen personaje jugador
        img_j = cargar_imagen(pj.get("imagen_ruta"), 180, 180)
        if img_j:
            cv.create_image(145, 255, image=img_j)
            self.cache_imgs["pj"] = img_j
        else:
            cv.create_rectangle(55, 165, 235, 345, fill="#223344", outline="#4488BB")
            cv.create_text(145, 255, text=pj["nombre"][:12], font=("Helvetica",10), fill="white")

        # HP bar jugador
        hp_pct = max(0.0, pj["vida"] / pj["vida_max"])
        hp_col = "#22DD44" if hp_pct > 0.5 else ("#FFAA00" if hp_pct > 0.25 else "#FF3333")
        cv.create_rectangle(50, 350, 240, 364, fill="#333333", outline="#666666")
        cv.create_rectangle(50, 350, 50 + int(190*hp_pct), 364, fill=hp_col, outline="")
        cv.create_text(145, 357, text=f"HP {pj['vida']}/{pj['vida_max']}",
                       font=("Helvetica",8,"bold"), fill="white")
        cv.create_text(145, 378, text=pj["nombre"],
                       font=("Helvetica",10,"bold"), fill="#00FF88")
        cv.create_text(145, 394, text=f"ATK {pj['ataque']}   DEF {pj['defensa']}",
                       font=("Helvetica",9), fill="#AADDCC")

        # ── LADO HOLLOW ──
        av_h = self.avatar_hollow
        ph   = self.ph_activo

        # Avatar del Hollow
        cv.create_rectangle(870, 4, 956, 54, fill="#330000", outline="#FF3333")
        cv.create_text(913, 20, text=av_h["emoji"], font=("Helvetica",20))
        cv.create_text(913, 42, text=av_h["nombre"], font=("Helvetica",7), fill="#FF4444")

        # Imagen personaje hollow
        img_h = cargar_imagen(ph.get("imagen_ruta"), 160, 160)
        if img_h:
            cv.create_image(790, 190, image=img_h)
            self.cache_imgs["ph"] = img_h
        else:
            cv.create_rectangle(710, 110, 870, 270, fill="#332222", outline="#BB4444")
            cv.create_text(790, 190, text=ph["nombre"][:12], font=("Helvetica",10), fill="white")

        # HP bar hollow
        hp_pct_h = max(0.0, ph["vida"] / ph["vida_max"])
        hp_col_h = "#22DD44" if hp_pct_h > 0.5 else ("#FFAA00" if hp_pct_h > 0.25 else "#FF3333")
        cv.create_rectangle(710, 278, 870, 292, fill="#333333", outline="#666666")
        cv.create_rectangle(710, 278, 710 + int(160*hp_pct_h), 292, fill=hp_col_h, outline="")
        cv.create_text(790, 285, text=f"HP {ph['vida']}/{ph['vida_max']}",
                       font=("Helvetica",8,"bold"), fill="white")
        cv.create_text(790, 306, text=ph["nombre"],
                       font=("Helvetica",10,"bold"), fill="#FF4444")
        cv.create_text(790, 322, text=f"ATK {ph['ataque']}   DEF {ph['defensa']}",
                       font=("Helvetica",9), fill="#DDAAAA")

        # ── VS ──
        cv.create_text(480, 200, text="VS", font=("Georgia",26,"bold"), fill="#FFD700")

        # ── CRÍTICO en pantalla ──
        if mensaje_critico:
            # Sombra
            cv.create_text(482, 122, text="⚡ ¡CRÍTICO! ⚡",
                           font=("Impact",36,"bold"), fill="#FF6600")
            # Texto principal
            cv.create_text(480, 120, text="⚡ ¡CRÍTICO! ⚡",
                           font=("Impact",36,"bold"), fill="#FFE500")

        # ── PANEL INFERIOR ──
        panel = tk.Frame(self.contenedor, bg=BG)
        panel.pack(fill="x", padx=8, pady=2)

        self.lbl_log = tk.Label(
            panel,
            text="⚔  Turno del jugador — elige una acción",
            font=("Helvetica",10), bg=BG, fg="#CCCCFF",
            wraplength=520, justify="left", anchor="w"
        )
        self.lbl_log.pack(side="left", padx=10, fill="x", expand=True)

        btn_f = tk.Frame(panel, bg=BG)
        btn_f.pack(side="right", padx=6)
        tk.Button(btn_f, text="🗺 Mapa",     command=self._volver_mapa,
                  bg="#446699", fg="white", font=("Helvetica",9)).pack(side="left", padx=3)
        tk.Button(btn_f, text="🔄 Cambiar",  command=self.mostrar_cambio,
                  bg="#5EBF8A", fg="white", font=("Helvetica",9)).pack(side="left", padx=3)
        tk.Button(btn_f, text="⚔  ATACAR",   command=self.turno_jugador,
                  bg="#E85D9A", fg="white", font=("Helvetica",10,"bold"),
                  padx=8).pack(side="left", padx=3)

        # ── EQUIPOS ──
        eq_frame = tk.Frame(self.contenedor, bg=BG)
        eq_frame.pack(fill="x", padx=8, pady=2)
        izq = tk.Frame(eq_frame, bg=BG); izq.pack(side="left", fill="x", expand=True)
        der = tk.Frame(eq_frame, bg=BG); der.pack(side="right", fill="x", expand=True)

        tk.Label(izq, text=f"── Tu equipo ({self.nombre_jugador}) ──",
                 font=("Helvetica",9,"bold"), fg="#00FF88", bg=BG).pack(anchor="w", padx=8)
        self._mostrar_equipo_labels(izq, self.equipo_jugador, "#00BB55", 0)

        tk.Label(der, text="── Equipo Hollow ──",
                 font=("Helvetica",9,"bold"), fg="#FF4444", bg=BG).pack(anchor="w", padx=8)
        self._mostrar_equipo_labels(der, self.equipo_hueco, "#CC2222", 0)

    def _mostrar_equipo_labels(self, parent, lista, color_vivo, idx):
        if idx >= len(lista): return
        p = lista[idx]
        if p["ko"]:
            txt = f"  💀  {p['nombre']}"
            fg  = "#555555"
        else:
            bar = "█" * int(10 * p["vida"] / p["vida_max"])
            txt = f"  ✦  {p['nombre']}   HP:{p['vida']}/{p['vida_max']}  [{bar:<10}]"
            fg  = color_vivo
        tk.Label(parent, text=txt, font=("Courier",9), fg=fg, bg="#1C1C2E").pack(anchor="w", padx=8)
        self._mostrar_equipo_labels(parent, lista, color_vivo, idx+1)

    def _volver_mapa(self):
        if messagebox.askyesno("Mapa","¿Abandonar el combate y volver al mapa?"):
            self.contenedor.configure(bg="#1A1A2E")
            self.mostrar_mapa()

    # ══════════════════════════════════════════
    # CRÍTICO — muestra pantalla y espera
    # ══════════════════════════════════════════
    def _mostrar_critico_y_continuar(self, log_texto, callback_post):
        """Muestra el mensaje CRÍTICO en la batalla por 1.8 s, luego llama callback."""
        self.mostrar_batalla(mensaje_critico=True)
        if self.lbl_log:
            self.lbl_log.config(text=log_texto)
        self.root.after(1800, callback_post)

    # ══════════════════════════════════════════
    # TURNOS
    # ══════════════════════════════════════════
    def turno_jugador(self):
        """
        Ejecuta el TURNO DEL JUGADOR cuando presiona el botón "⚔ ATACAR".

        Mecánica del turno:
        ───────────────────
        1. GOLPE DEL JUGADOR
           • Se tira la probabilidad de crítico (5%).
           • Se calcula el daño: ATK_jugador − DEF_hollow (mínimo 1).
             Si es crítico, el daño se duplica.
           • Se resta la vida al Hollow activo.

        2. ¿EL HOLLOW CAE EN KO?
           • Si su vida llega a 0 → lo marcamos KO y lo capturamos:
               ─ Se agrega una copia restaurada al equipo del jugador (+1 puntaje).
               ─ Si era el último Hollow → llamamos _victoria_batalla().
               ─ Si quedan más → avanzamos al siguiente Hollow vivo.
           • Si hay crítico mostramos la animación antes de continuar.

        3. CONTRAATAQUE DEL HOLLOW (si no hubo KO ni victoria)
           • Llamamos _turno_hueco() que decide si el Hollow ataca o cambia.
           • Si alguno de los dos golpes fue crítico → animación de crítico.
           • Luego se vuelve a llamar mostrar_batalla() para refrescar la UI.

        Esta función es el corazón del sistema de combate por turnos.
        """
        ph = self.ph_activo
        es_critico = tirar_critico()
        danio = calcular_danio(pj["ataque"], ph["defensa"], es_critico)
        ph["vida"] -= danio

        if es_critico:
            log = f"⚡ ¡CRÍTICO! ⚡  {pj['nombre']} atacó a {ph['nombre']}  →  {danio} de daño (x2)"
        else:
            log = f"⚔  {pj['nombre']} atacó a {ph['nombre']}  →  {danio} de daño"

        if ph["vida"] <= 0:
            ph["vida"] = 0
            ph["ko"]   = True
            log += f"\n🏆  ¡KO!  ¡{ph['nombre']} derrotado!  ➜  ¡Lo capturas! (+1 punto)"
            self.equipo_jugador.append(restaurar_vida(copiar_personaje(ph)))
            self.puntaje_jugador += 1

            if es_critico:
                def post():
                    if todos_ko(self.equipo_hueco):
                        self._victoria_batalla()
                    else:
                        self.ph_activo = siguiente_vivo(self.equipo_hueco)
                        self.mostrar_batalla()
                self._mostrar_critico_y_continuar(log, post)
            else:
                if todos_ko(self.equipo_hueco):
                    self._actualizar_log(log)
                    self._victoria_batalla()
                else:
                    self.ph_activo = siguiente_vivo(self.equipo_hueco)
                    self._actualizar_log(log)
                    self.mostrar_batalla()
            return

        # Hollow contraataca
        log_hueco, hueco_critico = self._turno_hueco()
        log_total = log + log_hueco

        if es_critico or hueco_critico:
            self._mostrar_critico_y_continuar(log_total, lambda: self.mostrar_batalla())
        else:
            self._actualizar_log(log_total)
            self.mostrar_batalla()

    def _turno_hueco(self):
        """Devuelve (texto_log, fue_critico)."""
        pj = self.pj_activo
        ph = self.ph_activo
        accion = random.choices(["atacar","cambiar"], weights=[70,30])[0]

        if accion == "cambiar":
            opts = [p for p in self.equipo_hueco if not p["ko"] and p["nombre"] != ph["nombre"]]
            if opts:
                nuevo = random.choice(opts)
                self.ph_activo = nuevo
                return f"\n🔄  El Hollow cambió a {nuevo['nombre']}.", False

        es_critico = tirar_critico()
        danio = calcular_danio(ph["ataque"], pj["defensa"], es_critico)
        pj["vida"] -= danio

        if es_critico:
            txt = f"\n⚡ ¡CRÍTICO! ⚡  {ph['nombre']} atacó a {pj['nombre']}  →  {danio} de daño (x2)"
        else:
            txt = f"\n💢  {ph['nombre']} atacó a {pj['nombre']}  →  {danio} de daño"

        if pj["vida"] <= 0:
            pj["vida"] = 0
            pj["ko"]   = True
            txt += f"\n💀  ¡KO!  ¡{pj['nombre']} derrotado!  ➜  ¡El Hollow lo captura! (+1 para Hollow)"
            self.equipo_hueco.append(restaurar_vida(copiar_personaje(pj)))
            self.puntaje_hueco += 1

            if todos_ko(self.equipo_jugador):
                return txt, es_critico   # se maneja arriba
            self.pj_activo = siguiente_vivo(self.equipo_jugador)

        return txt, es_critico

    def _actualizar_log(self, texto):
        try:
            self.lbl_log.config(text=texto)
            self.lbl_log.update()
        except Exception:
            pass

    # ══════════════════════════════════════════
    # VICTORIA / DERROTA
    # ══════════════════════════════════════════
    def _victoria_batalla(self):
        loc = UBICACIONES_MAPA[self.ubicacion_actual]
        self.ubicaciones_completadas.add(self.ubicacion_actual)

        if len(self.ubicaciones_completadas) == len(UBICACIONES_MAPA):
            self._pantalla_victoria_total()
            return

        v = tk.Toplevel(self.root)
        v.title("¡Victoria!")
        v.geometry("480x290")
        v.configure(bg="#0A2010")
        v.grab_set()
        tk.Label(v, text="🏆  ¡VICTORIA! 🏆", font=("Georgia",22,"bold"),
                 fg="#FFD700", bg="#0A2010").pack(pady=16)
        tk.Label(v, text=f"Derrotaste al Hollow en\n{loc['emoji']} {loc['nombre']}",
                 font=("Helvetica",13), fg="#AAFFAA", bg="#0A2010").pack()
        tk.Label(v, text=f"Puntaje acumulado: {self.puntaje_jugador} personaje(s)",
                 font=("Helvetica",11), fg="#FFD700", bg="#0A2010").pack(pady=6)
        zonas_restantes = len(UBICACIONES_MAPA) - len(self.ubicaciones_completadas)
        tk.Label(v,
                 text=f"Zonas completadas: {len(self.ubicaciones_completadas)}/{len(UBICACIONES_MAPA)}"
                      f"   |   Faltan: {zonas_restantes}",
                 font=("Helvetica",10), fg="#88DDFF", bg="#0A2010").pack(pady=4)
        def cerrar():
            v.destroy()
            self.contenedor.configure(bg="#1A1A2E")
            self.mostrar_mapa()
        tk.Button(v, text="➜  Continuar al mapa", command=cerrar,
                  bg="#E85D9A", fg="white", font=("Helvetica",12,"bold"),
                  padx=16, pady=6).pack(pady=16)

    def _derrota_batalla(self):
        loc = UBICACIONES_MAPA[self.ubicacion_actual]
        v = tk.Toplevel(self.root)
        v.title("Derrota")
        v.geometry("420x240")
        v.configure(bg="#1A0000")
        v.grab_set()
        tk.Label(v, text="💀  DERROTA 💀", font=("Georgia",20,"bold"),
                 fg="#FF3333", bg="#1A0000").pack(pady=14)
        tk.Label(v, text=f"Todos tus personajes cayeron en KO\nen {loc['emoji']} {loc['nombre']}.",
                 font=("Helvetica",11), fg="#FFAAAA", bg="#1A0000").pack()
        tk.Label(v, text=f"Puntaje total: {self.puntaje_jugador}",
                 font=("Helvetica",10), fg="#FFDD88", bg="#1A0000").pack(pady=6)
        def cerrar():
            v.destroy()
            self.contenedor.configure(bg="#1A1A2E")
            self.mostrar_mapa()
        tk.Button(v, text="↩  Volver al mapa", command=cerrar,
                  bg="#881111", fg="white", font=("Helvetica",11,"bold"),
                  padx=14, pady=5).pack(pady=14)

    def _pantalla_victoria_total(self):
        for w in self.contenedor.winfo_children(): w.destroy()
        BG = "#0A0A1A"
        self.contenedor.configure(bg=BG)

        tk.Label(self.contenedor, text=" ", bg=BG).pack(pady=16)
        tk.Label(self.contenedor,
                 text="🌟  ¡¡¡ GANASTE EL JUEGO !!!  🌟",
                 font=("Georgia",26,"bold"), fg="#FFD700", bg=BG).pack()
        tk.Label(self.contenedor,
                 text="Has completado todas las zonas y derrotado a todos los Hollows.",
                 font=("Helvetica",13), fg="#AADDFF", bg=BG).pack(pady=8)
        tk.Frame(self.contenedor, bg="#FFD700", height=2).pack(fill="x", padx=60, pady=8)
        av = self.avatar_jugador
        tk.Label(self.contenedor,
                 text=f"👤  Jugador:  {av['emoji']} {self.nombre_jugador}",
                 font=("Helvetica",13), fg="#FFFFFF", bg=BG).pack()
        tk.Label(self.contenedor,
                 text=f"🏆  Personajes capturados:  {self.puntaje_jugador}",
                 font=("Helvetica",14,"bold"), fg="#FFD700", bg=BG).pack(pady=4)
        tk.Label(self.contenedor,
                 text=f"🗺️  Zonas completadas:  {len(self.ubicaciones_completadas)}/{len(UBICACIONES_MAPA)}",
                 font=("Helvetica",12), fg="#AADDFF", bg=BG).pack()
        tk.Frame(self.contenedor, bg="#444466", height=1).pack(fill="x", padx=60, pady=10)
        tk.Label(self.contenedor, text="Tu equipo final:",
                 font=("Helvetica",11,"bold"), fg="#88FFAA", bg=BG).pack()
        self._equipo_victoria_labels(self.equipo_jugador, 0)
        tk.Frame(self.contenedor, bg="#444466", height=1).pack(fill="x", padx=60, pady=8)
        bf = tk.Frame(self.contenedor, bg=BG)
        bf.pack(pady=12)
        tk.Button(bf, text="🔁  Jugar de nuevo", command=self.mostrar_inicio,
                  bg="#E85D9A", fg="white", font=("Helvetica",12,"bold"),
                  padx=16, pady=8).pack(side="left", padx=10)
        tk.Button(bf, text="❌  Salir", command=self.root.quit,
                  bg="#444", fg="white", font=("Helvetica",11),
                  padx=12, pady=8).pack(side="left", padx=10)

    def _equipo_victoria_labels(self, lista, idx):
        if idx >= len(lista): return
        p = lista[idx]
        estado = "💀 KO" if p["ko"] else "✅ Vivo"
        fg = "#CCFFCC" if not p["ko"] else "#555555"
        tk.Label(self.contenedor,
                 text=f"   {estado}  {p['nombre']}   HP:{p['vida']}/{p['vida_max']}",
                 font=("Courier",10), fg=fg, bg="#0A0A1A").pack(anchor="center")
        self._equipo_victoria_labels(lista, idx+1)

    # ══════════════════════════════════════════
    # CAMBIO DE PERSONAJE
    # ══════════════════════════════════════════
    def mostrar_cambio(self):
        vivos = [p for p in self.equipo_jugador
                 if not p["ko"] and p["nombre"] != self.pj_activo["nombre"]]
        if not vivos:
            messagebox.showinfo("Sin opciones","No tienes otros personajes disponibles.")
            return
        v = tk.Toplevel(self.root)
        v.title("Cambiar personaje")
        v.geometry("400x360")
        v.configure(bg="#1C1C2E")
        tk.Label(v, text="Elige tu personaje:", font=("Helvetica",12,"bold"),
                 fg="#CCCCFF", bg="#1C1C2E").pack(pady=10)

        for p in vivos:
            bar = "█" * int(10 * p["vida"] / p["vida_max"])
            txt = f"{p['nombre']}   HP:{p['vida']}/{p['vida_max']}  [{bar:<10}]"
            tk.Button(v, text=txt, font=("Courier",10),
                      command=lambda x=p: _sel(x),
                      bg="#2E4057", fg="#00FF88", relief="flat",
                      activebackground="#3A5070").pack(fill="x", padx=14, pady=4)

        def _sel(p):
            self.pj_activo = p
            v.destroy()
            self.mostrar_batalla()


# ═══════════════════════════════════════════════════
# EJECUCIÓN
# ═══════════════════════════════════════════════════
if __name__ == "__main__":
    root = tk.Tk()
    app = EpicAdventureApp(root)
    root.mainloop()
