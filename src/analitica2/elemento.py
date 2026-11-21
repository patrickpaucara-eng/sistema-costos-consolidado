# -*- coding: utf-8 -*-
"""ALG-13 · Evaluación por elemento (ESPEC_ANALITICA2 §3, OT-087). Pura: no escribe ni muta entradas."""
from decimal import Decimal as D

from .comun import (ELEMENTOS, d, q6, parametros, indice_objetos, can, poblacion, familias_agrupadas,
                    mensaje_6_campos, html_mensaje)


def _evaluaciones(hechos, resultado_metodo, per, emp, familias=None):
    """Lista de dicts con todos los cálculos por (OT, elemento) de las familias con n ≥ 2 (sin umbral aplicado)."""
    idx = indice_objetos(resultado_metodo, per, emp)
    pob = poblacion(hechos, idx, emp, familias)
    fams = familias_agrupadas(pob)
    out = []
    for fam, ots in fams.items():
        for o in ots:
            resto = [p for p in ots if p != o]
            can_o = can(idx, o)
            den = sum(can(idx, p) for p in resto)
            for e in ELEMENTOS:
                c_o = idx.get((o, "C_" + e), D(0))
                mu = (sum(idx.get((p, "C_" + e), D(0)) for p in resto) / den) if den else D(0)
                if mu == 0:
                    continue
                cu_e = c_o / can_o
                out.append(dict(ot=o, e=e, fam=fam, n=len(ots), cu_e=cu_e, mu=mu, d=cu_e / mu - 1,
                                imp=can_o * (cu_e - mu)))
    return out


def evaluar(hechos, resultado_metodo, per, emp, familias=None, con_mejor=True):
    """Filas H-13 según §3, ordenadas por (TIPO, REFERENCIA, REFERENCIA_2). Con `con_mejor=True` agrega las filas
    informativas H-13-MEJOR (D-3, siempre por defecto); `con_mejor=False` publica solo H-13."""
    par = parametros(hechos, per)
    ev = _evaluaciones(hechos, resultado_metodo, per, emp, familias)
    disparos = {}
    for x in ev:
        if x["d"] > par["A2.ELE_DESV_" + x["e"]]:
            disparos.setdefault(x["ot"], []).append(x)
    dominante = {o: max(xs, key=lambda x: (x["imp"], -ELEMENTOS.index(x["e"])))["e"] for o, xs in disparos.items()}
    filas = []
    for x in ev:
        u = par["A2.ELE_DESV_" + x["e"]]
        if x["d"] > u:
            tipo = "H-13"
        elif con_mejor and x["d"] < -u:
            tipo = "H-13-MEJOR"
        else:
            continue
        filas.append({"PERIODO": per, "EMPRESA": emp, "TIPO": tipo, "REFERENCIA": x["ot"], "REFERENCIA_2": x["e"],
                      "VALOR": q6(x["d"]), "UMBRAL": q6(u), "FAMILIA": x["fam"], "N_FAMILIA": x["n"],
                      "CU_ELEMENTO": q6(x["cu_e"]), "BENCHMARK": q6(x["mu"]), "IMPACTO": q6(x["imp"]),
                      "DOMINANTE": "S" if tipo == "H-13" and dominante.get(x["ot"]) == x["e"] else "N"})
    return sorted(filas, key=lambda f: (f["TIPO"], str(f["REFERENCIA"]), str(f["REFERENCIA_2"])))


_PROPUESTA = {"MD": "revisar consumo y precio de material", "PD": "revisar minutos y asignación de personal",
              "SD": "revisar servicios contratados", "CIF": "revisar la base de reparto y la capacidad usada"}


def _n(x, n=2):
    return f"{d(x):,.{n}f}"


def _sigma_mas(ot, fam, filas, idx):
    """Σ⁺ (D-6): suma de imp_e positivos de `ot` sobre TODOS sus elementos evaluados (incluye los que no disparan).
    La familia se infere de las OT con filas de la misma FAMILIA; se recalcula imp_e = CAN·(CU_e − μ_e) con μ_e del resto."""
    miembros = sorted({str(f["REFERENCIA"]) for f in filas if f.get("FAMILIA") == fam} | {ot})
    resto = [p for p in miembros if p != ot]
    can_o = can(idx, ot)
    den = sum(can(idx, p) for p in resto)
    if not can_o or not den:
        return None
    suma = D(0)
    for e in ELEMENTOS:
        mu = sum(idx.get((p, "C_" + e), D(0)) for p in resto) / den
        if mu == 0:
            continue
        imp = idx.get((ot, "C_" + e), D(0)) - can_o * mu
        if imp > 0:
            suma += imp
    return suma


def mensajes(filas, resultado_metodo, per, emp, carpeta=None, meses=1):
    """Mensajes de 6 campos (§3) para las filas H-13 dominantes. Con `carpeta`, escribe el HTML. Devuelve lista de dicts."""
    idx = indice_objetos(resultado_metodo, per, emp)
    por_ot = {}
    for f in filas:
        if f["TIPO"] == "H-13":
            por_ot.setdefault(f["REFERENCIA"], []).append(f)
    out = []
    for ot in sorted(por_ot):
        fs = por_ot[ot]
        f = next(x for x in fs if x["DOMINANTE"] == "S")
        e = f["REFERENCIA_2"]
        suma = _sigma_mas(ot, f["FAMILIA"], filas, idx)
        if suma is None or suma < d(f["IMPACTO"]):
            suma = sum(d(x["IMPACTO"]) for x in fs if d(x["IMPACTO"]) > 0)
        pct = d(f["VALOR"]) * 100
        c1 = f"En {ot}, el costo unitario de {e} es S/ {_n(f['CU_ELEMENTO'], 4)} frente a S/ {_n(f['BENCHMARK'], 4)} del resto de su familia (+{_n(pct)} %)"
        c2 = f"Es el elemento que más pesa en la desviación: S/ {_n(f['IMPACTO'])}" + (
            f" de S/ {_n(suma)} de exceso total ({_n(d(f['IMPACTO']) / suma * 100, 1)} %)" if suma > 0 else "")
        c3 = _PROPUESTA[e].capitalize()
        c4 = f"CONTRAFACTUAL: S/ {_n(f['IMPACTO'])}"
        ini = idx.get((ot, "INI_" + e), D(0))
        c5 = f"Benchmark con {f['N_FAMILIA'] - 1} OT de {meses} mes(es)" + (
            f"; incluye S/ {_n(ini)} de inventario inicial en proceso" if ini > 0 else "")
        enl = [f"N3/OBJETO_{ot}_C_{e}.html"]
        campos = mensaje_6_campos((c1, c2, c3, c4, c5), enl)
        ruta = html_mensaje(campos, f"H-13 · {ot} · {e}", carpeta, f"mensaje_H-13_{ot}.html") if carpeta else None
        out.append({"campos": campos, "tipo_impacto": "CONTRAFACTUAL", "html": ruta, "REFERENCIA": ot, "REFERENCIA_2": e})
    return out
