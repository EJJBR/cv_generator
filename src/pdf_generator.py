"""
pdf_generator.py
Genera el CV en PDF utilizando Platypus (ReportLab).
Fondo gestionado por callback de página para evitar errores de desbordamiento (LayoutError).
"""

import os
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Flowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from PIL import Image as PILImage

# ── Paleta de Colores (Armonía Guinda Institucional) ────────────────────
GUINDA_FACULTAD = colors.HexColor("#4B0002")
DORADO_LABEL = colors.HexColor("#D4AF37")
BLANCO = colors.white
GRIS_TEXTO = colors.HexColor("#2C2C2C")

# ── Dimensiones del Grid ─────────────────────────────────────────────────────
W, H = A4
ANCHO_COL_IZQ = W * 0.35
ANCHO_COL_DER = W * 0.65
PADDING_DER = 24
ANCHO_LINEA = ANCHO_COL_DER - (PADDING_DER * 2)


# ── Callbacks de Fondo (Evita usar rowHeights=[H] que rompe el layout) ───────
def dibujar_fondos_cv(canvas, doc):
    """Dibuja las dos columnas de color directamente en la lona base."""
    canvas.saveState()
    # Barra izquierda Guinda
    canvas.setFillColor(GUINDA_FACULTAD)
    canvas.rect(0, 0, ANCHO_COL_IZQ, H, stroke=0, fill=1)
    # Cuerpo derecho Blanco
    canvas.setFillColor(BLANCO)
    canvas.rect(ANCHO_COL_IZQ, 0, ANCHO_COL_DER, H, stroke=0, fill=1)
    canvas.restoreState()


# ── Componentes Visuales Personalizados (Flowables) ──────────────────────────
class LineaDivisoria(Flowable):
    """Equivalente a un <hr> con estilos personalizados."""
    def __init__(self, ancho, color, grosor=1.5):
        Flowable.__init__(self)
        self.ancho = ancho
        self.color = color
        self.grosor = grosor

    def draw(self):
        self.canv.saveState()
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.grosor)
        self.canv.line(0, 0, self.ancho, 0)
        self.canv.restoreState()


class FotoCircularFlowable(Flowable):
    """Encapsula la foto circular para que actúe como un elemento de bloque."""
    def __init__(self, foto_path, radio, color_borde):
        Flowable.__init__(self)
        self.foto_path = foto_path
        self.radio = radio
        self.color_borde = color_borde
        self.width = radio * 2
        self.height = radio * 2

    def draw(self):
        self.canv.saveState()
        cx, cy = self.radio, self.radio
        try:
            if self.foto_path and os.path.exists(self.foto_path):
                img = PILImage.open(self.foto_path).convert("RGB")
                lado = min(img.size)
                left = (img.size[0] - lado) // 2
                top = (img.size[1] - lado) // 2
                img = img.crop((left, top, left + lado, top + lado))
                img = img.resize((300, 300), PILImage.LANCZOS)

                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=90)
                buf.seek(0)

                path = self.canv.beginPath()
                path.circle(cx, cy, self.radio)
                self.canv.clipPath(path, stroke=0, fill=0)
                self.canv.drawImage(ImageReader(buf), 0, 0, width=self.width, height=self.height, preserveAspectRatio=True, mask="auto")
            else:
                raise Exception()
        except Exception:
            # Silueta Placeholder segura si no encuentra foto
            self.canv.setFillColor(colors.HexColor("#A38A53"))
            self.canv.circle(cx, cy, self.radio, stroke=0, fill=1)
            self.canv.setFillColor(colors.HexColor("#D4AF37"))
            self.canv.circle(cx, cy + self.radio * 0.35, self.radio * 0.28, stroke=0, fill=1)
            path = self.canv.beginPath()
            path.arc(cx - self.radio * 0.45, cy - self.radio * 0.15, cx + self.radio * 0.45, cy + self.radio * 0.55, startAng=0, extent=180)
            path.close()
            self.canv.drawPath(path, stroke=0, fill=1)
        
        self.canv.restoreState()
        self.canv.setStrokeColor(self.color_borde)
        self.canv.setLineWidth(2.5)
        self.canv.circle(cx, cy, self.radio, stroke=1, fill=0)


class LogoFlowable(Flowable):
    """Renderiza el logo manteniendo su proporción original de forma segura."""
    def __init__(self, logo_path, ancho_max, alto_max):
        Flowable.__init__(self)
        self.logo_path = logo_path
        self.ancho_max = ancho_max
        self.alto_max = alto_max
        self.width = ancho_max
        self.height = alto_max

    def draw(self):
        try:
            if self.logo_path and os.path.exists(self.logo_path):
                self.canv.drawImage(ImageReader(self.logo_path), 0, 0, width=self.ancho_max, height=self.alto_max, preserveAspectRatio=True, mask="auto")
        except Exception:
            pass


