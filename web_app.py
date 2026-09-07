import os
import re
import sys
import tempfile
import threading
import uuid
import webbrowser
from pathlib import Path
from threading import Lock, Timer

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR / "src"))

from controllers.individual_controller import IndividualController
from controllers.masivo_controller import MasivoController, _imagen_valida, _ruta_imagen
from data_reader import _mapear_columnas, leer_excel
from pdf_generator import generar_cv
from ui.config import OUTPUT_DIR, OUTPUT_IMAGENES, OUTPUT_REGISTROS
from ui.utils import nombre_archivo_pdf

WEB_DIR = ROOT_DIR / "web"
app = FastAPI(title="Generador de CVs Docentes")
app.mount("/static", StaticFiles(directory=WEB_DIR / "static"), name="static")
app.mount("/assets", StaticFiles(directory=ROOT_DIR / "assets"), name="assets")
templates = Jinja2Templates(directory=WEB_DIR / "templates")
download_tasks = {}
download_tasks_lock = Lock()
generation_tasks = {}
generation_tasks_lock = Lock()


def _crear_masivo_controller():
    return MasivoController(lambda _: None, lambda _: None, lambda: None)


def _ruta_cv(id_val: str, nombre: str) -> Path:
    return Path(OUTPUT_DIR) / nombre_archivo_pdf(nombre, id_val)


def _id_valido(id_val: str) -> bool:
    return bool(id_val and re.fullmatch(r"[A-Za-z0-9_-]+", id_val))


def _filas_excel(ruta_excel: str, incluir_cv: bool = False):
    import openpyxl

    wb = openpyxl.load_workbook(ruta_excel, data_only=True)
    filas = list(wb.active.iter_rows(values_only=True))
    if not filas:
        return []

    mapa = _mapear_columnas(filas[0])
    resultado = []
    for fila in filas[1:]:
        if not any(valor is not None and str(valor).strip() for valor in fila):
            continue

        def valor(campo):
            indice = mapa.get(campo)
            return str(fila[indice]).strip() if indice is not None and indice < len(fila) and fila[indice] is not None else ""

        nombre = valor("nombre")
        id_val = valor("id")
        ruta_foto = _ruta_imagen(id_val, nombre) if id_val else ""
        descargada = bool(
            ruta_foto and Path(ruta_foto).is_file() and _imagen_valida(ruta_foto)
        )
        ruta_cv = _ruta_cv(id_val, nombre) if id_val else Path()
        cv_generado = bool(incluir_cv and ruta_cv and ruta_cv.is_file())
        resultado.append({
            "id": id_val,
            "nombre": nombre,
            "tiene_enlace": bool(valor("foto_drive")),
            "descargada": descargada,
            "fallida": False,
            "can_retry": False,
            "progreso": 100 if descargada else 0,
            "ruta_foto": ruta_foto,
            "cv_generado": cv_generado,
            "ruta_cv": str(ruta_cv) if cv_generado else "",
            "estado": "Descargada" if descargada else ("Pendiente de descarga" if valor("foto_drive") else "Sin enlace disponible"),
        })
    return resultado


@app.get("/", response_class=HTMLResponse)
def index(request: Request, mensaje: str = "", error: str = ""):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"mensaje": mensaje, "error": error},
    )


@app.post("/individual", response_class=HTMLResponse)
async def generar_individual(
    request: Request,
    nombre: str = Form(""),
    correo: str = Form(""),
    escuela: str = Form(""),
    departamento: str = Form(""),
    tipo_docente: str = Form(""),
    categoria: str = Form(""),
    clase_docente: str = Form(""),
    formacion: str = Form(""),
    trayectoria: str = Form(""),
    experiencia: str = Form(""),
    foto: UploadFile | None = File(None),
):
    foto_path = None
    try:
        if foto and foto.filename:
            suffix = Path(foto.filename).suffix.lower() or ".jpg"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as archivo:
                archivo.write(await foto.read())
                foto_path = archivo.name

        datos = {
            "nombre": nombre.strip(),
            "correo": correo.strip(),
            "escuela": escuela.strip(),
            "departamento": departamento.strip(),
            "tipo_docente": tipo_docente.strip(),
            "categoria": categoria.strip(),
            "clase_docente": clase_docente.strip(),
            "formacion": formacion.strip(),
            "trayectoria": trayectoria.strip(),
            "experiencia": experiencia.strip(),
            "foto_path": foto_path,
        }
        exito, resultado = IndividualController.generar(datos)
        mensaje = resultado if exito else ""
        error = "" if exito else resultado
    except Exception as exc:
        mensaje = ""
        error = f"Error inesperado: {exc}"
    finally:
        if foto_path:
            Path(foto_path).unlink(missing_ok=True)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"mensaje": mensaje, "error": error},
    )


