# -*- coding: utf-8 -*-
"""OT-085 (B8a) · Mensaje estandarizado de seis campos (ARQUITECTURA_V4_1 §9.4, §9.7 #3).

generar(hallazgo, entrada, carpeta) -> {"campos": {"1".."6": texto}, "tipo_impacto": str, "html": ruta}

Campos: 1 Qué pasa · 2 Por qué (con su traza) · 3 Qué se propone · 4 Impacto en S/ con su tipo ·
5 Riesgo · 6 Evidencia (enlaces al nivel 3 y al libro). Un campo vacío impide publicar: ValueError, sin escribir.
Implementado a fondo H-01 y H-03 (CONTRAFACTUAL con el CU de la familia, §9.3); H-06 y H-07 dicen
SIN_IMPACTO_MONETARIO con su motivo; H-02, H-04 y H-05 usan los datos del hallazgo (ver informes/V41/OT-085_dudas.md).
"""
import itertools
import os
from decimal import Decimal, ROUND_HALF_UP
from html import escape

NOMBRES = {"1": "Qué pasa", "2": "Por qué", "3": "Qué se propone", "4": "Impacto en S/", "5": "Riesgo", "6": "Evidencia"}
TIPO_IMPACTO = {"H-01": "CONTRAFACTUAL", "H-02": "CONTRAFACTUAL", "H-03": "CONTRAFACTUAL", "H-04": "SIMULACION",
                "H-05": "SIMULACION", "H-06": "SIN_IMPACTO_MONETARIO", "H-07": "SIN_IMPACTO_MONETARIO"}   # §9.7 #3
TOL_CU = Decimal("0.000005")


def _d(x):
    return Decimal(str(x))


def _n(x, n=2):
    return f"{_d(x).quantize(Decimal(1).scaleb(-n), rounding=ROUND_HALF_UP):,.{n}f}"


def _indice(entrada):
    return {(r["tipo"], str(r["clave"]), r["concepto"]): r["valor"] for r in entrada.get("resultado_metodo", [])}


def _familia(rm, entrada, ot):
    """(CU de la familia, nº de OT, nombre) de la familia de `ot`.
    Preferencia: COMPONENTE en hechos; si no hay hechos, la única familia cuyo CU coincide con el promedio
    ponderado por unidades vendidas de un subconjunto de OT terminadas que incluye a `ot` (ver dudas)."""
    familias = {c: v for (t, c, k), v in rm.items() if t == "FAMILIA" and k == "CU"}
    objetos = {str(o.get("NUMERO")): o for o in (entrada.get("hechos") or {}).get("(sin MCD) OBJETO", [])}
    if ot in objetos and objetos[ot].get("COMPONENTE") in familias:
        comp = objetos[ot]["COMPONENTE"]
        miembros = [o for o, x in objetos.items() if x.get("COMPONENTE") == comp and x.get("ESTADO") == "T"
                    and ("OBJETO", o, "UNIDADES_VENDIDAS") in rm]
        return _d(familias[comp]), len(miembros) or None, comp
    cand = [o for (t, o, k) in rm if t == "OBJETO" and k == "CU" and rm[(t, o, k)] is not None
            and ("OBJETO", o, "UNIDADES_VENDIDAS") in rm]
    otros = [o for o in cand if o != ot]
    hallados = []
    for r in range(0, len(otros) + 1):
        for sub in itertools.combinations(otros, r):
            grupo = (ot,) + sub
            u = [_d(rm[("OBJETO", g, "UNIDADES_VENDIDAS")]) for g in grupo]
            if sum(u) == 0:
                continue
            cu = sum(_d(rm[("OBJETO", g, "CU")]) * x for g, x in zip(grupo, u)) / sum(u)
            for comp, v in familias.items():
                if abs(cu - _d(v)) <= TOL_CU:
                    hallados.append((_d(v), len(grupo), comp))
    return hallados[0] if len({h[2] for h in hallados}) == 1 else (None, None, None)


def _enlaces(hallazgo, rm, entrada):
    ref = str(hallazgo.get("REFERENCIA", ""))
    trazas = entrada.get("trazas") or {}
    vistos = [k for k in trazas if k.split("|")[1:2] == [ref]]
    n3 = ["N3/" + "".join(c if c.isalnum() or c in "._-" else "_" for c in k) + ".html" for k in vistos]
    return n3, "libro_auditoria.xlsx"


