"""
services/docs_service/worker.py
Microservicio independiente de Generación de Documentos (DocsService).
Consume mensajes de la cola 'expedientes.generar_documentos' en RabbitMQ,
genera los archivos PDF requeridos (Declaración Jurada e Informe de Actividades)
con ReportLab y realiza un callback HTTP a la API REST para actualizar el estado
a 'Documentos_Generados'.
"""

import os
import sys
import json
import time
import logging
import requests
import pika

# Agregar raíz del proyecto al path para importar el módulo desacoplado core
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.pdf_engine import generar_declaracion_jurada, generar_informe_actividades

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [DocsService]: %(message)s"
)
logger = logging.getLogger("docs_service")

QUEUE_NAME = "expedientes.generar_documentos"
API_URL = os.environ.get("API_URL", "http://localhost:8000")
OUTPUT_BASE = os.environ.get("OUTPUT_DIR", os.path.join(PROJECT_ROOT, "output"))
LOGO_PATH = os.path.join(PROJECT_ROOT, "assets", "logofdcp.png")


def obtener_parametros_rabbitmq():
    """Obtiene parámetros de conexión a RabbitMQ soportando CloudAMQP o local."""
    amqp_url = os.environ.get("AMQP_URL")
    if amqp_url:
        logger.info("Usando conexión por AMQP_URL (CloudAMQP / Remoto)")
        return pika.URLParameters(amqp_url)

    host = os.environ.get("RABBITMQ_HOST", "localhost")
    port = int(os.environ.get("RABBITMQ_PORT", "5672"))
    user = os.environ.get("RABBITMQ_USER", "guest")
    password = os.environ.get("RABBITMQ_PASSWORD", "guest")
    credentials = pika.PlainCredentials(user, password)
    logger.info(f"Usando conexión directa a {host}:{port}")
    return pika.ConnectionParameters(host=host, port=port, credentials=credentials, heartbeat=60)


def procesar_mensaje(ch, method, properties, body):
    """Callback de procesamiento cuando llega un mensaje de la cola."""
    try:
        data = json.loads(body.decode("utf-8"))
        expediente_id = data.get("expediente_id")
        datos = data.get("datos_bolsista", {})

        logger.info(f"📥 Procesando mensaje recibido para expediente: {expediente_id}")

        # Directorio de salida para este expediente
        salida_dir = os.path.join(OUTPUT_BASE, "expedientes", expediente_id)
        os.makedirs(salida_dir, exist_ok=True)

        ruta_dj = os.path.join(salida_dir, f"Declaracion_Jurada_{expediente_id}.pdf")
        ruta_inf = os.path.join(salida_dir, f"Informe_Actividades_{expediente_id}.pdf")

        # 1. Generar Declaración Jurada con ReportLab
        logger.info(f"   ⚙️ Generando Declaración Jurada...")
        generar_declaracion_jurada(datos, ruta_dj, logo_path=LOGO_PATH if os.path.exists(LOGO_PATH) else None)

        # 2. Generar Informe de Actividades con ReportLab
        logger.info(f"   ⚙️ Generando Informe de Actividades...")
        generar_informe_actividades(datos, ruta_inf)

        documentos_generados = {
            "declaracion_jurada": ruta_dj,
            "informe_actividades": ruta_inf
        }
        logger.info(f"   ✅ Documentos generados exitosamente en: {salida_dir}")

        # 3. Notificar a la API REST (Callback HTTP)
        callback_url = f"{API_URL}/api/expedientes/{expediente_id}/completar"
        logger.info(f"   📤 Notificando a la API en: {callback_url}")
        
        auto_enviar = datos.get("auto_enviar_a_jefe", True)
        try:
            resp = requests.patch(
                callback_url,
                json={
                    "documentos": documentos_generados,
                    "auto_enviar_a_jefe": auto_enviar
                },
                timeout=10
            )
            if resp.status_code == 200:
                logger.info(f"   🎉 API confirmó actualización y envío para {expediente_id}")
            else:
                logger.warning(f"   ⚠️ API retornó código {resp.status_code}: {resp.text}")
        except Exception as api_err:
            logger.error(f"   ❌ No se pudo conectar con la API en {callback_url}: {api_err}")

        # Confirmar recepción a RabbitMQ
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.info(f"✔️ Mensaje confirmado (ACK) en RabbitMQ para {expediente_id}\n")

    except Exception as e:
        logger.error(f"❌ Error al procesar expediente: {str(e)}", exc_info=True)
        # Rechazar y no reencolar para evitar loops si el payload está mal formado
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def iniciar_worker(reintentos: int = 5, espera: int = 4):
    """Inicia el consumidor en segundo plano con lógica de reconexión."""
    params = obtener_parametros_rabbitmq()

    for intento in range(1, reintentos + 1):
        try:
            logger.info(f"Conectando a RabbitMQ (intento {intento}/{reintentos})...")
            connection = pika.BlockingConnection(params)
            channel = connection.channel()

            # Declarar cola durable y prefetch de 1 tarea a la vez
            channel.queue_declare(queue=QUEUE_NAME, durable=True)
            channel.basic_qos(prefetch_count=1)

            channel.basic_consume(
                queue=QUEUE_NAME,
                on_message_callback=procesar_mensaje,
                auto_ack=False
            )

            logger.info(f"🚀 DocsService Worker activo y esperando mensajes en '{QUEUE_NAME}'...")
            logger.info("Presiona CTRL+C para detener el servicio.\n")
            channel.start_consuming()

        except pika.exceptions.AMQPConnectionError as conn_err:
            logger.warning(f"No se pudo conectar al broker RabbitMQ: {conn_err}")
            if intento < reintentos:
                logger.info(f"Esperando {espera} segundos antes de reintentar...")
                time.sleep(espera)
            else:
                logger.error("Se agotaron los intentos de conexión con RabbitMQ.")
                raise
        except KeyboardInterrupt:
            logger.info("DocsService detenido manualmente.")
            break
        except Exception as e:
            logger.error(f"Error inesperado en DocsService: {e}")
            time.sleep(espera)


if __name__ == "__main__":
    iniciar_worker()