@app.post("/masivo/procesar")
async def procesar_masivo(excel: UploadFile = File(...)):
    if not excel.filename:
        return JSONResponse({"error": "Selecciona un archivo Excel."}, status_code=400)

    suffix = Path(excel.filename).suffix.lower()
    if suffix not in {".xlsx", ".xls"}:
        return JSONResponse({"error": "El archivo debe ser Excel (.xlsx o .xls)."}, status_code=400)

    temporal = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as archivo:
            archivo.write(await excel.read())
            temporal = archivo.name

        ok, mensaje, ruta_transformada = _crear_masivo_controller().transformar_excel(temporal)
        if not ok:
            return JSONResponse({"error": mensaje}, status_code=400)

        filas = _filas_excel(ruta_transformada)
        if not filas:
            return JSONResponse({"error": "No se encontraron docentes en el Excel."}, status_code=400)
        return {"mensaje": mensaje, "filas": filas, "stage": "download"}
    except Exception as exc:
        return JSONResponse({"error": f"Error procesando Excel: {exc}"}, status_code=500)
    finally:
        if temporal:
            Path(temporal).unlink(missing_ok=True)


@app.post("/masivo/descargar")
async def descargar_imagenes(
    excel: UploadFile = File(...),
    id_reintento: str | None = Form(None),
):
    if not excel.filename:
        return JSONResponse({"error": "Selecciona un archivo Excel."}, status_code=400)

    suffix = Path(excel.filename).suffix.lower()
    if suffix not in {".xlsx", ".xls"}:
        return JSONResponse({"error": "El archivo debe ser Excel (.xlsx o .xls)."}, status_code=400)

    temporal = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as archivo:
            archivo.write(await excel.read())
            temporal = archivo.name

        controller = _crear_masivo_controller()
        ok, mensaje, ruta_transformada = controller.transformar_excel(temporal)
        if not ok:
            return JSONResponse({"error": mensaje}, status_code=400)

        filas = _filas_excel(ruta_transformada)
        task_id = uuid.uuid4().hex
        with download_tasks_lock:
            download_tasks[task_id] = {
                "estado": "running",
                "mensaje": "Descarga iniciada.",
                "filas": filas,
            }

        def actualizar_fila(item):
            with download_tasks_lock:
                task = download_tasks.get(task_id)
                if task:
                    for indice, fila in enumerate(task["filas"]):
                        if str(fila.get("id")) == str(item.get("id")):
                            task["filas"][indice] = {**fila, **item}
                            break

        def ejecutar_descarga():
            ok_descarga, resumen, filas_finales = controller.descargar_fotos_excel_detallado(
                ruta_transformada,
                callback_estado=actualizar_fila,
                solo_ids={id_reintento} if id_reintento else None,
            )
            with download_tasks_lock:
                task = download_tasks.get(task_id)
                if task:
                    task["estado"] = "completed" if ok_descarga else "failed"
                    task["mensaje"] = resumen
                    if id_reintento:
                        filas_por_id = {
                            str(fila.get("id")): fila for fila in filas_finales
                        }
                        for indice, fila in enumerate(task["filas"]):
                            actualizado = filas_por_id.get(str(fila.get("id")))
                            if actualizado and str(fila.get("id")) == id_reintento:
                                task["filas"][indice] = actualizado
                    else:
                        task["filas"] = filas_finales

        threading.Thread(target=ejecutar_descarga, daemon=True).start()
        return {"task_id": task_id, "filas": filas, "stage": "downloading"}
    except Exception as exc:
        return JSONResponse({"error": f"Error descargando imágenes: {exc}"}, status_code=500)
    finally:
        if temporal:
            Path(temporal).unlink(missing_ok=True)


