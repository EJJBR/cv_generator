"""
tests/test_cv_crop.py
Prueba de rendimiento y funcionamiento del recorte de rostro y hombros con OpenCV.
"""

import sys
import os
import time
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from image_processor import recortar_rostro_y_hombros


def test_performance_and_fallback():
    # 1. Crear una imagen sintetizada de prueba (800x1000)
    test_img_path = os.path.join(os.path.dirname(__file__), "test_temp_img.jpg")
    img_array = np.zeros((1000, 800, 3), dtype=np.uint8) + 200  # Fondo gris claro
    
    # Dibujar una forma de rostro simple para simulación si es necesario
    img_pil = Image.fromarray(img_array)
    img_pil.save(test_img_path)

    try:
        t0 = time.perf_counter()
        resultado = recortar_rostro_y_hombros(test_img_path, target_size=(300, 300))
        t1 = time.perf_counter()
        
        duration_ms = (t1 - t0) * 1000.0
        print(f"[OK] Tiempo de procesamiento: {duration_ms:.2f} ms")
        assert resultado.size == (300, 300), f"Tamaño incorrecto: {resultado.size}"
        print("[OK] Prueba de recorte y fallback completada con exito.")
    finally:
        if os.path.exists(test_img_path):
            os.remove(test_img_path)


if __name__ == "__main__":
    test_performance_and_fallback()
