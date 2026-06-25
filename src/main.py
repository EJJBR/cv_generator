"""
main.py
Punto de entrada: Inicializa y lanza la aplicación GUI.
"""

import os
import sys
import customtkinter as ctk

# Agregar src/ al path para importaciones relativas
sys.path.insert(0, os.path.dirname(__file__))

from ui.config import (
    COLOR_PRIMARIO, COLOR_HOVER, COLOR_FONDO, 
    WINDOW_WIDTH, WINDOW_HEIGHT, OUTPUT_DIR
)
from ui.utils import obtener_posicion_ventana_centrada
from ui.tab_masivo import TabMasivo
from ui.tab_individual import TabIndividual


# ── Configuración de tema ────────────────────────────────────────────────────
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


# ── Ventana principal ────────────────────────────────────────────────────────
class App(ctk.CTk):
    """Aplicación principal del Generador de CVs."""
    
    def __init__(self):
        super().__init__()
        self.title("Generador de CVs Docentes — FDCP UNMSM")
        
        # Obtener posición centrada según el SO
        x, y, _, _ = obtener_posicion_ventana_centrada()
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_FONDO)
        
        self._build_ui()
    
    def _build_ui(self):
        """Construye la interfaz de usuario."""
        # Header
        header = ctk.CTkFrame(self, fg_color=COLOR_PRIMARIO,
                              corner_radius=0, height=65)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(header,
                     text="  Generador de CVs Docentes — FDCP UNMSM",
                     font=ctk.CTkFont(size=17, weight="bold"),
                     text_color="white").pack(side="left", padx=20, pady=18)
        
        # Tabs
        tabs = ctk.CTkTabview(
            self, fg_color="white",
            segmented_button_fg_color=COLOR_PRIMARIO,
            segmented_button_selected_color=COLOR_HOVER,
            segmented_button_unselected_color="#6B0003",
            segmented_button_selected_hover_color=COLOR_HOVER,
            text_color_disabled="white"
        )
        tabs.pack(fill="both", expand=True, padx=20, pady=15)
        tabs.add("📋  Carga Masiva")
        tabs.add("✏️  Individual Manual")
        
        # Inicializar tabs
        TabMasivo(tabs.tab("📋  Carga Masiva"))
        TabIndividual(tabs.tab("✏️  Individual Manual"))


# ── Entry point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    app = App()
    app.mainloop()