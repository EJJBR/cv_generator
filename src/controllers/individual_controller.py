"""
controllers/individual_controller.py
Lógica para generación individual de CVs.
"""

import os
from pdf_generator import generar_cv
from ui.config import OUTPUT_DIR, LOGO_PATH
from ui.utils import nombre_archivo_pdf


class IndividualController:
    """Controlador para generación individual de CVs."""

    @staticmethod
    def generar(datos: dict) -> tuple[bool, str]:
        """
        Genera un CV individual.
        
        Retorna: (éxito: bool, ruta_pdf: str o mensaje_error: str)
        """
        nombre = datos.get("nombre", "").strip()
        if not nombre:
            return False, "El nombre es obligatorio."

        try:
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            ruta_pdf = os.path.join(OUTPUT_DIR, nombre_archivo_pdf(nombre))
            generar_cv(datos, ruta_pdf, logo_path=LOGO_PATH)
            return True, ruta_pdf
        except Exception as e:
            return False, str(e)
