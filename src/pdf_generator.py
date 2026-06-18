"""
pdf_generator.py
Genera el CV en PDF con el diseño de dos columnas:
- Izquierda: azul oscuro con foto circular y datos de contacto
- Derecha: blanca con logo, formación, trayectoria y experiencia
"""

import os
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image as PILImage


# ── Colores ─────────────────────────────────────────────────────────────────
AZUL_OSCURO = colors.HexColor("#1B3A6B")
AZUL_TITULO = colors.HexColor("#2B5DA1")
BLANCO      = colors.white
GRIS_TEXTO  = colors.HexColor("#333333")
AZUL_LABEL  = colors.HexColor("#7FB3E8")

# ── Medidas ──────────────────────────────────────────────────────────────────
W, H       = A4                  # 595 x 842 pts
COL_IZQ    = W * 0.36            # ancho columna izquierda
MARGEN     = 14                  # margen interno general
X_DER      = COL_IZQ + MARGEN   # x inicio columna derecha
ANCHO_DER  = W - COL_IZQ - MARGEN * 2


# ── Utilidades de texto ──────────────────────────────────────────────────────
def _wrap_text(c, texto, x, y, ancho, fuente, tamanio, color, interlinea=13):
    """Dibuja texto con salto de línea automático. Retorna Y final."""
    from reportlab.pdfbase.pdfmetrics import stringWidth
    c.setFillColor(color)
    c.setFont(fuente, tamanio)
    palabras = texto.split()
    linea = ""
    for palabra in palabras:
        prueba = (linea + " " + palabra).strip()
        if stringWidth(prueba, fuente, tamanio) <= ancho:
            linea = prueba
        else:
            if linea:
                c.drawString(x, y, linea)
                y -= interlinea
            linea = palabra
    if linea:
        c.drawString(x, y, linea)
        y -= interlinea
    return y


def _bullets(c, texto, x, y, ancho, color, tamanio=8):
    """Dibuja lista de bullets. Cada ítem separado por salto de línea."""
    items = [i.strip() for i in texto.strip().split("\n") if i.strip()]
    for item in items:
        y = _wrap_text(c, "•  " + item, x, y, ancho,
                       "Helvetica", tamanio, color, 12)
        y -= 2
    return y


def _seccion_der(c, titulo, y):
    """Dibuja título de sección en columna derecha con línea azul."""
    c.setFillColor(AZUL_TITULO)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(X_DER, y, titulo)
    y -= 5
    c.setStrokeColor(AZUL_TITULO)
    c.setLineWidth(0.8)
    c.line(X_DER, y, X_DER + ANCHO_DER, y)
    return y - 10


def _seccion_izq(c, titulo, valor, y):
    """Dibuja label + valor en columna izquierda."""
    c.setFillColor(AZUL_LABEL)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(MARGEN, y, titulo.upper())
    y -= 12
    y = _wrap_text(c, valor, MARGEN, y,
                   COL_IZQ - MARGEN * 2,
                   "Helvetica", 8, BLANCO, 11)
    return y - 10


