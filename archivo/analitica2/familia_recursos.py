# -*- coding: utf-8 -*-
"""ALG-12 · Familia por conjunto de recursos (ESPEC_ANALITICA2 §5, D-1). OT-089.
firma(OT) = conjunto ordenado de recursos MD y SD que consume: de su cotización (LIN_ESTIM de la ESTIMACION con
OBJETO = OT) si existe; si no, de sus líneas reales (LINEA de eventos con OBJETO = OT). PD y CIF no forman firma.
Agrupación determinista por NUMERO, contra la firma del primer miembro de cada familia, Jaccard >= A2.FIRMA_TOL.
Firma vacía → SIN_FIRMA / SIN_DATOS, nunca se agrupa. El precio no interviene (F-1). Solo capa 3 (§17.3)."""
from decimal import Decimal as D

from analitica2 import comun

ELEMENTOS_FIRMA = {"MD", "MAT", "SD"}


def _filas(hechos, *nombres):
    for n in nombres:
        if hechos.get(n):
            return hechos[n]
    return []


def _v(fila, *claves):
    for k in claves:
        if k in fila and fila[k] not in (None, ""):
            return fila[k]
    return None


def _elemento_de_recurso(hechos):
    """{REC_COD: elemento} vía RECURSO.TIPO_RECURSO → TIPO_RECURSO.ELEMENTO_COSTO."""
    tipos = {str(_v(t, "CODIGO", "TRE_COD")): str(_v(t, "ELEMENTO_COSTO", "TRE_ELE") or "")
             for t in _filas(hechos, "TIPO_RECURSO", "(sin MCD) TIPO_RECURSO")}
    out = {}
    for r in _filas(hechos, "RECURSO", "(sin MCD) RECURSO"):
        cod, tre = _v(r, "CODIGO", "REC_COD"), _v(r, "TIPO_RECURSO", "REC_TRE")
        if cod is not None:
            out[str(cod)] = tipos.get(str(tre), str(tre or ""))
    return out


def _es_firma(rec, elem):
    e = elem.get(rec)
    if e is None:                       # sin catálogo de recursos: se acepta por prefijo (MD.., SD..)
        return rec[:2] in ("MD", "SD")
    return e in ELEMENTOS_FIRMA


def firmas(hechos, emp=None, per=None):
    """{OT: (firma tuple, origen)} para las OT de `emp`."""
    elem = _elemento_de_recurso(hechos)
    cot = {}
    est_ot = {}
    for e in _filas(hechos, "ESTIMACION", "(sin MCD) ESTIMACION"):
        if emp in (None, _v(e, "EMPRESA", "EST_EMP")) or _v(e, "EMPRESA", "EST_EMP") is None:
            ot = _v(e, "OBJETO", "EST_OBJ")
            if ot is not None:
                est_ot[str(_v(e, "NUMERO", "EST_NUM"))] = str(ot)
    for l in _filas(hechos, "LIN_ESTIM", "(sin MCD) LIN_ESTIM"):
        ot = est_ot.get(str(_v(l, "ESTIMACION", "LES_EST")))
        rec = _v(l, "RECURSO", "LES_REC")
        if ot and rec is not None and _es_firma(str(rec), elem):
            cot.setdefault(ot, set()).add(str(rec))
    eve_ot = {}
    for e in _filas(hechos, "EVENTO", "(sin MCD) EVENTO"):
        ot = _v(e, "OBJETO", "EVE_OBJ")
        if ot is not None and (emp is None or _v(e, "EMPRESA", "EVE_EMP") in (None, emp)):
            eve_ot[str(_v(e, "NUMERO", "EVE_NUM"))] = str(ot)
    real = {}
    for l in _filas(hechos, "LINEA", "(sin MCD) LINEA"):
        ot = eve_ot.get(str(_v(l, "EVENTO", "LIN_EVE")))
        rec = _v(l, "RECURSO", "LIN_REC")
        if ot and rec is not None and _es_firma(str(rec), elem):
            real.setdefault(ot, set()).add(str(rec))
    no_ot = {str(_v(o, "NUMERO", "OBJ_NUM")) for o in comun.objetos(hechos)
             if str(_v(o, "TIPO", "OBJ_TIPO") or "OT") not in ("OT", "ORDEN")}
    ots = ({str(_v(o, "NUMERO", "OBJ_NUM")) for o in comun.objetos(hechos)
            if (emp is None or _v(o, "EMPRESA", "OBJ_EMP") in (None, emp))
            and str(_v(o, "TIPO", "OBJ_TIPO") or "OT") in ("OT", "ORDEN")} | set(cot) | set(real)) - no_ot   # §5: solo OT
    # D-9: una OT con inventario inicial en proceso consumió recursos en periodos que los hechos no traen
    con_inicial = {str(_v(i, "OBJETO", "IPR_OBJ")) for i in _filas(hechos, "INV_PROCESO", "(sin MCD) INV_PROCESO")
                   if D(str(_v(i, "VALOR", "IPR_VAL") or 0)) != 0
                   and (per is None or str(_v(i, "PERIODO", "IPR_PER") or "") < per)}      # D-10: solo inventario inicial
    out = {}
    for ot in sorted(ots):
        if cot.get(ot):
            out[ot] = (tuple(sorted(cot[ot])), "COTIZACION")
        elif ot in con_inicial:                                  # D-10: con o sin líneas del periodo
            out[ot] = ((), "REAL_PARCIAL")
        elif real.get(ot):
            out[ot] = (tuple(sorted(real[ot])), "REAL")
        else:
            out[ot] = ((), "SIN_DATOS")
    return out


def jaccard(a, b):
    """|A∩B| / |A∪B|; None si la unión es vacía (D-1: no se calcula 0/0)."""
    a, b = set(a), set(b)
    u = a | b
    return None if not u else D(len(a & b)) / D(len(u))


def agrupar(hechos, per, emp, tol=None):
    """{OT: {"familia", "firma", "origen"}} (§5)."""
    if tol is None:
        tol = comun.parametros(hechos, per).get("A2.FIRMA_TOL", D("1.00"))
    tol = D(str(tol))
    fam = []                                   # [(nombre, firma del primer miembro)]
    out = {}
    for ot, (firma, origen) in sorted(firmas(hechos, emp, per).items()):
        if not firma:
            out[ot] = {"familia": "SIN_FIRMA", "firma": [], "origen": origen}
            continue
        destino = None
        for nombre, f0 in fam:
            j = jaccard(firma, f0)
            if j is not None and j >= tol:
                destino = nombre
                break
        if destino is None:
            destino = f"F-{len(fam) + 1}"
            fam.append((destino, firma))
        out[ot] = {"familia": destino, "firma": list(firma), "origen": origen}
    return out


def familias_para_elemento(grupos):
    """Mapa {OT: familia} para analitica2.elemento.evaluar(familias=...); SIN_FIRMA queda fuera (no se compara)."""
    return {ot: g["familia"] for ot, g in grupos.items() if g["familia"] != "SIN_FIRMA"}
