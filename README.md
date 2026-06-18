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

    [Periodo abierto - primeras 3 semanas del ciclo]
    Docentes llenan Google Forms con correo institucional
            ↓
    [Periodo cerrado]
    Personal descarga Excel + carpeta de fotos desde Drive
            ↓
    App genera PDFs automáticamente
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

    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

## ▶️ Uso

    python src/main.py

## 👥 Equipo
- Edgardo Barboza — Desarrollo
- Maximo Roman — Google Forms / integración