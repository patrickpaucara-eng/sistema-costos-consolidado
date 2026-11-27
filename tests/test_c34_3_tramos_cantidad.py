import unittest

from openpyxl import Workbook

from reyna_local.tramos_cantidad import (
    calcular_costo_recurso,
    calcular_costos_recursos,
    guardar_tramos_en_libro,
    leer_tramos_de_libro,
)


TRAMOS_SOLDADURA = [
    {"desde": 0, "hasta": 160, "tasa": 30},
    {"desde": 160, "hasta": None, "tasa": 45},
]


class TramosCantidadTest(unittest.TestCase):
    def test_caso_manual_200_horas(self):
        self.assertEqual(calcular_costo_recurso(200, 30, TRAMOS_SOLDADURA), 6600)

    def test_limite_de_primer_tramo(self):
        self.assertEqual(calcular_costo_recurso(160, 30, TRAMOS_SOLDADURA), 4800)

    def test_sin_tramos_conserva_multiplicacion_lineal(self):
        cantidad, tasa = 183.75, 30.125
        self.assertEqual(calcular_costo_recurso(cantidad, tasa), cantidad * tasa)
        self.assertEqual(calcular_costos_recursos({"SOLD_H": cantidad}, {"SOLD_H": tasa})["total"], cantidad * tasa)

    def test_tramos_por_recurso_y_recurso_sin_tramos(self):
        resultado = calcular_costos_recursos(
            {"SOLD_H": 200, "MATERIAL": 10},
            {"SOLD_H": 30, "MATERIAL": 2},
            {"SOLD_H": TRAMOS_SOLDADURA},
        )
        self.assertEqual(resultado["detalle"], {"SOLD_H": 6600, "MATERIAL": 20})
        self.assertEqual(resultado["total"], 6620)

    def test_hoja_opcional_ausente_y_roundtrip(self):
        libro = Workbook()
        self.assertEqual(leer_tramos_de_libro(libro), {})
        guardar_tramos_en_libro(libro, {"SOLD_H": TRAMOS_SOLDADURA})
        recuperados = leer_tramos_de_libro(libro)
        self.assertEqual(calcular_costo_recurso(200, 30, recuperados["SOLD_H"]), 6600)
        self.assertIn("Sheet", libro.sheetnames)

    def test_rechaza_tramos_discontinuos_o_incompletos(self):
        with self.assertRaisesRegex(ValueError, "discontinuos"):
            calcular_costo_recurso(200, 30, [
                {"desde": 0, "hasta": 160, "tasa": 30},
                {"desde": 170, "hasta": None, "tasa": 45},
            ])
        with self.assertRaisesRegex(ValueError, "no cubre"):
            calcular_costo_recurso(200, 30, [{"desde": 0, "hasta": 160, "tasa": 30}])


if __name__ == "__main__":
    unittest.main()
