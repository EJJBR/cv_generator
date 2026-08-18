import os
import re
import sys
from datetime import datetime
from pathlib import Path

import openpyxl
import requests


EXCEL_PATH = Path(r"C:\Users\LENOVO\Downloads\Hoja de Vida Docente (respuestas) (2)_limpio.xlsx")
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "output"
IMAGES_DIR = OUTPUT_DIR / "imagenes"
LOGS_DIR = OUTPUT_DIR / "logs"
LOG_FILE = LOGS_DIR / "descarga_fotos.log"


def limpiar_texto(valor):
    if valor is None:
        return ""
    return str(valor).strip()


def pertenece_drive(url: str) -> bool:
    if not url:
        return False
    texto = url.lower()
    return "drive.google.com" in texto or "docs.google.com" in texto or "googleusercontent" in texto


def extraer_file_id(url: str) -> str | None:
    if not url:
        return None
    match = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
    if match:
        return match.group(1)
    match = re.search(r"[?&]id=([a-zA-Z0-9_-]+)", url)
    return match.group(1) if match else None


def escribir_log(mensaje: str):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as archivo:
        archivo.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {mensaje}\n")


def descargar_drive(file_id: str, destino: Path, timeout: int = 60) -> None:
    api_url = "https://docs.google.com/uc?export=download"
    session = requests.Session()
    respuesta = session.get(api_url, params={"id": file_id}, stream=True, timeout=timeout)

    token = None
    for key, value in respuesta.cookies.items():
        if key.startswith("download_warning"):
            token = value

    if token:
        respuesta = session.get(
            api_url,
            params={"id": file_id, "confirm": token},
            stream=True,
            timeout=timeout,
        )

    if respuesta.status_code != 200:
        raise RuntimeError(f"Google Drive respondió HTTP {respuesta.status_code}")

    if "image" not in respuesta.headers.get("Content-Type", "").lower():
        raise RuntimeError(
            f"La URL no devolvió una imagen válida: {respuesta.headers.get('Content-Type')}"
        )

    with open(destino, "wb") as archivo:
        for chunk in respuesta.iter_content(32768):
            if chunk:
                archivo.write(chunk)


def buscar_celda_foto(row, columnas):
    for nombre in columnas:
        if nombre.strip().lower() == "foto de perfil (sólo jpg)":
            return row[3] if len(row) > 3 else None
        if nombre.strip().lower() == "foto":
            return row[2] if len(row) > 2 else None
    return None


def main():
    if not EXCEL_PATH.exists():
        print(f"❌ No existe el Excel: {EXCEL_PATH}")
        escribir_log(f"No existe el Excel: {EXCEL_PATH}")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))

    if not rows:
        print("❌ El archivo Excel está vacío.")
        escribir_log("El archivo Excel está vacío.")
        return

    encabezados = [limpiar_texto(h) for h in rows[0]]
    idx_id = None
    idx_foto = None

    for i, nombre in enumerate(encabezados):
        clave = nombre.lower()
        if clave == "id":
            idx_id = i
        if "foto" in clave and ("perfil" in clave or "drive" in clave or "jpg" in clave):
            idx_foto = i

    if idx_id is None or idx_foto is None:
        print("❌ No se encontraron columnas 'ID' o 'Foto de Perfil'.")
        escribir_log("No se encontraron columnas 'ID' o 'Foto de Perfil'.")
        return

    total = 0
    descargadas = 0
    faltantes = 0
    errores = 0

    for fila_idx, fila in enumerate(rows[1:], start=2):
        if not fila or not any((valor is not None and str(valor).strip() != "") for valor in fila):
            continue

        id_val = fila[idx_id] if idx_id < len(fila) else None
        if id_val is None or str(id_val).strip() == "":
            continue

        total += 1
        foto_val = fila[idx_foto] if idx_foto < len(fila) else None
        url = limpiar_texto(foto_val)

        if not url or not pertenece_drive(url):
            faltantes += 1
            mensaje = f"ID {id_val}: falta link de Drive en la columna de foto."
            print(f"⚠️ {mensaje}")
            escribir_log(mensaje)
            continue

        try:
            file_id = extraer_file_id(url)
            if not file_id:
                raise ValueError("No se pudo extraer file_id del link de Drive")

            nombre_archivo = f"{id_val}_{file_id}.jpg"
            destino = IMAGES_DIR / nombre_archivo
            descargar_drive(file_id, destino)
            descargadas += 1
            print(f"✅ ID {id_val}: descargada -> {destino.name}")
            escribir_log(f"ID {id_val}: descargada correctamente -> {destino.name}")

        except Exception as exc:
            errores += 1
            mensaje = f"ID {id_val}: error al descargar la foto -> {exc}"
            print(f"❌ {mensaje}")
            escribir_log(mensaje)

    print("\n==== RESUMEN ====")
    print(f"Registros con ID: {total}")
    print(f"Descargadas: {descargadas}")
    print(f"Faltantes de link: {faltantes}")
    print(f"Errores de descarga: {errores}")
    print(f"Log: {LOG_FILE}")

    escribir_log(
        f"RESUMEN: total={total}, descargadas={descargadas}, faltantes={faltantes}, errores={errores}"
    )


if __name__ == "__main__":
    main()
