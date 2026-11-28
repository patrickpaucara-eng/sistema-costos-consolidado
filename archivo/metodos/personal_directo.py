# -*- coding: utf-8 -*-
"""MÉTODO · PERSONAL DIRECTO por persona (formato compatible, E-106 + OT-022). Reemplaza la tarifa (ALG-TAR).
CONSUME por CONCEPTOS (OT-022): entidad MCD -> conceptos. El traductor semántico resuelve las columnas físicas."""
from metodos import caso_excel

FICHA = dict(nombre="PERSONAL_PLANILLA", version="1.1", vigente_desde="2026-01-01", eje="MEDIDA", objetivo="REAL",
    que_hace="Costea el personal directo de cada objeto con el costo REAL por minuto de cada persona; el tiempo no asignado es ocio.",
    formula="costo por minuto = costo de planilla / (horas efectivas × 60); costo del objeto = Σ minutos × costo por minuto",
    fuente="Horngren, Datar y Rajan (2012) cap. 4; plantilla ENVASE del usuario (P2)",
    supuestos="La planilla del periodo incluye todas las cargas; los minutos los registra la planta (T18.3)",
    limites="Sin planilla de la persona en el periodo, no se costea (no se usa tarifa de respaldo)",
    caso="Caso_PERSONAL_PLANILLA_7.xlsx")
CONSUME = {
    "(sin MCD) PLANILLA": ["PERIODO", "EMPRESA", "PERSONA", "COSTO", "HORAS"],
    "(sin MCD) CTA_PERS_OBJ": ["PERIODO", "EMPRESA", "PERSONA", "OBJETO", "MINUTOS"],
}
DEPENDE_DE = {}
PARAMETROS = [dict(id="PER", etq="Periodo", tipo="texto"), dict(id="EMP", etq="Empresa", tipo="texto")]
ENTREGA = {"OBJETO": ["COSTO_PERSONAL"], "PERSONA": ["COSTO_MINUTO", "MINUTOS_OCIO", "COSTO_OCIO"]}


def red(x, n=2):
    from decimal import Decimal as D, ROUND_HALF_UP
    return float(D(str(x)).quantize(D(1).scaleb(-n), rounding=ROUND_HALF_UP))


def calcular(hechos, parametros, previos):
    per, emp = parametros["PER"], parametros["EMP"]
    pla = {p["PERSONA"]: p for p in hechos["(sin MCD) PLANILLA"]
           if p["PERIODO"] == per and p["EMPRESA"] == emp}
    mins = [r for r in hechos["(sin MCD) CTA_PERS_OBJ"] if r["PERIODO"] == per and r["EMPRESA"] == emp]
    res, expl, obj, usados = [], [], {}, {}
    for r in mins:
        p = pla.get(r["PERSONA"])
        if not p or not float(p["HORAS"] or 0):
            raise ValueError(f"{r['PERSONA']}: no hay planilla con horas en {per}")
        cm = float(p["COSTO"]) / (float(p["HORAS"]) * 60)
        obj[r["OBJETO"]] = obj.get(r["OBJETO"], 0) + float(r["MINUTOS"]) * cm
        usados[r["PERSONA"]] = usados.get(r["PERSONA"], 0) + float(r["MINUTOS"])
        expl.append(f"{r['PERSONA']} en {r['OBJETO']}: {r['MINUTOS']} min × {cm:.6f} = {red(float(r['MINUTOS']) * cm)}")
    for o, v in obj.items():
        res.append(("OBJETO", o, "COSTO_PERSONAL", red(v)))
    for k, p in pla.items():
        disp = float(p["HORAS"]) * 60
        usados_k = usados.get(k, 0)
        if usados_k > disp:
            raise ValueError(f"{k}: {usados_k:.0f} min asignados > {disp:.0f} min pagados en {per}; "
                             f"registre las horas extra en la planilla o corrija los minutos")
        cm = float(p["COSTO"]) / disp
        ocio = disp - usados_k
        if ocio < 0:                                    # nunca puede ser negativo; la comparación es exacta
            raise ValueError(f"{k}: minutos de ocio negativos en {per}")
        res += [("PERSONA", k, "COSTO_MINUTO", round(cm, 6)), ("PERSONA", k, "MINUTOS_OCIO", ocio),
                ("PERSONA", k, "COSTO_OCIO", red(ocio * cm))]
    return res, expl


CASOS = caso_excel.cargar(FICHA["caso"]) + [dict(nombre="Julio a mano: P01 3000/180 h con 5400 min; P02 2400/160 h con 3000 min en OE-03",
    hechos={"(sin MCD) PLANILLA": [dict(PERIODO="2026-07", EMPRESA="B", PERSONA="P01", COSTO=3000, HORAS=180),
                                   dict(PERIODO="2026-07", EMPRESA="B", PERSONA="P02", COSTO=2400, HORAS=160)],
            "(sin MCD) CTA_PERS_OBJ": [dict(PERIODO="2026-07", EMPRESA="B", PERSONA="P01", OBJETO="OE-03", MINUTOS=5400),
                                       dict(PERIODO="2026-07", EMPRESA="B", PERSONA="P02", OBJETO="OE-03", MINUTOS=3000)]},
    parametros=dict(PER="2026-07", EMP="B"), previos={},
    espera=[("OBJETO", "OE-03", "COSTO_PERSONAL", 2250.0), ("PERSONA", "P01", "COSTO_OCIO", 1500.0), ("PERSONA", "P02", "COSTO_OCIO", 1650.0)])]
