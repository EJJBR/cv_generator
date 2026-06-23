# 🎓 Generador de CVs Docentes — UNMSM
### Facultad de Derecho y Ciencia Política

Sistema de escritorio para generar CVs en PDF para docentes universitarios,
a partir de un formulario Google Forms o ingreso manual por el personal administrativo.

## 🚧 Estado del proyecto
En desarrollo

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

## ✅ Decisiones de arquitectura
- Sin APIs de Google (sin Google Cloud Console, sin tarjetas de crédito)
- Sin base de datos externa
- Sin servidor, todo corre localmente en la PC del personal
- Las fotos se conectan con los registros por el campo "Apellidos y Nombres"
- Si una foto no se encuentra, el sistema alerta y permite seleccionarla manualmente
- Los CVs con foto faltante se pueden previsualizar antes de guardar definitivamente

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

## 👥 Equipo
- Edgardo Barboza — Desarrollo
- Maximo Roman — Google Forms / integración