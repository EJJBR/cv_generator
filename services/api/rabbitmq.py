"""
services/api/rabbitmq.py
Módulo publicador de eventos al Middleware RabbitMQ.
Cola objetivo: expedientes.generar_documentos
Soporta CloudAMQP (AMQP_URL) y RabbitMQ local (docker-compose).
"""

import os
import json
import logging
import pika

logger = logging.getLogger("api.rabbitmq")
QUEUE_NAME = "expedientes.generar_documentos"


def obtener_conexion_parametros():
    """Obtiene los parámetros de conexión para Pika según variables de entorno."""
    amqp_url = os.environ.get("AMQP_URL")
    if amqp_url:
        return pika.URLParameters(amqp_url)

    host = os.environ.get("RABBITMQ_HOST", "localhost")
    port = int(os.environ.get("RABBITMQ_PORT", "5672"))
    user = os.environ.get("RABBITMQ_USER", "guest")
    password = os.environ.get("RABBITMQ_PASSWORD", "guest")
    credentials = pika.PlainCredentials(user, password)
    return pika.ConnectionParameters(host=host, port=port, credentials=credentials)


def publicar_evento_generacion(expediente_id: str, datos_bolsista: dict) -> tuple[bool, str]:
    """
    Publica un mensaje asíncrono en la cola RabbitMQ para solicitar
    la generación de la Declaración Jurada y el Informe de Actividades.
    """
    params = obtener_conexion_parametros()
    try:
        connection = pika.BlockingConnection(params)
        channel = connection.channel()

        # Declarar cola durable para garantizar persistencia
        channel.queue_declare(queue=QUEUE_NAME, durable=True)

        payload = {
            "expediente_id": expediente_id,
            "datos_bolsista": datos_bolsista,
            "evento": "EXPEDIENTE_CREADO_GENERAR_DOCUMENTOS"
        }

        channel.basic_publish(
            exchange="",
            routing_key=QUEUE_NAME,
            body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Mensaje persistente en disco
                content_type="application/json"
            )
        )
        connection.close()
        logger.info(f"Mensaje publicado exitosamente en cola {QUEUE_NAME} para expediente {expediente_id}")
        return True, f"Evento publicado en RabbitMQ ({QUEUE_NAME})"
    except Exception as e:
        logger.error(f"Fallo al publicar mensaje en RabbitMQ: {str(e)}")
        return False, f"Fallo al conectar con RabbitMQ: {str(e)}"