# ── Generador Principal ──────────────────────────────────────────────────────
def generar_cv(datos: dict, ruta_salida: str, logo_path: str = None) -> str:
    # Definimos el lienzo de la página ocupando el 100% del espacio
    doc = SimpleDocTemplate(ruta_salida, pagesize=A4, leftMargin=0, rightMargin=0, topMargin=0, bottomMargin=0)
    
    styles = getSampleStyleSheet()
    
    # Configuramos las fuentes escaladas deseadas
    style_nombre = ParagraphStyle('Nom', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=15, leading=19, textColor=BLANCO, alignment=1)
    style_label_izq = ParagraphStyle('Lab', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9.5, leading=12, textColor=DORADO_LABEL)
    style_valor_izq = ParagraphStyle('Val', parent=styles['Normal'], fontName='Helvetica', fontSize=9.5, leading=14, textColor=BLANCO)
    
    style_unmsm = ParagraphStyle('Uni', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=GUINDA_FACULTAD)
    style_facultad = ParagraphStyle('Fac', parent=styles['Normal'], fontName='Helvetica', fontSize=11, leading=14, textColor=GRIS_TEXTO)
    
    style_titulo_der = ParagraphStyle('TitDer', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=13, leading=16, textColor=GUINDA_FACULTAD)
    style_cuerpo = ParagraphStyle('Cue', parent=styles['Normal'], fontName='Helvetica', fontSize=10.5, leading=16, textColor=GRIS_TEXTO, alignment=4)
    style_bullet = ParagraphStyle('Bul', parent=style_cuerpo, leftIndent=12, firstLineIndent=-12)

    # 📦 Elementos Fluyentes - COLUMNA IZQUIERDA
    story_izq = [
        Spacer(1, 35),
        FotoCircularFlowable(datos.get("foto_path"), 65, DORADO_LABEL),
        Spacer(1, 20),
        Paragraph(datos.get("nombre", "").upper(), style_nombre),
        Spacer(1, 30)
    ]
    
    def agregar_bloque_izq(titulo, valor):
        story_izq.append(Paragraph(titulo.upper(), style_label_izq))
        story_izq.append(Spacer(1, 4))
        story_izq.append(Paragraph(valor if valor else "—", style_valor_izq))
        story_izq.append(Spacer(1, 18))

    agregar_bloque_izq("Correo institucional", datos.get("correo"))
    agregar_bloque_izq("Escuela Profesional", datos.get("escuela"))
    agregar_bloque_izq("Departamento Académico", datos.get("departamento"))
    agregar_bloque_izq("Categoría / Clase", datos.get("categoria"))

    # 📦 Elementos Fluyentes - COLUMNA DERECHA
    story_der = [Spacer(1, 25)]
    
    if logo_path and os.path.exists(logo_path):
        story_der.append(LogoFlowable(logo_path, ANCHO_LINEA, 70))
        story_der.append(Spacer(1, 20))
    else:
        story_der.append(Paragraph("UNMSM", style_unmsm))
        story_der.append(Paragraph("Facultad de Derecho y Ciencia Política", style_facultad))
        story_der.append(Spacer(1, 25))

    def agregar_seccion_der(titulo, texto, es_lista=False):
        if not texto: return
        story_der.append(Paragraph(titulo, style_titulo_der))
        story_der.append(Spacer(1, 4))
        story_der.append(LineaDivisoria(ANCHO_LINEA, GUINDA_FACULTAD, 1.5))
        story_der.append(Spacer(1, 10))
        
        if es_lista:
            elementos = [e.strip() for e in texto.strip().split("\n") if e.strip()]
            for el in elementos:
                story_der.append(Paragraph(f"• &nbsp;{el}", style_bullet))
                story_der.append(Spacer(1, 5))
        else:
            story_der.append(Paragraph(texto, style_cuerpo))
        story_der.append(Spacer(1, 22))

    agregar_seccion_der("Formación Académica", datos.get("formacion", ""), es_lista=True)
    agregar_seccion_der("Trayectoria", datos.get("trayectoria", ""))
    agregar_seccion_der("Experiencia Laboral", datos.get("experiencia", ""), es_lista=True)

    # 🎛️ Estructura Grid de Doble Columna (Sin forzar rowHeights)
    grid_principal = Table([[story_izq, story_der]], colWidths=[ANCHO_COL_IZQ, ANCHO_COL_DER])
    grid_principal.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (0, 0), 18),
        ('RIGHTPADDING', (0, 0), (0, 0), 18),
        ('LEFTPADDING', (1, 0), (1, 0), PADDING_DER),
        ('RIGHTPADDING', (1, 0), (1, 0), PADDING_DER),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))

    # Compilamos inyectando el fondo a través del parámetro onFirstPage
    doc.build([grid_principal], onFirstPage=dibujar_fondos_cv)
    return ruta_salida