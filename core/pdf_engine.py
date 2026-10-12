"""
core/pdf_engine.py
Motor de generación de PDFs en ReportLab para los documentos del Bolsista UNMSM:
1. Declaración Jurada de No Pertenecer a Órganos de Gobierno (Formato Oficial UNMSM).
2. Informe de Actividades de Bolsista.

Este módulo es 100% independiente de cualquier framework de GUI (CustomTkinter)
y de librerías de visión por computadora (OpenCV).
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from core.utils import sanitizar_para_reportlab

# Dimensiones estándar A4
W, H = A4
NEGRO = colors.HexColor("#000000")


def generar_declaracion_jurada(datos: dict, ruta_salida: str, logo_path: str = None) -> str:
    """Genera la Declaración Jurada oficial de la UNMSM en formato PDF."""
    os.makedirs(os.path.dirname(os.path.abspath(ruta_salida)), exist_ok=True)

    doc = SimpleDocTemplate(
        ruta_salida, pagesize=A4,
        leftMargin=45, rightMargin=45, topMargin=40, bottomMargin=40
    )

    style_header_unmsm = ParagraphStyle('HeadUNMSM', fontName='Helvetica-Bold', fontSize=13, leading=16, alignment=1)
    style_header_sub   = ParagraphStyle('HeadSub', fontName='Helvetica', fontSize=10.5, leading=13, alignment=1)
    style_header_dir   = ParagraphStyle('HeadDir', fontName='Helvetica-Bold', fontSize=11.5, leading=14, alignment=1)

    style_tit_main = ParagraphStyle('TitMain', fontName='Helvetica-Bold', fontSize=11, leading=14, alignment=1)
    style_tit_sub  = ParagraphStyle('TitSub', fontName='Helvetica-Oblique', fontSize=9.5, leading=12, alignment=1)

    style_body      = ParagraphStyle('BodyText', fontName='Helvetica', fontSize=9.5, leading=13.5, alignment=4)
    style_cell_txt  = ParagraphStyle('CellTxt', fontName='Helvetica', fontSize=9.5, leading=12, alignment=1)
    style_cell_lbl  = ParagraphStyle('CellLbl', fontName='Helvetica', fontSize=8, leading=10, alignment=1)

    story = []

    # Encabezado institucional con Logo
    logo_img = None
    if logo_path and os.path.exists(logo_path):
        try:
            logo_img = Image(logo_path, width=65, height=70)
        except Exception:
            logo_img = ""

    text_header = [
        Paragraph("UNIVERSIDAD NACIONAL MAYOR DE SAN MARCOS", style_header_unmsm),
        Paragraph("(Universidad del Perú, DECANA DE AMÉRICA)", style_header_sub),
        Spacer(1, 3),
        Paragraph("DIRECCIÓN GENERAL DE ADMINISTRACIÓN", style_header_dir)
    ]

    t_header = Table([[logo_img or "", text_header]], colWidths=[75, W - 165])
    t_header.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(t_header)
    story.append(Spacer(1, 12))

    # Línea Divisoria Superior
    t_line = Table([[""]], colWidths=[W - 90], rowHeights=[1.5])
    t_line.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), NEGRO)]))
    story.append(t_line)
    story.append(Spacer(1, 14))

    # Título
    story.append(Paragraph("DECLARACIÓN JURADA DE NO PERTENECER A LOS ÓRGANOS DE GOBIERNO DE LA UNMSM", style_tit_main))
    story.append(Spacer(1, 3))
    story.append(Paragraph("<i>Ley Universitaria<br/>Ley Nº 30220</i>", style_tit_sub))
    story.append(Spacer(1, 14))

    # Texto introductorio
    intro_txt = (
        "En cumplimiento de lo dispuesto en el Art. 104º de la Ley Universitaria – Ley Nº 30220, que señala:<br/>"
        "<i>“Los representantes de los estudiantes en los órganos de gobierno de la Universidad, están impedidos de tener cargo o actividad rentada en ellas durante su mandato y hasta un año después de terminado éste”.</i>"
    )
    story.append(Paragraph(intro_txt, style_body))
    story.append(Spacer(1, 14))

    # Datos del declarante
    ap_paterno = datos.get("ap_paterno", "").strip().upper()
    ap_materno = datos.get("ap_materno", "").strip().upper()
    apellidos_completos = f"{ap_paterno} {ap_materno}".strip()
    nombres    = datos.get("nombres", "").strip().upper()
    dni        = datos.get("dni", "").strip()
    domicilio  = datos.get("domicilio", "").strip().upper()
    distrito   = datos.get("distrito", "").strip().upper()
    telefono   = datos.get("telefono", "").strip()
    email      = datos.get("email", "").strip()
    condicion  = datos.get("condicion", "Estudiante").strip()
    facultad   = datos.get("facultad", "").strip()
    fecha      = datos.get("fecha", "").strip() or "Lima, 30 de Octubre del 2026"

    if fecha.startswith("Lma"):
        fecha = fecha.replace("Lma", "Lima")

    # Tabla 1: Apellidos, Nombres y DNI
    t1_data = [
        [Paragraph("El que suscribe,", style_body), Paragraph(sanitizar_para_reportlab(apellidos_completos), style_cell_txt), ""],
        ["", Paragraph("(Ap. Paterno)", style_cell_lbl), Paragraph("(Ap. Materno)", style_cell_lbl)],
        ["", Paragraph(sanitizar_para_reportlab(nombres), style_cell_txt), Paragraph(sanitizar_para_reportlab(dni), style_cell_txt)],
        ["", Paragraph("(Nombres Completos)", style_cell_lbl), Paragraph("(Nº Documento Nacional de Identidad – DNI)", style_cell_lbl)]
    ]
    t1 = Table(t1_data, colWidths=[105, 230, 170])
    t1.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('SPAN', (1, 0), (2, 0)),
        ('BOX', (1, 0), (2, 0), 1, NEGRO),
        ('BOX', (1, 2), (1, 2), 1, NEGRO),
        ('BOX', (2, 2), (2, 2), 1, NEGRO),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(t1)
    story.append(Spacer(1, 10))

    # Tabla 2: Domicilio y Distrito
    t2_data = [
        [Paragraph("Domiciliado en", style_body), Paragraph(sanitizar_para_reportlab(domicilio), style_cell_txt), Paragraph(sanitizar_para_reportlab(distrito), style_cell_txt)],
        ["", "", Paragraph("(Distrito)", style_cell_lbl)]
    ]
    t2 = Table(t2_data, colWidths=[105, 255, 145])
    t2.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (1, 0), (1, 0), 1, NEGRO),
        ('BOX', (2, 0), (2, 0), 1, NEGRO),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(t2)
    story.append(Spacer(1, 10))

    # Tabla 3: Teléfono y Email
    t3_data = [
        [
            Paragraph("Con Nº de Teléfono", style_body),
            Paragraph(sanitizar_para_reportlab(telefono), style_cell_txt),
            Paragraph(f"Email: <u>{sanitizar_para_reportlab(email)}</u>", ParagraphStyle('Em', fontName='Helvetica', fontSize=9.5))
        ]
    ]
    t3 = Table(t3_data, colWidths=[110, 160, 235])
    t3.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (1, 0), (1, 0), 1, NEGRO),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(t3)
    story.append(Spacer(1, 12))

    # Condición y Facultad
    story.append(Paragraph(f"En mi condición de: <b>{sanitizar_para_reportlab(condicion)}</b>", style_body))
    story.append(Spacer(1, 8))

    t_fac = Table([[
        Paragraph("Indicar la Facultad a la que pertenece:", style_body),
        Paragraph(f"<b>{sanitizar_para_reportlab(facultad)}</b>", ParagraphStyle('FacVal', fontName='Helvetica-Bold', fontSize=9.5))
    ]], colWidths=[205, 300])
    t_fac.setStyle(TableStyle([
        ('LINEBELOW', (1, 0), (1, 0), 1, NEGRO),
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1)
    ]))
    story.append(t_fac)
    story.append(Spacer(1, 18))

    # Declaración jurada legal
    dec_txt = (
        "<b>Declaro bajo juramento el no pertenecer a los Órganos de Gobierno de la Universidad Nacional Mayor de San Marcos "
        "y no encontrarme comprendido en los impedimentos del Art. 104º de la Ley Universitaria Nº 30220.</b><br/><br/>"
        "Asimismo, declaro conocer las consecuencias administrativas, civiles y penales por la falsedad de la información "
        "proporcionada, previstas en la Ley Nº 27444 y en los códigos civil y penal vigente."
    )
    story.append(Paragraph(dec_txt, style_body))
    story.append(Spacer(1, 30))

    # Fecha y Firma
    story.append(Paragraph(sanitizar_para_reportlab(fecha), style_body))
    story.append(Spacer(1, 15))

    firma_img = ""
    firma_path = datos.get("firma_path")
    if firma_path and os.path.exists(firma_path):
        try:
            firma_img = Image(firma_path, width=150, height=55)
        except Exception:
            firma_img = ""

    t_firma_rows = [
        [firma_img or ""],
        [""],
        [Paragraph("FIRMA DEL DECLARANTE", ParagraphStyle('FirmaLabel', fontName='Helvetica', fontSize=9, alignment=1))]
    ]
    t_firma = Table(t_firma_rows, colWidths=[210], rowHeights=[55, 2, 16])
    t_firma.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('LINEBELOW', (0, 1), (0, 1), 1, NEGRO),
    ]))

    t_pie = Table([["", t_firma]], colWidths=[W - 300, 210])
    story.append(t_pie)

    doc.build(story)
    return ruta_salida


def generar_informe_actividades(datos: dict, ruta_salida: str) -> str:
    """Genera el Informe de Actividades oficial en formato PDF."""
    os.makedirs(os.path.dirname(os.path.abspath(ruta_salida)), exist_ok=True)

    doc = SimpleDocTemplate(
        ruta_salida, pagesize=A4,
        leftMargin=50, rightMargin=50, topMargin=45, bottomMargin=45
    )

    style_title = ParagraphStyle('InfTitle', fontName='Helvetica-Bold', fontSize=14, leading=18, alignment=1)
    style_label = ParagraphStyle('InfLab', fontName='Helvetica-Bold', fontSize=10.5, leading=15)
    style_val   = ParagraphStyle('InfVal', fontName='Helvetica', fontSize=10.5, leading=15)
    style_body  = ParagraphStyle('InfBody', fontName='Helvetica', fontSize=10.5, leading=15, alignment=4)
    style_bullet= ParagraphStyle('InfBullet', fontName='Helvetica-Bold', fontSize=10.5, leading=15, leftIndent=20)

    story = []

    anio = datos.get("anio", "2026")
    story.append(Paragraph(f"INFORME DE ACTIVIDADES - {sanitizar_para_reportlab(str(anio))}", style_title))
    story.append(Spacer(1, 20))

    para_nom = sanitizar_para_reportlab(datos.get("para_nombre", "").upper())
    para_car = sanitizar_para_reportlab(datos.get("para_cargo", ""))
    de_nom   = sanitizar_para_reportlab(datos.get("de_nombre", "").upper())
    asunto   = sanitizar_para_reportlab(datos.get("asunto", "Informe de actividades"))
    fecha    = sanitizar_para_reportlab(datos.get("fecha", "Lima, 30 de Octubre de 2026"))

    header_table_data = [
        [Paragraph("A:", style_label), Paragraph(f"<b>{para_nom}</b><br/>{para_car}", style_val)],
        ["", ""],
        [Paragraph("De:", style_label), Paragraph(f"<b>{de_nom}</b>", style_val)],
        ["", ""],
        [Paragraph("Asunto:", style_label), Paragraph(asunto, style_val)],
        ["", ""],
        [Paragraph("Fecha:", style_label), Paragraph(fecha, style_val)],
    ]
    t_header = Table(header_table_data, colWidths=[60, W - 160])
    t_header.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(t_header)
    story.append(Spacer(1, 15))

    t_line = Table([[""]], colWidths=[W - 100], rowHeights=[1])
    t_line.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#A0A0A0"))]))
    story.append(t_line)
    story.append(Spacer(1, 18))

    fecha_ini = sanitizar_para_reportlab(datos.get("fecha_inicio", "01 de Octubre"))
    intro_txt = f"Tengo el agrado de dirigirme a usted, a fin de informarle sobre el desarrollo del servicio realizado a partir del día {fecha_ini} del presente año, tal como se señala a continuación."
    story.append(Paragraph(intro_txt, style_body))
    story.append(Spacer(1, 15))

    actividades = datos.get("actividades", [])
    if isinstance(actividades, str):
        actividades = [a.strip() for a in actividades.split("\n") if a.strip()]

    for act in actividades:
        story.append(Paragraph(f"➢ &nbsp; {sanitizar_para_reportlab(act)}", style_bullet))
        story.append(Spacer(1, 8))

    story.append(Spacer(1, 15))
    story.append(Paragraph("Asimismo, se adjuntan evidencias de la labor realizada.", style_body))
    story.append(Spacer(1, 25))

    evidencias = datos.get("evidencias", [])
    if evidencias:
        story.append(PageBreak())
        story.append(Paragraph("<b>EVIDENCIAS FOTOGRÁFICAS DE LAS ACTIVIDADES</b>", ParagraphStyle('EvTitle', fontName='Helvetica-Bold', fontSize=12, alignment=1)))
        story.append(Spacer(1, 15))

        img_cells = []
        for ev in evidencias:
            img_path = ev if isinstance(ev, str) else ev.get("path")
            if img_path and os.path.exists(img_path):
                try:
                    img_obj = Image(img_path, width=220, height=160)
                    img_cells.append(img_obj)
                except Exception:
                    pass

        grid_rows = []
        for i in range(0, len(img_cells), 2):
            row = [img_cells[i]]
            if i + 1 < len(img_cells):
                row.append(img_cells[i+1])
            else:
                row.append("")
            grid_rows.append(row)

        if grid_rows:
            t_grid = Table(grid_rows, colWidths=[240, 240])
            t_grid.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
            ]))
            story.append(t_grid)
            story.append(Spacer(1, 20))

    story.append(Spacer(1, 20))
    story.append(Paragraph("Es todo cuanto tengo que informar", style_body))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Atentamente", style_body))
    story.append(Spacer(1, 20))

    firma_img = ""
    firma_path = datos.get("firma_path")
    if firma_path and os.path.exists(firma_path):
        try:
            firma_img = Image(firma_path, width=160, height=60)
        except Exception:
            firma_img = ""

    t_firma_rows = [
        [firma_img or ""],
        [""],
        [Paragraph(f"<b>{de_nom}</b>", ParagraphStyle('FN', fontName='Helvetica-Bold', fontSize=10, alignment=1))],
        [Paragraph(f"DNI: {sanitizar_para_reportlab(datos.get('dni', ''))}", ParagraphStyle('FD', fontName='Helvetica', fontSize=9.5, alignment=1))]
    ]
    t_firma = Table(t_firma_rows, colWidths=[220], rowHeights=[60, 2, 16, 14])
    t_firma.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('LINEBELOW', (0, 1), (0, 1), 1, NEGRO),
    ]))

    t_pie_inf = Table([["", t_firma]], colWidths=[W - 320, 220])
    story.append(t_pie_inf)

    doc.build(story)
    return ruta_salida
