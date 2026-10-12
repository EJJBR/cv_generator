"""
docs/diagrams/render_diagrams.py
Renderizador automático de diagramas PlantUML a formatos .png y .svg de alta calidad.
Utiliza el servicio público Kroki / PlantUML para generar los archivos sin necesidad de Java o Graphviz local.
"""

import os
import sys
import requests

DIAGRAMS_DIR = os.path.dirname(os.path.abspath(__file__))
DIAGRAM_FILES = [
    "evolucion_arquitectura.puml",
    "arquitectura_final.puml"
]


def render_puml(file_name: str):
    puml_path = os.path.join(DIAGRAMS_DIR, file_name)
    if not os.path.exists(puml_path):
        print(f"Archivo no encontrado: {puml_path}")
        return

    base_name = os.path.splitext(file_name)[0]
    with open(puml_path, "r", encoding="utf-8") as f:
        puml_content = f.read()

    print(f"🎨 Renderizando {file_name}...")

    # 1. Renderizar PNG
    try:
        resp_png = requests.post(
            "https://kroki.io/plantuml/png",
            data=puml_content.encode("utf-8"),
            headers={"Content-Type": "text/plain; charset=utf-8"},
            timeout=20
        )
        if resp_png.status_code == 200:
            png_path = os.path.join(DIAGRAMS_DIR, f"{base_name}.png")
            with open(png_path, "wb") as f_out:
                f_out.write(resp_png.content)
            print(f"  ✓ PNG generado: {png_path} ({len(resp_png.content)} bytes)")
        else:
            print(f"  ✗ Error generando PNG ({resp_png.status_code}): {resp_png.text}")
    except Exception as e:
        print(f"  ⚠️ No se pudo descargar PNG: {e}")

    # 2. Renderizar SVG
    try:
        resp_svg = requests.post(
            "https://kroki.io/plantuml/svg",
            data=puml_content.encode("utf-8"),
            headers={"Content-Type": "text/plain; charset=utf-8"},
            timeout=20
        )
        if resp_svg.status_code == 200:
            svg_path = os.path.join(DIAGRAMS_DIR, f"{base_name}.svg")
            with open(svg_path, "wb") as f_out:
                f_out.write(resp_svg.content)
            print(f"  ✓ SVG generado: {svg_path} ({len(resp_svg.content)} bytes)")
        else:
            print(f"  ✗ Error generando SVG ({resp_svg.status_code}): {resp_svg.text}")
    except Exception as e:
        print(f"  ⚠️ No se pudo descargar SVG: {e}")


def main():
    print("Iniciando renderizado de diagramas PlantUML para diapositivas...")
    for diag in DIAGRAM_FILES:
        render_puml(diag)
    print("\n✅ Proceso de renderizado concluido.")


if __name__ == "__main__":
    main()
