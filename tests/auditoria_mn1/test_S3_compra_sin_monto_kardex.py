"""S3 · Una compra sin LIN_MTO entra al kardex derivado a valor 0.

Código: reyna_local/flujo.py:62 `val = round(_num(LIN_MTO) or 0, 2) if can > 0`.
Escenario: se quita de KARDEX la fila de la compra de julio (evento 50) para que flujo.py la derive de LINEA, y se deja
LIN_MTO vacío en esa línea (LIN_CAN 200, LIN_CU_DOC 43).
Correcto: la entrada vale 200 × 43 = 8,600 (REB 22,975 · MPR 5,165) o el cálculo se detiene con un mensaje.
"""
import unittest

import _comun as C


def _sin_fila_kardex(mto):
    def cambio(wb):
        kdx = wb["KARDEX"]; kdx.delete_rows(C.fila(kdx, KDX_EVE=50, KDX_LIN=1))
        lin = wb["LINEA"]; C.poner(lin, C.fila(lin, LIN_EVE=50, LIN_NUM=1), "LIN_MTO", mto)
    return cambio


class S3(unittest.TestCase):
    def test_control_fila_derivada_con_LIN_MTO(self):
        """Sin la fila en KARDEX pero con LIN_MTO: el kardex derivado debe dar lo mismo que el libro original."""
        res = C.calcular(C.libro(_sin_fila_kardex(8600)))
        self.assertEqual(res["etapa"], "ok", C.resumen(res))
        self.assertEqual(C.costos(res), C.BASE)

    def test_S3_compra_sin_LIN_MTO(self):
        res = C.calcular(C.libro(_sin_fila_kardex(None)))
        if res["etapa"] != "ok":
            return
        ent = [k for k in res["resultado"]["kardex"] if k["evento"] == "50-1"]
        self.assertEqual(C.costos(res), C.BASE,
                         msg=f"La compra se valúa a {ent[0]['importe'] if ent else '?'} en lugar de 8,600 sin aviso. "
                             f"Hoy: {C.resumen(res)}; costo unitario de la salida a REB: "
                             f"{[k['costo_unitario'] for k in res['resultado']['kardex'] if k['evento'] == '51-1']}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