# ── Foto circular ────────────────────────────────────────────────────────────
def _foto_circular(c, foto_path, cx, cy, radio):
    """Dibuja la foto recortada en círculo."""
    try:
        img = PILImage.open(foto_path).convert("RGB")
        # recorte cuadrado centrado
        w, h  = img.size
        lado  = min(w, h)
        left  = (w - lado) // 2
        top   = (h - lado) // 2
        img   = img.crop((left, top, left + lado, top + lado))
        img   = img.resize((300, 300), PILImage.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        buf.seek(0)

        # clip circular
        path = c.beginPath()
        path.circle(cx, cy, radio)
        c.saveState()
        c.clipPath(path, stroke=0, fill=0)
        c.drawImage(ImageReader(buf),
                    cx - radio, cy - radio,
                    width=radio * 2, height=radio * 2,
                    preserveAspectRatio=True, mask="auto")
        c.restoreState()

    except Exception:
        _foto_placeholder(c, cx, cy, radio)

    # borde blanco siempre
    c.setStrokeColor(BLANCO)
    c.setLineWidth(3)
    c.circle(cx, cy, radio, stroke=1, fill=0)


def _foto_placeholder(c, cx, cy, radio):
    """Silueta genérica cuando no hay foto."""
    c.setFillColor(colors.HexColor("#B0C4DE"))
    c.circle(cx, cy, radio, stroke=0, fill=1)
    c.setFillColor(colors.HexColor("#778899"))
    c.circle(cx, cy + radio * 0.35, radio * 0.28, stroke=0, fill=1)
    path = c.beginPath()
    path.arc(cx - radio * 0.45, cy - radio * 0.15,
             cx + radio * 0.45, cy + radio * 0.55,
             startAng=0, extent=180)
    path.close()
    c.drawPath(path, stroke=0, fill=1)


# ── Generador principal ──────────────────────────────────────────────────────
def generar_cv(datos: dict, ruta_salida: str, logo_path: str = None) -> str:
    """
    Genera el PDF del CV.

    datos: dict con claves:
        nombre, correo, escuela, departamento, categoria,
        formacion, trayectoria, experiencia, foto_path

    ruta_salida: ruta completa del PDF a generar
    logo_path: ruta al logo de la facultad (assets/logofdcp.png)

    Retorna la ruta del PDF generado.
    """
    c = canvas.Canvas(ruta_salida, pagesize=A4)

    # ── Fondos ───────────────────────────────────────────────────────────────
    c.setFillColor(AZUL_OSCURO)
    c.rect(0, 0, COL_IZQ, H, stroke=0, fill=1)
    c.setFillColor(BLANCO)
    c.rect(COL_IZQ, 0, W - COL_IZQ, H, stroke=0, fill=1)

    # ── Foto ─────────────────────────────────────────────────────────────────
    foto_cx = COL_IZQ / 2
    foto_cy = H - 115
    radio   = 70

    foto_path = datos.get("foto_path")
    if foto_path and os.path.exists(foto_path):
        _foto_circular(c, foto_path, foto_cx, foto_cy, radio)
    else:
        _foto_placeholder(c, foto_cx, foto_cy, radio)
        c.setStrokeColor(BLANCO)
        c.setLineWidth(3)
        c.circle(foto_cx, foto_cy, radio, stroke=1, fill=0)

    # ── Nombre ───────────────────────────────────────────────────────────────
    y_nombre = foto_cy - radio - 18
    nombre   = datos.get("nombre", "").upper()
    partes   = nombre.split()
    lineas   = []
    linea    = []
    for p in partes:
        linea.append(p)
        if len(linea) >= 3:
            lineas.append(" ".join(linea))
            linea = []
    if linea:
        lineas.append(" ".join(linea))

    c.setFillColor(BLANCO)
    c.setFont("Helvetica-Bold", 13)
    for ln in lineas:
        c.drawCentredString(COL_IZQ / 2, y_nombre, ln)
        y_nombre -= 17

    # ── Datos columna izquierda ───────────────────────────────────────────────
    y_izq = y_nombre - 15
    y_izq = _seccion_izq(c, "Correo institucional",
                          datos.get("correo", "—"), y_izq)
    y_izq = _seccion_izq(c, "Escuela Profesional",
                          datos.get("escuela", "—"), y_izq)
    y_izq = _seccion_izq(c, "Departamento Académico",
                          datos.get("departamento", "—"), y_izq)
    y_izq = _seccion_izq(c, "Categoría / Clase",
                          datos.get("categoria", "—"), y_izq)

    # ── Logo facultad ─────────────────────────────────────────────────────────
    y_der = H - 20
    if logo_path and os.path.exists(logo_path):
        try:
            c.drawImage(ImageReader(logo_path),
                        X_DER, H - 85,
                        width=ANCHO_DER, height=70,
                        preserveAspectRatio=True, mask="auto")
            y_der = H - 95
        except Exception:
            y_der = H - 30
    else:
        c.setFillColor(AZUL_OSCURO)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(X_DER, y_der - 10, "UNMSM")
        c.setFont("Helvetica", 9)
        c.setFillColor(GRIS_TEXTO)
        c.drawString(X_DER, y_der - 24, "Facultad de Derecho y Ciencia Política")
        y_der = H - 55

    # ── Secciones columna derecha ─────────────────────────────────────────────
    y_der = _seccion_der(c, "Formación Académica", y_der)
    formacion = datos.get("formacion", "")
    if formacion:
        y_der = _bullets(c, formacion, X_DER, y_der, ANCHO_DER, GRIS_TEXTO)
    y_der -= 12

    y_der = _seccion_der(c, "Trayectoria", y_der)
    trayectoria = datos.get("trayectoria", "")
    if trayectoria:
        y_der = _wrap_text(c, trayectoria, X_DER, y_der, ANCHO_DER,
                           "Helvetica", 8, GRIS_TEXTO, 12)
    y_der -= 12

    y_der = _seccion_der(c, "Experiencia Laboral", y_der)
    experiencia = datos.get("experiencia", "")
    if experiencia:
        y_der = _bullets(c, experiencia, X_DER, y_der, ANCHO_DER, GRIS_TEXTO)

    c.save()
    return ruta_salida