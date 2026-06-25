"""
ui/tab_masivo.py
UI y lógica del tab de carga masiva.
"""

import os
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from ui.config import (
    COLOR_PRIMARIO, COLOR_HOVER, COLOR_ALERTA, COLOR_EXITO, 
    EXCEL_FILETYPES, IMAGE_FILETYPES, OUTPUT_DIR
)
from controllers.masivo_controller import MasivoController
from ui.utils import nombre_archivo_pdf


class TabMasivo:
    """Gestiona la UI y lógica del tab de carga masiva."""
    
    def __init__(self, tab_widget):
        """tab_widget: CTkTabview frame."""
        self.tab = tab_widget
        self.tab.columnconfigure(1, weight=1)
        
        # Estado
        self._ruta_excel = tk.StringVar(value="")
        self._ruta_fotos = tk.StringVar(value="")
        self._filas_pendientes = []
        self.btn_generar = None
        self.log = None
        self.frame_pendientes = None
        self.controller = None
        
        self._build()
    
    def _build(self):
        """Construye la UI del tab."""
        # Selección de Excel
        ctk.CTkLabel(self.tab, text="Archivo Excel:",
                     font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, sticky="w", padx=(10, 5), pady=(15, 5))
        ctk.CTkEntry(self.tab, textvariable=self._ruta_excel,
                     state="readonly", width=480).grid(
            row=0, column=1, sticky="ew", padx=(0, 5), pady=(15, 5))
        ctk.CTkButton(self.tab, text="📂 Buscar", width=90,
                      fg_color=COLOR_PRIMARIO, hover_color=COLOR_HOVER,
                      command=self._buscar_excel).grid(
            row=0, column=2, padx=(0, 10), pady=(15, 5))

        # Selección de fotos
        ctk.CTkLabel(self.tab, text="Carpeta de fotos:",
                     font=ctk.CTkFont(weight="bold")).grid(
            row=1, column=0, sticky="w", padx=(10, 5), pady=(0, 5))
        ctk.CTkEntry(self.tab, textvariable=self._ruta_fotos,
                     state="readonly", width=480).grid(
            row=1, column=1, sticky="ew", padx=(0, 5), pady=(0, 5))
        ctk.CTkButton(self.tab, text="📂 Buscar", width=90,
                      fg_color=COLOR_PRIMARIO, hover_color=COLOR_HOVER,
                      command=self._buscar_fotos).grid(
            row=1, column=2, padx=(0, 10), pady=(0, 5))

        # Botón generar
        self.btn_generar = ctk.CTkButton(
            self.tab, text="⚡  Generar todos los CVs",
            fg_color=COLOR_PRIMARIO, hover_color=COLOR_HOVER,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._iniciar_generacion)
        self.btn_generar.grid(row=2, column=0, columnspan=3,
                              pady=(10, 5), padx=10, sticky="ew")

        # Log
        ctk.CTkLabel(self.tab, text="Progreso:",
                     font=ctk.CTkFont(weight="bold")).grid(
            row=3, column=0, columnspan=3, sticky="w", padx=10, pady=(10, 2))

        self.log = ctk.CTkTextbox(self.tab, height=130, state="disabled",
                                   fg_color="#F8F8F8",
                                   font=ctk.CTkFont(family="Courier", size=11))
        self.log.grid(row=4, column=0, columnspan=3, padx=10, sticky="ew")

        # Sección pendientes
        ctk.CTkLabel(self.tab, text="⚠️  Docentes sin foto — selecciona manualmente:",
                     font=ctk.CTkFont(weight="bold"),
                     text_color=COLOR_ALERTA).grid(
            row=5, column=0, columnspan=3, sticky="w", padx=10, pady=(12, 2))

        self.frame_pendientes = ctk.CTkScrollableFrame(
            self.tab, height=130, fg_color="#FFF8F8")
        self.frame_pendientes.grid(row=6, column=0, columnspan=3,
                                   padx=10, pady=(0, 10), sticky="ew")
        self.frame_pendientes.columnconfigure(1, weight=1)

    def _buscar_excel(self):
        """Abre diálogo para seleccionar Excel."""
        ruta = filedialog.askopenfilename(
            title="Seleccionar Excel del Forms",
            filetypes=EXCEL_FILETYPES)
        if ruta:
            self._ruta_excel.set(ruta)

    def _buscar_fotos(self):
        """Abre diálogo para seleccionar carpeta de fotos."""
        ruta = filedialog.askdirectory(title="Seleccionar carpeta de fotos")
        if ruta:
            self._ruta_fotos.set(ruta)

    def _log_append(self, texto: str):
        """Agrega texto al log."""
        self.log.configure(state="normal")
        self.log.insert("end", texto + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _iniciar_generacion(self):
        """Inicia la generación masiva."""
        excel = self._ruta_excel.get()
        fotos = self._ruta_fotos.get()

        if not excel:
            self._log_append("❌ Selecciona el archivo Excel primero.")
            return
        if not fotos:
            self._log_append("❌ Selecciona la carpeta de fotos primero.")
            return

        self.btn_generar.configure(state="disabled", text="Procesando...")
        for w in self.frame_pendientes.winfo_children():
            w.destroy()
        self._filas_pendientes.clear()

        self.controller = MasivoController(
            callback_log=lambda t: self.tab.after(0, lambda: self._log_append(t)),
            callback_agregar_pendiente=lambda d: self.tab.after(0, lambda: self._agregar_pendiente(d)),
            callback_completar=lambda: self.tab.after(0, lambda: self.btn_generar.configure(
                state="normal", text="⚡  Generar todos los CVs"))
        )
        self.controller.procesar(excel, fotos)

    def _agregar_pendiente(self, datos: dict):
        """Agrega un docente sin foto al panel de pendientes."""
        nombre = datos.get("nombre", "Sin nombre")
        fila = len(self._filas_pendientes)

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
        """Permite seleccionar foto manualmente y genera el CV."""
        ruta_foto = filedialog.askopenfilename(
            title=f"Foto de {datos.get('nombre', '')}",
            filetypes=IMAGE_FILETYPES)

        if not ruta_foto:
            return

        datos["foto_path"] = ruta_foto
        nombre = datos.get("nombre", "sin_nombre")

        exito, msg = self.controller.generar_cv_manual(datos)
        
        if exito:
            lbl_ref, btn_ref, _ = self._filas_pendientes[fila_idx]
            lbl_ref.configure(text=f"✅  {nombre}", text_color=COLOR_EXITO)
            btn_ref.configure(state="disabled", text="Generado",
                              fg_color="gray", hover_color="gray")

        self._log_append(msg)
