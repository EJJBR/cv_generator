"""
tests/test_all_photos.py
Prueba masiva de recortar_rostro_y_hombros sobre todas las fotos reales en output/imagenes.
"""

import sys
import os
import glob
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from image_processor import recortar_rostro_y_hombros


def test_all_photos():
    fotos = glob.glob("output/imagenes/*.jpg") + glob.glob("output/imagenes/*.png")
    if not fotos:
        print("[WARN] No se encontraron fotos en output/imagenes/")
        return

    print(f"Probando {len(fotos)} fotos reales...")
    exitos = 0
    t_total = 0

    for foto in fotos:
        t0 = time.perf_counter()
        try:
            res = recortar_rostro_y_hombros(foto, target_size=(300, 300))
            t1 = time.perf_counter()
            dt = (t1 - t0) * 1000.0
            t_total += dt
            exitos += 1
            # Guardar muestra recortada en output/test_crops/
            os.makedirs("output/test_crops", exist_ok=True)
            base = os.path.basename(foto)
            res.save(os.path.join("output/test_crops", f"crop_{base}"))
        except Exception as e:
            print(f"[ERROR] {os.path.basename(foto)}: {e}")

    prom = t_total / exitos if exitos else 0
    print(f"[OK] Procesadas {exitos}/{len(fotos)} fotos con exito.")
    print(f"[OK] Tiempo promedio por foto: {prom:.2f} ms")


if __name__ == "__main__":
    test_all_photos()
