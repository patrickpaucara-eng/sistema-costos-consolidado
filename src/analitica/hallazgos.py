# -*- coding: utf-8 -*-
"""B7a · Capa 3, hallazgos H-01 a H-04, H-06 y H-07 (ARQUITECTURA_V4_1 §9.3, §9.7 contratos 1 y 5). OT-083.
Funciones puras: leen RESULTADO_METODO y PARAMETRO (hechos) y devuelven filas de ALERTA; no escriben en ninguna base.
Los hallazgos son derivados: republicar el mismo periodo REEMPLAZA sus filas (publicar_alertas). H-05 es de B7b."""
from decimal import Decimal as D, getcontext, ROUND_HALF_UP

getcontext().prec = 28
_E6 = D("0.000001")


def _d(v):
    return D(str(v))


def _q(x):
    return x.quantize(_E6, rounding=ROUND_HALF_UP)


def _parametros(hechos, per):
    """{código: valor} con la fila vigente al inicio del periodo (DESDE <= AAAA-MM-01; la más reciente)."""
    filas = hechos.get("PARAMETRO") or hechos.get("(sin MCD) PARAMETRO") or []
    ini = f"{per}-01"
    vig = {}
    def fecha(x):   # 19000101 (número del catálogo) o "1900-01-01"
        x = str(x or "")
        return f"{x[:4]}-{x[4:6]}-{x[6:8]}" if x.isdigit() and len(x) == 8 else x
    for f in sorted(filas, key=lambda r: (str(r.get("CODIGO")), fecha(r.get("DESDE")))):
        if fecha(f.get("DESDE")) <= ini:
            try:
                vig[f["CODIGO"]] = _d(f["VALOR"])
            except Exception:   # noqa: BLE001 — parámetros de texto (p. ej. METODO_SRV) no son umbrales
                continue
    # R-72: si la fila vigente empieza después del periodo, rige el PCA_ANT del último cambio aprobado de ese parámetro
    cambios = hechos.get("PARAM_CAMBIO") or hechos.get("(sin MCD) PARAM_CAMBIO") or []
    for f in filas:
        cod = f.get("CODIGO")
        if cod in vig or fecha(f.get("DESDE")) <= ini:
            continue
        ap = [c for c in cambios if c.get("TABLA") == "PARAMETRO" and c.get("CLAVE") == cod and c.get("COLUMNA") == "PAR_VAL"
              and c.get("ESTADO") == "A"]
        if ap:
            try:
                vig[cod] = _d(sorted(ap, key=lambda c: float(c.get("NUMERO") or 0))[-1]["ANTERIOR"])
            except Exception:   # noqa: BLE001
                continue
    return vig


def _requerido(par, codigo):
    if codigo not in par:
        raise ValueError(f"falta el parámetro {codigo} en PARAMETRO")
    return par[codigo]


def _indice(resultado_metodo, per, emp):
    """{(tipo, clave, concepto): valor Decimal} del periodo y empresa; por orden de código."""
    out = {}
    for r in sorted(resultado_metodo, key=lambda r: (str(r.get("tipo")), str(r.get("clave")), str(r.get("concepto")), str(r.get("metodo")))):
        if r.get("per") in (None, per) and r.get("emp") in (None, emp) and isinstance(r.get("valor"), (int, float, D)):
            out[(r["tipo"], str(r["clave"]), r["concepto"], r.get("sistema"))] = _d(r["valor"])
    return out


def _por(idx, tipo, concepto, sistema=None):
    return {c: v for (t, c, k, s), v in sorted(idx.items()) if t == tipo and k == concepto and (sistema is None or s == sistema)}


def _objetos(hechos):
    return hechos.get("OBJETO") or hechos.get("(sin MCD) OBJETO") or []


def _fila(per, emp, tipo, ref, ref2, valor, umbral):
    return {"PERIODO": per, "EMPRESA": emp, "TIPO": tipo, "REFERENCIA": ref, "REFERENCIA_2": ref2,
            "VALOR": _q(valor), "UMBRAL": _q(umbral)}


