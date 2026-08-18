import os
import re
import sys
from pathlib import Path

import requests

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "output" / "imagenes"


def extraer_file_id(url: str) -> str | None:
    if not url:
        return None
    match = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
    if match:
        return match.group(1)
    match = re.search(r"[?&]id=([a-zA-Z0-9_-]+)", url)
    return match.group(1) if match else None


def descargar_drive(url: str, destino: str | os.PathLike[str], timeout: int = 60) -> str:
    file_id = extraer_file_id(url)
    if not file_id:
        raise ValueError(f"No se pudo extraer el file_id del enlace: {url}")

    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)

    api_url = "https://docs.google.com/uc?export=download"
    session = requests.Session()
    respuesta = session.get(api_url, params={"id": file_id}, stream=True, timeout=timeout)

    token = None
    for key, value in respuesta.cookies.items():
        if key.startswith("download_warning"):
            token = value

    if token:
        respuesta = session.get(
            api_url,
            params={"id": file_id, "confirm": token},
            stream=True,
            timeout=timeout,
        )

    if respuesta.status_code != 200:
        raise RuntimeError(
            f"No se pudo descargar Drive. HTTP {respuesta.status_code} para {url}"
        )

    with open(destino, "wb") as archivo:
        for chunk in respuesta.iter_content(32768):
            if chunk:
                archivo.write(chunk)

    return str(destino)


def main() -> None:
    urls = sys.argv[1:]
    if not urls:
        urls = [
            "https://drive.google.com/file/d/1qUMtbsyOvE13jIiz9CpIFVM963c7jRtH/view"
        ]

    for i, url in enumerate(urls, start=1):
        nombre = f"img_{i}.jpg"
        destino = OUTPUT_DIR / nombre
        try:
            ruta = descargar_drive(url, destino)
            print(f"✅ Descargada: {ruta}")
        except Exception as exc:
            print(f"❌ Error con {url}: {exc}")


if __name__ == "__main__":
    main()
