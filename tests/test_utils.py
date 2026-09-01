import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from ui.utils import sanitizar_para_reportlab


class SanitizarReportLabTests(unittest.TestCase):
    def test_conserva_apostrofe_y_escapa_simbolos_xml(self):
        texto = "Dell'Erba Ugolini, Italo Joshua & Asociados <FDCP>"

        resultado = sanitizar_para_reportlab(texto)

        self.assertEqual(
            resultado,
            "Dell'Erba Ugolini, Italo Joshua &amp; Asociados &lt;FDCP&gt;",
        )


if __name__ == "__main__":
    unittest.main()