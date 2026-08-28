"""
ui/config.py
Configuración centralizada: colores, rutas, constantes UI.
"""

import os

# ── Paleta de Colores ────────────────────────────────────────────────────────
COLOR_PRIMARIO   = "#4B0002"   # guinda facultad
COLOR_HOVER      = "#6B0003"
COLOR_ALERTA     = "#B22222"
COLOR_EXITO      = "#2E7D32"
COLOR_FONDO      = "#F5F5F5"

# ── Rutas ────────────────────────────────────────────────────────────────────
SRC_DIR          = os.path.dirname(os.path.dirname(__file__))
PROJECT_DIR      = os.path.dirname(SRC_DIR)
LOGO_PATH        = os.path.join(PROJECT_DIR, "assets", "logofdcp.png")
OUTPUT_DIR       = os.path.join(PROJECT_DIR, "output")
OUTPUT_REGISTROS = os.path.join(OUTPUT_DIR, "registros")
OUTPUT_IMAGENES  = os.path.join(OUTPUT_DIR, "imagenes")
OUTPUT_LOGS      = os.path.join(OUTPUT_DIR, "logs")

# ── Dimensiones de la ventana ────────────────────────────────────────────────
WINDOW_WIDTH     = 800
WINDOW_HEIGHT    = 620

# ── Tipos de archivo ────────────────────────────────────────────────────────
EXCEL_FILETYPES  = [("Excel", "*.xlsx *.xls"), ("Todos", "*.*")]
IMAGE_FILETYPES  = [("Imágenes", "*.jpg *.jpeg *.png *.webp"), ("Todos", "*.*")]
