"""
controllers/masivo_controller.py
Lógica para procesamiento masivo de CVs.
"""

import os
import threading
from data_reader import leer_excel
from pdf_generator import generar_cv
from ui.config import OUTPUT_DIR, LOGO_PATH
from ui.utils import nombre_archivo_pdf


class MasivoController:
    """Controlador para generación masiva de CVs."""
    
    def __init__(self, callback_log, callback_agregar_pendiente, callback_completar):
        """
        callback_log: función para escribir en el log (texto)
        callback_agregar_pendiente: función para agregar docente sin foto (dict)
        callback_completar: función al terminar el proceso
        """
        self.callback_log = callback_log
        self.callback_agregar_pendiente = callback_agregar_pendiente
        self.callback_completar = callback_completar

    def procesar(self, ruta_excel: str, ruta_fotos: str):
        """Inicia procesamiento en thread separado."""
        threading.Thread(
            target=self._procesar_interno,
            args=(ruta_excel, ruta_fotos),
            daemon=True
        ).start()

    def _procesar_interno(self, ruta_excel: str, ruta_fotos: str):
        """Lógica interna de procesamiento."""
        try:
            completos, sin_foto = leer_excel(ruta_excel, ruta_fotos)
        except Exception as e:
            self.callback_log(f"❌ Error leyendo Excel: {e}")
            self.callback_completar()
            return

        total = len(completos) + len(sin_foto)
        self.callback_log(
            f"📊 {total} registros encontrados — {len(completos)} con foto, "
            f"{len(sin_foto)} sin foto\n"
        )

        os.makedirs(OUTPUT_DIR, exist_ok=True)

        # Generar CVs de los que sí tienen foto
        for datos in completos:
            nombre = datos.get("nombre", "sin_nombre")
            try:
                ruta_pdf = os.path.join(OUTPUT_DIR, nombre_archivo_pdf(nombre))
                generar_cv(datos, ruta_pdf, logo_path=LOGO_PATH)
                self.callback_log(f"✅ {nombre}")
            except Exception as e:
                self.callback_log(f"❌ {nombre} → {e}")

        # Agregar pendientes
        if sin_foto:
            self.callback_log(
                f"\n⚠️  {len(sin_foto)} docente(s) sin foto — selecciona manualmente:"
            )
            for datos in sin_foto:
                self.callback_agregar_pendiente(datos)

        self.callback_log("\n✔ Proceso completado.")
        self.callback_completar()

    def generar_cv_manual(self, datos: dict) -> tuple[bool, str]:
        """
        Genera CV para docente sin foto (seleccionada manualmente).
        Retorna: (éxito: bool, mensaje: str)
        """
        nombre = datos.get("nombre", "sin_nombre")
        try:
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            ruta_pdf = os.path.join(OUTPUT_DIR, nombre_archivo_pdf(nombre))
            generar_cv(datos, ruta_pdf, logo_path=LOGO_PATH)
            return True, f"✅ {nombre} → generado manualmente"
        except Exception as e:
            return False, f"❌ {nombre} → {e}"
