"""S4 · Un exceso de merma mayor que el consumo da material normal negativo.

Código: metodos/reparto_etapas.py:147 `parte = (q - x) / q`; con LIN_EXC > LIN_CAN la parte normal es negativa.
Escenario: línea T15 de REB en julio (evento 51, LIN_CAN 150) con LIN_EXC = 160.
Correcto: rechazo «exceso mayor que el consumo» (en validar() o en calcular()).
"""
import unittest

import _comun as C

REB = "OT-SRV-REB-2025-07"


def _exc(x):
    def cambio(wb):
        lin = wb["LINEA"]; C.poner(lin, C.fila(lin, LIN_EVE=51, LIN_NUM=1), "LIN_EXC", x)
    return cambio


class S4(unittest.TestCase):
    def test_control_exceso_dentro_del_consumo(self):
        """LIN_EXC = 10 ≤ 150: material normal = 140 × 42, pérdida = 10 × 42."""
        res = C.calcular(C.libro(_exc(10)))
        self.assertEqual(res["etapa"], "ok", C.resumen(res))
        o = C.objeto(res, REB)
        self.assertAlmostEqual(o["md"], 140 * 42 - 0, delta=0.05)
        self.assertAlmostEqual(o["perdida"], 10 * 42, delta=0.05)

    def test_S4_exceso_160_de_150(self):
        res = C.calcular(C.libro(_exc(160)))
        if res["etapa"] == "ok":
            o = C.objeto(res, REB)
            self.fail(f"Acepta LIN_EXC 160 > LIN_CAN 150 sin aviso: MD normal de REB {o['md']}, pérdida {o['perdida']} "
                      f"(se consumieron 150 × 42 = 6,300). {C.resumen(res)}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
