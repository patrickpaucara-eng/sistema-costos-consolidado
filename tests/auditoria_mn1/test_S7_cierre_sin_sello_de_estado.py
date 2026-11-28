"""S7 · El cierre no sella el estado ni el historial.

Código: reyna_local/cierre.py:141 (`verificar()`): la huella se calcula sin `estado` ni `historial`; `accion()` (:121) solo
continúa si verificar() da INTEGRO.
Escenario: se emite el cierre de julio con el motor real y luego se edita el JSON del paquete.
Correcto: cualquier cambio en estado o historial da ALTERADO, y accion() no deja seguir.

Preparación del libro: SERVITEC no trae la cuenta del motor operativo CTA_OBJ_PER.COP_PERD, y sin ella el cierre se bloquea
en la conciliación (merma 126 del costeo contra 0 del motor). Se agrega esa cuenta con 126, lo que el motor habría acumulado.
"""
import json
import unittest

import _comun as C
import reyna_local.cierre as CI


def cuenta_merma(wb):
    C.agregar(wb["CTA_OBJ_PER"], COP_OBJ="OT-SRV-REB-2025-07", COP_PER="2025-07", COP_PERD=126, COP_EMP="SRV")


def emitir_julio():
    """Devuelve (carpeta, id del paquete, ruta del libro registrado)."""
    res = C.calcular(C.libro(cuenta_merma))
    assert res["etapa"] == "ok", C.resumen(res)
    lib = C.CL.ruta_libro(res["carpeta"], res["id"])
    out = CI.emitir(res["carpeta"], res["id"], C.PERIODO, "JCOSTOS", C.CL.calcular, lib)
    return res["carpeta"], out["id"], lib


class S7(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base, cls.pid, cls.lib = emitir_julio()
        cls.archivo = CI._carpeta(cls.base) / f"{cls.pid}.json"
        cls.original = cls.archivo.read_text(encoding="utf-8")

    def setUp(self):
        self.archivo.write_text(self.original, encoding="utf-8")        # cada prueba parte del paquete recién emitido

    def _editar(self, f):
        p = json.loads(self.archivo.read_text(encoding="utf-8")); f(p)
        self.archivo.write_text(json.dumps(p, ensure_ascii=False), encoding="utf-8")

    def test_control_recien_emitido_integro(self):
        self.assertEqual(CI.verificar(self.base, self.pid)["estado"], "INTEGRO")

    def test_control_cifra_alterada(self):
        self._editar(lambda p: p["resultados"]["REAL"]["kpi"].update(margen_operativo=999999))
        self.assertEqual(CI.verificar(self.base, self.pid)["estado"], "ALTERADO")

    def test_S7a_estado_y_aprobacion_falsos(self):
        def f(p):
            p["estado"] = "APROBADO"
            p["historial"].append(dict(accion="APROBAR", usuario="GERENTE", fecha="2025-08-01T09:00:00", comentario="(falso)"))
        self._editar(f)
        self.assertEqual(CI.verificar(self.base, self.pid)["estado"], "ALTERADO",
                         "Se cambió el estado a APROBADO y se agregó una aprobación falsa: verificar() responde INTEGRO.")

    def test_S7b_saltarse_la_revision_de_contabilidad(self):
        """Se pone «REVISADO» a mano (sin CONTAB) y la gerencia aprueba por la vía normal."""
        self._editar(lambda p: p.update(estado="REVISADO"))
        try:
            r = CI.accion(self.base, self.pid, "APROBAR", "GERENTE", "ok", self.lib)
        except CI.Rechazo:
            return                                                       # correcto: no deja seguir
        self.fail(f"accion(APROBAR) aceptó un paquete que nadie revisó: {r}. Historial final: "
                  f"{[h['accion'] for h in json.loads(self.archivo.read_text(encoding='utf-8'))['historial']]}")

    def test_S7c_borrar_quien_emitio(self):
        """Separación de funciones: quien emitió no puede aprobar. Se cambia el usuario del paso EMITIR en el historial."""
        def f(p):
            p["historial"][0]["usuario"] = "OTRO"; p["estado"] = "REVISADO"
        self._editar(f)
        # JCOSTOS no tiene perfil GERENCIA; la prueba usa GERENTE, que tampoco figura ya en el historial
        self.assertEqual(CI.verificar(self.base, self.pid)["estado"], "ALTERADO",
                         "Se reescribió quién emitió el cierre y verificar() responde INTEGRO.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