def _h01_h03(hallazgo, rm, entrada):
    tipo, ot = hallazgo["TIPO"], str(hallazgo["REFERENCIA"])
    cu, umbral = _d(hallazgo["VALOR"]), _d(hallazgo["UMBRAL"])
    if tipo == "H-03" and rm.get(("OBJETO", ot, "CU")) is not None:   # en H-03 VALOR es la desviación (fracción), no el CU
        cu = _d(rm[("OBJETO", ot, "CU")])
    venta, vend = rm.get(("OBJETO", ot, "VENTA")), rm.get(("OBJETO", ot, "UNIDADES_VENDIDAS"))
    mb, ctot, cmd = rm.get(("OBJETO", ot, "MB")), rm.get(("OBJETO", ot, "CTOT")), rm.get(("OBJETO", ot, "C_MD"))
    cu_f, n_ot, fam = _familia(rm, entrada, ot)
    rent = _d(hallazgo.get("RENTABILIDAD_EXIGIDA", 0))
    meses = len({r["per"] for r in entrada.get("resultado_metodo", []) if r.get("per")}) or 1
    c = {}
    if tipo == "H-01":
        precio = umbral / (1 - rent) if rent != 1 else umbral
        perdida = f"; pérdida S/ {_n(-_d(mb))}" if mb is not None and _d(mb) < 0 else ""
        c["1"] = (f"El CU real de {ot} es S/ {_n(cu, 6)} frente a un costo máximo admisible de S/ {_n(umbral)} "
                  f"(precio S/ {_n(precio)}, rentabilidad exigida {_n(rent * 100, 0)} %){perdida}.")
    else:
        c["1"] = (f"El CU de {ot} es S/ {_n(cu, 6)} y supera el umbral S/ {_n(cu_f * (1 + umbral) if cu_f else umbral, 6)} "
                  "(CU de su familia × (1 + umbral de desviación)).")
    if cu_f:
        exceso = (cu / cu_f - 1) * 100
        md = f"; MD = {_n(_d(cmd) / _d(ctot) * 100, 1)} % del costo" if cmd is not None and ctot else ""
        traza = rm.get(("OBJETO", ot, "C_CIF"))
        tz = (f" Traza del CIF: S/ {_n(traza)} = suma de las líneas de la cadena de etapas (nivel 3)."
              if any(k.endswith("|C_CIF") for k in (entrada.get("trazas") or {})) and traza is not None else "")
        c["2"] = f"Su CU supera en {_n(exceso)} % al de su familia (S/ {_n(cu_f, 6)}){md}.{tz}"
        if tipo == "H-03" and ctot:      # ENM-V41-18: exceso de costo sobre lo producido = OBJ_CAN × (CU − CU familia)
            cu_r = _d(rm[("OBJETO", ot, "CU")]); und = _d(ctot) / cu_r
            c["4"] = (f"CONTRAFACTUAL: si su CU hubiera sido el de la familia, las {_n(und, 0)} unidades producidas "
                      f"habrían costado S/ {_n(und * (cu_r - cu_f))} menos.")
        elif venta is not None and vend is not None:
            impacto = _d(venta) - _d(vend) * cu_f
            c["4"] = (f"CONTRAFACTUAL: si su CU hubiera sido el de la familia, las {_n(vend, 0)} unidades vendidas "
                      f"habrían dejado S/ {_n(impacto)}.")
        c["5"] = (f"La familia se calcula con {n_ot} OT de {'un solo mes' if meses == 1 else str(meses) + ' meses'}."
                  if n_ot else "")
    else:
        c["2"] = c["4"] = c["5"] = ""        # sin familia no hay causa ni impacto: no se publica
    c["3"] = (f"Revisar el consumo de material de {ot} frente a la familia"
              + (", o renegociar el precio con ventas." if tipo == "H-01" else "."))
    return c


