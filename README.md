<<<<<<< Updated upstream
# 🎓 Generador de CVs Docentes — UNMSM
### Facultad de Derecho y Ciencia Política

Sistema de escritorio para generar CVs en PDF para docentes universitarios,
a partir de un formulario Google Forms o ingreso manual por el personal administrativo.
=======
# 🎓 Sistema de Gestión de Expedientes de Bolsistas — UNMSM
### Arquitectura Distribuida Evolutiva — Taller de Arquitectura de Software (TARQSW-06)

Sistema integral para la tramitación mensual del pago de bolsistas en la Universidad Nacional Mayor de San Marcos (UNMSM). Evolucionado desde un monolito de escritorio hacia una **arquitectura distribuida desacoplada, resiliente y orientada a eventos**, cumpliendo rigurosamente los 5 retos de la rúbrica de examen (20 pts).
>>>>>>> Stashed changes

## 🚧 Estado del proyecto
En desarrollo

<<<<<<< Updated upstream
## 📋 Descripción
Los docentes llenan un Google Form con sus datos personales, académicos y foto carné
usando obligatoriamente su correo institucional (@unmsm.edu.pe). El personal administrativo
descarga el Excel y la carpeta de fotos al cerrar el periodo de registro, ejecuta el programa
y genera los CVs en PDF automáticamente.

## 🔄 Flujo general

    [Periodo abierto - primeras 3 semanas del ciclo (ejemplo)]
    Docentes llenan Google Forms con correo institucional
            ↓
    [Periodo cerrado]
    Personal descarga Excel + carpeta de fotos desde Drive
    y los ubica en cualquier lugar de su PC (Descargas, Escritorio, USB, etc.)
            ↓
    En la app selecciona:
        1. El archivo Excel descargado
        2. La carpeta de fotos descargada
            ↓
    App conecta cada registro con su foto por nombre del docente
    Si no encuentra una foto → alerta + selección manual
            ↓
    App genera todos los PDFs automáticamente
            ↓
    Personal limpia el Sheets manualmente para el siguiente ciclo
=======
## 🏆 Rúbrica de Evaluación (20 / 20 Pts)

| # | Reto | Implementación y Justificación | Archivos Clave | Pts |
|:---:|---|---|---|:---:|
| **1** | **Middleware** | **RabbitMQ** (cola `expedientes.generar_documentos`). Amortigua picos de demanda a fin de mes y desacopla la API del proceso pesado de renderizado. Soporta CloudAMQP (`AMQP_URL`). | `services/api/rabbitmq.py`<br/>`docker-compose.yml` | **4** |
| **2** | **Servicios Web / API** | **FastAPI** en `services/api/`. Implementa el ciclo de estados `Borrador` ➔ `Documentos_Generados` ➔ `Pendiente_Jefe`. Validación estricta con Pydantic y Swagger UI en `/docs`. | `services/api/main.py`<br/>`services/api/database.py` | **4** |
| **3** | **Cloud (PaaS)** | Configuración para despliegue en **Render** (Web Service gratuito) con blueprint declarativo `render.yaml`, variables `.env` y endpoint de monitoreo `/health`. | `render.yaml`<br/>`.env.example`<br/>`GET /health` | **4** |
| **4** | **Microservicio** | **DocsService** en `services/docs_service/`. Worker independiente con Dockerfile propio. Consume RabbitMQ, genera la Declaración Jurada e Informe con ReportLab y actualiza el estado por callback HTTP a la API. | `services/docs_service/worker.py`<br/>`core/pdf_engine.py` | **4** |
| **5** | **Serverless (FaaS)** | **AWS Lambda** en `functions/notificar_jefe/`. Disparada al pasar a `Pendiente_Jefe` para notificar al Jefe de Área. Modo seguro `DRY_RUN` para la exposición y emulador HTTP local. | `functions/notificar_jefe/lambda_function.py`<br/>`local_server.py` | **4** |
>>>>>>> Stashed changes

## ✅ Decisiones de arquitectura
- Sin APIs de Google (sin Google Cloud Console, sin tarjetas de crédito)
- Sin base de datos externa
- Sin servidor, todo corre localmente en la PC del personal
- Las fotos se conectan con los registros por el campo "Apellidos y Nombres"
- Si una foto no se encuentra, el sistema alerta y permite seleccionarla manualmente
- Los CVs con foto faltante se pueden previsualizar antes de guardar definitivamente

