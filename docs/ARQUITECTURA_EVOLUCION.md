# 🏛️ Evolución de la Arquitectura de Software
## Caso de Estudio: Sistema de Tramitación de Pagos de Bolsistas UNMSM
**Asignatura:** Taller de Arquitectura de Software (TARQSW-06)  
**Proceso Crítico Evaluado:** *"Registro del expediente, generación de documentos y envío a revisión del Jefe"*  
**Máquina de Estados del Proceso:** `Borrador` ➔ `Documentos_Generados` ➔ `Pendiente_Jefe`

---

## 1. Justificación del Proceso Crítico Elegido
En la Universidad Nacional Mayor de San Marcos (UNMSM), los bolsistas están obligados mensualmente a presentar su expediente compuesto por la Declaración Jurada de No Pertenecer a Órganos de Gobierno (Ley N° 30220), su Reporte de Asistencia y su Informe de Actividades para la aprobación del estipendio. 

En un entorno real universitario con cientos de alumnos concentrando sus trámites en la última semana del mes, este proceso enfrenta picos intensos de carga, cuellos de botella por renderizado de documentos y requerimientos de notificación formal a las jefaturas de dependencia. Por ello, es el candidato idóneo para demostrar la evolución arquitectónica desde un monolito de escritorio hacia un sistema distribuido escalable, desacoplado y resiliente.

---

## 2. Evolución Arquitectónica Paso a Paso

### 📍 Etapa 0: Arquitectura Base (Monolito de Escritorio)
* **Descripción:** Aplicación cliente pesada desarrollada en Python con CustomTkinter para la interfaz gráfica y ReportLab / OpenCV embebidos directamente en el mismo proceso.
* **Problema:** Fuerte acoplamiento entre la capa de presentación (GUI) y la lógica de generación documental. Si la máquina del usuario carece de recursos, el hilo de la interfaz se congela durante el renderizado. No hay centralización ni trazabilidad del estado del expediente.
* **Archivos clave:** `src/main.py`, `src/pdf_generator.py`, `src/ui/`.

---

### 🚀 Etapa 1: Incorporación del Middleware (+4 Pts)
* **Qué se agregó:** Broker de mensajería **RabbitMQ** con cola persistente y durable `expedientes.generar_documentos`. Soporte híbrido para despliegue local mediante Docker Compose o en la nube mediante CloudAMQP (instancia gestionada gratuita vía `AMQP_URL`).
* **Por qué se eligió:** Protocolo estándar abierto AMQP 0-9-1, alta madurez, soporte nativo de colas persistentes, confirmaciones de entrega (`ACK/NACK`) y panel de monitoreo visual en tiempo real.
* **Qué problema resuelve:** Desacopla temporalmente el registro del expediente de su costoso procesamiento documental. Actúa como un amortiguador (buffer) frente a picos masivos de entrega de expedientes al cierre de mes, evitando caídas por sobrecarga.
* **Trade-off:** Introduce un componente de infraestructura adicional que debe ser administrado, monitoreado y protegido contra caídas (necesidad de alta disponibilidad o clustering en entornos empresariales).
* **Evidencia en el código:**
  - `services/api/rabbitmq.py` (Publicador con manejo de fallos y reconexión).
  - `docker-compose.yml` (Servicio `rabbitmq:3-management-alpine` con puerto 5672 y panel 15672).

---

### 🌐 Etapa 2: Servicios Web / API REST (+4 Pts)
* **Qué se agregó:** Servicio Web API en **FastAPI** ubicado en `services/api/`, con documentación interactiva estandarizada OpenAPI/Swagger UI en `/docs`.
* **Endpoints implementados:**
  - `POST /api/expedientes`: Recibe el payload del bolsista, persiste el expediente en estado `Borrador` y publica el evento en la cola RabbitMQ.
  - `GET /api/expedientes/{id}`: Consulta el estado del expediente (`Borrador`, `Documentos_Generados`, `Pendiente_Jefe`) y devuelve enlaces de descarga de los PDFs.
  - `PATCH /api/expedientes/{id}/completar`: Endpoint interno (webhook/callback) invocado por el microservicio al culminar los PDFs.
  - `POST /api/expedientes/{id}/enviar`: Valida que los documentos existan, realiza la transición a `Pendiente_Jefe` e invoca la función Serverless.
  - `GET /api/expedientes/{id}/documentos/{tipo}`: Descarga de los PDFs generados.
  - `GET /health`: Healthcheck para orquestadores y plataformas PaaS.
* **Por qué se eligió:** FastAPI ofrece alto rendimiento (asíncrono con `asyncio`/Starlette), validación automática de esquemas con Pydantic y generación automática de Swagger interactivo sin código adicional, ideal para una sustentación en vivo.
* **Qué problema resuelve:** Centraliza las reglas de negocio, valida la integridad de los datos de los estudiantes y permite que múltiples clientes (app de escritorio, app web, dispositivos móviles) consuman la misma lógica de negocio.
* **Trade-off:** Mayor sobrecarga de serialización JSON y latencia de red frente a llamadas a funciones locales en memoria.
* **Evidencia en el código:**
  - `services/api/main.py`
  - `services/api/database.py` (Persistencia simple y segura de `expedientes.json` con locks thread-safe).

---