def evaluar(hechos, resultado_metodo, per, emp):
    """Filas ALERTA {PERIODO, EMPRESA, TIPO, REFERENCIA, REFERENCIA_2, VALOR, UMBRAL}, ordenadas por (TIPO, REFERENCIA).
    VALOR de H-02, H-03 y H-04 es fracción (0.0804 = 8.04 %). Una regla cuyo parámetro no existe se omite (no se inventa)."""
    par = _parametros(hechos, per)
    idx = _indice(resultado_metodo, per, emp)
    filas = []
    cu = _por(idx, "OBJETO", "CU")

    # H-01: CU real de una OT vendida > precio × (1 − rentabilidad exigida)
    if "ENV.RENT_EXIGIDA" in par:
        rent_def = par["ENV.RENT_EXIGIDA"]
        ventas = {}
        for v in hechos.get("VENTA") or []:
            if v.get("PERIODO") in (None, per) and v.get("EMPRESA") in (None, emp) and _d(v["CANTIDAD"]) > 0:
                ventas[str(v["OBJETO"])] = v
        for ot in sorted(ventas):
            v = ventas[ot]
            propia = v.get("RENTABILIDAD", v.get("EST_RENT"))
            rent = _d(propia) if propia not in (None, "") else rent_def
            precio = _d(v["INGRESO"]) / _d(v["CANTIDAD"])
            maximo = precio * (1 - rent)
            if ot in cu and cu[ot] > maximo:
                filas.append(_fila(per, emp, "H-01", ot, "ENV.RENT_EXIGIDA", cu[ot], maximo))

    # H-02: variación total / estimado flexible > ENV.DIF_MAX
    if "ENV.DIF_MAX" in par:
        dif, flex = _por(idx, "OBJETO", "DIFERENCIA"), _por(idx, "OBJETO", "ESTIMADO_FLEXIBLE")
        for ot in sorted(dif):
            if flex.get(ot, D(0)) > 0 and dif[ot] / flex[ot] > par["ENV.DIF_MAX"]:
                filas.append(_fila(per, emp, "H-02", ot, "ENV.DIF_MAX", dif[ot] / flex[ot], par["ENV.DIF_MAX"]))

    # H-03: CU(OT) > CU familia × (1 + ENV.FAM_DESV), en familias con >= 2 OT terminadas
    if "ENV.FAM_DESV" in par:
        cu_fam = _por(idx, "FAMILIA", "CU")
        term = {}
        for o in _objetos(hechos):
            if o.get("ESTADO") == "T" and o.get("TIPO", "OT") == "OT" and o.get("EMPRESA") in (None, emp):
                term.setdefault(o["COMPONENTE"], []).append(str(o["NUMERO"]))
        for fam in sorted(term):
            if len(term[fam]) < 2 or fam not in cu_fam or cu_fam[fam] <= 0:
                continue
            for ot in sorted(term[fam]):
                if ot in cu and cu[ot] > cu_fam[fam] * (1 + par["ENV.FAM_DESV"]):
                    filas.append(_fila(per, emp, "H-03", ot, "ENV.FAM_DESV", cu[ot] / cu_fam[fam] - 1, par["ENV.FAM_DESV"]))

    # H-04: |CIF unitario ABC − tradicional| / tradicional > P10.ABC_DESV, en algún objeto
    if "P10.ABC_DESV" in par:
        trad, abc = _por(idx, "OBJETO", "CIF_UNITARIO", "TRADICIONAL"), _por(idx, "OBJETO", "CIF_UNITARIO", "ABC")
        for obj in sorted(set(trad) & set(abc)):
            if trad[obj] != 0:
                d = (abc[obj] - trad[obj]) / trad[obj]
                if abs(d) > par["P10.ABC_DESV"]:
                    filas.append(_fila(per, emp, "H-04", obj, "P10.ABC_DESV", d, par["P10.ABC_DESV"]))

    # H-06: ineficiencia de un recurso de capacidad > PD_OCIO_TOL
    if "PD_OCIO_TOL" in par:
        for rec, v in sorted(_por(idx, "RECURSO", "INEF").items()):
            if v > par["PD_OCIO_TOL"]:
                filas.append(_fila(per, emp, "H-06", rec, "PD_OCIO_TOL", v, par["PD_OCIO_TOL"]))

    # H-07: una cotización emitida queda EXCEDIDA (el estado es texto: se lee de RESULTADO_METODO sin filtrar numéricos)
    for r in sorted(resultado_metodo, key=lambda r: str(r.get("clave"))):
        if (r.get("tipo") == "ESTIMACION" and r.get("concepto") == "ESTADO" and r.get("valor") == "EXCEDIDO"
                and r.get("per") in (None, per) and r.get("emp") in (None, emp)):
            filas.append(_fila(per, emp, "H-07", str(r["clave"]), "COSTO_MAXIMO", D(0), D(0)))

    return sorted(filas, key=lambda f: (f["TIPO"], str(f["REFERENCIA"]), str(f["REFERENCIA_2"])))


def publicar_alertas(alertas_actuales, nuevas, per, emp):
    """Contrato 1: republicar el mismo periodo/empresa REEMPLAZA sus filas H-xx, no las duplica. Devuelve la lista nueva."""
    resto = [a for a in alertas_actuales if not (a.get("PERIODO") == per and a.get("EMPRESA") == emp and str(a.get("TIPO", "")).startswith("H-"))]
    return resto + [dict(n) for n in nuevas if n["PERIODO"] == per and n["EMPRESA"] == emp]


def paquete_abc(hechos):
    """H-04 (contrato 5): filas de REGLA_REPARTO nuevas o retiradas del sistema ABC de P10.
    La especificación no fija las actividades ni los inductores de P10 (OT-076_dudas.md n.º 9): no se inventan."""
    import json, os
    ruta = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "casos", "V41", "P10_paquete_abc.json")
    with open(ruta, encoding="utf-8") as fh:
        return json.load(fh)["filas"]     # lo arma la carga del caso P10 (B2) con las actividades e inductores de Oria


def proponer_paquete_abc(usuario, paquete, pca_paq, motivo="H-04"):
    """Crea el paquete ABC como PARAM_CAMBIO de nivel 2 (un PCA_PAQ para todas las filas) dejando tramas PROPONER en CARGA."""
    from analitica.canal_carga import trama_proponer
    return trama_proponer(usuario, paquete, pca_paq, motivo)