<<<<<<< Updated upstream
## 🛠️ Tecnologías
- Python 3
- customtkinter (GUI)
- ReportLab (generación de PDF)
- openpyxl (lectura de Excel)
- Pillow (procesamiento de imagen)

## 🗂️ Campos del formulario
| Campo | Tipo |
|---|---|
| Apellidos y Nombres | Texto corto |
| Foto carné | Subida de imagen |
| Correo Institucional | Texto corto |
| Escuela Profesional | Texto corto |
| Departamento Académico | Texto corto |
| Categoría / Clase | Texto corto |
| Formación Académica 1, 2, 3 | Texto corto |
| Trayectoria | Párrafo |
| Experiencia Laboral 1, 2, 3 | Texto corto |

## 🖥️ Modos de la aplicación
| Modo | Descripción |
|---|---|
| 📋 Carga masiva | Carga el Excel descargado del Forms y genera todos los CVs |
| ✏️ Individual manual | El personal ingresa los datos de un docente directamente |

## 📁 Estructura del proyecto

    cv_generator/
    ├── src/
    │   ├── main.py           # GUI principal
    │   ├── pdf_generator.py  # Generador de PDF
    │   └── data_reader.py    # Lector de Excel
    ├── assets/               # Logo de la facultad
    ├── output/               # PDFs generados (ignorado en git)
    ├── requirements.txt
    └── README.md

## ⚙️ Instalación

Linux / macOS (Bash):

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Windows (CMD):

```
python -m venv venv
venv\Scripts\activate.bat
python -m pip install -r requirements.txt
```

Windows (PowerShell):

