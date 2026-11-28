# -*- coding: utf-8 -*-
"""CAT-01 · Catálogo de propuestas (ESPEC_ANALITICA2 §7, D-5, §2.5). OT-091.
Ninguna propuesta se publica si su entrada no está en el catálogo con ACTIVO = "S". EVALUADOR e IMPACTO son nombres de
registros (nunca texto evaluable). Las plantillas ACCION y RIESGO usan solo {campos} de la fila del hallazgo (enriquecida por
el redactor de la regla con TXT_1..TXT_6), {IMPACTO} e {IMPACTO_TIPO}; un campo inexistente = la entrada no publica.
Migración literal: los textos de H-01..H-07 los redacta el constructor de mensajes del prototipo (solo importado, G-4) y los
de H-13 el de ALG-13, para que la regresión contra salidas/ y salidas_a2/ sea idéntica."""
import json
import os
import string
from decimal import Decimal as D

from analitica2.evaluadores import REGISTRO_EVALUADORES
from analitica2.impactos import REGISTRO_IMPACTOS

RUTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "catalogo.json")
CAMPOS = "123456"


def cargar():
    with open(RUTA, encoding="utf-8") as f:
        return json.load(f)


# I-2 (OT-098 I2-c n.º 1, V3): concepto del DBD (tabla PROPUESTA) → clave del catálogo
CONCEPTO_CLAVE = {"CODIGO": "COD", "REGLA": "REGLA", "EVALUADOR": "EVALUADOR", "ACCION": "ACCION", "IMPACTO": "IMPACTO",
                  "NIVEL": "NIVEL", "ACTIVO": "ACTIVO", "RIESGO": "RIESGO"}
CLAVES_PROPUESTA = ("(sin MCD) PROPUESTA", "PROPUESTA")


def desde_hechos(hechos):
    """Catálogo leído de la tabla PROPUESTA de los hechos (conceptos del DBD) o None si los hechos no la traen."""
    for k in CLAVES_PROPUESTA:
        filas = (hechos or {}).get(k)
        if filas:
            cat = []
            for f in filas:
                e = {CONCEPTO_CLAVE[c]: v for c, v in f.items() if c in CONCEPTO_CLAVE}
                if e.get("COD") in (None, ""):
                    continue
                if e.get("NIVEL") not in (None, ""):
                    e["NIVEL"] = int(D(str(e["NIVEL"])))
                cat.append(e)
            return cat
    return None


def _indice(rm, per, emp):
    out = {}
    for r in rm:
        if r.get("per") in (None, per) and r.get("emp") in (None, emp) and isinstance(r.get("valor"), (int, float)):
            out[(r["tipo"], str(r["clave"]), r["concepto"])] = D(str(r["valor"]))
    return out


def _redactar_prototipo(h, entrada):
    """6 campos del prototipo sin escribir archivos (misma lógica que analitica.mensajes.generar)."""
    from analitica import mensajes as M
    tipo = h["TIPO"]
    rm = M._indice(entrada)
    c = (M._h01_h03(h, rm, entrada) if tipo in ("H-01", "H-03") else M._h02(h, rm, entrada) if tipo == "H-02"
         else M._generico(h, rm, entrada))
    n3, libro = M._enlaces(h, rm, entrada)
    c["6"] = ("Nivel 3 de la consulta: " + ", ".join(n3) if n3 else "Nivel 3 de la consulta: sin traza disponible")
    c["6"] += f". Libro de auditoría: {libro}."
    c = {k: str(c.get(k, "")).strip() for k in CAMPOS}
    ti = M.TIPO_IMPACTO.get(tipo)
    if ti and ti not in c["4"]:
        c["4"] = f"{ti}: {c['4']}"
    return c


def _redactar_h13(filas, rm, per, emp):
    from analitica2 import elemento
    return {m["REFERENCIA"]: m["campos"] for m in elemento.mensajes(filas, rm, per, emp)}


