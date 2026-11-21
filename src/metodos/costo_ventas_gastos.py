# -*- coding: utf-8 -*-
"""MÉTODO · COSTO_VENTAS_OT (ARQUITECTURA_V4_1 §7.7 ALG-06, R-54, I2 b).
CV(OT) = unidades vendidas × CU(OT); PT final = (OBJ_CAN − vendidas) × CU; MB = venta − CV; MBI = venta − vendidas × CUI."""
from decimal import Decimal as D
from collections import defaultdict

PENDIENTE = False
REDONDEO = "ALG-09"
FICHA = dict(nombre="COSTO_VENTAS_OT", version="1.0", vigente_desde="2026-01-01", eje="COSTO_VENTAS", objetivo="REAL",
    que_hace="Costo de ventas, productos terminados al cierre y márgenes por OT vendida",
    formula="CV = vendidas × CU; PT = (OBJ_CAN − vendidas) × CU; MB = venta − CV; MB% = MB/venta; MBI = venta − vendidas × CUI",
    fuente="ARQUITECTURA_V4_1 ALG-06; Oria (2026) hoja ER", supuestos="Las ventas son de OT terminadas (R-54)",
    limites="Productos terminados de periodos anteriores no se modelan en el MVP")
CONSUME = {"VENTA": ["EVENTO", "PERIODO", "CANTIDAD", "INGRESO", "EMPRESA"],
           "EVENTO": ["NUMERO", "OBJETO"], "(sin MCD) OBJETO": ["NUMERO", "EMPRESA", "ESTADO", "CANTIDAD"]}
DEPENDE_DE = {"LIQUIDACION_OT": [("OBJETO", "CU"), ("OBJETO", "CUI"), ("PERIODO", "CPT"), ("PERIODO", "IFPP")]}
PARAMETROS = [dict(id="PER", etq="Periodo", tipo="texto"), dict(id="EMP", etq="Empresa", tipo="texto")]
ENTREGA = {"OBJETO": ["UNIDADES_VENDIDAS", "VENTA", "CV", "MB", "MB_PCT", "MBI", "PT_UNIDADES", "PT_VALOR"],
           "PERIODO": ["VENTAS", "CV", "MB", "PT_FINAL", "CPT", "IFPP"]}


def _d(x):
    return D(repr(float(x))) if isinstance(x, float) else D(str(x if x not in (None, "") else 0))


def interno(hechos, parametros, previos):
    per, emp = parametros["PER"], parametros["EMP"]
    ev = {r["NUMERO"]: r["OBJETO"] for r in hechos["EVENTO"]}
    objs = {r["NUMERO"]: r for r in hechos["(sin MCD) OBJETO"] if r["EMPRESA"] == emp}
    liq = defaultdict(dict)
    for t, k, c, v in previos["LIQUIDACION_OT"]: liq[(t, k)][c] = _d(v)
    vend, ing = defaultdict(D), defaultdict(D)
    for r in hechos["VENTA"]:
        if r["PERIODO"] != per or r["EMPRESA"] != emp: continue
        o = ev.get(r["EVENTO"])
        if not o or str(objs.get(o, {}).get("ESTADO")) != "T": raise ValueError(f"R-54: venta del evento {r['EVENTO']} sobre una OT no terminada")
        vend[o] += _d(r["CANTIDAD"]); ing[o] += _d(r["INGRESO"])
    out, tot = {}, defaultdict(D)
    for o in sorted(objs):
        if str(objs[o]["ESTADO"]) != "T" or ("OBJETO", o) not in liq: continue
        cu, cui = liq[("OBJETO", o)]["CU"], liq[("OBJETO", o)]["CUI"]
        u = vend[o]; x = dict(UNIDADES_VENDIDAS=u, VENTA=ing[o], CV=u * cu)
        x["MB"] = x["VENTA"] - x["CV"]
        x["MB_PCT"] = x["MB"] / x["VENTA"] if x["VENTA"] else D(0)
        x["MBI"] = x["VENTA"] - u * cui
        x["PT_UNIDADES"] = _d(objs[o]["CANTIDAD"]) - u; x["PT_VALOR"] = x["PT_UNIDADES"] * cu
        out[o] = x
        tot["VENTAS"] += x["VENTA"]; tot["CV"] += x["CV"]; tot["PT_FINAL"] += x["PT_VALOR"]
    tot["MB"] = tot["VENTAS"] - tot["CV"]
    p_ = liq.get(("PERIODO", emp), {}); tot["CPT"] = p_.get("CPT", D(0)); tot["IFPP"] = p_.get("IFPP", D(0))
    if abs(tot["CPT"] - tot["CV"] - tot["PT_FINAL"]) > D("1e-9"): raise ValueError("I2 (b): CPT ≠ CV + PT final")
    return out, dict(tot)


def calcular(hechos, parametros, previos):
    out, tot = interno(hechos, parametros, previos)
    res = [("OBJETO", o, c, float(v)) for o, x in out.items() for c, v in x.items()]
    res += [("PERIODO", parametros["EMP"], c, float(v)) for c, v in tot.items()]
    return res, [f"Ventas {float(tot['VENTAS']):.2f}; CV {float(tot['CV']):.2f}; I2 (b) cuadra"]


CASOS = []
