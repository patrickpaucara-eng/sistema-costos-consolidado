"""S1 · Un elemento de costo que el motor no reconoce se descarta en silencio.

Código: metodos/reparto_etapas.py:57 (ELEM) y :140 (`if e is None: continue`). libro_dbd.py:24 documenta TRE_ELE como
«MAT, PER, IND, ADM, VTA, FIN…»; validar() no revisa TRE_ELE.
Correcto: o el libro se rechaza nombrando el recurso/tipo, o los S/ 2,000 de ADM01 siguen en el costo (total 28,140).
"""
import unittest

import _comun as C


def _tipo_adm(elemento):
    def cambio(wb):
        tre, rec = wb["TIPO_RECURSO"], wb["RECURSO"]
        C.agregar(tre, TRE_COD="GASTO_ADM", TRE_ELE=elemento, TRE_CAP=0, TRE_INV="N")
        C.poner(rec, C.fila(rec, REC_COD="ADM01"), "REC_TRE", "GASTO_ADM")
    return cambio


def _ind_mal_escrito(texto):
    def cambio(wb):
        tre = wb["TIPO_RECURSO"]
        C.poner(tre, C.fila(tre, TRE_COD="INDIRECTO"), "TRE_ELE", texto)
    return cambio


class S1(unittest.TestCase):
    def _no_pierde(self, res, que):
        if res["etapa"] != "ok":
            return                                              # rechazo con mensaje: comportamiento correcto
        total = round(sum(C.costos(res).values()), 2)
        self.assertAlmostEqual(total, C.BASE_TOTAL, delta=0.05,
                               msg=f"{que}: el costo se pierde sin aviso. Hoy: {C.resumen(res)}")

    def test_control_tipo_nuevo_con_IND(self):
        res = C.calcular(C.libro(_tipo_adm("IND")))
        self.assertEqual(res["etapa"], "ok", C.resumen(res))
        self.assertEqual(C.costos(res), C.BASE)

    def test_S1a_TRE_ELE_ADM(self):
        """TRE_ELE = ADM (valor que libro_dbd documenta como válido)."""
        self._no_pierde(C.calcular(C.libro(_tipo_adm("ADM"))), "ADM01 con TRE_ELE=ADM")

    def test_S1b_TRE_ELE_IND_con_espacio(self):
        """«IND » (espacio al final) en el tipo INDIRECTO: afecta ALQ, ENE, SUP y ADM01."""
        self._no_pierde(C.calcular(C.libro(_ind_mal_escrito("IND "))), "INDIRECTO con TRE_ELE='IND '")

    def test_S1c_TRE_ELE_minusculas(self):
        self._no_pierde(C.calcular(C.libro(_ind_mal_escrito("Ind"))), "INDIRECTO con TRE_ELE='Ind'")


if __name__ == "__main__":
    unittest.main(verbosity=2)
