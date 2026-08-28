"""
src/image_processor.py
Módulo de visión por computadora para encuadre automático de rostro y hombros.
Diseñado para encontrar la caja de corte 1:1 óptima DENTRO de los bordes reales de la foto.
SIN editar, estirar ni modificar los píxeles originales de la imagen.
"""

import os
import cv2
import numpy as np
from PIL import Image as PILImage, ImageOps

# Clasificadores de rostros de OpenCV (se cargan una sola vez en memoria)
_CASCADE_DEFAULT = None
_CASCADE_ALT = None

def _get_cascades():
    global _CASCADE_DEFAULT, _CASCADE_ALT
    if _CASCADE_DEFAULT is None:
        _CASCADE_DEFAULT = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        _CASCADE_ALT = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_alt2.xml')
    return _CASCADE_DEFAULT, _CASCADE_ALT


def recortar_rostro_y_hombros(foto_path: str, target_size: tuple[int, int] = (300, 300)) -> PILImage.Image:
    """
    Lee una foto, corrige la orientación EXIF y calcula el mejor encuadre cuadrado (1:1)
    para el rostro y los hombros del docente estrictamente DENTRO de las dimensiones reales de la foto.
    
    NO altera, deforma, estira ni añade bordes artificiales a la imagen original.
    """
    if not foto_path or not os.path.exists(foto_path):
        raise FileNotFoundError(f"No se encontró la foto en la ruta: {foto_path}")

    # 1. Cargar imagen y corregir orientación EXIF (rotación de celular)
    img_pil = PILImage.open(foto_path)
    img_pil = ImageOps.exif_transpose(img_pil).convert("RGB")
    orig_w, orig_h = img_pil.size

    try:
        # Convertir a numpy BGR para OpenCV
        img_np = np.array(img_pil)[:, :, ::-1]

        # Redimensionar temporalmente para detección ultrarrápida (máx 600px)
        max_dim = 600
        scale = 1.0
        if max(orig_w, orig_h) > max_dim:
            scale = max_dim / float(max(orig_w, orig_h))
            detect_w = int(orig_w * scale)
            detect_h = int(orig_h * scale)
            img_detect = cv2.resize(img_np, (detect_w, detect_h), interpolation=cv2.INTER_AREA)
        else:
            img_detect = img_np

        gray = cv2.cvtColor(img_detect, cv2.COLOR_BGR2GRAY)
        
        casc_default, casc_alt = _get_cascades()
        
        # Tamaño mínimo del rostro (al menos 12% de la altura) para evitar falsos positivos en cuello o ropa
        min_face_dim = int(img_detect.shape[0] * 0.12)

        faces = casc_default.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(min_face_dim, min_face_dim)
        )

        if len(faces) == 0:
            faces = casc_alt.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=4,
                minSize=(min_face_dim, min_face_dim)
            )

        if len(faces) > 0:
            # Priorizar rostros en la parte superior/media de la imagen y de mayor tamaño
            faces = sorted(faces, key=lambda f: (f[1] < img_detect.shape[0] * 0.65, f[2] * f[3]), reverse=True)
            fx, fy, fw, fh = faces[0]

            # Reescalar coordenadas a la imagen original
            if scale != 1.0:
                fx = int(fx / scale)
                fy = int(fy / scale)
                fw = int(fw / scale)
                fh = int(fh / scale)

            # --- Encuadre Cuadrado Pronominal (STRICTLY INSIDE ORIGINAL BOUNDS) ---
            cx = fx + (fw // 2)
            
            # Tamaño deseado para el recuadro 1:1 (rostro + cabeza + hombros)
            desired_s = int(fh * 2.7)
            
            # El recuadro S no puede exceder las dimensiones de la imagen original
            max_possible_s = min(orig_w, orig_h)
            S = min(desired_s, max_possible_s)
            
            # Posición superior deseada: incluir margen sobre el rostro (cabello)
            top_ideal = fy - int(0.4 * fh)
            left_ideal = cx - (S // 2)

            # Restringir estrictamente DENTRO de la imagen sin salirse [0, orig_w - S] y [0, orig_h - S]
            top = max(0, min(top_ideal, orig_h - S))
            left = max(0, min(left_ideal, orig_w - S))

            crop_box = (left, top, left + S, top + S)
            cropped = img_pil.crop(crop_box)
            return cropped.resize(target_size, PILImage.LANCZOS)

    except Exception:
        pass  # En caso de cualquier imprevisto, usar el fallback seguro

    # --- FALLBACK SEGURO: Recorte al centro/superior dentro de los bordes reales ---
    S = min(orig_w, orig_h)
    left = (orig_w - S) // 2
    top = int(orig_h * 0.05)
    if top + S > orig_h:
        top = max(0, orig_h - S)
    
    cropped = img_pil.crop((left, top, left + S, top + S))
    return cropped.resize(target_size, PILImage.LANCZOS)
