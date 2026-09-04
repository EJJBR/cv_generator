import os
import sys
import tempfile
import webbrowser
from pathlib import Path
from threading import Timer

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR / "src"))

from controllers.individual_controller import IndividualController
from controllers.masivo_controller import MasivoController
from data_reader import _mapear_columnas

WEB_DIR = ROOT_DIR / "web"
app = FastAPI(title="Generador de CVs Docentes")
app.mount("/static", StaticFiles(directory=WEB_DIR / "static"), name="static")
app.mount("/assets", StaticFiles(directory=ROOT_DIR / "assets"), name="assets")
templates = Jinja2Templates(directory=WEB_DIR / "templates")


def _crear_masivo_controller():
    return MasivoController(lambda _: None, lambda _: None, lambda: None)


def _filas_excel(ruta_excel: str):
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
        resultado.append({
            "id": valor("id"),
            "nombre": nombre,
            "tiene_enlace": bool(valor("foto_drive")),
            "estado": "Pendiente de descarga" if valor("foto_drive") else "Sin enlace disponible",
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
async def descargar_imagenes(excel: UploadFile = File(...)):
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

        ok_descarga, resumen, filas = controller.descargar_fotos_excel_detallado(ruta_transformada)
        if not ok_descarga:
            return JSONResponse({"error": resumen}, status_code=400)

        return {
            "mensaje": resumen,
            "filas": filas,
            "stage": "done",
        }
    except Exception as exc:
        return JSONResponse({"error": f"Error descargando imágenes: {exc}"}, status_code=500)
    finally:
        if temporal:
            Path(temporal).unlink(missing_ok=True)


def abrir_navegador():
    webbrowser.open("http://127.0.0.1:8000")


if __name__ == "__main__":
    import uvicorn

    Timer(1.2, abrir_navegador).start()
    uvicorn.run(app, host="127.0.0.1", port=8000)