@app.post("/masivo/generar")
async def generar_cvs_masivo(excel: UploadFile = File(...)):
    if not excel.filename:
        return JSONResponse({"error": "Selecciona un archivo Excel."}, status_code=400)

    suffix = Path(excel.filename).suffix.lower()
    if suffix not in {".xlsx", ".xls"}:
        return JSONResponse({"error": "El archivo debe ser Excel (.xlsx o .xls)."}, status_code=400)

    temporal = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as archivo:
            archivo.write(await excel.read())
            temporal = archivo.name

        controller = _crear_masivo_controller()
        ok, mensaje, ruta_transformada = controller.transformar_excel(temporal)
        if not ok:
            return JSONResponse({"error": mensaje}, status_code=400)

        filas = _filas_excel(ruta_transformada)
        cv_total = len(filas)
        task_id = uuid.uuid4().hex
        with generation_tasks_lock:
            generation_tasks[task_id] = {
                "estado": "running",
                "mensaje": "Generación de CVs iniciada.",
                "filas": filas,
                "cv_total": cv_total,
                "cv_completados": 0,
            }

        def ejecutar_generacion():
            try:
                def actualizar_cv(item):
                    with generation_tasks_lock:
                        task = generation_tasks.get(task_id)
                        if not task:
                            return
                        for indice, fila in enumerate(task["filas"]):
                            if str(fila.get("id")) == str(item.get("id")):
                                task["filas"][indice] = {**fila, **item}
                                task["cv_completados"] += 1
                                break

                controller._procesar_interno(
                    ruta_transformada,
                    OUTPUT_IMAGENES,
                    callback_cv=actualizar_cv,
                )
                with generation_tasks_lock:
                    task = generation_tasks.get(task_id)
                    if task:
                        task["estado"] = "completed"
                        task["mensaje"] = "Generación de CVs terminada."
            except Exception as exc:
                with generation_tasks_lock:
                    task = generation_tasks.get(task_id)
                    if task:
                        task["estado"] = "failed"
                        task["mensaje"] = f"Error generando CVs: {exc}"

        threading.Thread(target=ejecutar_generacion, daemon=True).start()
        return {
            "task_id": task_id,
            "filas": filas,
            "cv_total": cv_total,
            "cv_completados": 0,
            "stage": "generating",
        }
    except Exception as exc:
        return JSONResponse({"error": f"Error generando CVs: {exc}"}, status_code=500)
    finally:
        if temporal:
            Path(temporal).unlink(missing_ok=True)


@app.post("/masivo/imagen-local")
async def guardar_imagen_local(
    imagen: UploadFile = File(...),
    id_val: str = Form(...),
    nombre: str = Form(""),
):
    if not _id_valido(id_val):
        return JSONResponse({"error": "ID de imagen no válido."}, status_code=400)
    if not imagen.filename:
        return JSONResponse({"error": "Selecciona una imagen."}, status_code=400)

    temporal = None
    try:
        Path(OUTPUT_IMAGENES).mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(imagen.filename).suffix.lower() or ".img") as archivo:
            archivo.write(await imagen.read())
            temporal = archivo.name

        with Image.open(temporal) as original:
            original.load()
            destino = Path(_ruta_imagen(id_val, nombre))
            original.convert("RGB").save(destino, format="JPEG", quality=95)

        return {
            "id": id_val,
            "nombre": nombre,
            "descargada": True,
            "tiene_enlace": True,
            "fallida": False,
            "estado": "Imagen agregada",
            "progreso": 100,
            "ruta_foto": str(destino),
        }
    except Exception as exc:
        return JSONResponse({"error": f"No se pudo guardar la imagen: {exc}"}, status_code=400)
    finally:
        if temporal:
            Path(temporal).unlink(missing_ok=True)


