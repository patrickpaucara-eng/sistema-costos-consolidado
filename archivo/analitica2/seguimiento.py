# -*- coding: utf-8 -*-
"""SEG-01 · Seguimiento y reversión (ESPEC_ANALITICA2 §6, D-4; OT-090; I-2 OT-098 I2-c n.º 2-3). Función pura, Decimal,
orden por código (G-8). No ejecuta las tramas: las arma con analitica.canal_carga (G-4) y el runner las ejecuta por el canal.
I-2: estado «MEDIDO» (V2); filas CARGA @SEGUIM en la clave `carga_seguim` (V4); la reversión es solo un PROPONER de SISTEMA
con PCA_PROP = P-H05 (V5), sin APRUEBA-PARM: la aprueba una persona distinta (nivel 2, V8)."""
import re
from decimal import Decimal as D

from analitica import hallazgos, canal_carga
from analitica2.comun import d, q6

USUARIO = "SISTEMA"
MAX_PENDIENTE = 3                                   # §6 (D-4): más de 3 periodos pendiente ⇒ SIN_MEDICION
AUTO_TOL_DEF = D("0.10")                            # valor de catálogo de AUTO_TOL
REGLA = {"ENV.FAM_DESV": "H-03", "ENV.DIF_MAX": "H-02"}     # parámetro de nivel 1 → regla vigilada
PROP_REVERSION = "P-H05"                            # V5: entrada del catálogo cuya regla abre el motivo «H-05 R-71»
_PAQ = re.compile(r"^H05-(\d{4}-\d{2})-")


def _mes(per):
    return int(per[:4]) * 12 + int(per[5:7]) - 1


def _per(n):
    return f"{n // 12:04d}-{n % 12 + 1:02d}"


def _periodo_decision(c):
    """p sale de PCA_PAQ = H05-<p>-<código> (formato de autonomia_n1)."""
    m = _PAQ.match(str(c.get("PAQUETE") or ""))
    return m.group(1) if m else None


def _base(regla, hechos, rm, per, emp):
    """Número de objetos que evalúa la regla (misma base que hallazgos.evaluar)."""
    idx = hallazgos._indice(rm, per, emp)
    cu = hallazgos._por(idx, "OBJETO", "CU")
    if regla == "H-03":
        fam = hallazgos._por(idx, "FAMILIA", "CU")
        term = {}
        for o in hallazgos._objetos(hechos):
            if o.get("ESTADO") == "T" and o.get("TIPO", "OT") == "OT" and o.get("EMPRESA") in (None, emp):
                term.setdefault(o["COMPONENTE"], []).append(str(o["NUMERO"]))
        return sum(1 for f, ots in term.items() if len(ots) >= 2 and fam.get(f, D(0)) > 0 for ot in ots if ot in cu)
    dif, flex = hallazgos._por(idx, "OBJETO", "DIFERENCIA"), hallazgos._por(idx, "OBJETO", "ESTIMADO_FLEXIBLE")
    return sum(1 for ot in dif if flex.get(ot, D(0)) > 0)


def _pct(regla, hechos, rm, per, emp):
    n = _base(regla, hechos, rm, per, emp)
    if n == 0:
        return None
    marcados = sum(1 for a in hallazgos.evaluar(hechos, rm, per, emp) if a["TIPO"] == regla)
    return D(marcados) / D(n)


def _con_umbral(hechos, codigo, valor):
    """Hechos con solo `codigo` = valor vigente desde siempre (el umbral nuevo aplicado sobre p)."""
    return {"OBJETO": hallazgos._objetos(hechos),
            "PARAMETRO": [{"CODIGO": codigo, "VALOR": str(valor), "DESDE": "1900-01-01"}]}


def seguir(hechos, resultados_por_periodo, emp):
    hechos = hechos or {}
    rpp = resultados_por_periodo or {}
    cambios = hechos.get("PARAM_CAMBIO") or hechos.get("(sin MCD) PARAM_CAMBIO") or []
    ultimo = max(rpp) if rpp else None
    est, tramas = [], []
    for c in sorted(cambios, key=lambda c: float(c.get("NUMERO") or 0)):
        if (c.get("ESTADO") != "A" or c.get("TABLA", "PARAMETRO") != "PARAMETRO"
                or not str(c.get("MOTIVO") or "").startswith("H-05 R-71")):
            continue
        cod, p = c.get("CLAVE"), _periodo_decision(c)
        regla = REGLA.get(cod)
        if regla is None or p is None or p not in rpp:
            continue
        p1 = _per(_mes(p) + 1)
        pred = _pct(regla, _con_umbral(hechos, cod, d(c["VALOR_NUEVO"])), rpp[p], p, emp)
        fila = {"EDE_OBJ": cod, "EDE_REF": c.get("NUMERO"), "EDE_PER": p1, "EDE_PRED": None if pred is None else q6(pred),
                "EDE_REAL": None, "EDE_ERR": None, "EDE_REGLA": regla}
        if p1 not in rpp or pred is None:
            pendiente = _mes(ultimo) - _mes(p1) if ultimo else 0
            fila["ESTADO"] = "SIN_MEDICION" if pendiente > MAX_PENDIENTE else "PENDIENTE"
            est.append(fila)
            continue
        real = _pct(regla, hechos, rpp[p1], p1, emp)
        if real is None:
            fila["ESTADO"] = "PENDIENTE"
            est.append(fila)
            continue
        err = abs(real - pred)
        fila.update(EDE_REAL=q6(real), EDE_ERR=q6(err), ESTADO="MEDIDO")
        est.append(fila)
        tol = hallazgos._parametros(hechos, p1).get("AUTO_TOL", AUTO_TOL_DEF)
        if err > tol:
            paq = f"SEG01-{p1}-{cod}-{c.get('NUMERO')}"
            prop = canal_carga.trama_proponer(
                USUARIO, [dict(TABLA="PARAMETRO", CLAVE=cod, COLUMNA="PAR_VAL", VALOR_NUEVO=q6(d(c["ANTERIOR"])))],
                paq, f"REVERSION SEG-01 PCA_NUM={_ref(c.get('NUMERO'))}")
            for t in prop:                                 # canal_carga.ejecutar lee PCA_PROP de la trama (G-4: no se modifica)
                t["TRAMA"] += f";PCA_PROP={canal_carga._val(PROP_REVERSION)}"
            tramas += prop                                 # sin APRUEBA-PARM (I2-c n.º 3): vigencia p+2 la fija quien aprueba
    for f in est:
        f["EDE_ESTADO"] = f["ESTADO"]
    carga = canal_carga.trama_seguim(USUARIO, [dict(f, EDE_REF=_ref(f["EDE_REF"])) for f in est]) if est else []
    return {"est_decision": est, "carga_seguim": carga, "tramas": tramas}


def _ref(n):
    """PCA_NUM sin «.0» (los números de Excel llegan como float)."""
    try:
        x = D(str(n))
        return int(x) if x == x.to_integral_value() else n
    except Exception:
        return n
