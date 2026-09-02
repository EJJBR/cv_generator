"""
data_reader.py
Lee el Excel descargado de Google Forms y busca las fotos
en la carpeta descargada de Drive.
"""

import os
import re
import unicodedata
import openpyxl


NOISE_TOKENS = {
    "foto", "fotos", "perfil", "photo", "docente", "carnet", "carne",
    "jpg", "jpeg", "png", "jfif", "dpi", "copy", "snapseed", "crop",
    "mg", "dr", "dra", "ing", "lic", "msc", "phd", "prof"
}


def _normalizar_texto(texto: str) -> str:
    """Quita tildes, normaliza mayúsculas y elimina caracteres no alfanuméricos."""
    if not texto:
        return ""
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9]+", " ", texto)
    return " ".join(texto.split())


def _tokens_importantes(texto: str) -> list[str]:
    """Devuelve los tokens significativos de un nombre, ignorando ruido y números."""
    normalizado = _normalizar_texto(texto)
    tokens = []
    for token in normalizado.split():
        if token.isdigit():
            continue
        if token in NOISE_TOKENS:
            continue
        tokens.append(token)
    return tokens


def _normalizar_header(value: str | None) -> str:
    """Normaliza encabezados para comparar nombres con variantes del formulario."""
    if value is None:
        return ""
    value = unicodedata.normalize("NFKD", str(value))
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def _encabezado_contiene(encabezado: str, *tokens: str) -> bool:
    """Comprueba si el encabezado contiene todos los tokens clave requeridos."""
    encabezado_norm = _normalizar_header(encabezado)
    if not encabezado_norm:
        return False
    return all(token in encabezado_norm for token in tokens if token)


# Encabezados actuales del Excel exportado por Google Forms.
# Los alias anteriores se conservan para aceptar archivos ya descargados.
COLUMNAS = {
    "id":          ("ID", "Id", "Identificacion", "Identificación", "Numero de identificacion", "Número de identificación"),
    "nombre":      ("Apellidos y Nombres", "Apellidos y nombres", "Apellidos y Nombres del docente", "Apellidos y nombres del docente", "Nombre Completo", "Nombre completo", "Apellidos", "Nombres"),
    "foto_drive":  ("Foto de Perfil (sólo JPG)", "Foto de perfil", "Foto", "URL foto", "Link de foto", "Foto de Perfil", "Foto de Perfil (sólo JPG) colocar en el nombre del archivo los apellidos y nombres del docente"),
    "correo":      ("Correo Institucional (no personal)", "Correo Institucional", "Correo institucional", "Correo", "Correo Institucional del docente(no personal)", "Correo Institucional del docente"),
    "escuela":     ("Escuela Profesional o area que pertenece", "Escuela Profesional", "Escuela profesional", "Área o escuela profesional"),
    "departamento": ("Departamento Academico", "Departamento Académico", "Departamento académico", "Departamento"),
    "tipo_docente": ("Tipo de docente", "Tipo de docente ", "Tipo docente"),
    "categoria":   ("Categoría (de corresponder)", "Categoría / Clase", "Categoria", "Categoría", "Clase"),
    "clase_docente": ("Clase de docente (de corresponder)", "Clase de docente", "Clase docente"),
    "formacion1":  ("Formación Académica 1", "Formacion Academica 1", "Formación 1", "Formacion 1"),
    "formacion2":  ("Formación Académica 2", "Formacion Academica 2", "Formación 2", "Formacion 2"),
    "formacion3":  ("Formación Académica 3", "Formacion Academica 3", "Formación 3", "Formacion 3"),
    "investigacion": ("Sobre Investigación", "Sobre investigacion", "Investigación", "Investigacion"),
    "trayectoria": ("Trayectoria", "Trayectoria académica"),
    "exp1":        ("Experiencia Laboral 1", "Experiencia 1", "Experiencia laboral 1"),
    "exp2":        ("Experiencia Laboral 2", "Experiencia 2", "Experiencia laboral 2"),
    "exp3":        ("Experiencia Laboral 3", "Experiencia 3", "Experiencia laboral 3"),
}


def _buscar_foto(nombre_docente: str, carpeta_fotos: str, id_registro: str | None = None) -> str | None:
    """
    Busca la foto del docente en la carpeta de fotos.
    Si existe un ID, prioriza buscar el archivo con ese prefijo para soportar
    imágenes descargadas en formato ID_Apellido_Nombre.jpg. No usa el nombre
    como alternativa cuando existe un ID, para evitar asignar la foto de otro docente.
    Sin ID, acepta nombres con mayúsculas, tildes, abreviaturas y apellidos aislados.
    """
    if not os.path.exists(carpeta_fotos):
        return None

    id_registro = str(id_registro or "").strip()
    if id_registro:
        prefijo = f"{id_registro}_"
        for archivo in os.listdir(carpeta_fotos):
            ruta_archivo = os.path.join(carpeta_fotos, archivo)
            if os.path.isdir(ruta_archivo):
                continue
            if archivo.startswith(prefijo):
                return ruta_archivo
            nombre_base, _ = os.path.splitext(archivo)
            if nombre_base == str(id_registro):
                return ruta_archivo

        return None

    nombre_docente = (nombre_docente or "").strip()
    if not nombre_docente:
        return None

    nombre_norm = _normalizar_texto(nombre_docente)
    nombre_tokens = _tokens_importantes(nombre_docente)

    for archivo in os.listdir(carpeta_fotos):
        ruta_archivo = os.path.join(carpeta_fotos, archivo)
        if os.path.isdir(ruta_archivo):
            continue

        nombre_archivo = os.path.splitext(archivo)[0]
        archivo_norm = _normalizar_texto(nombre_archivo)

        if nombre_norm and nombre_norm in archivo_norm:
            return ruta_archivo

        if nombre_norm and archivo_norm in nombre_norm:
            return ruta_archivo

        archivo_tokens = _tokens_importantes(nombre_archivo)
        if not nombre_tokens or not archivo_tokens:
            continue

        if set(nombre_tokens).issubset(set(archivo_tokens)):
            return ruta_archivo

        overlap = len(set(nombre_tokens) & set(archivo_tokens))
        if overlap and (overlap >= 2 or overlap / max(len(nombre_tokens), 1) >= 0.6):
            return ruta_archivo

        apellidos = nombre_tokens[-2:]
        if len(apellidos) >= 2 and set(apellidos).issubset(set(archivo_tokens)):
            return ruta_archivo

    return None


