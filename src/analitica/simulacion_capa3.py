# -*- coding: utf-8 -*-
"""B7a · Simulación y contrafactual de la capa 3 (§9.4, §9.7 contratos 3 y 4). OT-083. No escribe nada."""
import copy
import importlib
from decimal import Decimal as D, getcontext, ROUND_HALF_UP

getcontext().prec = 28
_CADENA = ("reparto_etapas", "liquidacion", "costo_ventas_gastos")   # métodos de capa 2 que se re-ejecutan, en orden


def _d(v):
    return D(str(v))


def _aplicar_paquete(hechos, paquete):
    """Copia profunda de los hechos con los cambios del paquete (§9.7 contrato 4). Acepta dos formas de fila:
    - paquete de PARAM_CAMBIO (casos/V41/P10_paquete_abc.json): {tabla, clave "ETAPA|ORIGEN", col, anterior, nuevo};
      col = RRE_CRIT cambia el criterio; col = (NUEVA) agrega la fila "ETAPA|ORIGEN|CRITERIO|DESDE|FUENTE";
    - forma genérica: {TABLA, CLAVE, COLUMNA, VALOR_NUEVO} con (NUEVA)/(RETIRA)."""
    h = copy.deepcopy(hechos)
    for c in paquete:
        if "tabla" in c:
            if c["tabla"] != "REGLA_REPARTO": raise ValueError(f"simular: tabla {c['tabla']} no soportada en el paquete")
            rr = h.setdefault("(sin MCD) REGLA_REPARTO", [])
            if c["col"] == "(NUEVA)":
                et, org, crit, desde = str(c["nuevo"]).split("|")[:4]
                rr.append(dict(ETAPA=et, ORIGEN=org, CRITERIO=crit, DESDE=int(desde)))
            else:
                et, org = str(c["clave"]).split("|")
                hit = [f for f in rr if str(f["ETAPA"]) == et and str(f["ORIGEN"]) == org]
                if not hit: raise ValueError(f"simular: no existe la regla {c['clave']}")
                for f in hit: f["CRITERIO"] = c["nuevo"]
            continue
        filas = h.setdefault(c["TABLA"], [])
        k = str(c["CLAVE"])
        if c["COLUMNA"] == "(NUEVA)":
            filas.append(dict(c["VALOR_NUEVO"]))
        elif c["COLUMNA"] == "(RETIRA)":
            filas[:] = [f for f in filas if str(f.get("CLAVE", f.get("CODIGO"))) != k]
        else:
            hit = [f for f in filas if str(f.get("CLAVE", f.get("CODIGO"))) == k]
            if not hit:
                raise ValueError(f"simular: no existe {c['TABLA']} {k}")
            hit[0][c["COLUMNA"]] = c["VALOR_NUEVO"]
    return h


def simular(hechos, paquete, per=None, emp=None):
    """Corre la misma cadena de capa 2 (valuación → reparto → liquidación) con objetivo ESTIMADO sobre una COPIA con el
    paquete aplicado. No publica (I6). Devuelve {"OBJETO": {obj: {CIF_UNITARIO, CU, CTOT}}, "TOTAL", "publicado": False}."""
    from metodos import valuacion, reparto_etapas, liquidacion
    h = _aplicar_paquete(hechos, paquete)
    if per is None or emp is None:
        ps = sorted((int(p["INICIO"]), p["CODIGO"], p["EMPRESA"]) for p in h.get("PERIODO", []))
        if not ps: raise ValueError("simular: sin PERIODO en los hechos")
        per, emp = per or ps[-1][1], emp or ps[-1][2]
    par = {"PER": per, "EMP": emp, "OBJETIVO": "ESTIMADO"}
    prev = {"VALUACION_PROMEDIO": valuacion.calcular(h, par, {})[0] if "(sin MCD) KARDEX" in h else []}
    prev["REPARTO_ETAPAS"] = reparto_etapas.calcular(h, par, prev)[0]
    liq = liquidacion.calcular(h, par, prev)[0]
    can = {str(o["NUMERO"]): _d(o["CANTIDAD"]) for o in h.get("(sin MCD) OBJETO", []) if o.get("EMPRESA") in (None, emp)}
    out = {}
    for t, k, c, v in liq:
        if t == "OBJETO" and c in ("C_CIF", "CU", "CTOT"):
            out.setdefault(str(k), {})["CIF_UNITARIO" if c == "C_CIF" else c] = _d(v) / can[str(k)] if c == "C_CIF" else _d(v)
    return {"OBJETO": out, "TOTAL": {"CTOT": sum((x.get("CTOT", D(0)) for x in out.values()), D(0))},
            "publicado": False, "objetivo": "ESTIMADO"}


def _red2(x):
    return x.quantize(D("0.01"), rounding=ROUND_HALF_UP)


def contrafactual(hallazgo, hechos, resultado_metodo):
    """Impacto en S/ con su tipo para H-01, H-02 y H-03 (fórmula cerrada con otro insumo; §9.3, §9.7 contrato 3).
    H-01/H-03: valor = margen que habría dejado la OT con el CU de su familia (P-34: 2,971.87 para OT1520);
    H-02: valor = diferencia total y su detalle ALG-08."""
    t, ot, per, emp = hallazgo["TIPO"], str(hallazgo["REFERENCIA"]), hallazgo["PERIODO"], hallazgo["EMPRESA"]
    idx = {(r["tipo"], str(r["clave"]), r["concepto"]): r["valor"] for r in resultado_metodo
           if r.get("per") in (None, per) and r.get("emp") in (None, emp) and r.get("sistema") in (None, "REAL")}
    if t == "H-02":
        det = {k: _d(v) for (tp, c, k), v in idx.items() if tp == "OBJETO" and c == ot and k.startswith("VAR_")}
        return {"tipo": "CONTRAFACTUAL", "valor": _red2(_d(idx[("OBJETO", ot, "DIFERENCIA")])), "detalle": det}
    if t not in ("H-01", "H-03"):
        raise ValueError(f"contrafactual: {t} no tiene impacto contrafactual (H-04/H-05 simulan; H-06/H-07 sin impacto)")
    comp = next(o["COMPONENTE"] for o in (hechos.get("OBJETO") or hechos.get("(sin MCD) OBJETO") or []) if str(o["NUMERO"]) == ot)
    cu_fam = _d(idx[("FAMILIA", comp, "CU")])
    vend = next(v for v in hechos.get("VENTA", []) if str(v["OBJETO"]) == ot and v.get("PERIODO") in (None, per))
    margen = _d(vend["INGRESO"]) - cu_fam * _d(vend["CANTIDAD"])
    return {"tipo": "CONTRAFACTUAL", "valor": _red2(margen), "cu_familia": cu_fam, "unidades": _d(vend["CANTIDAD"])}


def sin_impacto(motivo):
    """H-06 y H-07: el campo 4 del mensaje dice SIN_IMPACTO_MONETARIO y por qué."""
    if not motivo:
        raise ValueError("SIN_IMPACTO_MONETARIO exige el motivo")
    return {"tipo": "SIN_IMPACTO_MONETARIO", "valor": None, "motivo": motivo}
