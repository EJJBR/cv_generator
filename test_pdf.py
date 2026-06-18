import sys, os
sys.path.insert(0, "src")
from pdf_generator import generar_cv

datos = {
    "nombre":       "Quispe Mamani Juan Carlos",
    "correo":       "jquispe@unmsm.edu.pe",
    "escuela":      "Derecho y Ciencia Política",
    "departamento": "Derecho Público",
    "categoria":    "Principal / DE",
    "foto_path":    None,
    "formacion":    "Doctorado en Derecho Constitucional, UNMSM (2010)\nMaestría en Derecho Público, PUCP (2003)\nBachiller en Derecho, UNMSM (1998)",
    "trayectoria":  "Abogado constitucionalista con más de 25 años de experiencia en derecho público y litigios ante el Tribunal Constitucional.",
    "experiencia":  "Docente principal UNMSM (2005–presente)\nAsesor legal, Congreso de la República (2001–2004)\nAbogado litigante, Estudio Jurídico Quispe & Asociados (1999–2001)",
}

os.makedirs("output", exist_ok=True)
logo = os.path.join("assets", "logofdcp.png")
ruta = generar_cv(datos, "output/CV_prueba.pdf", logo_path=logo)
print(f"✅ CV generado: {ruta}")