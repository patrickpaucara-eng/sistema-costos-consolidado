"""S9 · Las trazas recalculan todo el reparto por cada orden y elemento.

Código: reyna_local/resultados.py:287 (`_trazas()` llama a R.trazar por orden y elemento) y metodos/reparto_etapas.py:386
(`trazar()` vuelve a correr `correr()` entero).
Escenario: SERVITEC julio con N órdenes (las 2 de julio más N−2 copias de la de REB, con sus medidas DES_OT, BOB_OT, PRU_OT
y ADM_OT; sin material propio, para no agotar el stock). Se cuentan las llamadas a reparto_etapas.correr() durante un
calcular() y se mide el tiempo.
Correcto: las llamadas a correr() no crecen con el número de órdenes (las aristas se calculan una vez por cálculo).
Las mediciones se imprimen y quedan en resultados/S9_tiempos.json.
"""
import json
import os
import time
import unittest
from pathlib import Path

import _comun as C
from metodos import reparto_etapas as R

MEDIDAS_REB = {"DES_OT": 200, "BOB_OT": 500, "PRU_OT": 100, "ADM_OT": 1}
N_MEDIR = [int(x) for x in os.environ.get("AUDIT_S9_N", "2,10,20,50").split(",")]


def con_ordenes(n):
    def cambio(wb):
        obj, med = wb["OBJETO"], wb["MEDIDA"]
        modelo = [c.value for c in obj[C.fila(obj, OBJ_NUM="OT-SRV-REB-2025-07")]]
        for i in range(3, n + 1):
            cod = f"OT-SRV-X{i:03d}-2025-07"
            r = obj.max_row + 1
            for j, v in enumerate(modelo, 1): obj.cell(r, j).value = v
            C.poner(obj, r, "OBJ_NUM", cod)
            for crit, q in MEDIDAS_REB.items():
                C.agregar(med, MED_PER=C.PERIODO, MED_EMP="SRV", MED_CRIT=crit, MED_NIVEL="OBJ", MED_DEST=cod, MED_CAN=q)
    return cambio


def medir(n):
    """(llamadas a correr(), segundos de calcular(), órdenes en el resultado, segundos de UN correr())."""
    p = C.libro(con_ordenes(n) if n > 2 else None)
    original = R.correr; cuenta = [0]

    def contado(*a, **k):
        cuenta[0] += 1
        return original(*a, **k)
    R.correr = contado
    try:
        t = time.perf_counter(); res = C.calcular(p); seg = time.perf_counter() - t
    finally:
        R.correr = original
    assert res["etapa"] == "ok", C.resumen(res)
    return cuenta[0], seg, len(res["resultado"]["objetos"]), len(res["resultado"]["trazas"])


class S9(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.medidas = {}
        for n in N_MEDIR:
            cls.medidas[n] = medir(n)
            ll, seg, no, nt = cls.medidas[n]
            print(f"  S9 · {n:>4} órdenes: {ll:>5} llamadas a correr(), calcular() {seg:6.1f} s, {nt} tramos de traza")
        d = Path(__file__).resolve().parent / "resultados"; d.mkdir(exist_ok=True)
        (d / "S9_tiempos.json").write_text(json.dumps(
            {str(n): dict(llamadas_correr=v[0], segundos=round(v[1], 2), ordenes=v[2], tramos=v[3]) for n, v in cls.medidas.items()},
            ensure_ascii=False, indent=1), encoding="utf-8")

    def test_control_escenario_tiene_las_ordenes(self):
        for n, (_, _, no, _) in self.medidas.items():
            self.assertEqual(no, n)

    def test_S9_llamadas_no_crecen_con_las_ordenes(self):
        a, b = min(self.medidas), max(self.medidas)
        self.assertEqual(self.medidas[b][0], self.medidas[a][0],
                         f"Llamadas a correr(): {a} órdenes → {self.medidas[a][0]}; {b} órdenes → {self.medidas[b][0]}. "
                         f"Tiempo de calcular(): {self.medidas[a][1]:.1f} s → {self.medidas[b][1]:.1f} s.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
