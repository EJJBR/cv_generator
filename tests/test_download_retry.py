import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import openpyxl
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from controllers.masivo_controller import MasivoController


class DownloadRetryTests(unittest.TestCase):
    def test_reintento_descarga_solo_el_id_seleccionado(self):
        with tempfile.TemporaryDirectory() as temporary_dir:
            temporary_path = Path(temporary_dir)
            excel_path = temporary_path / "docentes.xlsx"
            images_path = temporary_path / "imagenes"
            logs_path = temporary_path / "logs"

            workbook = openpyxl.Workbook()
            sheet = workbook.active
            sheet.append(["ID", "Nombre", "Foto de Perfil"])
            sheet.append(["1", "Docente Uno", "https://drive.google.com/file/d/uno/view"])
            sheet.append(["2", "Docente Dos", "https://drive.google.com/file/d/dos/view"])
            workbook.save(excel_path)

            existing = images_path / "1_DOCENTE UNO.jpg"
            images_path.mkdir()
            Image.new("RGB", (2, 2), "white").save(existing, format="JPEG")

            controller = MasivoController(lambda _: None, lambda _: None, lambda: None)
            downloaded_ids = []

            def fake_download(file_id, destination):
                downloaded_ids.append(file_id)
                Path(destination).write_bytes(b"downloaded")

            with patch("controllers.masivo_controller.OUTPUT_IMAGENES", str(images_path)), patch(
                "controllers.masivo_controller.OUTPUT_LOGS", str(logs_path)
            ), patch.object(controller, "_descargar_foto", side_effect=fake_download):
                ok, _, filas = controller.descargar_fotos_excel_detallado(
                    str(excel_path), solo_ids={"2"}
                )

            self.assertTrue(ok)
            self.assertEqual(downloaded_ids, ["dos"])
            estados = {fila["id"]: fila for fila in filas}
            self.assertTrue(estados["1"]["descargada"])
            self.assertTrue(estados["2"]["descargada"])


if __name__ == "__main__":
    unittest.main()