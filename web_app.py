import os
import sys
import tempfile
import webbrowser
from pathlib import Path
from threading import Timer

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR / "src"))

from controllers.individual_controller import IndividualController

WEB_DIR = ROOT_DIR / "web"
app = FastAPI(title="Generador de CVs Docentes")
app.mount("/static", StaticFiles(directory=WEB_DIR / "static"), name="static")
templates = Jinja2Templates(directory=WEB_DIR / "templates")


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


def abrir_navegador():
    webbrowser.open("http://127.0.0.1:8000")


if __name__ == "__main__":
    import uvicorn

    Timer(1.2, abrir_navegador).start()
    uvicorn.run(app, host="127.0.0.1", port=8000)
