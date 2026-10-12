"""
core/utils.py
Utilidades puras de texto, sanitización y manejo de rutas sin dependencias de interfaz gráfica.
"""

from html import escape


def sanitizar_para_reportlab(texto: str) -> str:
    """
    Escapa caracteres especiales (&, <, >, quotes) para que ReportLab no interprete el texto como XML.
    Previene el error 'parse ended with unclosed tags'.
    """
    if not texto:
        return ""
    return escape(str(texto), quote=True)


def sanitizar_nombre_archivo(nombre: str) -> str:
    """Genera un nombre de archivo seguro removiendo caracteres inválidos."""
    if not nombre:
        return "documento"
    limpio = "".join(c for c in nombre if c.isalnum() or c in " _-").strip()
    return limpio.replace(" ", "_")