### ☁️ Etapa 3: Despliegue Cloud (PaaS) (+4 Pts)
* **Qué se agregó:** Configuración y manifiesto de infraestructura para despliegue en **Render** (Platform as a Service - Web Service gratuito), complementado con soporte de variables de entorno y el endpoint `/health`.
* **Por qué se eligió:** Render ofrece despliegue automatizado directo desde repositorios Git, soporte nativo de Python/Docker, certificados SSL automáticos y un free tier funcional para prototipos académicos sin complejidades operativas de IaaS puro.
* **Qué problema resuelve:** Elimina la dependencia de la máquina local del desarrollador; el servicio queda disponible públicamente en Internet 24/7 con DNS seguro.
* **Trade-off:** En el tier gratuito de Render, el contenedor entra en modo reposo (*sleep*) tras inactividad, requiriendo entre 30 y 50 segundos para el *cold start* en la primera petición si no se configura un ping de keep-alive en `/health`.
* **Evidencia en el código:**
  - `render.yaml` (Manifiesto PaaS Blueprint de Render).
  - `.env.example` (Gestión centralizada de credenciales sin secretos expuestos).
  - Endpoint `GET /health` en `services/api/main.py`.

---

### 🧩 Etapa 4: Microservicio Independiente (+4 Pts)
* **Qué se agregó:** Microservicio **DocsService** en `services/docs_service/`, autónomo con su propio `requirements.txt` y `Dockerfile`. Desacoplado totalmente de bibliotecas de escritorio (CustomTkinter) y visión por computadora (OpenCV).
* **Por qué se eligió:** Arquitectura de microservicios basada en core desacoplado (`core/pdf_engine.py` y `core/utils.py`). El servicio opera como un worker consumidor en segundo plano que escucha a RabbitMQ, ejecuta el motor de maquetación vectorial de ReportLab y comunica la finalización a la API mediante callback HTTP.
* **Qué problema resuelve:** Aislamiento de fallos y escalabilidad independiente: la generación de PDFs es intensiva en CPU y memoria; al separarla en un microservicio, se puede escalar horizontalmente en múltiples réplicas de contenedores sin afectar la respuesta de la API REST.
* **Trade-off:** Comunicación entre procesos asíncrona mediante un patrón de coreografía que requiere mecanismos de reintentos, idempotencia y monitoreo de colas.
* **Evidencia en el código:**
  - `core/pdf_engine.py` (Lógica de ReportLab pura y desacoplada).
  - `services/docs_service/worker.py` (Consumidor RabbitMQ y callback HTTP).
  - `services/docs_service/Dockerfile` y `services/docs_service/requirements.txt`.

---

### ⚡ Etapa 5: Cómputo Serverless (FaaS) (+4 Pts)
* **Qué se agregó:** Función **AWS Lambda** en Python ubicada en `functions/notificar_jefe/lambda_function.py`, configurada para responder al evento de transición del expediente a `Pendiente_Jefe`.
* **Por qué se eligió:** Modelo Serverless (Function-as-a-Service): la notificación al jefe de área es un evento esporádico (ocurre una vez por expediente al mes). Mantener un servidor dedicado encendido 24/7 para esta tarea es un desperdicio de recursos económicos y de cómputo.
* **Modo DRY_RUN & Resiliencia en Examen:** Incluye un modo seguro `DRY_RUN=true` por defecto que simula el envío y registra los logs formateados con el asunto, destinatario y cuerpo del oficio. Si se configuran credenciales SMTP reales (`SMTP_HOST`, `SMTP_USER`, `SMTP_PASS`), realiza el envío de correo auténtico. Además, cuenta con un emulador HTTP independiente en `functions/notificar_jefe/local_server.py` (:8001) para pruebas locales offline.
* **Qué problema resuelve:** Costo cero mientras está en reposo (*pay-per-use*), escalabilidad elástica instantánea y desacoplamiento del canal de notificación.
* **Trade-off:** *Cold start* inherente a funciones serverless y dependencia de un entorno de ejecución efímero sin estado local persistente.
* **Evidencia en el código:**
  - `functions/notificar_jefe/lambda_function.py` (Handler nativo `lambda_handler`).
  - `functions/notificar_jefe/local_server.py` (Emulador HTTP local para contingencia).

---

## 3. Matriz de Cumplimiento de la Rúbrica de Evaluación

| # | Reto Evaluado | Componente / Tecnología | Evidencia en el Proyecto | Puntos |
|---|---------------|-------------------------|--------------------------|:------:|
| **1** | **Middleware** | RabbitMQ / CloudAMQP (cola `expedientes.generar_documentos`) | `services/api/rabbitmq.py`, `docker-compose.yml` | **4 / 4** |
| **2** | **Servicios Web/API** | FastAPI (REST + OpenAPI/Swagger en `/docs`) | `services/api/main.py`, `services/api/database.py` | **4 / 4** |
| **3** | **Cloud (PaaS)** | Render (Web Service) + `/health` + Blueprint | `render.yaml`, `.env.example`, `GET /health` | **4 / 4** |
| **4** | **Microservicio** | DocsService (Worker ReportLab desacoplado) | `services/docs_service/worker.py`, `core/pdf_engine.py` | **4 / 4** |
| **5** | **Serverless (FaaS)** | AWS Lambda con `DRY_RUN` y fallback | `functions/notificar_jefe/lambda_function.py`, `local_server.py` | **4 / 4** |
| **TOTAL** | | | | **20 / 20** |
