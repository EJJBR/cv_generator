"""
ui/utils.py
Utilidades para UI: centrado de ventana, nombres de archivo, sanitización, etc.
"""

import sys
import subprocess
import re
from html import escape
from ui.config import WINDOW_WIDTH, WINDOW_HEIGHT


def obtener_posicion_ventana_centrada():
    """
    Detecta el SO y retorna (x, y) para centrar la ventana en el monitor principal.
    Soporta: Windows (multi-monitor), Linux (Xrandr), fallback genérico.
    """
    ancho_pantalla = 0
    alto_pantalla = 0
    offset_x = 0
    offset_y = 0

    if sys.platform.startswith("win"):
        # 🪟 LÓGICA PARA WINDOWS
        try:
            import ctypes
            ancho_pantalla = ctypes.windll.user32.GetSystemMetrics(0)
            alto_pantalla = ctypes.windll.user32.GetSystemMetrics(1)
        except Exception:
            pass

    elif sys.platform.startswith("linux"):
        # 🐧 LÓGICA PARA LINUX (xrandr)
        try:
            output = subprocess.check_output("xrandr", shell=True, text=True, stderr=subprocess.DEVNULL)
            for linea in output.splitlines():
                if " primary " in linea:
                    match = re.search(r"(\d+)x(\d+)\+(\d+)\+(\d+)", linea)
                    if match:
                        ancho_pantalla = int(match.group(1))
                        alto_pantalla = int(match.group(2))
                        offset_x = int(match.group(3))
                        offset_y = int(match.group(4))
                        break
        except Exception:
            pass

    # Fallback si no se detectó
    if not ancho_pantalla:
        ancho_pantalla = 1920
        alto_pantalla = 1080

    # Calcular centro
    x = offset_x + (ancho_pantalla // 2) - (WINDOW_WIDTH // 2)
    y = offset_y + (alto_pantalla // 2) - (WINDOW_HEIGHT // 2)

    return x, y, ancho_pantalla, alto_pantalla


def nombre_archivo_pdf(nombre: str) -> str:
    """Genera nombre de archivo PDF seguro a partir del nombre del docente."""
    limpio = "".join(c for c in nombre if c.isalnum() or c in " _-").strip()
    return f"CV_{limpio.replace(' ', '_')}.pdf"


def sanitizar_para_reportlab(texto: str) -> str:
    """
    Escapa caracteres especiales para que ReportLab no intente parsearlo como XML.
    Esto evita el error: "parse ended with 1 unclosed tags"
    """
    if not texto:
        return ""
    return escape(texto, quote=True)
