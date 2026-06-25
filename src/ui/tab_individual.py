"""
ui/tab_individual.py
UI y lógica del tab de generación individual.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from ui.config import COLOR_PRIMARIO, COLOR_HOVER, IMAGE_FILETYPES
from controllers.individual_controller import IndividualController


class TabIndividual:
    """Gestiona la UI y lógica del tab de generación individual."""
    
    def __init__(self, tab_widget):
        """tab_widget: CTkTabview frame."""
        self.tab = tab_widget
        self.tab.columnconfigure(1, weight=1)
        
        self._campos_ind = {}
        self._textos_ind = {}
        self._foto_ind = tk.StringVar(value="")
        
        self._build()
    
    def _build(self):
        """Construye la UI del tab."""
        # Campos cortos
        campos = [
            ("nombre",       "Apellidos y Nombres *"),
            ("correo",       "Correo Institucional"),
            ("escuela",      "Escuela Profesional"),
            ("departamento", "Departamento Académico"),
            ("categoria",    "Categoría / Clase"),
        ]
        
        for i, (key, label) in enumerate(campos):
            ctk.CTkLabel(self.tab, text=label,
                         font=ctk.CTkFont(weight="bold")).grid(
                row=i, column=0, sticky="w", padx=(10, 5), pady=(8, 0))
            entry = ctk.CTkEntry(self.tab, width=460)
            entry.grid(row=i, column=1, sticky="ew",
                       padx=(0, 10), pady=(8, 0))
            self._campos_ind[key] = entry

        # Campos de texto largo
        textos = [
            ("formacion",   "Formación Académica\n(uno por línea)"),
            ("trayectoria", "Trayectoria"),
            ("experiencia", "Experiencia Laboral\n(uno por línea)"),
        ]
        base = len(campos)
        for i, (key, label) in enumerate(textos):
            ctk.CTkLabel(self.tab, text=label,
                         font=ctk.CTkFont(weight="bold")).grid(
                row=base + i, column=0, sticky="nw",
                padx=(10, 5), pady=(8, 0))
            tb = ctk.CTkTextbox(self.tab, height=60, width=460)
            tb.grid(row=base + i, column=1, sticky="ew",
                    padx=(0, 10), pady=(8, 0))
            self._textos_ind[key] = tb

        # Foto
        fila_foto = base + len(textos)
        ctk.CTkLabel(self.tab, text="Foto carné",
                     font=ctk.CTkFont(weight="bold")).grid(
            row=fila_foto, column=0, sticky="w",
            padx=(10, 5), pady=(8, 0))

        ctk.CTkEntry(self.tab, textvariable=self._foto_ind,
                     state="readonly", width=340).grid(
            row=fila_foto, column=1, sticky="w",
            padx=(0, 5), pady=(8, 0))
        ctk.CTkButton(self.tab, text="📂", width=50,
                      fg_color=COLOR_PRIMARIO, hover_color=COLOR_HOVER,
                      command=self._buscar_foto_ind).grid(
            row=fila_foto, column=1, sticky="e",
            padx=(0, 10), pady=(8, 0))

        # Botón generar
        ctk.CTkButton(self.tab,
                      text="⚡  Generar CV",
                      fg_color=COLOR_PRIMARIO, hover_color=COLOR_HOVER,
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=self._generar_individual).grid(
            row=fila_foto + 1, column=0, columnspan=2,
            pady=15, padx=10, sticky="ew")

    def _buscar_foto_ind(self):
        """Abre diálogo para seleccionar foto."""
        ruta = filedialog.askopenfilename(
            title="Seleccionar foto carné",
            filetypes=IMAGE_FILETYPES)
        if ruta:
            self._foto_ind.set(ruta)

    def _generar_individual(self):
        """Genera CV individual."""
        datos = {
            "nombre":       self._campos_ind["nombre"].get().strip(),
            "correo":       self._campos_ind["correo"].get().strip(),
            "escuela":      self._campos_ind["escuela"].get().strip(),
            "departamento": self._campos_ind["departamento"].get().strip(),
            "categoria":    self._campos_ind["categoria"].get().strip(),
            "formacion":    self._textos_ind["formacion"].get("1.0", "end").strip(),
            "trayectoria":  self._textos_ind["trayectoria"].get("1.0", "end").strip(),
            "experiencia":  self._textos_ind["experiencia"].get("1.0", "end").strip(),
            "foto_path":    self._foto_ind.get() or None,
        }

        exito, resultado = IndividualController.generar(datos)
        
        if exito:
            messagebox.showinfo("✅ Listo", f"CV generado:\n{resultado}")
        else:
            messagebox.showerror("Error", resultado)
