# 🎓 Generador de CVs Docentes — UNMSM
### Facultad de Derecho y Ciencia Política

Sistema de escritorio y web para generar CVs en PDF para docentes universitarios,
a partir de un formulario Google Forms o ingreso manual por el personal administrativo.

## 🚧 Estado del proyecto
Funcional. La interfaz web permite procesar descargas, generar CVs y resolver
casos individuales desde la tabla. La GUI de escritorio se conserva como alternativa.

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

## 🌐 Flujo de la aplicación web

Ejecuta el servidor desde la raíz del proyecto:

```
python web_app.py
```

Después abre `http://127.0.0.1:8000`.

La carga masiva web funciona por etapas:

1. Procesar el Excel.
2. Descargar las imágenes.
3. Generar los CVs en paralelo.

La tabla incluye:

- Paginación configurable de 10, 15, 20, 25 o 50 filas.
- Búsqueda por ID, nombre o estado.
- Filtros para todos, registros sin enlace y descargas con error.
- Reintento individual de una descarga fallida.
- Carga manual de una imagen local para registros sin enlace.
- Generación individual de un CV excepcional.
- Vista previa modal de imágenes y PDFs.
- Navegación con flechas entre imágenes y CVs.
- Progreso independiente para descargas y generación de CVs.
- Guardado de todos los PDFs en una carpeta elegida por el usuario.
- Limpieza de imágenes, PDFs y Excels limpios generados.

Al abrir la aplicación, si encuentra resultados anteriores pregunta si se desean
conservar. Si se conservan, carga en la tabla el Excel limpio más reciente junto
con las imágenes y CVs disponibles. El navegador no puede rellenar visualmente el
selector de archivos por seguridad, aunque la aplicación sí puede continuar usando
el Excel restaurado en el servidor.

Nota conocida: las etapas reutilizan el Excel limpio durante una misma sesión,
pero pueden quedar Excels limpios históricos en `output/registros` después de varias
sesiones o reinicios. La opción **Finalizar y limpiar** permite eliminarlos junto
con las imágenes y PDFs generados.

## ✅ Decisiones de arquitectura
- Sin APIs de Google (sin Google Cloud Console, sin tarjetas de crédito)
- Sin base de datos externa
- Sin servidor, todo corre localmente en la PC del personal
- Las fotos se conectan con los registros por el campo "Apellidos y Nombres"
- Si una foto no se encuentra, el sistema alerta y permite seleccionarla manualmente
- Los CVs con foto faltante se pueden previsualizar antes de guardar definitivamente
- Las descargas se guardan primero en archivos temporales y se validan como imágenes
        completas antes de reemplazar el archivo final
- Los resultados de la aplicación web se conservan localmente en `output/`

## 🛠️ Tecnologías
- Python 3
- customtkinter (GUI)
- FastAPI + Uvicorn (interfaz web local)
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
| 🌐 Aplicación web | Flujo masivo con seguimiento, filtros, previsualización y acciones individuales |

## 📁 Estructura del proyecto

    cv_generator/
    ├── src/
    │   ├── main.py           # GUI principal
    │   ├── pdf_generator.py  # Generador de PDF
    │   └── data_reader.py    # Lector de Excel
        ├── web_app.py             # Servidor FastAPI de la interfaz web
        ├── web/
        │   ├── templates/         # Plantillas HTML
        │   └── static/            # JavaScript y estilos
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
```

Nota: la carpeta `venv/` ya está listada en `.gitignore`. Si por error ya la añadiste al repositorio, quítala del índice antes de volver a subir:

```
git rm -r --cached venv
git commit -m "Remove venv from repo"
```

## ▶️ Uso

Ejecuta la aplicación con el intérprete del entorno virtual activo:

```
python src/main.py
```

Para usar la interfaz web:

```
python web_app.py
```

La carpeta `output/` contiene los resultados locales:

- `output/imagenes/`: imágenes descargadas o agregadas manualmente.
- `output/registros/`: Excels transformados y limpios.
- `output/logs/`: registros de descargas.
- `output/*.pdf`: CVs generados.

## 👥 Equipo
- Edgardo Barboza — Desarrollo / integración
- Maximo Roman — Google Forms