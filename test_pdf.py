import sys, os
sys.path.insert(0, "src")
from pdf_generator import generar_cv

# Datos expandidos para probar el comportamiento del flujo vertical (Estilo Flexbox)
datos = {
    "nombre":       "Quispe Mamani Juan Carlos",
    "correo":       "jquispe@unmsm.edu.pe",
    "escuela":      "Derecho y Ciencia Política",
    "departamento": "Derecho Público",
    "categoria":    "Principal / DE",
    "foto_path":    None,
    "formacion": (
        "Doctorado en Derecho Constitucional, Universidad Nacional Mayor de San Marcos (2010)\n"
        "Maestría en Derecho Público con mención en Derecho Procesal, Pontificia Universidad Católica del Perú (2003)\n"
        "Bachiller en Derecho y Ciencia Política, Universidad Nacional Mayor de San Marcos (1998)\n"
        "Diplomado de Especialización en Justicia Constitucional y Procesos Constitucionales, Academia de la Magistratura (2012)\n"
        "Curso de Alta Especialización en Argumentación Jurídica y Litigación Oral, Universidad de Alicante (2015)"
    ),
    "trayectoria": (
        "Abogado constitucionalista con más de 25 años de sólida experiencia liderando la defensa de derechos fundamentales "
        "y litigios de alta complejidad ante el Tribunal Constitucional y el Poder Judicial. Investigador activo en "
        "derecho público, con múltiples publicaciones indexadas sobre reforma del Estado, control de convencionalidad "
        "y garantías procesales en el modelo peruano. Conferencista nacional e internacional en materia de "
        "procesos de amparo, hábeas corpus y derecho procesal constitucional comparado."
    ),
    "experiencia": (
        "Docente Principal de Derecho Constitucional, Universidad Nacional Mayor de San Marcos (2005–presente)\n"
        "Consultor Externo de la Comisión de Constitución y Reglamento, Congreso de la República (2018–2021)\n"
        "Asesor Legal de la Alta Dirección, Ministerio de Justicia y Derechos Humanos (2011–2014)\n"
        "Asesor Legal Principal de la Mesa Directiva, Congreso de la República (2001–2004)\n"
        "Abogado Litigante Senior, Estudio Jurídico Quispe & Asociados (1999–2001)\n"
        "Asistente Judicial de Sala Constitucional, Corte Superior de Justicia de Lima (1996–1998)"
    ),
}

os.makedirs("output", exist_ok=True)
logo = os.path.join("assets", "logofdcp.png")
ruta = generar_cv(datos, "output/CV_prueba_grande.pdf", logo_path=logo)
print(f"✅ CV con datos expandidos generado con éxito en: {ruta}")