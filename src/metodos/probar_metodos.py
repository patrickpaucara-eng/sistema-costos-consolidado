# -*- coding: utf-8 -*-
"""Pruebas de los métodos del almacén: (1) casos de verdad conocida (calculados a mano) y (2) equivalencia con la base:
el plug-in, alimentado con los hechos del kardex, debe dar el mismo valor que calculó la base. Uso (desde almacen/):
python -m metodos.probar_metodos ../Sistema_Costos.xlsx"""
import os, sys, io, contextlib
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # E-106: metodos/ está en la raíz, junto al sistema
for p in (RAIZ, os.path.join(RAIZ, "validacion_python")): sys.path.insert(0, p)
from metodos import valuacion as V
ok = []
def caso(n, c): ok.append(c); print(("PASA " if c else "FALLA") + "  " + n)
# 1) verdad conocida: entra 10 a 2.00, entra 10 a 4.00, sale 15
movs = [dict(tipo="E", cantidad=10, monto=20), dict(tipo="E", cantidad=10, monto=40), dict(tipo="S", cantidad=15)]
p, f = V.promedio_movil(movs), V.peps(movs)
caso("Promedio móvil a mano: sale 15 × 3.00 = 45.00; queda 5 por 15.00", (p["salidas"][0]["monto"], p["saldo"]["valor"]) == (45.0, 15.0))
caso("PEPS a mano: sale 10 × 2 + 5 × 4 = 40.00; queda 5 por 20.00", (f["salidas"][0]["monto"], f["saldo"]["valor"]) == (40.0, 20.0))
caso("Cambiar de método no cambia el total: salida + saldo = 60 en ambos", p["salidas"][0]["monto"] + p["saldo"]["valor"] == f["salidas"][0]["monto"] + f["saldo"]["valor"] == 60)
# 2) equivalencia con la base (materiales: recursos sin movimientos de cierre)
if len(sys.argv) > 1:
    import motor_espejo
    with contextlib.redirect_stdout(io.StringIO()): _, m = motor_espejo.autoprueba(sys.argv[1])
    h = m.T["KARDEX"]["h"]; K = [dict(zip(h, r)) for r in m.T["KARDEX"]["r"]]
    grupos = {}
    for r in K: grupos.setdefault((r["KDX_REC"], r["KDX_ALM"]), []).append(r)
    n = dif = 0
    for (rec, alm), rs in grupos.items():
        if any(str(r["KDX_TRX"]).startswith("T23") for r in rs) or any(float(r["KDX_SCAN"]) < 0 for r in rs): continue
        movs = [dict(tipo="E" if float(r["KDX_CAN"]) > 0 else "S", cantidad=abs(float(r["KDX_CAN"])), monto=float(r["KDX_VAL"])) for r in rs]
        sal = iter(V.promedio_movil(movs)["salidas"])
        for r in rs:
            if float(r["KDX_CAN"]) < 0:
                n += 1; dif += abs(next(sal)["monto"] - abs(float(r["KDX_VAL"]))) > 0.005
    caso(f"Equivalencia: el plug-in reproduce las {n} salidas valorizadas por la base", n > 0 and dif == 0)
    # 3) puerto de resultados (T25.4): el método publica y la base guarda sin tocar los hechos
    from metodos import publicar as PB
    hechos, filas = PB.valuacion_desde_kardex(K, "CAJA4KG", "ALM1", V.promedio_movil)
    def cargar(metodo):
        c = m.T["CARGA"]["r"]; nx = max([int(float(r[0])) for r in c] or [0]) + 1
        c.append([nx, "T25.4", "MODELO1", PB.trama("2026-07", "B", metodo, "1.0", hechos, filas), "", ""] + [""] * (len(m.T["CARGA"]["h"]) - 6))
        m.procesar_carga(); return c[-1]
    antes = [list(r) for r in m.T["LINEA"]["r"]]
    f1 = cargar("PROMEDIO_MOVIL"); RM = m.T["RESULTADO_METODO"]; n1 = len(RM["r"])
    caso("Un método APROBADO publica por el puerto: la base guarda sus valores", f1[4] == "OK" and n1 == len(filas))
    cargar("PROMEDIO_MOVIL")
    caso("Repetir la misma entrega no duplica (idempotente)", len(RM["r"]) == n1)
    caso("Un método EN_PRUEBA (PEPS) no puede publicar resultados oficiales", cargar("PEPS")[4] == "ERROR")
    caso("Los hechos no se tocan: LINEA queda igual", [list(r) for r in m.T["LINEA"]["r"]] == antes)
# 4) VIGENCIA (E-106): se usa la versión vigente al inicio del periodo, no la última
from metodos import correr_metodos as CR
from types import SimpleNamespace as NS
dm = lambda ver, desde: dict(archivo=f"v{ver}.py", faltas=[], modulo=NS(DEPENDE_DE={}), ficha=dict(nombre="X", version=ver, vigente_desde=desde, eje="VALUACION"))
reg = [dict(MRG_COD="X", MRG_VER="1.0", MRG_EST="APROBADO", MRG_DESDE=20260101), dict(MRG_COD="X", MRG_VER="2.0", MRG_EST="APROBADO", MRG_DESDE=20260801),
       dict(MRG_COD="X", MRG_VER="3.0", MRG_EST="EN_PRUEBA", MRG_DESDE=20260901)]
ms = [dm("1.0", "2026-01-01"), dm("2.0", "2026-08-01"), dm("3.0", "2026-09-01")]
caso("Julio usa la versión 1.0 (la 2.0 rige desde agosto)", [d["ficha"]["version"] for d in CR.elegir(ms, reg, 20260701)] == ["1.0"])
caso("Agosto usa la 2.0; una versión EN_PRUEBA no se usa sin pedirlo", [d["ficha"]["version"] for d in CR.elegir(ms, reg, 20261001)] == ["2.0"])
print(f"\nMÉTODOS: {sum(ok)} de {len(ok)} comprobaciones pasan"); sys.exit(0 if all(ok) else 1)
