"""
main.py
Interfaz gráfica principal del Generador de CVs Docentes — FDCP UNMSM
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import customtkinter as ctk

sys.path.insert(0, os.path.dirname(__file__))
from data_reader import leer_excel
from pdf_generator import generar_cv

# ── Tema ─────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

COLOR_PRIMARIO  = "#4B0002"   # guinda facultad
COLOR_HOVER     = "#6B0003"
COLOR_ALERTA    = "#B22222"
COLOR_EXITO     = "#2E7D32"
COLOR_FONDO     = "#F5F5F5"
LOGO_PATH       = os.path.join(os.path.dirname(__file__), "..", "assets", "logofdcp.png")
OUTPUT_DIR      = os.path.join(os.path.dirname(__file__), "..", "output")


def nombre_archivo_pdf(nombre: str) -> str:
    limpio = "".join(c for c in nombre if c.isalnum() or c in " _-").strip()
    return f"CV_{limpio.replace(' ', '_')}.pdf"


# ── Ventana principal ─────────────────────────────────────────────────────────
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Generador de CVs Docentes — FDCP UNMSM")
        
        # ── Ajuste Multiplataforma para centrar la ventana (Compatible con Multi-monitor) ──
        ancho_ventana = 800
        alto_ventana = 620

        # Valores por defecto base de Tkinter
        ancho_pantalla = self.winfo_screenwidth()
        alto_pantalla = self.winfo_screenheight()
        offset_x = 0
        offset_y = 0

        # DETECCIÓN DEL SISTEMA OPERATIVO
        if sys.platform.startswith("win"):
            # 🪟 LÓGICA PARA WINDOWS 11 (Tu jefe)
            try:
                import ctypes
                # GetSystemMetrics 0 y 1 devuelven el ancho/alto del monitor PRINCIPAL en Windows,
                # aislando por completo las pantallas adicionales de cámaras de seguridad.
                ancho_pantalla = ctypes.windll.user32.GetSystemMetrics(0)
                alto_pantalla = ctypes.windll.user32.GetSystemMetrics(1)
            except Exception:
                pass  # Fallback a los valores base de Tkinter si falla la API de Windows

        elif sys.platform.startswith("linux"):
            # 🐧 LÓGICA PARA LINUX (Tu entorno de desarrollo)
            import subprocess
            import re
            try:
                output = subprocess.check_output("xrandr", shell=True, text=True, stderr=subprocess.DEVNULL)
                for linea in output.splitlines():
                    if " primary " in linea:
                        match = re.search(r"(\d+)x(\d+)\+(\d+)\+(\d+)", linea)
                        if match:
                            ancho_pantalla = int(match.group(1))
                            alto_pantalla = int(match.group(2))
                            offset_x       = int(match.group(3))
                            offset_y       = int(match.group(4))
                            break
            except Exception:
                # Plan B en Linux si xrandr falla por alguna razón
                if ancho_pantalla > 2000:
                    try:
                        pointer_x = self.winfo_pointerx()
                        bloque = pointer_x // 1920
                        offset_x = bloque * 1920
                        ancho_pantalla = 1920
                        alto_pantalla = 1080
                    except Exception:
                        ancho_pantalla = ancho_pantalla // 2

        # Calcular el centro matemático exacto según el sistema operativo detectado
        x = offset_x + (ancho_pantalla // 2) - (ancho_ventana // 2)
        y = offset_y + (alto_pantalla // 2) - (alto_ventana // 2)

        self.geometry(f"{ancho_ventana}x{alto_ventana}+{x}+{y}")
        # ───────────────────────────────────────────────────────────────────────────────────
        
        self.resizable(False, False)
        self.configure(fg_color=COLOR_FONDO)

        self._ruta_excel   = tk.StringVar(value="")
        self._ruta_fotos   = tk.StringVar(value="")
        self._pendientes   = []   
        self._filas_pendientes = []  

        self._build_header()
        self._build_tabs()

    # ── Header ────────────────────────────────────────────────────────────────
    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=COLOR_PRIMARIO,
                               corner_radius=0, height=65)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header,
                     text="  Generador de CVs Docentes — FDCP UNMSM",
                     font=ctk.CTkFont(size=17, weight="bold"),
                     text_color="white").pack(side="left", padx=20, pady=18)

    # ── Tabs ──────────────────────────────────────────────────────────────────
    def _build_tabs(self):
        self.tabs = ctk.CTkTabview(
            self, fg_color="white",
            segmented_button_fg_color=COLOR_PRIMARIO,
            segmented_button_selected_color=COLOR_HOVER,
            segmented_button_unselected_color="#6B0003",
            segmented_button_selected_hover_color=COLOR_HOVER,
            text_color_disabled="white"
        )
        self.tabs.pack(fill="both", expand=True, padx=20, pady=15)
        self.tabs.add("📋  Carga Masiva")
        self.tabs.add("✏️  Individual Manual")

        self._build_tab_masivo()
        self._build_tab_individual()

    # ══════════════════════════════════════════════════════════════════════════
    # TAB CARGA MASIVA
    # ══════════════════════════════════════════════════════════════════════════
    def _build_tab_masivo(self):
        tab = self.tabs.tab("📋  Carga Masiva")
        tab.columnconfigure(1, weight=1)

        # ── Selección de archivos ─────────────────────────────────────────────
        ctk.CTkLabel(tab, text="Archivo Excel:",
                     font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, sticky="w", padx=(10, 5), pady=(15, 5))
        ctk.CTkEntry(tab, textvariable=self._ruta_excel,
                     state="readonly", width=480).grid(
            row=0, column=1, sticky="ew", padx=(0, 5), pady=(15, 5))
        ctk.CTkButton(tab, text="📂 Buscar", width=90,
                      fg_color=COLOR_PRIMARIO, hover_color=COLOR_HOVER,
                      command=self._buscar_excel).grid(
            row=0, column=2, padx=(0, 10), pady=(15, 5))

        ctk.CTkLabel(tab, text="Carpeta de fotos:",
                     font=ctk.CTkFont(weight="bold")).grid(
            row=1, column=0, sticky="w", padx=(10, 5), pady=(0, 5))
        ctk.CTkEntry(tab, textvariable=self._ruta_fotos,
                     state="readonly", width=480).grid(
            row=1, column=1, sticky="ew", padx=(0, 5), pady=(0, 5))
        ctk.CTkButton(tab, text="📂 Buscar", width=90,
                      fg_color=COLOR_PRIMARIO, hover_color=COLOR_HOVER,
                      command=self._buscar_fotos).grid(
            row=1, column=2, padx=(0, 10), pady=(0, 5))

        # ── Botón generar ─────────────────────────────────────────────────────
        self.btn_generar = ctk.CTkButton(
            tab, text="⚡  Generar todos los CVs",
            fg_color=COLOR_PRIMARIO, hover_color=COLOR_HOVER,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._iniciar_generacion)
        self.btn_generar.grid(row=2, column=0, columnspan=3,
                              pady=(10, 5), padx=10, sticky="ew")

        # ── Log de progreso ───────────────────────────────────────────────────
        ctk.CTkLabel(tab, text="Progreso:",
                     font=ctk.CTkFont(weight="bold")).grid(
            row=3, column=0, columnspan=3, sticky="w", padx=10, pady=(10, 2))

        self.log = ctk.CTkTextbox(tab, height=130, state="disabled",
                                   fg_color="#F8F8F8",
                                   font=ctk.CTkFont(family="Courier", size=11))
        self.log.grid(row=4, column=0, columnspan=3,
                      padx=10, sticky="ew")

        # ── Sección pendientes ────────────────────────────────────────────────
        ctk.CTkLabel(tab, text="⚠️  Docentes sin foto — selecciona manualmente:",
                     font=ctk.CTkFont(weight="bold"),
                     text_color=COLOR_ALERTA).grid(
            row=5, column=0, columnspan=3, sticky="w", padx=10, pady=(12, 2))

        # Frame scrollable para los pendientes
        self.frame_pendientes = ctk.CTkScrollableFrame(
            tab, height=130, fg_color="#FFF8F8")
        self.frame_pendientes.grid(row=6, column=0, columnspan=3,
                                   padx=10, pady=(0, 10), sticky="ew")
        self.frame_pendientes.columnconfigure(1, weight=1)

    def _buscar_excel(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar Excel del Forms",
            filetypes=[("Excel", "*.xlsx *.xls"), ("Todos", "*.*")])
        if ruta:
            self._ruta_excel.set(ruta)

    def _buscar_fotos(self):
        ruta = filedialog.askdirectory(title="Seleccionar carpeta de fotos")
        if ruta:
            self._ruta_fotos.set(ruta)

    def _log_append(self, texto: str):
        self.log.configure(state="normal")
        self.log.insert("end", texto + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _iniciar_generacion(self):
        excel  = self._ruta_excel.get()
        fotos  = self._ruta_fotos.get()

        if not excel:
            self._log_append("❌ Selecciona el archivo Excel primero.")
            return
        if not fotos:
            self._log_append("❌ Selecciona la carpeta de fotos primero.")
            return

        self.btn_generar.configure(state="disabled", text="Procesando...")
        # limpiar pendientes anteriores
        for w in self.frame_pendientes.winfo_children():
            w.destroy()
        self._filas_pendientes.clear()

        threading.Thread(target=self._procesar_masivo,
                         args=(excel, fotos), daemon=True).start()

    def _procesar_masivo(self, excel, fotos):
        try:
            completos, sin_foto = leer_excel(excel, fotos)
        except Exception as e:
            self.after(0, lambda: self._log_append(f"❌ Error leyendo Excel: {e}"))
            self.after(0, lambda: self.btn_generar.configure(
                state="normal", text="⚡  Generar todos los CVs"))
            return

        total = len(completos) + len(sin_foto)
        self.after(0, lambda: self._log_append(
            f"📊 {total} registros encontrados — {len(completos)} con foto, "
            f"{len(sin_foto)} sin foto\n"))

        os.makedirs(OUTPUT_DIR, exist_ok=True)

        for datos in completos:
            nombre = datos.get("nombre", "sin_nombre")
            try:
                ruta_pdf = os.path.join(OUTPUT_DIR, nombre_archivo_pdf(nombre))
                generar_cv(datos, ruta_pdf, logo_path=LOGO_PATH)
                self.after(0, lambda n=nombre: self._log_append(f"✅ {n}"))
            except Exception as e:
                self.after(0, lambda n=nombre, err=e:
                           self._log_append(f"❌ {n} → {err}"))

        if sin_foto:
            self.after(0, lambda: self._log_append(
                f"\n⚠️  {len(sin_foto)} docente(s) sin foto — selecciona manualmente:"))
            for datos in sin_foto:
                self.after(0, lambda d=datos: self._agregar_pendiente(d))

        self.after(0, lambda: self._log_append("\n✔ Proceso completado."))
        self.after(0, lambda: self.btn_generar.configure(
            state="normal", text="⚡  Generar todos los CVs"))

    def _agregar_pendiente(self, datos: dict):
        """Agrega una fila en el panel de pendientes."""
        nombre = datos.get("nombre", "Sin nombre")
        fila   = len(self._filas_pendientes)

        lbl = ctk.CTkLabel(self.frame_pendientes,
                           text=f"⚠️  {nombre}",
                           text_color=COLOR_ALERTA,
                           font=ctk.CTkFont(size=11))
        lbl.grid(row=fila, column=0, sticky="w", padx=(5, 10), pady=4)

        btn = ctk.CTkButton(
            self.frame_pendientes,
            text="📂 Seleccionar foto",
            width=160,
            fg_color=COLOR_ALERTA,
            hover_color="#8B0000",
            font=ctk.CTkFont(size=11),
            command=lambda d=datos, l=lbl, f=fila: self._seleccionar_foto_manual(d, l, f))
        btn.grid(row=fila, column=1, sticky="e", padx=(0, 5), pady=4)

        self._filas_pendientes.append((lbl, btn, datos))

    def _seleccionar_foto_manual(self, datos: dict, lbl, fila_idx: int):
        """El personal selecciona la foto manualmente y se genera el CV."""
        ruta_foto = filedialog.askopenfilename(
            title=f"Foto de {datos.get('nombre', '')}",
            filetypes=[("Imágenes", "*.jpg *.jpeg *.png *.webp"), ("Todos", "*.*")])

        if not ruta_foto:
            return

        datos["foto_path"] = ruta_foto
        nombre = datos.get("nombre", "sin_nombre")

        try:
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            ruta_pdf = os.path.join(OUTPUT_DIR, nombre_archivo_pdf(nombre))
            generar_cv(datos, ruta_pdf, logo_path=LOGO_PATH)

            # marcar como resuelto en la UI
            lbl_ref, btn_ref, _ = self._filas_pendientes[fila_idx]
            lbl_ref.configure(text=f"✅  {nombre}", text_color=COLOR_EXITO)
            btn_ref.configure(state="disabled", text="Generado",
                              fg_color="gray", hover_color="gray")

            self._log_append(f"✅ {nombre} → generado manualmente")

        except Exception as e:
            self._log_append(f"❌ {nombre} → {e}")

    # ══════════════════════════════════════════════════════════════════════════
    # TAB INDIVIDUAL MANUAL
    # ══════════════════════════════════════════════════════════════════════════
    def _build_tab_individual(self):
        tab = self.tabs.tab("✏️  Individual Manual")
        tab.columnconfigure(1, weight=1)

        campos = [
            ("nombre",       "Apellidos y Nombres *"),
            ("correo",       "Correo Institucional"),
            ("escuela",      "Escuela Profesional"),
            ("departamento", "Departamento Académico"),
            ("categoria",    "Categoría / Clase"),
        ]
        self._campos_ind = {}

        for i, (key, label) in enumerate(campos):
            ctk.CTkLabel(tab, text=label,
                         font=ctk.CTkFont(weight="bold")).grid(
                row=i, column=0, sticky="w", padx=(10, 5), pady=(8, 0))
            entry = ctk.CTkEntry(tab, width=460)
            entry.grid(row=i, column=1, sticky="ew",
                       padx=(0, 10), pady=(8, 0))
            self._campos_ind[key] = entry

        # Campos de texto largo
        textos = [
            ("formacion",   "Formación Académica\n(uno por línea)"),
            ("trayectoria", "Trayectoria"),
            ("experiencia", "Experiencia Laboral\n(uno por línea)"),
        ]
        self._textos_ind = {}
        base = len(campos)
        for i, (key, label) in enumerate(textos):
            ctk.CTkLabel(tab, text=label,
                         font=ctk.CTkFont(weight="bold")).grid(
                row=base + i, column=0, sticky="nw",
                padx=(10, 5), pady=(8, 0))
            tb = ctk.CTkTextbox(tab, height=60, width=460)
            tb.grid(row=base + i, column=1, sticky="ew",
                    padx=(0, 10), pady=(8, 0))
            self._textos_ind[key] = tb

        # Foto
        fila_foto = base + len(textos)
        ctk.CTkLabel(tab, text="Foto carné",
                     font=ctk.CTkFont(weight="bold")).grid(
            row=fila_foto, column=0, sticky="w",
            padx=(10, 5), pady=(8, 0))

        self._foto_ind = tk.StringVar(value="")
        ctk.CTkEntry(tab, textvariable=self._foto_ind,
                     state="readonly", width=340).grid(
            row=fila_foto, column=1, sticky="w",
            padx=(0, 5), pady=(8, 0))
        ctk.CTkButton(tab, text="📂", width=50,
                      fg_color=COLOR_PRIMARIO, hover_color=COLOR_HOVER,
                      command=self._buscar_foto_ind).grid(
            row=fila_foto, column=1, sticky="e",
            padx=(0, 10), pady=(8, 0))

        # Botón generar
        ctk.CTkButton(tab,
                      text="⚡  Generar CV",
                      fg_color=COLOR_PRIMARIO, hover_color=COLOR_HOVER,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=self._generar_individual).grid(
            row=fila_foto + 1, column=0, columnspan=2,
            pady=15, padx=10, sticky="ew")

    def _buscar_foto_ind(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar foto carné",
            filetypes=[("Imágenes", "*.jpg *.jpeg *.png *.webp"),
                       ("Todos", "*.*")])
        if ruta:
            self._foto_ind.set(ruta)

    def _generar_individual(self):
        nombre = self._campos_ind["nombre"].get().strip()
        if not nombre:
            messagebox.showwarning("Campo requerido",
                                      "El nombre es obligatorio.")
            return

        datos = {
            "nombre":       nombre,
            "correo":       self._campos_ind["correo"].get().strip(),
            "escuela":      self._campos_ind["escuela"].get().strip(),
            "departamento": self._campos_ind["departamento"].get().strip(),
            "categoria":    self._campos_ind["categoria"].get().strip(),
            "formacion":    self._textos_ind["formacion"].get("1.0", "end").strip(),
            "trayectoria":  self._textos_ind["trayectoria"].get("1.0", "end").strip(),
            "experiencia":  self._textos_ind["experiencia"].get("1.0", "end").strip(),
            "foto_path":    self._foto_ind.get() or None,
        }

        try:
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            ruta_pdf = os.path.join(OUTPUT_DIR, nombre_archivo_pdf(nombre))
            generar_cv(datos, ruta_pdf, logo_path=LOGO_PATH)
            messagebox.showinfo("✅ Listo",
                                   f"CV generado:\n{ruta_pdf}")
        except Exception as e:
            messagebox.showerror("Error", str(e))


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    app = App()
    app.mainloop()