```
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
=======
## 🔄 Proceso Crítico y Ciclo de Estados
El sistema gestiona el proceso crítico: **"Registro del expediente, generación de documentos y envío a revisión del Jefe"**:

```
[Borrador]  ───────────────>  [Documentos_Generados]  ───────────────>  [Pendiente_Jefe]
(POST /api/expedientes)       (DocsService vía Callback)              (POST .../enviar + FaaS)
```

1. **Borrador:** El bolsista registra sus datos en la API REST o desde la app de escritorio. Se publica el mensaje a la cola RabbitMQ.
2. **Documentos_Generados:** El microservicio `DocsService` consume el mensaje, maqueta los PDFs con ReportLab, los almacena en `output/expedientes/{id}/` y notifica a la API vía HTTP PATCH.
3. **Pendiente_Jefe:** El usuario confirma el envío. La API valida que los documentos existan, actualiza el estado y dispara la función Serverless FaaS (AWS Lambda) para notificar formalmente a la jefatura.

---

## 📁 Estructura del Proyecto

```
PagoBolsista-Generator/
├── core/                               # 🧠 Motor puro desacoplado (Sin dependencias de GUI)
│   ├── __init__.py
│   ├── utils.py                        # Sanitización segura para ReportLab
│   └── pdf_engine.py                   # Generación de Decl. Jurada e Informe de Actividades
├── services/
│   ├── api/                            # 🌐 Reto 2 & 3: API REST (FastAPI) & Cloud PaaS
│   │   ├── main.py                     # Endpoints, Swagger UI, transiciones de estado
│   │   ├── database.py                 # Persistencia JSON thread-safe (expedientes.json)
│   │   ├── rabbitmq.py                 # Reto 1: Publicador a cola RabbitMQ
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── docs_service/                   # 🧩 Reto 4: Microservicio de Generación de PDFs
│       ├── worker.py                   # Consumidor de RabbitMQ + Callback HTTP a la API
│       ├── requirements.txt            # Dependencias ligeras (sin CustomTkinter/OpenCV)
│       └── Dockerfile
├── functions/
│   └── notificar_jefe/                 # ⚡ Reto 5: Serverless FaaS (AWS Lambda)
│       ├── lambda_function.py          # Handler AWS Lambda nativo (Modo DRY_RUN + SMTP)
│       └── local_server.py             # Emulador local HTTP (:8001) para contingencia
├── demo/                               # 🚀 Automatización y pruebas de sustentación
│   ├── payload_ejemplo.json            # Datos de prueba ficticios (Privacidad protegida)
│   ├── test_e2e.py                     # Script E2E automatizado de punta a punta
│   └── run_demo.ps1                    # Menú interactivo en PowerShell
├── docs/                               # 📚 Documentación formal de arquitectura
│   ├── ARQUITECTURA_EVOLUCION.md       # Justificación profunda por cada etapa y trade-offs
│   ├── GUION_DEMO.md                   # Guion de 2 minutos para el ponente + Plan B
│   ├── CHECKLIST_RUBRICA.md            # Verificación paso a paso para el jurado
│   └── diagrams/                       # Diagramas PlantUML (.puml) y renderizados
│       ├── evolucion_arquitectura.puml
│       ├── arquitectura_final.puml
│       └── render_diagrams.py
├── src/                                # 🖥️ Aplicación de escritorio original (Monolito)
│   ├── main.py                         # GUI en CustomTkinter (Sigue funcionando intacta)
│   ├── pdf_generator.py                # Adaptador que delega al módulo core/
│   └── ui/view_declaracion.py          # Incluye botón "☁️ Enviar a API REST"
├── docker-compose.yml                  # Orquestación de RabbitMQ + API + DocsService
├── render.yaml                         # Blueprint de despliegue PaaS en Render
├── .env.example                        # Plantilla de variables de entorno seguras
└── requirements.txt                    # Dependencias generales del proyecto
```

---

## ⚡ Guía de Ejecución Rápida (Windows + PowerShell)

### Opción 1: Todo Automatizado con Docker Compose (Recomendada)
Para levantar la arquitectura completa (RabbitMQ + API + Microservicio):
```powershell
docker-compose up --build
```
* **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **Panel de RabbitMQ:** [http://localhost:15672](http://localhost:15672) (Usuario: `guest`, Password: `guest`)
* **Endpoint de Salud PaaS:** [http://localhost:8000/health](http://localhost:8000/health)

En otra terminal, ejecuta la prueba automatizada del proceso crítico:
```powershell
python demo/test_e2e.py
>>>>>>> Stashed changes
```

Nota: la carpeta `venv/` ya está listada en `.gitignore`. Si por error ya la añadiste al repositorio, quítala del índice antes de volver a subir:

<<<<<<< Updated upstream
```
git rm -r --cached venv
git commit -m "Remove venv from repo"
```

## ▶️ Uso

Ejecuta la aplicación con el intérprete del entorno virtual activo:

```
python src/main.py
```

## 👥 Equipo
- Edgardo Barboza — Desarrollo
- Maximo Roman — Google Forms / integración
=======
### Opción 2: Ejecución Modular (Terminales Independientes)

1. **Instalar dependencias del entorno virtual:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   pip install -r services/api/requirements.txt
   ```

2. **Terminal 1: Iniciar API REST:**
   ```powershell
   uvicorn services.api.main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Terminal 2: Iniciar Microservicio DocsService (Consumidor):**
   ```powershell
   python services/docs_service/worker.py
   ```

4. **Terminal 3: Iniciar Emulador Serverless (Opcional):**
   ```powershell
   python functions/notificar_jefe/local_server.py
   ```

---

### Opción 3: Menú Interactivo en PowerShell
Ejecuta el script facilitador de la demo:
```powershell
.\demo\run_demo.ps1
```

---

### Opción 4: Ejecutar la Aplicación de Escritorio
La aplicación de escritorio original no se rompe y se puede ejecutar normalmente:
```powershell
python src/main.py
```
> En la pantalla de **Declaración Jurada**, cuenta con el botón **`☁️ Enviar a API REST (Distribuido)`** para enviar los datos directamente a la API en vivo.

---

## 🛡️ Privacidad y Seguridad de Datos
* Se agregaron `user_profile.json` y `expedientes.json` a `.gitignore` para evitar la filtración de datos personales reales (DNI, domicilios, firmas).
* Las demostraciones y pruebas automatizadas utilizan exclusivamente `demo/payload_ejemplo.json` con datos simulados de estudiantes de la UNMSM.
>>>>>>> Stashed changes
