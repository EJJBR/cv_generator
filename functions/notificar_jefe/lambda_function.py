"""
functions/notificar_jefe/lambda_function.py
Función AWS Lambda (Serverless FaaS) para notificación al Jefe de Área.
Se activa cuando el expediente pasa al estado 'Pendiente_Jefe'.

Características:
- Formato nativo AWS Lambda: lambda_handler(event, context).
- Soporte de modo DRY_RUN para exposiciones sin dependencia de internet ni credenciales de correo.
- Soporte SMTP real para envío de correos cuando DRY_RUN=false.
"""

import os
import json
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

logger = logging.getLogger("serverless.notificar_jefe")
logging.basicConfig(level=logging.INFO)


def construir_cuerpo_correo(datos: dict) -> str:
    """Construye el cuerpo del correo formal institucional para el Jefe de Área."""
    estudiante = datos.get("estudiante", "Bolsista UNMSM")
    expediente_id = datos.get("expediente_id", "N/A")
    mes = datos.get("mes", "Mes en curso")
    anio = datos.get("anio", "2026")
    para_nombre = datos.get("para_nombre", "Jefe de Dependencia")
    para_cargo = datos.get("para_cargo", "Jefatura")
    docs = datos.get("documentos", {})

    base_url = os.environ.get("API_URL", "http://localhost:8000")
    url_dj = f"{base_url}/api/expedientes/{expediente_id}/documentos/declaracion"
    url_inf = f"{base_url}/api/expedientes/{expediente_id}/documentos/informe"

    cuerpo = f"""
Estimado(a) {para_nombre},
{para_cargo}
Universidad Nacional Mayor de San Marcos

Por medio de la presente, se le notifica que el bolsista {estudiante} ha completado satisfactoriamente el registro y generación de los documentos correspondientes a su estipendio del periodo: {mes} {anio}.

DATOS DEL EXPEDIENTE:
- Código de Expediente: {expediente_id}
- Estado Actual: Pendiente_Jefe
- Fecha de Envío: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

ENLACES DE ACCESO DIRECTO A LOS DOCUMENTOS GENERADOS:
- 📜 Ver Declaración Jurada: {url_dj}
- 📊 Ver Informe de Actividades: {url_inf}

Por favor, proceda a la revisión y visación correspondiente en el Sistema de Gestión de Bolsistas UNMSM.

Atentamente,
Sistema Automatizado de Gestión de Bolsistas - UNMSM
Facultad de Ingeniería de Sistemas e Informática
"""
    return cuerpo.strip()


def lambda_handler(event, context):
    """
    Handler principal de la función AWS Lambda.
    Soporta invocación directa o payload recibido vía AWS Lambda Function URL / API Gateway.
    """
    # Si viene de API Gateway / Function URL, parsear 'body' si es string
    if isinstance(event, dict) and "body" in event and isinstance(event["body"], str):
        try:
            datos = json.loads(event["body"])
        except Exception:
            datos = event
    elif isinstance(event, dict):
        datos = event
    else:
        datos = {}

    expediente_id = datos.get("expediente_id", "DESCONOCIDO")
    destinatario = datos.get("jefe_email", "jefe.area@unmsm.edu.pe")
    estudiante = datos.get("estudiante", "Bolsista")
    mes = datos.get("mes", "Periodo Actual")
    asunto = f"[UNMSM - Trámite Bolsista] Expediente {expediente_id} listo para revisión - {estudiante} ({mes})"
    cuerpo = construir_cuerpo_correo(datos)

    dry_run = os.environ.get("DRY_RUN", "true").lower() in ["true", "1", "yes"]

    resultado_envio = {}

    if dry_run:
        logger.info("================ [SERVERLESS AWS LAMBDA - MODO DRY_RUN ACTIVO] ================")
        logger.info(f"Destinatario : {destinatario}")
        logger.info(f"Asunto       : {asunto}")
        logger.info(f"Expediente ID: {expediente_id}")
        logger.info(f"Contenido:\n{cuerpo}")
        logger.info("================================================================================")
        resultado_envio = {
            "estado": "SIMULADO_EXITOSO",
            "motivo": "Modo DRY_RUN activo para demostración",
            "servidor_smtp": "Ninguno (Simulación controlada para examen)"
        }
    else:
        smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        smtp_user = os.environ.get("SMTP_USER", "")
        smtp_pass = os.environ.get("SMTP_PASS", "")

        if not (smtp_user and smtp_pass):
            logger.warning("Credenciales SMTP no configuradas. Recurriendo a simulación segura.")
            resultado_envio = {
                "estado": "SIMULADO_FALLBACK",
                "motivo": "Sin credenciales SMTP en variables de entorno"
            }
        else:
            try:
                msg = MIMEMultipart()
                msg["From"] = smtp_user
                msg["To"] = destinatario
                msg["Subject"] = asunto
                msg.attach(MIMEText(cuerpo, "plain"))

                server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
                server.quit()

                resultado_envio = {
                    "estado": "ENVIADO_REAL",
                    "servidor_smtp": f"{smtp_host}:{smtp_port}"
                }
                logger.info(f"Correo real enviado a {destinatario} para expediente {expediente_id}")
            except Exception as e:
                logger.error(f"Error al enviar correo real: {e}")
                resultado_envio = {
                    "estado": "ERROR_ENVIO",
                    "error": str(e)
                }

    respuesta = {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": {
            "notificado": True,
            "expediente_id": expediente_id,
            "destinatario": destinatario,
            "asunto": asunto,
            "modo": "DRY_RUN" if dry_run else "REAL",
            "resultado": resultado_envio,
            "timestamp": datetime.now().isoformat()
        }
    }

    return respuesta


if __name__ == "__main__":
    # Prueba manual local
    evento_prueba = {
        "expediente_id": "exp-test-001",
        "estudiante": "JUAN CARLOS PÉREZ QUISPE",
        "jefe_email": "jefe.sistemas@unmsm.edu.pe",
        "para_nombre": "DR. CARLOS SÁNCHEZ VELÁSQUEZ",
        "para_cargo": "Director de Escuela Profesional",
        "mes": "Octubre",
        "anio": "2026",
        "documentos": {
            "declaracion_jurada": "output/Declaracion_Jurada.pdf",
            "informe_actividades": "output/Informe_Actividades.pdf"
        }
    }
    print(json.dumps(lambda_handler(evento_prueba, None), indent=2, ensure_ascii=False))
