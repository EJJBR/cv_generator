"""
services/api/main.py
API REST para la Gestión de Expedientes de Bolsistas UNMSM.
Asignatura: Taller de Arquitectura de Software (TARQSW-06).
Proceso Crítico: Registro del expediente -> Generación de documentos -> Envío a revisión del Jefe.
Estados: Borrador -> Documentos_Generados -> Pendiente_Jefe.
"""

import os
import sys
import uuid
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

import requests
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Asegurar importaciones relativas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import database
import rabbitmq

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("api.main")

app = FastAPI(
    title="UNMSM - API Gestión de Expedientes de Bolsistas",
    description="""
    ## Proceso Crítico: Tramitación de Pago de Bolsistas UNMSM
    Prototipo evolutivo de arquitectura de software para el examen de Arquitectura:
    1. **Middleware**: RabbitMQ (cola `expedientes.generar_documentos`).
    2. **API REST**: FastAPI con OpenAPI/Swagger interactivo.
    3. **Cloud PaaS**: Despliegue en Render con endpoint `/health`.
    4. **Microservicio**: Generador de PDFs con ReportLab desacoplado de UI.
    5. **Serverless FaaS**: Notificación al Jefe de Área (AWS Lambda / DRY_RUN).
    
    ### Ciclo de Estados:
    `Borrador` ➔ `Documentos_Generados` ➔ `Pendiente_Jefe`
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Modelos Pydantic ──────────────────────────────────────────────────────────
class BolsistaPayload(BaseModel):
    nombres: str = Field(..., example="JUAN CARLOS")
    ap_paterno: str = Field(..., example="PÉREZ")
    ap_materno: str = Field(..., example="QUISPE")
    dni: str = Field(..., example="71234567")
    domicilio: str = Field(default="Av. Germán Amézaga 375, Ciudad Universitaria", example="Av. Germán Amézaga 375")
    distrito: str = Field(default="Cercado de Lima", example="Cercado de Lima")
    telefono: str = Field(default="987654321", example="987654321")
    email: str = Field(..., example="juan.perez@unmsm.edu.pe")
    facultad: str = Field(default="Facultad de Ingeniería de Sistemas e Informática", example="Facultad de Ingeniería de Sistemas e Informática")
    condicion: str = Field(default="Estudiante", example="Estudiante")
    mes: str = Field(default="Octubre", example="Octubre")
    anio: str = Field(default="2026", example="2026")
    fecha: Optional[str] = Field(default="Lima, 30 de Octubre del 2026", example="Lima, 30 de Octubre del 2026")
    de_nombre: Optional[str] = Field(default="JUAN CARLOS PÉREZ QUISPE", example="JUAN CARLOS PÉREZ QUISPE")
    para_nombre: str = Field(default="DR. CARLOS SÁNCHEZ VELÁSQUEZ", example="DR. CARLOS SÁNCHEZ VELÁSQUEZ")
    para_cargo: str = Field(default="Director de la Escuela Profesional de Ingeniería de Software", example="Director de Escuela")
    asunto: Optional[str] = Field(default="Informe de actividades de bolsista - Octubre 2026")
    auto_enviar_a_jefe: bool = Field(
        default=True,
        description="Si es True, una vez generados los PDFs se envía automáticamente el correo al Jefe vía Serverless"
    )
    actividades: List[str] = Field(
        default=[
            "Mantenimiento preventivo y correctivo de estaciones de cómputo.",
            "Configuración de laboratorios para cátedras de software.",
            "Desarrollo de scripts de automatización para consolidación de reportes."
        ],
        example=["Mantenimiento de laboratorios", "Soporte a docentes"]
    )


class CompletarDocumentosPayload(BaseModel):
    documentos: Dict[str, str] = Field(
        ...,
        example={
            "declaracion_jurada": "output/expedientes/exp-123456/Declaracion_Jurada.pdf",
            "informe_actividades": "output/expedientes/exp-123456/Informe_Actividades.pdf"
        }
    )
    auto_enviar_a_jefe: Optional[bool] = Field(default=True)


class EnviarRevisionPayload(BaseModel):
    jefe_email: Optional[str] = Field(default="jefe.area@unmsm.edu.pe", example="jefe.area@unmsm.edu.pe")
    observaciones: Optional[str] = Field(default="Expediente completado y listo para visación.", example="Listo para firma")


# ── Endpoints del Proceso Crítico ─────────────────────────────────────────────

@app.get("/health", tags=["Monitoreo & PaaS"], summary="Verificación de estado de salud del servicio")
def health_check():
    """Endpoint de salud requerido por plataformas PaaS (Render) para keep-alive y healthcheck."""
    return {
        "status": "healthy",
        "service": "PagoBolsista API",
        "ambiente": os.environ.get("ENV", "local"),
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/expedientes", status_code=status.HTTP_201_CREATED, tags=["Expedientes"], summary="1. Registrar expediente y publicar a la cola RabbitMQ")
def registrar_expediente(payload: BolsistaPayload):
    """
    **Paso 1 del Proceso Crítico**:
    - Registra el expediente en estado **Borrador**.
    - Publica asíncronamente el evento en la cola RabbitMQ `expedientes.generar_documentos`.
    - Desacopla la API del proceso pesado de renderizado PDF.
    """
    expediente_id = f"exp-{uuid.uuid4().hex[:8]}"
    datos_dict = payload.model_dump()
    
    # Persistir en estado Borrador
    expediente = database.crear_expediente(expediente_id, datos_dict)
    
    # Publicar en RabbitMQ (Middleware)
    ok, mensaje_mq = rabbitmq.publicar_evento_generacion(expediente_id, datos_dict)
    
    return {
        "mensaje": "Expediente registrado exitosamente",
        "expediente_id": expediente_id,
        "estado": expediente["estado"],
        "middleware_status": {
            "publicado": ok,
            "detalle": mensaje_mq,
            "cola": rabbitmq.QUEUE_NAME
        },
        "expediente": expediente
    }


@app.get("/api/expedientes/{expediente_id}", tags=["Expedientes"], summary="2. Consultar estado y documentos del expediente")
def obtener_expediente(expediente_id: str):
    """
    **Consulta de Estado**:
    Devuelve el estado actual (`Borrador`, `Documentos_Generados`, `Pendiente_Jefe`),
    los enlaces de descarga de documentos y el historial de transiciones.
    """
    expediente = database.obtener_expediente(expediente_id)
    if not expediente:
        raise HTTPException(status_code=404, detail=f"Expediente '{expediente_id}' no encontrado.")
    
    # Construir enlaces de descarga
    base_url = "/api/expedientes/" + expediente_id + "/documentos/"
    descargas = {}
    if "declaracion_jurada" in expediente.get("documentos", {}):
        descargas["declaracion_jurada_url"] = f"{base_url}declaracion"
    if "informe_actividades" in expediente.get("documentos", {}):
        descargas["informe_actividades_url"] = f"{base_url}informe"

    return {
        **expediente,
        "descargas": descargas
    }


@app.get("/api/expedientes", tags=["Expedientes"], summary="Listar todos los expedientes")
def listar_expedientes():
    """Lista todos los expedientes registrados en el sistema."""
    return {"total": len(database.listar_expedientes()), "expedientes": database.listar_expedientes()}


@app.patch("/api/expedientes/{expediente_id}/completar", tags=["Microservicio Callback"], summary="3. Callback invocado por DocsService al terminar PDFs")
def completar_documentos(expediente_id: str, payload: CompletarDocumentosPayload):
    """
    **Callback del Microservicio DocsService**:
    Invocado cuando los documentos PDF han sido generados exitosamente.
    Actualiza el estado de `Borrador` a **Documentos_Generados**.
    """
    expediente = database.obtener_expediente(expediente_id)
    if not expediente:
        raise HTTPException(status_code=404, detail=f"Expediente '{expediente_id}' no encontrado.")

    exp_actualizado = database.registrar_documentos_generados(expediente_id, payload.documentos)
    logger.info(f"Expediente {expediente_id} pasó a Documentos_Generados con archivos: {payload.documentos}")

    # Si auto_enviar_a_jefe está activo, automatizar el envío al Jefe inmediatamente
    serverless_response = None
    if payload.auto_enviar_a_jefe:
        exp_actualizado = database.actualizar_estado(
            expediente_id,
            "Pendiente_Jefe",
            "Envío automático al Jefe tras generación exitosa de documentos."
        )
        evento_serverless = {
            "expediente_id": expediente_id,
            "estudiante": f"{expediente['datos_bolsista'].get('nombres')} {expediente['datos_bolsista'].get('ap_paterno')}",
            "jefe_email": expediente['datos_bolsista'].get('jefe_email', 'director.software@unmsm.edu.pe'),
            "para_nombre": expediente['datos_bolsista'].get('para_nombre'),
            "para_cargo": expediente['datos_bolsista'].get('para_cargo'),
            "mes": expediente['datos_bolsista'].get('mes', 'Mes en curso'),
            "anio": expediente['datos_bolsista'].get('anio', '2026'),
            "documentos": payload.documentos,
            "timestamp": datetime.now().isoformat()
        }
        serverless_response = invocar_serverless_notificacion(evento_serverless)
        database.registrar_notificacion_jefe(expediente_id, serverless_response)
        logger.info(f"Expediente {expediente_id} notificado automáticamente al Jefe vía Serverless FaaS.")

    return {
        "mensaje": "Documentos registrados y proceso completado",
        "expediente_id": expediente_id,
        "estado": exp_actualizado["estado"],
        "documentos": exp_actualizado["documentos"],
        "auto_enviado_jefe": payload.auto_enviar_a_jefe,
        "serverless_invocacion": serverless_response
    }


@app.post("/api/expedientes/{expediente_id}/enviar", tags=["Expedientes"], summary="4. Enviar a revisión del Jefe y disparar Serverless")
def enviar_a_revision(expediente_id: str, payload: EnviarRevisionPayload = EnviarRevisionPayload()):
    """
    **Paso 3 del Proceso Crítico**:
    - Valida que el expediente esté en estado **Documentos_Generados**.
    - Cambia el estado a **Pendiente_Jefe**.
    - Dispara la función Serverless FaaS (AWS Lambda) para notificar al Jefe de Área.
    """
    expediente = database.obtener_expediente(expediente_id)
    if not expediente:
        raise HTTPException(status_code=404, detail=f"Expediente '{expediente_id}' no encontrado.")

    if expediente.get("estado") == "Pendiente_Jefe":
        return {
            "mensaje": "Expediente ya fue enviado automáticamente a revisión del Jefe de Área",
            "expediente_id": expediente_id,
            "estado": "Pendiente_Jefe",
            "serverless_invocacion": expediente.get("notificacion_jefe")
        }

    if expediente.get("estado") != "Documentos_Generados":
        raise HTTPException(
            status_code=400,
            detail=f"No se puede enviar a revisión. El estado actual es '{expediente.get('estado')}'. Se requiere 'Documentos_Generados'."
        )

    # Actualizar estado a Pendiente_Jefe
    exp_actualizado = database.actualizar_estado(
        expediente_id,
        "Pendiente_Jefe",
        f"Enviado a revisión del Jefe: {payload.jefe_email}. Observaciones: {payload.observaciones}"
    )

    # Disparar Serverless (AWS Lambda o simulador)
    evento_serverless = {
        "expediente_id": expediente_id,
        "estudiante": f"{expediente['datos_bolsista'].get('nombres')} {expediente['datos_bolsista'].get('ap_paterno')}",
        "jefe_email": payload.jefe_email,
        "para_nombre": expediente['datos_bolsista'].get('para_nombre'),
        "para_cargo": expediente['datos_bolsista'].get('para_cargo'),
        "mes": expediente['datos_bolsista'].get('mes', 'Mes en curso'),
        "anio": expediente['datos_bolsista'].get('anio', '2026'),
        "documentos": expediente.get("documentos", {}),
        "timestamp": datetime.now().isoformat()
    }

    serverless_response = invocar_serverless_notificacion(evento_serverless)
    database.registrar_notificacion_jefe(expediente_id, serverless_response)

    return {
        "mensaje": "Expediente enviado exitosamente a revisión del Jefe de Área",
        "expediente_id": expediente_id,
        "estado": exp_actualizado["estado"],
        "serverless_invocacion": serverless_response
    }


@app.get("/api/expedientes/{expediente_id}/documentos/{tipo}", tags=["Descargas"], summary="Descargar documento PDF generado")
def descargar_documento(expediente_id: str, tipo: str):
    """Descarga el PDF generado de la Declaración Jurada o Informe de Actividades."""
    expediente = database.obtener_expediente(expediente_id)
    if not expediente:
        raise HTTPException(status_code=404, detail="Expediente no encontrado.")

    clave = "declaracion_jurada" if tipo in ["declaracion", "declaracion_jurada"] else "informe_actividades"
    ruta_pdf = expediente.get("documentos", {}).get(clave)

    if not ruta_pdf or not os.path.exists(ruta_pdf):
        raise HTTPException(status_code=404, detail=f"El documento '{tipo}' aún no existe en el almacenamiento.")

    return FileResponse(
        path=ruta_pdf,
        filename=os.path.basename(ruta_pdf),
        media_type="application/pdf"
    )


def invocar_serverless_notificacion(evento: dict) -> dict:
    """
    Invoca la función Serverless FaaS.
    Si LAMBDA_URL está configurada, realiza una llamada HTTP POST a la URL de la función en AWS Lambda.
    De lo contrario o si falla la red, ejecuta el handler Lambda localmente con modo DRY_RUN.
    """
    lambda_url = os.environ.get("LAMBDA_URL")
    if lambda_url:
        try:
            logger.info(f"Invocando AWS Lambda en {lambda_url}...")
            resp = requests.post(lambda_url, json=evento, timeout=8)
            if resp.status_code == 200:
                return {
                    "metodo": "AWS Lambda HTTP Function URL",
                    "status_code": resp.status_code,
                    "resultado": resp.json()
                }
        except Exception as e:
            logger.warning(f"Error invocando Lambda remoto: {e}. Usando ejecución Serverless local.")

    # Ejecución Serverless local (FaaS Runner embebido)
    try:
        from functions.notificar_jefe.lambda_function import lambda_handler
        resultado = lambda_handler(evento, context=None)
        return {
            "metodo": "Serverless Lambda Local Handler (FaaS Runner)",
            "status_code": resultado.get("statusCode", 200),
            "resultado": resultado.get("body")
        }
    except Exception as e:
        logger.error(f"Error ejecutando handler serverless: {e}")
        return {
            "metodo": "Serverless Fallback",
            "error": str(e)
        }
