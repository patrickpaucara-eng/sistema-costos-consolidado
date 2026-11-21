# -*- coding: utf-8 -*-
"""MÉTODO · LIQUIDACION_OT (ARQUITECTURA_V4_1 §7.7 ALG-05, R-11, R-31, I2 a).
Costo de la OT por elemento = IIPP (INV_PROCESO del periodo anterior) + periodo (REPARTO_ETAPAS). CU solo para OT terminadas.
CPT = Σ CTOT de las terminadas; IFPP = Σ CTOT de las abiertas, SIN gastos (NIC 2 §16). Costo integral = CTOT + GAD + GVT."""
from decimal import Decimal as D
from collections import defaultdict

PENDIENTE = False
REDONDEO = "ALG-09"
FICHA = dict(nombre="LIQUIDACION_OT", version="1.0", vigente_desde="2026-01-01", eje="LIQUIDACION_OBJETO", objetivo="REAL",
    que_hace="Liquida cada OT por elemento: inicial + periodo; costo unitario de las terminadas; producción terminada y en proceso; costo integral",
    formula="C(OT,ele) = IIPP(OT,ele) + periodo(OT,ele); CU = CTOT/OBJ_CAN (T); CPT = Σ CTOT(T); IFPP = Σ CTOT(P); CI = CTOT + GAD + GVT",
    fuente="ARQUITECTURA_V4_1 ALG-05; Oria (2026) hoja de costos HC; NIC 2 §10-§16",
    supuestos="La IIPP del periodo anterior está en INV_PROCESO por elemento", limites="Sin unidades equivalentes (costeo por órdenes)")
CONSUME = {"(sin MCD) OBJETO": ["NUMERO", "EMPRESA", "ESTADO", "CANTIDAD", "TIPO", "COMPONENTE"],
           "(sin MCD) INV_PROCESO": ["PERIODO", "OBJETO", "VALOR", "EMPRESA", "ELEMENTO"],
           "PERIODO": ["CODIGO", "EMPRESA", "INICIO"]}
DEPENDE_DE = {"REPARTO_ETAPAS": [("OBJETO", "MD"), ("OBJETO", "PD"), ("OBJETO", "SD"), ("OBJETO", "CIF"), ("OBJETO", "GAD"), ("OBJETO", "GVT")]}
PARAMETROS = [dict(id="PER", etq="Periodo", tipo="texto"), dict(id="EMP", etq="Empresa", tipo="texto")]
ELEMENTOS = ["MD", "PD", "SD", "CIF"]
ENTREGA = {"OBJETO": [f"{x}_{e}" for e in ELEMENTOS for x in ("INI", "PER", "C")] + ["CTOT", "CU", "GAD", "GVT", "CI", "CUI"],
           "PERIODO": ELEMENTOS + ["GAD", "GVT", "IIPP", "CPT", "IFPP"], "IFPP": ELEMENTOS, "FAMILIA": ["CIF_UNITARIO", "CU"]}


def _d(x):
    return D(repr(float(x))) if isinstance(x, float) else D(str(x if x not in (None, "") else 0))


def periodo_anterior(periodos, per, emp):
    ps = sorted((int(r["INICIO"]), r["CODIGO"]) for r in periodos if r["EMPRESA"] == emp)
    ini = next(i for i, c in ps if c == per)
    ant = [c for i, c in ps if i < ini]
    return ant[-1] if ant else None


def interno(hechos, parametros, previos):
    per, emp = parametros["PER"], parametros["EMP"]
    objs = {r["NUMERO"]: r for r in hechos["(sin MCD) OBJETO"] if r["EMPRESA"] == emp and str(r["TIPO"]) != "INEF"}
    ant = periodo_anterior(hechos["PERIODO"], per, emp)
    ini = defaultdict(lambda: defaultdict(D))
    for r in hechos["(sin MCD) INV_PROCESO"]:
        if r["EMPRESA"] == emp and r["PERIODO"] == ant and r["ELEMENTO"] in ELEMENTOS: ini[r["OBJETO"]][r["ELEMENTO"]] += _d(r["VALOR"])
    per_v = defaultdict(lambda: defaultdict(D))
    for t, k, c, v in previos["REPARTO_ETAPAS"]:
        if t == "OBJETO": per_v[k][c] += _d(v)
    out, tot = {}, defaultdict(D)
    for o in sorted(set(objs) | set(ini)):
        if o not in objs: raise ValueError(f"INV_PROCESO trae la OT {o}, que no existe")
        x = {}
        for e in ELEMENTOS:
            x[f"INI_{e}"] = ini[o][e]; x[f"PER_{e}"] = per_v[o][e]; x[f"C_{e}"] = ini[o][e] + per_v[o][e]
            tot[e] += per_v[o][e]
        x["CTOT"] = sum(x[f"C_{e}"] for e in ELEMENTOS)
        x["GAD"], x["GVT"] = per_v[o]["GAD"], per_v[o]["GVT"]; tot["GAD"] += x["GAD"]; tot["GVT"] += x["GVT"]
        x["CI"] = x["CTOT"] + x["GAD"] + x["GVT"]
        can = _d(objs[o]["CANTIDAD"])
        if str(objs[o]["ESTADO"]) == "T":
            x["CU"] = x["CTOT"] / can; x["CUI"] = x["CI"] / can
            tot["CPT"] += x["CTOT"]
        else:
            tot["IFPP"] += x["CTOT"]          # R-31: sin GAD ni GVT
            for e in ELEMENTOS: x[f"IFPP_{e}"] = x[f"C_{e}"]
        tot["IIPP"] += sum(ini[o].values())
        out[o] = x
    fam = defaultdict(lambda: [D(0), D(0), D(0)])
    for o, x in out.items():
        if "CU" in x:
            f = fam[str(objs[o].get("COMPONENTE") or "")]; f[0] += x["C_CIF"]; f[1] += x["CTOT"]; f[2] += _d(objs[o]["CANTIDAD"])
    tot["_FAMILIA"] = {k: (v[0] / v[2], v[1] / v[2]) for k, v in fam.items() if v[2]}
    if abs(sum(tot[e] for e in ELEMENTOS) + tot["IIPP"] - tot["CPT"] - tot["IFPP"]) > D("1e-9"):
        raise ValueError("I2 (a): costos del periodo + IIPP ≠ CPT + IFPP")
    return out, dict(tot)


def calcular(hechos, parametros, previos):
    out, tot = interno(hechos, parametros, previos)
    res = []
    for o, x in out.items():
        for c in ENTREGA["OBJETO"]:
            if c in x: res.append(("OBJETO", o, c, float(x[c])))
        for e in ELEMENTOS:
            if f"IFPP_{e}" in x: res.append(("IFPP", o, e, float(x[f"IFPP_{e}"])))
    for c, v in tot.items():
        if c != "_FAMILIA": res.append(("PERIODO", parametros["EMP"], c, float(v)))
    for f, (ciu, cu) in sorted(tot["_FAMILIA"].items()): res += [("FAMILIA", f, "CIF_UNITARIO", float(ciu)), ("FAMILIA", f, "CU", float(cu))]
    return res, [f"CPT {float(tot.get('CPT', 0)):.2f}; IFPP {float(tot.get('IFPP', 0)):.2f}; I2 (a) cuadra"]


CASOS = []
