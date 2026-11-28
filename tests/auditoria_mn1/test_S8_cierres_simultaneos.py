"""S8 · Dos emisiones de cierre simultáneas: la segunda pisa a la primera.

Código: reyna_local/cierre.py:104-115 (`emitir()`): lee versiones previas, calcula `version = 1 + max(...)` y escribe con
`write_text`, sin bloqueo ni creación exclusiva. El servidor es ThreadingHTTPServer (__main__.py:31) y la ruta
/api/cierres/emitir no toma ningún bloqueo propio.
Correcto: de dos emisiones del mismo periodo queda una versión 1 y un rechazo, o una versión 1 y una versión 2; nunca dos
respuestas «versión 1» con un solo archivo.

La ventana de carrera es corta (medida el 28/11: unos 4 ms entre listar() y escribir). Por eso:
- S8a repite AUDIT_S8_INTENTOS veces (30 por defecto) dos emisiones lanzadas juntas, con un calcular que devuelve resultados
  reales ya calculados (sin esperar): prueba el código de emitir() y cuenta cuántas veces se pisa;
- S8b hace AUDIT_S8_REALES intentos (2 por defecto) con el calcular real: mide si el _lock de calculo_local.calcular()
  lo evita en la práctica.
"""
import os
import threading
import unittest

import _comun as C
import reyna_local.cierre as CI
import test_S7_cierre_sin_sello_de_estado as S7

INTENTOS = int(os.environ.get("AUDIT_S8_INTENTOS", "30"))
REALES = int(os.environ.get("AUDIT_S8_REALES", "2"))


def _dos_a_la_vez(base, empresa, lib, calcular):
    for p in CI._carpeta(base).glob("*.json"): p.unlink()
    salidas, barrera = [None, None], threading.Barrier(2)

    def uno(i):
        barrera.wait()
        try:
            salidas[i] = ("ok", CI.emitir(base, empresa, C.PERIODO, "JCOSTOS", calcular, lib)["version"])
        except Exception as e:
            salidas[i] = ("rechazo", str(e)[:80])
    hilos = [threading.Thread(target=uno, args=(i,)) for i in (0, 1)]
    [h.start() for h in hilos]; [h.join() for h in hilos]
    return salidas, sorted(p.name for p in CI._carpeta(base).glob("*.json"))


def _pisada(salidas, archivos):
    """Dos respuestas «versión 1» (o la misma versión dos veces): una emisión quedó pisada por la otra."""
    oks = [v for k, v in salidas if k == "ok"]
    return len(oks) == 2 and oks[0] == oks[1]


def _valido(salidas, archivos):
    """Al menos una emisión terminó: el intento sirve para juzgar (si las dos fallan por otra causa, no)."""
    return any(k == "ok" for k, _ in salidas) and archivos


class S8(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        res = C.calcular(C.libro(S7.cuenta_merma))
        assert res["etapa"] == "ok", C.resumen(res)
        cls.res = res
        cls.lib = C.CL.ruta_libro(res["carpeta"], res["id"])
        cls.cache = {s: C.CL.calcular(res["carpeta"], C.PERIODO, s, res["id"]) for s in ("REAL", "CONTABLE", "ESTIMADO")}
        cls.rapido = staticmethod(lambda b, p, s, e: cls.cache[s])

    def test_control_emisiones_seguidas(self):
        """Una tras otra (no simultáneas): la segunda, sin motivo, se rechaza."""
        for p in CI._carpeta(self.res["carpeta"]).glob("*.json"): p.unlink()
        self.assertEqual(CI.emitir(self.res["carpeta"], self.res["id"], C.PERIODO, "JCOSTOS", self.rapido, self.lib)["version"], 1)
        with self.assertRaises(CI.Rechazo):
            CI.emitir(self.res["carpeta"], self.res["id"], C.PERIODO, "JCOSTOS", self.rapido, self.lib)

    def test_S8a_simultaneas_codigo_de_emitir(self):
        corridas = [_dos_a_la_vez(self.res["carpeta"], self.res["id"], self.lib, self.rapido) for _ in range(INTENTOS)]
        self.assertTrue(all(_valido(*o) for o in corridas), f"Intentos sin ninguna emisión: {[o for o in corridas if not _valido(*o)][:1]}")
        malas = [o for o in corridas if _pisada(*o)]
        print(f"  S8a · {len(malas)} de {INTENTOS} intentos terminaron con dos «versión 1» y un solo archivo")
        self.assertFalse(malas, f"{len(malas)} de {INTENTOS} intentos: la segunda emisión pisó a la primera. Ejemplo: {malas[:1]}")

    def test_S8b_simultaneas_calcular_real(self):
        corridas = [_dos_a_la_vez(self.res["carpeta"], self.res["id"], self.lib, C.CL.calcular) for _ in range(REALES)]
        self.assertTrue(all(_valido(*o) for o in corridas), f"Intentos sin ninguna emisión: {[o for o in corridas if not _valido(*o)][:1]}")
        malas = [o for o in corridas if _pisada(*o)]
        print(f"  S8b · {len(malas)} de {REALES} intentos con el calcular real se pisaron")
        self.assertFalse(malas, f"{len(malas)} de {REALES} intentos con el calcular real: se pisaron. Ejemplo: {malas[:1]}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
