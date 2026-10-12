# ⏱️ Guion de Demostración en Vivo (2 Minutos)
## Examen de Arquitectura de Software — UNMSM (TARQSW-06)
**Proceso Crítico:** Tramitación del pago de bolsistas UNMSM (`Borrador` ➔ `Documentos_Generados` ➔ `Pendiente_Jefe`).

---

## 🕒 Cronograma de la Presentación (120 Segundos)

### [00:00 - 00:20] Introducción y Contexto del Proceso
> *"Buenos días profesor y compañeros. Presentamos la evolución arquitectónica del sistema de expedientes de pago para bolsistas de la UNMSM. Evaluamos un único proceso crítico: el registro del bolsista, la generación de su Declaración Jurada e Informe de Actividades, y su envío a revisión de jefatura. Pasamos de un monolito de escritorio a una arquitectura distribuida que cumple los 5 retos de la rúbrica."*

### [00:20 - 00:45] Reto 1 (Middleware) y Reto 2 (API REST)
1. Abrir terminal de PowerShell y ejecutar el script automatizado E2E:
   ```powershell
   python demo/test_e2e.py
   ```
2. **Explicación al jurado:**
   > *"Nuestra API desarrollada en FastAPI recibe la solicitud del bolsista y crea el expediente en estado **Borrador**. Inmediatamente, para no bloquear la API con la pesada generación de PDFs, publica un mensaje persistente en nuestro **Middleware RabbitMQ** en la cola `expedientes.generar_documentos`. Esto garantiza absorción ante picos de entrega al cierre de mes."*

### [00:45 - 01:10] Reto 4 (Microservicio) y Transición de Estado
1. Apuntar a la salida del terminal donde se visualiza la generación de documentos:
   > *"El **Microservicio DocsService**, que corre como un worker independiente y desacoplado de la interfaz gráfica, consume el mensaje de RabbitMQ, ejecuta el motor ReportLab y almacena los dos PDFs. Luego, mediante un callback HTTP PATCH a la API, actualiza el estado a **Documentos_Generados**."*
2. *(Opcional)* Abrir Swagger en el navegador: [http://localhost:8000/docs](http://localhost:8000/docs) para mostrar los endpoints y los esquemas validados con Pydantic.

### [01:10 - 01:35] Reto 5 (Serverless FaaS) y Reto 3 (Cloud PaaS)
1. Apuntar al paso final en el terminal:
   > *"Al aprobar el expediente mediante el endpoint `POST /enviar`, se valida la existencia de los PDFs y pasa al estado **Pendiente_Jefe**. En este momento se dispara nuestra función **Serverless AWS Lambda**, la cual notifica vía correo formal a la jefatura con los datos del expediente. Cuenta con modo `DRY_RUN` para garantizar disponibilidad instantánea durante la demo."*
2. **Justificación Cloud PaaS:**
   > *"La API está configurada y lista para despliegue PaaS en Render mediante el archivo `render.yaml`, cumpliendo el estándar de observabilidad con el endpoint `/health`."*

### [01:35 - 02:00] Conclusión y Preguntas
> *"En conclusión, logramos una arquitectura altamente desacoplada, con tolerancia a fallos mediante colas, escalabilidad independiente de componentes intensivos y computación serverless de costo cero en reposo. Quedamos atentos a sus preguntas."*

---

## 🛡️ Plan B: Contingencia ante Fallas Técnicas (A Prueba de Todo)

| Escenario de Falla | Causa Posible | Solución Inmediata (Plan B) |
|---|---|---|
| **Se cae la conexión a Internet** | Falla de red en el aula | La demo funciona **100% en local** con `docker-compose up` o ejecutando `python demo/test_e2e.py`, el cual incluye un fallback autónomo en memoria. |
| **RabbitMQ no inicia** | Docker Desktop cerrado | Ejecuta `python demo/test_e2e.py`. Si detecta que no hay broker activo, ejecutará el modo directo de demostración mostrando los estados y generando los PDFs locales. |
| **Falla de credenciales de correo** | Bloqueo SMTP de Gmail | El parámetro `DRY_RUN=true` en `.env` simula la notificación y registra los logs formateados de la función AWS Lambda sin arrojar error. |
| **El jurado pide probar la App de Escritorio** | Interés en el monolito original | Ejecuta `python src/main.py`. La app de escritorio original sigue funcionando intacta e incluye el botón *"☁️ Enviar a API REST"* para conectar con la arquitectura distribuida. |
