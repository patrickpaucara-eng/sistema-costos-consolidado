import unittest

from openpyxl import Workbook

from reyna_local.recetas_pedido import (
    aprender_familia,
    calcular_cantidades,
    guardar_familias_en_libro,
    leer_familias_de_libro,
)


DEFINICIONES = [{"codigo": "kg", "nombre": "Peso", "unidad": "kg", "minimo": 500, "maximo": 2000}]
ORDENES_TOLVA = [
    {"familia": "TOLVA", "sintesis": "REAL", "parametros": {"kg": 1000}, "inductores": {"SOLD_H": 60}},
    {"familia": "TOLVA", "sintesis": "REAL", "parametros": {"kg": 1200}, "inductores": {"SOLD_H": 70}},
    {"familia": "TOLVA", "sintesis": "REAL", "parametros": {"kg": 1500}, "inductores": {"SOLD_H": 85}},
]


class RecetasPedidoTest(unittest.TestCase):
    def test_caso_manual_tolva_aprende_y_explota_receta(self):
        modelo = aprender_familia("TOLVA", DEFINICIONES, ORDENES_TOLVA)
        receta = modelo["inductores"]["SOLD_H"]
        self.assertAlmostEqual(receta["base"], 10.0, places=8)
        self.assertAlmostEqual(receta["coeficientes"]["kg"], 0.05, places=10)
        self.assertAlmostEqual(calcular_cantidades(modelo, {"kg": 1300})["SOLD_H"], 75.0, places=8)

    def test_falta_parametro_obligatorio_indica_nombre(self):
        modelo = aprender_familia("TOLVA", DEFINICIONES, ORDENES_TOLVA)
        with self.assertRaisesRegex(ValueError, "Falta parámetro obligatorio: Peso"):
            calcular_cantidades(modelo, {})

    def test_rechaza_parametro_fuera_de_rango(self):
        modelo = aprender_familia("TOLVA", DEFINICIONES, ORDENES_TOLVA)
        with self.assertRaisesRegex(ValueError, "supera el máximo válido"):
            calcular_cantidades(modelo, {"kg": 2500})

    def test_no_entrena_con_sintesis_no_real(self):
        estimada = [dict(ORDENES_TOLVA[0], sintesis="ESTIMADO"), *ORDENES_TOLVA[1:]]
        with self.assertRaisesRegex(ValueError, "Solo se aprende con órdenes de síntesis REAL"):
            aprender_familia("TOLVA", DEFINICIONES, estimada)

    def test_hoja_opcional_roundtrip_y_libro_anterior(self):
        libro = Workbook()
        self.assertEqual(leer_familias_de_libro(libro), {})
        modelo = aprender_familia("TOLVA", DEFINICIONES, ORDENES_TOLVA)
        guardar_familias_en_libro(libro, {"TOLVA": modelo})
        recuperado = leer_familias_de_libro(libro)["TOLVA"]
        self.assertAlmostEqual(calcular_cantidades(recuperado, {"kg": 1300})["SOLD_H"], 75.0, places=8)
        self.assertIn("Sheet", libro.sheetnames)

    def test_rechaza_historia_sin_rango_suficiente(self):
        filas = [dict(orden, parametros={"kg": 1000}) for orden in ORDENES_TOLVA]
        with self.assertRaisesRegex(ValueError, "no permiten distinguir"):
            aprender_familia("TOLVA", DEFINICIONES, filas)


if __name__ == "__main__":
    unittest.main()
