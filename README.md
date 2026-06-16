# 🎓 Generador de CVs Docentes — UNMSM

Sistema de escritorio para generar CVs en PDF para docentes universitarios,
a partir de un formulario Google Forms o carga masiva desde Excel.

## 🚧 Estado del proyecto
En desarrollo

## 📋 Descripción
- Los docentes llenan un Google Form con sus datos y foto carné
- El personal administrativo ejecuta el programa y genera los PDFs automáticamente
- Soporta generación individual y carga masiva desde Excel

## 🛠️ Tecnologías
- Python 3
- customtkinter (GUI)
- ReportLab (generación de PDF)
- openpyxl (lectura de Excel)
- Pillow (procesamiento de imagen)
- requests (descarga de fotos desde Drive)

## 📁 Estructura del proyecto

    cv_generator/
    ├── src/
    │   ├── main.py           # GUI principal
    │   ├── pdf_generator.py  # Generador de PDF
    │   └── data_reader.py    # Lector de Sheets/Excel
    ├── assets/               # Logo de la facultad
    ├── output/               # PDFs generados (ignorado en git)
    ├── requirements.txt
    └── README.md

## ⚙️ Instalación
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## ▶️ Uso
```bash
python src/main.py
```

## 👥 Equipo
- [Edgardo Barboza] — Desarrollo
- [Maximo Roman] — Google Forms / integración