def _h02(hallazgo, rm, entrada):
    """H-02 (§9.3): causa y contrafactual desde el detalle de DIFERENCIAS_OT (ALG-08)."""
    ot = str(hallazgo["REFERENCIA"])
    g = lambda c: rm.get(("OBJETO", ot, c))
    real, flex, dif = g("REAL"), g("ESTIMADO_FLEXIBLE"), g("DIFERENCIA")
    if None in (real, flex, dif):
        return _generico(hallazgo, rm, entrada)
    pct = _d(dif) / _d(flex) * 100 if flex else 0
    det = [("cantidad de material", "VAR_CANTIDAD_MD"), ("precio de material", "VAR_PRECIO_MD"), ("cantidad de personal", "VAR_CANTIDAD_PD"),
           ("precio de personal", "VAR_PRECIO_PD"), ("servicios", "VAR_SD"), ("CIF frente a la tasa de la familia", "VAR_CIF")]
    partes = ", ".join(f"{n} S/ {_n(g(c))}" for n, c in det if g(c) is not None)
    return {"1": f"El costo real de {ot} (S/ {_n(real)}) superó lo cotizado ajustado a la cantidad producida (S/ {_n(flex)}) "
                 f"en S/ {_n(dif)} ({_n(pct)} %).",
            "2": f"Causas: {partes}.",
            "3": f"Revisar el consumo de material y los minutos de {ot} frente a lo cotizado, y actualizar las cantidades de la "
                 f"próxima cotización de la familia.",
            "4": f"CONTRAFACTUAL: si se hubiera cumplido la cotización, el costo habría sido S/ {_n(dif)} menor.",
            "5": "Las cantidades cotizadas las fijó el presupuestador; la tasa de CIF de la familia sale de un solo mes."}


def _generico(hallazgo, rm, entrada):
    tipo, ref = hallazgo["TIPO"], str(hallazgo["REFERENCIA"])
    v, u = hallazgo.get("VALOR"), hallazgo.get("UMBRAL")
    c = {"1": f"{tipo} sobre {ref}: valor medido {_n(v, 6)} frente a umbral {_n(u, 6)}.",
         "2": hallazgo.get("POR_QUE", ""), "3": hallazgo.get("PROPUESTA", ""),
         "4": hallazgo.get("IMPACTO", ""), "5": hallazgo.get("RIESGO", "")}
    if TIPO_IMPACTO.get(tipo) == "SIN_IMPACTO_MONETARIO" and c["4"] == "":
        c["4"] = f"SIN_IMPACTO_MONETARIO: {hallazgo.get('MOTIVO_SIN_IMPACTO', '')}".rstrip(": ")
        if not hallazgo.get("MOTIVO_SIN_IMPACTO"):
            c["4"] = ""
    return c


def generar(hallazgo, entrada, carpeta):
    tipo, ref = str(hallazgo.get("TIPO", "")), str(hallazgo.get("REFERENCIA", "")).strip()
    if not tipo or not ref:
        raise ValueError("hallazgo sin TIPO o REFERENCIA: no se publica")
    rm = _indice(entrada)
    campos = (_h01_h03(hallazgo, rm, entrada) if tipo in ("H-01", "H-03") else _h02(hallazgo, rm, entrada) if tipo == "H-02"
              else _generico(hallazgo, rm, entrada))
    n3, libro = _enlaces(hallazgo, rm, entrada)
    campos["6"] = ("Nivel 3 de la consulta: " + ", ".join(n3) if n3 else "Nivel 3 de la consulta: sin traza disponible")
    campos["6"] += f". Libro de auditoría: {libro}."
    campos = {k: str(campos.get(k, "")).strip() for k in "123456"}
    vacios = [k for k, v in campos.items() if not v]
    if vacios:
        raise ValueError(f"mensaje {tipo} {ref}: campos vacíos {vacios}; no se publica")
    tipo_imp = TIPO_IMPACTO.get(tipo)
    if tipo_imp is None:
        raise ValueError(f"mensaje {tipo}: regla sin tipo de impacto en §9.7 #3")
    if tipo_imp not in campos["4"]:
        campos["4"] = f"{tipo_imp}: {campos['4']}"
    cuerpo = "".join(f"<h2>{k}. {NOMBRES[k]}</h2><p>{escape(campos[k])}</p>" for k in "123456")
    html = ("<!DOCTYPE html>\n<html lang=\"es\"><head><meta charset=\"utf-8\">"
            f"<title>{escape(tipo)} · {escape(ref)}</title></head><body><h1>{escape(tipo)} · {escape(ref)}</h1>"
            f"<p><small>Periodo {escape(str(hallazgo.get('PERIODO', '')))} · empresa {escape(str(hallazgo.get('EMPRESA', '')))}"
            f" · impacto {tipo_imp}</small></p>{cuerpo}</body></html>\n")
    os.makedirs(os.fspath(carpeta), exist_ok=True)
    ruta = os.path.join(os.fspath(carpeta), f"mensaje_{tipo}_{ref}.html")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(html)
    return {"campos": campos, "tipo_impacto": tipo_imp, "html": ruta}
