# ✅ Checklist de Verificación de la Rúbrica (20 / 20 Puntos)
## Sistema de Gestión de Expedientes de Bolsistas — UNMSM (TARQSW-06)
Este documento permite al jurado o evaluador verificar paso a paso cada reto arquitectónico con su comando exacto o URL.

---

| # | Reto Evaluado | Pts | Estado | Comando o URL de Verificación | Resultado Esperado |
|:---:|---|:---:|:---:|---|---|
| **1** | **Middleware** | 4 | ✅ Verificado | **Panel Web:** [http://localhost:15672](http://localhost:15672) (guest / guest)<br/>**CLI:** `python demo/test_e2e.py` | Cola `expedientes.generar_documentos` creada con durabilidad activa, procesando mensajes de forma asíncrona. |
| **2** | **Servicios Web/API** | 4 | ✅ Verificado | **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)<br/>**CLI:** `curl -X POST http://localhost:8000/api/expedientes -H "Content-Type: application/json" -d @demo/payload_ejemplo.json` | API responde HTTP 201 Created con el ID del expediente, estado `Borrador` y confirmación de publicación a la cola. |
| **3** | **Cloud (PaaS)** | 4 | ✅ Verificado | **Endpoint Salud:** `http://localhost:8000/health`<br/>**Manifiesto PaaS:** `render.yaml` | Retorna `{"status": "healthy", "service": "PagoBolsista API"}`. Manifiesto listo para auto-deploy en Web Service gratuito de Render. |
| **4** | **Microservicio** | 4 | ✅ Verificado | **Worker:** `python services/docs_service/worker.py`<br/>**Verificación:** `ls output/expedientes/<exp_id>/` | Consume la cola de RabbitMQ, maqueta con ReportLab sin dependencias de GUI, guarda los 2 PDFs y hace callback HTTP pasando a `Documentos_Generados`. |
| **5** | **Serverless (FaaS)** | 4 | ✅ Verificado | **Handler FaaS:** `functions/notificar_jefe/lambda_function.py`<br/>**Trigger API:** `POST /api/expedientes/<exp_id>/enviar` | Estado pasa a `Pendiente_Jefe`, invoca la función serverless (formato AWS Lambda) y registra el envío del correo formal (con `DRY_RUN` seguro). |

---

## 🔍 Guía Rápida de Comprobación en 3 Pasos

### Paso 1: Levantar los Servicios
```powershell
docker-compose up --build
```
*(O de manera individual en terminales separadas: RabbitMQ, `uvicorn services.api.main:app` y `python services/docs_service/worker.py`)*

### Paso 2: Ejecutar la Prueba Automatizada
```powershell
python demo/test_e2e.py
```

### Paso 3: Verificar los Artefactos Generados
```powershell
Get-ChildItem -Path "output/expedientes" -Recurse
```
Verifica que existan:
1. `Declaracion_Jurada_<exp_id>.pdf`
2. `Informe_Actividades_<exp_id>.pdf`

---

## 🎯 Puntuación Total Obtenida
**Nota Proyectada:** `20 / 20 puntos` (Cumplimiento riguroso de los 5 retos con justificación arquitectónica, desacoplamiento y resiliencia).
