# -*- coding: utf-8 -*-
"""I-3 (OT-102, pieza 2; regla L-2 de ARQUITECTURA_V4_1; lección L-12): recalcular un periodo CERRADO solo como simulación.
Puente de diferencias por OT y elemento entre lo publicado del periodo (eventos con EVE_PER = periodo y sin EVE_PER_REF) y lo
recalculado (lo mismo + los hechos tardíos registrados después con EVE_PER_REF = periodo). Nunca escribe ni publica (G-7, ADR-04).
Alcance: elementos directos del objeto (MD, MOD/PD, SD) desde LINEA; los tardíos de gasto de centros (sin objeto) se informan por
centro, porque su efecto en el CIF de las OT exige volver a repartir (se reporta, no se inventa)."""
FICHA = dict(nombre="SIMULAR_CIERRE", version="1.0", vigente_desde="2026-11-15", eje="CIERRE", objetivo="ESTIMADO",
             que_hace="Puente de diferencias de un periodo cerrado por hechos tardíos, sin publicar",
             formula="DIF = Σ LIN_MTO tardíos (EVE_PER_REF = periodo) por OT y elemento; RECALCULADO = PUBLICADO + DIF",
             fuente="ARQUITECTURA_V4_1 L-2; Oria (2026) L-12 corrección histórica con puente", supuestos="valuación promedio vigente al registrar el tardío",
             limites="el CIF reaplicado por tardíos de gasto de centros se informa por centro, no se reparte")
DEVUELVEN = {"T16"}
ELEMENTO = {"MAT": "MD", "MOD": "MOD", "PD": "MOD", "SD": "SD"}


def _s(v):
    return "" if v is None else str(v).strip()


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def calcular(hechos, per, emp):
    """hechos: {tabla física: [ {columna: valor} ]} (EVENTO, LINEA, RECURSO, TIPO_RECURSO). Devuelve
    {"OT": {ot|TOTAL: {ele: {PUBLICADO, RECALCULADO, DIF}}}, "CENTROS": {cen: DIF}, "publicado": False, "rotulo": str}."""
    tre = {_s(t.get("TRE_COD")): _s(t.get("TRE_ELE")).upper() for t in hechos.get("TIPO_RECURSO", [])}
    ele_rec = {_s(r.get("REC_COD")): ELEMENTO.get(tre.get(_s(r.get("REC_TRE")), ""), "") for r in hechos.get("RECURSO", [])}
    ev = {}
    for e in hechos.get("EVENTO", []):
        if _s(e.get("EVE_EMP")) != _s(emp):
            continue
        ref = _s(e.get("EVE_PER_REF"))
        if ref == _s(per):
            clase = "TARDIO"
        elif _s(e.get("EVE_PER")) == _s(per) and not ref:
            clase = "PUBLICADO"
        else:
            continue
        ev[_f(e.get("EVE_NUM"))] = (clase, _s(e.get("EVE_OBJ")), _s(e.get("EVE_CEN")), -1.0 if _s(e.get("EVE_TRX")) in DEVUELVEN else 1.0)
    pub, tar, cen = {}, {}, {}
    for l in hechos.get("LINEA", []):
        x = ev.get(_f(l.get("LIN_EVE")))
        if not x:
            continue
        clase, ot, c, sg = x
        e = ele_rec.get(_s(l.get("LIN_REC")), "")
        if not e:
            continue
        m = sg * _f(l.get("LIN_MTO"))
        if not ot:
            if clase == "TARDIO":
                cen[c] = round(cen.get(c, 0.0) + m, 2)
            continue
        dst = pub if clase == "PUBLICADO" else tar
        dst.setdefault(ot, {}).setdefault(e, 0.0)
        dst[ot][e] += m
    out, tot = {}, {}
    for ot in sorted(set(pub) | set(tar)):
        out[ot] = {}
        for e in ("MD", "MOD", "SD"):
            p, d = pub.get(ot, {}).get(e, 0.0), tar.get(ot, {}).get(e, 0.0)
            out[ot][e] = dict(PUBLICADO=round(p, 2), RECALCULADO=round(p + d, 2), DIF=round(d, 2))
            t = tot.setdefault(e, [0.0, 0.0]); t[0] += p; t[1] += d
    out["TOTAL"] = {e: dict(PUBLICADO=round(v[0], 2), RECALCULADO=round(v[0] + v[1], 2), DIF=round(v[1], 2)) for e, v in tot.items()}
    for e in ("MD", "MOD", "SD"):
        out["TOTAL"].setdefault(e, dict(PUBLICADO=0.0, RECALCULADO=0.0, DIF=0.0))
    return {"OT": out, "CENTROS": cen, "publicado": False,
            "rotulo": f"SIMULACIÓN del periodo cerrado {per}: no se publica; los tardíos ya entraron al periodo abierto"}
