"""
controllers/masivo_controller.py
Lógica para procesamiento masivo de CVs.
"""

import os
import re
import threading
from datetime import datetime
from pathlib import Path

import openpyxl
import requests

from data_reader import leer_excel
from pdf_generator import generar_cv
from ui.config import OUTPUT_DIR, OUTPUT_IMAGENES, OUTPUT_LOGS, OUTPUT_REGISTROS, LOGO_PATH
from ui.utils import nombre_archivo_pdf


def _slug_nombre(nombre: str) -> str:
    if not nombre:
        return "sin_nombre"
    nombre = str(nombre)
    nombre = re.sub(r"[^a-zA-Z0-9]+", "_", nombre).strip("_")
    return nombre or "sin_nombre"


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

    def transformar_excel(self, ruta_excel: str) -> tuple[bool, str, str]:
        """Limpia el Excel, elimina filas vacías y agrega la columna ID."""
        try:
            ruta_excel = str(ruta_excel)
            if not os.path.exists(ruta_excel):
                return False, "❌ No existe el archivo Excel seleccionado.", ""

            os.makedirs(OUTPUT_REGISTROS, exist_ok=True)
            wb = openpyxl.load_workbook(ruta_excel, data_only=True)
            ws = wb.active
            filas = list(ws.iter_rows(values_only=True))
            if not filas:
                return False, "❌ El Excel está vacío.", ""

            encabezados = [str(h).strip() if h is not None else "" for h in filas[0]]
            registros = []
            for fila in filas[1:]:
                if not fila or not any((valor is not None and str(valor).strip() != "") for valor in fila):
                    continue
                registros.append(list(fila))

            if not registros:
                return False, "❌ No se encontraron registros útiles después de limpiar filas vacías.", ""

            nombre_base = os.path.splitext(os.path.basename(ruta_excel))[0]
            output_path = os.path.join(OUTPUT_REGISTROS, f"{nombre_base}_limpio.xlsx")

            nueva_wb = openpyxl.Workbook()
            nueva_ws = nueva_wb.active
            nueva_ws.append(["ID"] + encabezados)

            for idx, fila in enumerate(registros, start=1):
                if len(fila) < len(encabezados):
                    fila = list(fila) + [None] * (len(encabezados) - len(fila))
                nueva_ws.append([idx] + fila)

            nueva_wb.save(output_path)
            return True, f"✅ Excel transformado en {output_path}", output_path
        except Exception as exc:
            return False, f"❌ Error al transformar Excel: {exc}", ""

    def descargar_fotos_excel(self, ruta_excel: str) -> tuple[bool, str]:
        """Descarga las imágenes desde la columna de foto según el ID del registro."""
        try:
            os.makedirs(OUTPUT_IMAGENES, exist_ok=True)
            os.makedirs(OUTPUT_LOGS, exist_ok=True)

            wb = openpyxl.load_workbook(ruta_excel, data_only=True)
            ws = wb.active
            filas = list(ws.iter_rows(values_only=True))
            if not filas:
                return False, "❌ El Excel transformado está vacío."

            encabezados = [str(h).strip().lower() if h is not None else "" for h in filas[0]]
            idx_id = encabezados.index("id") if "id" in encabezados else None
            idx_foto = None
            for i, nombre in enumerate(encabezados):
                if "foto" in nombre and ("perfil" in nombre or "drive" in nombre or "jpg" in nombre):
                    idx_foto = i
                    break

            if idx_id is None or idx_foto is None:
                return False, "❌ No se encontraron las columnas ID o Foto de Perfil en el Excel transformado."

            total = 0
            descargadas = 0
            faltantes = 0
            errores = 0
            log_path = os.path.join(OUTPUT_LOGS, "descarga_fotos.log")

            for fila in filas[1:]:
                if not fila or not any((valor is not None and str(valor).strip() != "") for valor in fila):
                    continue

                id_val = fila[idx_id] if idx_id < len(fila) else None
                if id_val is None or str(id_val).strip() == "":
                    continue

                total += 1
                foto_val = fila[idx_foto] if idx_foto < len(fila) else None
                url = str(foto_val).strip() if foto_val is not None else ""

                if not url or not ("drive.google.com" in url.lower() or "docs.google.com" in url.lower() or "googleusercontent" in url.lower()):
                    faltantes += 1
                    mensaje = f"ID {id_val}: falta link de Drive en la columna de foto."
                    with open(log_path, "a", encoding="utf-8") as archivo:
                        archivo.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {mensaje}\n")
                    print(f"⚠️ {mensaje}")
                    continue

                try:
                    match = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
                    if not match:
                        match = re.search(r"[?&]id=([a-zA-Z0-9_-]+)", url)
                    if not match:
                        raise ValueError("No se pudo extraer el file_id del link de Drive.")
                    file_id = match.group(1)

                    nombre_persona = ""
                    if len(fila) > 1:
                        nombre_persona = str(fila[1]).strip() if fila[1] is not None else ""
                    nombre_slug = _slug_nombre(nombre_persona)
                    destino = os.path.join(OUTPUT_IMAGENES, f"{id_val}_{nombre_slug}.jpg")

                    api_url = "https://docs.google.com/uc?export=download"
                    session = requests.Session()
                    response = session.get(api_url, params={"id": file_id}, stream=True, timeout=60)

                    token = None
                    for key, value in response.cookies.items():
                        if key.startswith("download_warning"):
                            token = value

                    if token:
                        response = session.get(api_url, params={"id": file_id, "confirm": token}, stream=True, timeout=60)

                    if response.status_code != 200:
                        raise RuntimeError(f"Google Drive respondió HTTP {response.status_code}")
                    if "image" not in response.headers.get("Content-Type", "").lower():
                        raise RuntimeError(f"La URL no devolvió una imagen válida: {response.headers.get('Content-Type')}")

                    with open(destino, "wb") as archivo:
                        for chunk in response.iter_content(32768):
                            if chunk:
                                archivo.write(chunk)

                    descargadas += 1
                    print(f"✅ ID {id_val}: descargada -> {os.path.basename(destino)}")
                    with open(log_path, "a", encoding="utf-8") as archivo:
                        archivo.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ID {id_val}: descargada -> {os.path.basename(destino)}\n")
                except Exception as exc:
                    errores += 1
                    mensaje = f"ID {id_val}: error al descargar la foto -> {exc}"
                    print(f"❌ {mensaje}")
                    with open(log_path, "a", encoding="utf-8") as archivo:
                        archivo.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {mensaje}\n")

            resumen = (
                f"\n==== RESUMEN ====\n"
                f"Registros con ID: {total}\n"
                f"Descargadas: {descargadas}\n"
                f"Faltantes de link: {faltantes}\n"
                f"Errores de descarga: {errores}\n"
                f"Log: {log_path}\n"
            )
            print(resumen)
            with open(log_path, "a", encoding="utf-8") as archivo:
                archivo.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {resumen}")
            return True, resumen
        except Exception as exc:
            return False, f"❌ Error intentando descargar imágenes: {exc}"

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