def _redactar_generico(h):
    ref, ref2 = h.get("REFERENCIA", ""), h.get("REFERENCIA_2", "")
    return {"1": f"{h['TIPO']} en {ref} {ref2}".strip(), "2": f"Valor {h.get('VALOR')} frente al umbral {h.get('UMBRAL')}",
            "3": "", "4": "", "5": f"Basado en {h.get('N', h.get('N_FAMILIA', '—'))} observación(es)", "6": "Ver salidas_a2"}


def _plantilla(texto, datos):
    """Rellena {X}; si falta un campo devuelve None (la entrada no publica)."""
    try:
        claves = [f for _, f, _, _ in string.Formatter().parse(texto) if f]
        if any(k not in datos for k in claves):
            return None
        return texto.format(**{k: datos[k] for k in claves})
    except (ValueError, KeyError, IndexError):
        return None


def publicar(hechos, resultado_metodo, per, emp, entrada=None, catalogo=None):
    """[{COD, REGLA, NIVEL, hallazgo, campos}] de las entradas ACTIVO = S, en orden de catálogo y de hallazgo."""
    cat = catalogo if catalogo is not None else (desde_hechos(hechos) or cargar())   # inyectado > PROPUESTA > catalogo.json
    entrada = entrada or {"hechos": hechos, "resultado_metodo": resultado_metodo, "per": per, "emp": emp, "trazas": {}}
    for e in cat:                                             # nombres no registrados: error claro antes de publicar
        if str(e.get("ACTIVO")) != "S":
            continue
        if e.get("EVALUADOR") not in REGISTRO_EVALUADORES:
            raise LookupError(f"CAT-01 {e.get('COD')}: EVALUADOR no registrado {e.get('EVALUADOR')!r}")
        if e.get("IMPACTO") not in REGISTRO_IMPACTOS:
            raise LookupError(f"CAT-01 {e.get('COD')}: IMPACTO no registrado {e.get('IMPACTO')!r}")
    idx = _indice(resultado_metodo, per, emp)
    out = []
    for e in cat:
        if str(e.get("ACTIVO")) != "S":
            continue
        filas = REGISTRO_EVALUADORES[e["EVALUADOR"]](hechos, resultado_metodo, per, emp, {})
        h13 = _redactar_h13(filas, resultado_metodo, per, emp) if e["EVALUADOR"] == "H13" else None
        for h in filas:
            if e["EVALUADOR"] == "H13":
                if h.get("DOMINANTE") != "S":
                    continue
                txt = h13.get(h["REFERENCIA"])
            elif e["EVALUADOR"].startswith("H0"):
                try:
                    txt = _redactar_prototipo(h, entrada)
                except (ValueError, KeyError):
                    continue
            else:
                txt = _redactar_generico(h)
            if not txt:
                continue
            imp = REGISTRO_IMPACTOS[e["IMPACTO"]](h, idx, hechos)
            datos = dict(h, **{f"TXT_{k}": txt.get(k, "") for k in CAMPOS},
                         IMPACTO=imp["valor"] if imp["valor"] is not None else "", IMPACTO_TIPO=imp["tipo"])
            c3, c5 = _plantilla(str(e.get("ACCION", "")), datos), _plantilla(str(e.get("RIESGO", "")), datos)
            if c3 is None or c5 is None:
                continue
            campos = {"1": txt.get("1", ""), "2": txt.get("2", ""), "3": c3, "4": txt.get("4", "") or f"{imp['tipo']}: {imp['motivo']}",
                      "5": c5, "6": txt.get("6", "")}
            if any(not str(v).strip() for v in campos.values()):
                continue                                      # un campo vacío no publica (§9.4 V4.1)
            out.append({"COD": e["COD"], "REGLA": e["REGLA"], "NIVEL": int(e["NIVEL"]), "hallazgo": h, "campos": campos})
    return out