def _mapear_columnas(encabezados: list) -> dict:
    """
    Mapea los nombres de columnas del Excel a los campos internos.
    Retorna dict {campo_interno: indice_columna}
    """
    mapa = {}

    for idx, encabezado in enumerate(encabezados):
        h = _normalizar_header(encabezado)
        if not h:
            continue

        if h in {"id", "identificacion", "numero de identificacion"} or h.startswith("id"):
            mapa.setdefault("id", idx)
        if "apellidos" in h and ("nombres" in h or "nombre" in h):
            mapa.setdefault("nombre", idx)
        if "foto" in h and ("perfil" in h or "drive" in h or "jpg" in h or "link" in h):
            mapa.setdefault("foto_drive", idx)
        if "correo" in h and ("institucional" in h or "personal" in h or "email" in h):
            mapa.setdefault("correo", idx)
        if "escuela" in h and ("profesional" in h or "area" in h):
            mapa.setdefault("escuela", idx)
        if "departamento" in h:
            mapa.setdefault("departamento", idx)
        if "tipo" in h and "docente" in h:
            mapa.setdefault("tipo_docente", idx)
        if "categoria" in h or "clase" in h:
            mapa.setdefault("categoria", idx)
        if "clase" in h and "docente" in h:
            mapa.setdefault("clase_docente", idx)
        if "formacion" in h and "academica" in h:
            if "formacion1" not in mapa:
                mapa.setdefault("formacion1", idx)
            elif "formacion2" not in mapa:
                mapa.setdefault("formacion2", idx)
            elif "formacion3" not in mapa:
                mapa.setdefault("formacion3", idx)
        if "investigacion" in h:
            mapa.setdefault("investigacion", idx)
        if "trayectoria" in h:
            mapa.setdefault("trayectoria", idx)
        if "experiencia" in h and "laboral" in h:
            if "exp1" not in mapa:
                mapa.setdefault("exp1", idx)
            elif "exp2" not in mapa:
                mapa.setdefault("exp2", idx)
            elif "exp3" not in mapa:
                mapa.setdefault("exp3", idx)

    for campo, nombre_columna in COLUMNAS.items():
        nombres = nombre_columna if isinstance(nombre_columna, tuple) else (nombre_columna,)
        if campo in mapa:
            continue
        for idx, encabezado in enumerate(encabezados):
            h = _normalizar_header(encabezado)
            for nombre in nombres:
                nombre_norm = _normalizar_header(nombre)
                if not nombre_norm:
                    continue
                if h == nombre_norm or nombre_norm in h or h in nombre_norm:
                    mapa[campo] = idx
                    break
            if campo in mapa:
                break

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

        nombre_real = cel("nombre")
        if not nombre_real:
            apellidos = ""
            nombres = ""
            for idx, encabezado in enumerate(encabezados):
                if idx >= len(fila):
                    continue
                nombre_col = _normalizar_header(encabezado)
                valor = str(fila[idx]).strip() if fila[idx] is not None else ""
                if not valor:
                    continue
                if nombre_col == "apellidos":
                    apellidos = valor
                elif nombre_col in {"nombres", "nombre"}:
                    nombres = valor
            nombre_real = " ".join(filter(None, [apellidos, nombres]))

        datos = {
            "id":           cel("id"),
            "nombre":       nombre_real,
            "correo":       cel("correo"),
            "escuela":      cel("escuela"),
            "departamento": cel("departamento"),
            "tipo_docente": cel("tipo_docente"),
            "categoria":    cel("categoria"),
            "clase_docente":cel("clase_docente"),
            "formacion": "\n".join(filter(None, [
                cel("formacion1"),
                cel("formacion2"),
                cel("formacion3"),
            ])),
            "investigacion":cel("investigacion"),
            "trayectoria":  cel("trayectoria"),
            "experiencia": "\n".join(filter(None, [
                cel("exp1"),
                cel("exp2"),
                cel("exp3"),
            ])),
            "foto_path":    None,
        }

        # buscar foto
        foto = _buscar_foto(datos["nombre"], carpeta_fotos, datos.get("id"))
        if foto:
            datos["foto_path"] = foto
            completos.append(datos)
        else:
            sin_foto.append(datos)

    return completos, sin_foto