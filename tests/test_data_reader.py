import os
import tempfile
import unittest

from src.data_reader import _buscar_foto


class BuscarFotoTests(unittest.TestCase):
    def test_match_con_prefijos_y_acentos(self):
        with tempfile.TemporaryDirectory() as d:
            nombre = "Jhoanna Ríos Delgado"
            ruta = os.path.join(d, "22. Foto Mg. Ríos Delgado (1).jpg")
            with open(ruta, "wb") as f:
                f.write(b"x")
            self.assertEqual(_buscar_foto(nombre, d), ruta)

    def test_match_con_mayusculas_y_acentos(self):
        with tempfile.TemporaryDirectory() as d:
            nombre = "Miguel Ángel Cayuela Berruezo"
            ruta = os.path.join(d, "2386.jpg - MIGUEL ANGEL CAYUELA BERRUEZO.jfif")
            with open(ruta, "wb") as f:
                f.write(b"x")
            self.assertEqual(_buscar_foto(nombre, d), ruta)


if __name__ == "__main__":
    unittest.main()
