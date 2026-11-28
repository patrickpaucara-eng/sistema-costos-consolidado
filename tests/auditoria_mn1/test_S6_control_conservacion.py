"""S6 · El control de conservación no detecta lo que se pierde a la entrada.

Código: reyna_local/resultados.py:349-353 (`_control`): «recursos del periodo» = Σ aristas que salen de un recurso, es decir,
lo que YA entró al reparto, no lo registrado en LINEA / KARDEX.
Escenarios: los de S1a (ADM01 con TRE_ELE = ADM) y S2 (energía sin LIN_CU_DOC), y el de S3 contra el control de kardex.
Correcto: si el motor calcula y falta dinero respecto de los hechos del libro, el panel «Calidad y cuadre» debe marcarlo
(ok = False). Si el motor rechaza el libro, el control no hace falta y la prueba pasa.
"""
import unittest

import _comun as C
import test_S1_elemento_no_reconocido as S1
import test_S2_linea_sin_costo_unitario as S2
import test_S3_compra_sin_monto_kardex as S3


class S6(unittest.TestCase):
    def _detecta(self, res, falta, que, prefijo="Conservación del reparto"):
        if res["etapa"] != "ok":
            return
        total = round(sum(C.costos(res).values()), 2)
        if abs(total - C.BASE_TOTAL) <= 0.05:
            return                                           # no falta dinero: nada que detectar
        k = C.control(res, prefijo)
        self.assertFalse(k["ok"], f"{que}: faltan S/ {round(C.BASE_TOTAL - total, 2)} (se esperaban {falta}) y el control "
                                  f"«{k['control'][:60]}…» dice OK ({k['esperado']} = {k['obtenido']}).")

    def test_control_libro_sano(self):
        res = C.calcular(C.libro())
        self.assertTrue(all(k["ok"] for k in res["resultado"]["control"]))

    def test_S6a_con_escenario_S1(self):
        self._detecta(C.calcular(C.libro(S1._tipo_adm("ADM"))), 2000, "Escenario S1a")

    def test_S6b_con_escenario_S2(self):
        self._detecta(C.calcular(C.libro(S2._ene(None))), 1500, "Escenario S2")

    def test_S6c_con_escenario_S3_control_de_kardex(self):
        """Con la compra valuada en 0, ¿algún control del panel lo marca? Se revisan todos."""
        res = C.calcular(C.libro(S3._sin_fila_kardex(None)))
        if res["etapa"] != "ok" or C.costos(res) == C.BASE:
            return
        malos = [k["control"] for k in res["resultado"]["control"] if not k["ok"]]
        self.assertTrue(malos, f"Escenario S3: costos {C.costos(res)} (base {C.BASE}) y todos los controles del panel dicen OK.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
