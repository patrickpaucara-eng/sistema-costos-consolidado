import unittest

from reyna_local.cotizador import costo_por_intervalos
from reyna_local.plazo_pedido import calcular_plazo_actividades


class CurvaSYPlazoTest(unittest.TestCase):
    def test_curva_s_caso_manual_seis_intervalos(self):
        resultado = costo_por_intervalos({"soldadura": 12}, lambda _codigo, _mes: 1,
                                         meses=6, intervalo=1, curva="s")
        self.assertEqual([x["costo"] for x in resultado["intervalos"]], [1, 2, 3, 3, 2, 1])
        self.assertEqual(resultado["total"], 12)

    def test_curva_s_se_reescala_a_numero_de_intervalos(self):
        resultado = costo_por_intervalos({"h": 10}, lambda _codigo, _mes: 1,
                                         meses=3, intervalo=1, curva="s")
        self.assertEqual([x["costo"] for x in resultado["intervalos"]], [2, 6, 2])
        self.assertEqual(sum(x["proporcion"] for x in resultado["intervalos"]), 1)

    def test_curvas_existentes_conservan_mismos_importes(self):
        for curva in ("pareja", "inicio", "final"):
            resultado = costo_por_intervalos({"h": 6}, lambda _codigo, _mes: 2,
                                             meses=3, intervalo=1, curva=curva)
            self.assertEqual(resultado["total"], 12)

    def test_caso_manual_85_horas_6_libres_y_12_solicitados(self):
        resultado = calcular_plazo_actividades(
            {"SOLD_H": 85}, {"SOLD_H": 8}, {"SOLD_H": [2] * 20}, 12)
        self.assertEqual(resultado["dias_earliest"], 15)
        self.assertEqual(resultado["dias_tarde"], 3)
        self.assertEqual(resultado["estado"], "3 días tarde")

    def test_carga_abierta_por_dia_reduce_capacidad_disponible(self):
        resultado = calcular_plazo_actividades(
            {"SOLD_H": 13}, {"SOLD_H": 8}, {"SOLD_H": [2, 4]}, 3)
        self.assertEqual(resultado["dias_earliest"], 3)
        self.assertEqual(resultado["estado"], "LLEGA")

    def test_varias_actividades_usan_la_que_mas_tarda(self):
        resultado = calcular_plazo_actividades(
            {"SOLD_H": 85, "PINTURA": 10}, {"SOLD_H": 6, "PINTURA": 5}, {}, 12)
        self.assertEqual(resultado["dias_earliest"], 15)
        self.assertEqual(resultado["por_actividad"]["PINTURA"]["dias"], 2)

    def test_rechaza_capacidad_inconsistente_o_ausente(self):
        with self.assertRaisesRegex(ValueError, "supera la capacidad"):
            calcular_plazo_actividades({"SOLD_H": 10}, {"SOLD_H": 6}, {"SOLD_H": [7]})
        with self.assertRaisesRegex(ValueError, "Falta capacidad"):
            calcular_plazo_actividades({"SOLD_H": 10}, {})


if __name__ == "__main__":
    unittest.main()
