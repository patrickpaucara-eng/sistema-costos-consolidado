"""S2 · Una línea con monto (LIN_MTO) pero sin costo unitario (LIN_CU_DOC) vale 0 en el reparto.

Código: metodos/reparto_etapas.py:151 `m = CANTIDAD × COSTO_UNITARIO_DOCUMENTO` (ignora LIN_MTO).
Escenario: línea T17 de energía de julio (evento 55, ENE, LIN_MTO = 1,500) con LIN_CU_DOC vacío.
Correcto: energía S/ 1,500 en el costo (total 28,140) o rechazo con mensaje.
"""
import unittest

import _comun as C


def _ene(cu, mto=1500):
    def cambio(wb):
        lin = wb["LINEA"]; f = C.fila(lin, LIN_EVE=55, LIN_NUM=1)
        C.poner(lin, f, "LIN_CU_DOC", cu); C.poner(lin, f, "LIN_MTO", mto)
    return cambio


class S2(unittest.TestCase):
    def test_control_mismo_dato_completo(self):
        res = C.calcular(C.libro(_ene(1500)))
        self.assertEqual(res["etapa"], "ok", C.resumen(res))
        self.assertEqual(C.costos(res), C.BASE)

    def test_S2_LIN_MTO_sin_LIN_CU_DOC(self):
        res = C.calcular(C.libro(_ene(None)))
        if res["etapa"] != "ok":
            return
        total = round(sum(C.costos(res).values()), 2)
        self.assertAlmostEqual(total, C.BASE_TOTAL, delta=0.05,
                               msg=f"La energía (LIN_MTO 1,500) se pierde sin aviso. Hoy: {C.resumen(res)}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
