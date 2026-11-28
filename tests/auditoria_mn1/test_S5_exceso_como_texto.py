"""S5 · Un exceso de merma escrito como texto se vuelve 0.

Código: reyna_local/resultados.py:21-22 (`previos()`): `try: float(LIN_EXC) except: x = 0`.
Escenario: línea T15 de REB en julio (evento 51) con LIN_EXC = «3 kg» (hoy vale 3 → pérdida 126).
Correcto: rechazo con mensaje (no convertir el texto en 0).
"""
import unittest

import _comun as C

REB = "OT-SRV-REB-2025-07"


def _exc(x):
    def cambio(wb):
        lin = wb["LINEA"]; C.poner(lin, C.fila(lin, LIN_EVE=51, LIN_NUM=1), "LIN_EXC", x)
    return cambio


class S5(unittest.TestCase):
    def test_control_exceso_numerico(self):
        res = C.calcular(C.libro(_exc(3)))
        self.assertEqual(res["etapa"], "ok", C.resumen(res))
        self.assertAlmostEqual(C.objeto(res, REB)["perdida"], 126.0, delta=0.05)

    def test_S5_exceso_3_kg(self):
        res = C.calcular(C.libro(_exc("3 kg")))
        if res["etapa"] == "ok":
            o = C.objeto(res, REB)
            self.fail(f"Acepta LIN_EXC «3 kg» sin aviso: pérdida de REB {o['perdida']} (con 3 sería 126), "
                      f"MD normal {o['md']} (con 3 sería 6,174). {C.resumen(res)}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