@app.post("/masivo/generar-cv")
async def generar_cv_individual(
    excel: UploadFile = File(...),
    id_val: str = Form(...),
):
    if not _id_valido(id_val):
        return JSONResponse({"error": "ID de CV no válido."}, status_code=400)

    temporal = None
    try:
        suffix = Path(excel.filename or "").suffix.lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix or ".xlsx") as archivo:
            archivo.write(await excel.read())
            temporal = archivo.name

        controller = _crear_masivo_controller()
        ok, mensaje, ruta_transformada = controller.transformar_excel(temporal)
        if not ok:
            return JSONResponse({"error": mensaje}, status_code=400)

        completos, _ = leer_excel(ruta_transformada, OUTPUT_IMAGENES)
        datos = next((item for item in completos if str(item.get("id")) == id_val), None)
        if not datos:
            return JSONResponse({"error": "No se encontró una imagen válida para ese docente."}, status_code=400)

        ruta_pdf = _ruta_cv(id_val, datos.get("nombre", ""))
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        generar_cv(datos, str(ruta_pdf))
        return {
            "id": id_val,
            "cv_generado": True,
            "cv_error": False,
            "cv_mensaje": "",
            "ruta_cv": str(ruta_pdf),
        }
    except Exception as exc:
        return JSONResponse({
            "error": "Contenido demasiado extenso o incompatible para generar el CV.",
            "detalle": str(exc),
        }, status_code=400)
    finally:
        if temporal:
            Path(temporal).unlink(missing_ok=True)


@app.get("/masivo/generar/{task_id}")
def estado_generacion(task_id: str):
    with generation_tasks_lock:
        task = generation_tasks.get(task_id)
        if not task:
            return JSONResponse({"error": "No se encontró la tarea de generación."}, status_code=404)
        return {
            "estado": task["estado"],
            "mensaje": task["mensaje"],
            "filas": task["filas"],
            "cv_total": task["cv_total"],
            "cv_completados": task["cv_completados"],
            "stage": "done" if task["estado"] in {"completed", "failed"} else "generating",
        }


@app.get("/masivo/cv/{id_val}")
def ver_cv(id_val: str):
    if not id_val or not re.fullmatch(r"[A-Za-z0-9_-]+", id_val):
        return JSONResponse({"error": "ID de CV no válido."}, status_code=400)

    for ruta in Path(OUTPUT_DIR).glob(f"{id_val}_CV_*.pdf"):
        if ruta.is_file():
            return FileResponse(
                ruta,
                media_type="application/pdf",
                filename=ruta.name,
                content_disposition_type="inline",
            )

    return JSONResponse({"error": "No se encontró un CV generado para ese ID."}, status_code=404)


@app.post("/masivo/limpiar")
def limpiar_salida_masiva():
    eliminados = 0
    for carpeta, patrones in (
        (Path(OUTPUT_IMAGENES), ("*",)),
        (Path(OUTPUT_DIR), ("*.pdf",)),
        (Path(OUTPUT_REGISTROS), ("*.xlsx", "*.xls")),
    ):
        carpeta.mkdir(parents=True, exist_ok=True)
        for patron in patrones:
            for ruta in carpeta.glob(patron):
                if ruta.is_file():
                    ruta.unlink()
                    eliminados += 1
    return {"mensaje": f"Limpieza terminada: {eliminados} archivos eliminados."}


@app.get("/masivo/descargar/{task_id}")
def estado_descarga(task_id: str):
    with download_tasks_lock:
        task = download_tasks.get(task_id)
        if not task:
            return JSONResponse({"error": "No se encontró la tarea de descarga."}, status_code=404)
        return {
            "estado": task["estado"],
            "mensaje": task["mensaje"],
            "filas": task["filas"],
            "stage": "done" if task["estado"] in {"completed", "failed"} else "downloading",
        }


@app.get("/masivo/imagen/{id_val}")
def ver_imagen(id_val: str):
    if not id_val or not re.fullmatch(r"[A-Za-z0-9_-]+", id_val):
        return JSONResponse({"error": "ID de imagen no válido."}, status_code=400)

    for ruta in sorted((ROOT_DIR / "output" / "imagenes").glob(f"{id_val}_*.jpg")):
        if _imagen_valida(str(ruta)):
            return FileResponse(
                ruta,
                media_type="image/jpeg",
                content_disposition_type="inline",
            )

    return JSONResponse({"error": "No se encontró una imagen válida para ese ID."}, status_code=404)


def abrir_navegador():
    webbrowser.open("http://127.0.0.1:8000")


if __name__ == "__main__":
    import uvicorn

    Timer(1.2, abrir_navegador).start()
    uvicorn.run(app, host="127.0.0.1", port=8000)
