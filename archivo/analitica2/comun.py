# -*- coding: utf-8 -*-
"""Utilidades comunes de la capa 2.0 (ESPEC_ANALITICA2 §2, §3). Funciones puras, Decimal, orden por código."""
import json
import os
from decimal import Decimal as D, getcontext, ROUND_HALF_UP

getcontext().prec = 28
ELEMENTOS = ("MD", "PD", "SD", "CIF")
_E6 = D("0.000001")
_RUTA_PARAMETROS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "parametros.json")


def d(v):
    return D(str(v))


def q6(x):
    return x.quantize(_E6, rounding=ROUND_HALF_UP)


def parametros_por_defecto():
    with open(_RUTA_PARAMETROS, encoding="utf-8") as f:
        return {p["CODIGO"]: d(p["VALOR"]) for p in json.load(f)}


def parametros(hechos, per):
    """§2.4: parametros.json; si hechos trae el mismo código (vigente en `per`), manda el de los hechos."""
    from analitica.hallazgos import _parametros     # G-4: solo importa, no modifica
    par = parametros_por_defecto()
    par.update({k: v for k, v in _parametros(hechos or {}, per).items() if k.startswith("A2.")})
    return par


def objetos(hechos):
    """D-7 n.º 3: acepta OBJETO y (sin MCD) OBJETO."""
    h = hechos or {}
    return h.get("OBJETO") or h.get("(sin MCD) OBJETO") or []


def indice_objetos(resultado_metodo, per, emp):
    """{(OT, concepto): Decimal} de los OBJETO/<OT>/<concepto> publicados en `per` y `emp`."""
    out = {}
    for r in sorted(resultado_metodo, key=lambda r: (str(r.get("clave")), str(r.get("concepto")), str(r.get("metodo")))):
        if (r.get("tipo") == "OBJETO" and r.get("per") in (None, per) and r.get("emp") in (None, emp)
                and isinstance(r.get("valor"), (int, float, D)) and not isinstance(r.get("valor"), bool)):
            out[(str(r["clave"]), r["concepto"])] = d(r["valor"])
    return out


def can(rm_idx, ot):
    """§2.2: CAN = CTOT / CU; None si CU falta o es 0."""
    cu = rm_idx.get((ot, "CU"))
    ctot = rm_idx.get((ot, "CTOT"))
    if not cu or ctot is None:
        return None
    return ctot / cu


def poblacion(hechos, rm_idx, emp, familias=None):
    """§3: OT con ESTADO = T, TIPO = OT (o vacío), de `emp`, con CU publicado. {OT: familia}, orden por código."""
    out = {}
    for o in sorted(objetos(hechos), key=lambda o: str(o.get("NUMERO"))):
        ot = str(o.get("NUMERO"))
        if o.get("ESTADO") != "T" or (o.get("TIPO") not in (None, "", "OT")) or o.get("EMPRESA") != emp:
            continue
        if can(rm_idx, ot) is None:
            continue
        fam = (familias or {}).get(ot) if familias is not None else o.get("COMPONENTE")
        if fam in (None, ""):
            continue
        out[ot] = fam
    return out


def familias_agrupadas(pob):
    """{familia: [OT ordenadas]} con n ≥ 2 (F-2)."""
    g = {}
    for ot, f in pob.items():
        g.setdefault(f, []).append(ot)
    return {f: sorted(v) for f, v in sorted(g.items(), key=lambda kv: str(kv[0])) if len(v) >= 2}


def mensaje_6_campos(textos, enlaces):
    """Mensaje de 6 campos (V4.1 §9.4). `textos` = (1..5); `enlaces` = lista de rutas del campo 6. Campo vacío → ValueError."""
    campos = {str(i + 1): t for i, t in enumerate(textos)}
    campos["6"] = "; ".join(enlaces)
    for k, v in campos.items():
        if not str(v).strip():
            raise ValueError(f"campo {k} vacío: no se publica")
    return campos


def html_mensaje(campos, titulo, carpeta, nombre):
    """Escribe el HTML con la misma estructura de analitica.mensajes (reutiliza NOMBRES)."""
    from html import escape
    from analitica.mensajes import NOMBRES
    cuerpo = "".join(f"<h3>{k}. {NOMBRES[k]}</h3><p>{escape(str(campos[k]))}</p>" for k in sorted(campos))
    html = ("<!DOCTYPE html>\n<html lang=\"es\"><head><meta charset=\"utf-8\">"
            f"<title>{escape(titulo)}</title></head><body><h2>{escape(titulo)}</h2>{cuerpo}</body></html>\n")
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(os.fspath(carpeta), nombre)
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(html)
    return ruta
