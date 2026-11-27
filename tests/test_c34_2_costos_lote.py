import unittest

from reyna_local.conceptos_pedido import (
    calcular_conceptos_adicionales,
    calcular_preparacion_lotes,
    comparar_tamanos_lote,
    cotizar_lote,
)


class CostosLoteTest(unittest.TestCase):
    def test_caso_manual_uno_y_dos_lotes(self):
        uno = calcular_preparacion_lotes(50000, 50000, 1200, 0.354)
        dos = calcular_preparacion_lotes(50000, 25000, 1200, 0.354)
        self.assertEqual(uno["numero_lotes"], 1)
        self.assertEqual(uno["costo_variable"], 17700.0)
        self.assertEqual(uno["costo_total"], 18900.0)
        self.assertEqual(dos["numero_lotes"], 2)
        self.assertEqual(dos["costo_total"], 20100.0)

    def test_comparacion_muestra_diferencia_entre_tamanos(self):
        resultado = comparar_tamanos_lote(50000, [50000, 25000], 1200, 0.354)
        self.assertEqual([x["costo_pedido"] for x in resultado["alternativas"]], [18900.0, 20100.0])
        self.assertEqual(resultado["alternativas"][1]["diferencia_vs_primera"], 1200.0)
        self.assertEqual(resultado["diferencia_max_min"], 1200.0)

    def test_lote_incompleto_se_cuenta_como_lote_completo(self):
        resultado = calcular_preparacion_lotes(50001, 25000, 1200, 0.354)
        self.assertEqual(resultado["numero_lotes"], 3)
        self.assertEqual(resultado["costo_preparacion"], 3600.0)

    def test_conceptos_fijos_y_contingencia(self):
        resultado = calcular_conceptos_adicionales(1000, [
            {"concepto": "SUBCONTRATO", "importe": 150},
            {"concepto": "TRANSPORTE", "importe": 50},
            {"concepto": "GASTOS_GENERALES", "importe": 100},
            {"concepto": "CONTINGENCIA", "porcentaje": 10},
        ])
        self.assertEqual(resultado["base_porcentual"], 1300.0)
        self.assertEqual(resultado["costo_adicionales"], 430.0)
        self.assertEqual(resultado["costo_total"], 1430.0)

    def test_cotizacion_combina_costos_y_no_abc(self):
        resultado = cotizar_lote(50000, 25000, 1200, 0.354,
                                 [{"concepto": "TRANSPORTE", "importe": 500}])
        self.assertEqual(resultado["costo_pedido"], 20600.0)
        self.assertEqual(resultado["costo_unitario_final"], 0.412)

    def test_rechaza_porcentajes_y_categorias_invalidas(self):
        with self.assertRaisesRegex(ValueError, "no puede superar 100"):
            calcular_conceptos_adicionales(100, [{"concepto": "CONTINGENCIA", "porcentaje": 101}])
        with self.assertRaisesRegex(ValueError, "no reconocido"):
            calcular_conceptos_adicionales(100, [{"concepto": "OTRO", "importe": 1}])


if __name__ == "__main__":
    unittest.main()
