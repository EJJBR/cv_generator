"""
data_reader.py
Lee el Excel descargado de Google Forms y busca las fotos
en la carpeta descargada de Drive.
"""

import os
import openpyxl


# Nombres de columnas esperados (ajustar si el Excel tiene nombres diferentes)
COLUMNAS = {
    "nombre":      "Apellidos y Nombres",
    "correo":      "Correo Institucional",
    "escuela":     "Escuela Profesional",
    "departamento":"Departamento Academico",
    "categoria":   "Categoría / Clase",
    "formacion1":  "Formación Académica 1",
    "formacion2":  "Formación Académica 2",
    "formacion3":  "Formación Académica 3",
    "trayectoria": "Treyectora",
    "exp1":        "Experiencia Laboral 1",
    "exp2":        "Experiencia Laboral 2",
    "exp3":        "Experiencia Laboral 3",
}


def _buscar_foto(nombre_docente: str, carpeta_fotos: str) -> str | None:
    """
    Busca la foto del docente en la carpeta de fotos.
    El archivo tiene formato: 'Foto - Nombre Apellido.jpg'
    Retorna la ruta completa si la encuentra, None si no.
    """
    if not os.path.exists(carpeta_fotos):
        return None

    nombre_limpio = nombre_docente.strip().lower()

    for archivo in os.listdir(carpeta_fotos):
        nombre_archivo = archivo.lower()
        # busca el nombre del docente dentro del nombre del archivo
        if nombre_limpio in nombre_archivo:
            return os.path.join(carpeta_fotos, archivo)

    return None


def _mapear_columnas(encabezados: list) -> dict:
    """
    Mapea los nombres de columnas del Excel a los campos internos.
    Retorna dict {campo_interno: indice_columna}
    """
    mapa = {}
    encabezados_lower = [str(h).strip().lower() if h else "" for h in encabezados]

    for campo, nombre_columna in COLUMNAS.items():
        nombre_lower = nombre_columna.lower()
        if nombre_lower in encabezados_lower:
            mapa[campo] = encabezados_lower.index(nombre_lower)
        else:
            mapa[campo] = None  # columna no encontrada

    return mapa


def leer_excel(ruta_excel: str, carpeta_fotos: str) -> tuple[list, list]:
    """
    Lee el Excel y busca las fotos de cada docente.

    Retorna:
        completos  → lista de dicts con todos los datos incluida ruta de foto
        sin_foto   → lista de dicts a los que no se les encontró foto
    """
    wb = openpyxl.load_workbook(ruta_excel, data_only=True)
    ws = wb.active

    filas = list(ws.iter_rows(values_only=True))
    if len(filas) < 2:
        return [], []

    encabezados = filas[0]
    mapa = _mapear_columnas(encabezados)

    completos = []
    sin_foto  = []

    for fila in filas[1:]:
        # omitir filas completamente vacías
        if not any(c for c in fila if c):
            continue

        def cel(campo):
            idx = mapa.get(campo)
            if idx is not None and idx < len(fila):
                return str(fila[idx]).strip() if fila[idx] else ""
            return ""

        datos = {
            "nombre":      cel("nombre"),
            "correo":      cel("correo"),
            "escuela":     cel("escuela"),
            "departamento":cel("departamento"),
            "categoria":   cel("categoria"),
            "formacion": "\n".join(filter(None, [
                cel("formacion1"),
                cel("formacion2"),
                cel("formacion3"),
            ])),
            "trayectoria": cel("trayectoria"),
            "experiencia": "\n".join(filter(None, [
                cel("exp1"),
                cel("exp2"),
                cel("exp3"),
            ])),
            "foto_path":   None,
        }

        # buscar foto
        foto = _buscar_foto(datos["nombre"], carpeta_fotos)
        if foto:
            datos["foto_path"] = foto
            completos.append(datos)
        else:
            sin_foto.append(datos)

    return completos, sin_foto