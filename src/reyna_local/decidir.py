# -*- coding: utf-8 -*-
"""Panel «Decidir» (sección H de docs/diseno/OLA2_REVISION_DUENO.md; criterios de Oria vistos en clase, 25-nov).
Solo lee el resultado REAL publicado (trazas raíz por recurso) y los atributos del recurso; nunca recalcula el costo.

Clasificación por recurso (rango relevante: el mes):
- REC_COMPORT F/V/M (+ REC_PCT_VAR) si el usuario lo declaró (MEDIDO); si no, por defecto según el elemento (SUPUESTO):
  material y servicios directos variables; el resto fijo.
- REC_CTRL S/N: controlable por el responsable del centro (vacío = S).
- REC_EVIT S/N: fijo evitable (desaparece si se elimina la línea o se terceriza). Vacío = N (SUPUESTO, conservador)."""
from collections import defaultdict
from math import isfinite

VARIABLES_POR_DEFECTO = {"MD", "MAT", "SD"}


def _clasificacion(recursos):
    out = {}
    for r in recursos:
        cod = str(r.get("REC_COD") or r.get("codigo")); ele = str(r.get("elemento") or r.get("REC_ELE") or "")
        modo = str(r.get("REC_COMPORT") or "").strip().upper()
        if modo == "V": v, fuente = 1.0, "MEDIDO"
        elif modo == "F": v, fuente = 0.0, "MEDIDO"
        elif modo == "M": v, fuente = float(r.get("REC_PCT_VAR") or 0) / 100, "MEDIDO"
        else: v, fuente = (1.0 if ele in VARIABLES_POR_DEFECTO else 0.0), "SUPUESTO"
        out[cod] = dict(variable=v, fuente=fuente, controlable=str(r.get("REC_CTRL") or "S").strip().upper() != "N",
                        evitable=str(r.get("REC_EVIT") or "N").strip().upper() == "S")
    return out


def estructura(resultado, recursos):
    """Por producto: ventas, cantidad, CV, CF controlable / no controlable / evitable, MC, utilidad (ER gerencial)."""
    cls = _clasificacion(recursos); prod = {o["codigo"]: o["producto"] for o in resultado["objetos"]}
    p = defaultdict(lambda: dict(ventas=0.0, cantidad=0.0, cv=0.0, cf_controlable=0.0, cf_no_controlable=0.0, cf_evitable=0.0))
    for o in resultado["objetos"]:
        x = p[o["producto"]]; x["ventas"] += float(o.get("ingreso") or 0); x["cantidad"] += float(o.get("cantidad") or 0)
    supuestos = set()
    for t in resultado.get("trazas") or []:
        if not t.get("raiz") or "|" in str(t.get("elemento")): continue
        c = cls.get(str(t["origen"])) or dict(variable=0.0, fuente="SUPUESTO", controlable=True, evitable=False)
        if c["fuente"] == "SUPUESTO": supuestos.add(str(t["origen"]))
        x = p[prod.get(t["objeto"], t["objeto"])]; m = float(t["monto"]); v = m * c["variable"]; f = m - v
        x["cv"] += v; x["cf_controlable" if c["controlable"] else "cf_no_controlable"] += f
        if c["evitable"]: x["cf_evitable"] += f
    filas = []
    for k, x in sorted(p.items()):
        cf = x["cf_controlable"] + x["cf_no_controlable"]; mc = x["ventas"] - x["cv"]
        filas.append({"producto": k, **{a: round(b, 2) for a, b in x.items()}, "margen_contribucion": round(mc, 2), "cf_total": round(cf, 2),
                      "utilidad_operativa": round(mc - cf, 2), "cv_unitario": round(x["cv"] / x["cantidad"], 6) if x["cantidad"] else None,
                      "precio_unitario": round(x["ventas"] / x["cantidad"], 6) if x["cantidad"] else None})
    return filas, sorted(supuestos)


def punto_equilibrio(filas):
    """Preciso: el CF de cada producto (asignado por ABC) entre su MC unitario. Ponderado (Oria: solo si falta información):
    CF total / (Σ MC / Σ ventas)."""
    pre = []
    for f in filas:
        mcu = (f["precio_unitario"] or 0) - (f["cv_unitario"] or 0)
        u = f["cf_total"] / mcu if mcu > 0 else None
        pre.append({"producto": f["producto"], "unidades": round(u, 2) if u is not None else None,
                    "soles": round(u * f["precio_unitario"], 2) if u is not None else None, "mc_unitario": round(mcu, 6)})
    ventas = sum(f["ventas"] for f in filas); mc = sum(f["margen_contribucion"] for f in filas); cf = sum(f["cf_total"] for f in filas)
    pond = round(cf / (mc / ventas), 2) if ventas > 0 and mc > 0 else None
    return {"preciso": pre, "ponderado_soles": pond, "mc_pct": round(mc / ventas, 6) if ventas else None}


def relevancia_10(resultado, umbral=0.10):
    """Regla de Oria: todo elemento que supera el 10 % del costo total es relevante; ordenado por prioridad."""
    nombres = {"md": "Material directo", "mod": "Mano de obra", "cif": "CIF", "admin": "Administración", "gasto_venta": "Ventas", "financiero": "Financiero"}
    tot = {k: sum(float(o.get(k) or 0) for o in resultado["objetos"]) for k in nombres}; T = sum(tot.values()) or 1.0
    return [{"elemento": nombres[k], "importe": round(v, 2), "porcentaje": round(v / T, 4), "relevante": v / T > umbral}
            for k, v in sorted(tot.items(), key=lambda x: -x[1])]


def producir_o_tercerizar(f, unidades, precio_compra, costo_mantener=0.0, costo_transicion=0.0):
    """Caso 1. Costo de producir relevante = CV × unidades + CF evitable del producto; costo de comprar = (precio + mantener) ×
    unidades + transición. Ahorro de tercerizar = producir − comprar (positivo: conviene tercerizar)."""
    producir = (f["cv_unitario"] or 0) * unidades + f["cf_evitable"]
    comprar = (precio_compra + costo_mantener) * unidades + costo_transicion
    return {"costo_producir": round(producir, 2), "costo_comprar": round(comprar, 2), "ahorro_tercerizar": round(producir - comprar, 2),
            "decision": "TERCERIZAR" if comprar < producir else "PRODUCIR",
            "otros_factores": "calidad, rendimiento, dependencia del proveedor y tiempo de transición"}


def eliminar_linea(f):
    """Caso 2. Impacto en la utilidad de eliminar = − MC + CF evitable (los fijos comunes se quedan)."""
    impacto = -f["margen_contribucion"] + f["cf_evitable"]
    return {"impacto_utilidad": round(impacto, 2), "decision": "ELIMINAR" if impacto > 0 else "MANTENER",
            "cf_que_se_queda": round(f["cf_total"] - f["cf_evitable"], 2)}


def pedido_especial(f, unidades, precio, cf_incremental=0.0, capacidad_ociosa=True, unidades_desplazadas=0.0):
    """Caso 3. Con capacidad ociosa: utilidad incremental = (precio − CV) × unidades − CF incremental.
    3.2 sin capacidad: además se resta el costo de oportunidad = MC unitario × unidades normales desplazadas."""
    mcu = (f["precio_unitario"] or 0) - (f["cv_unitario"] or 0)
    oportunidad = 0.0 if capacidad_ociosa else mcu * unidades_desplazadas
    inc = (precio - (f["cv_unitario"] or 0)) * unidades - cf_incremental - oportunidad
    minimo = (f["cv_unitario"] or 0) + (cf_incremental + oportunidad) / unidades if unidades else None
    return {"utilidad_incremental": round(inc, 2), "costo_oportunidad": round(oportunidad, 2),
            "precio_minimo": round(minimo, 4) if minimo is not None and isfinite(minimo) else None,
            "decision": "ACEPTAR" if inc > 0 else "RECHAZAR"}


def panel(resultado, recursos):
    filas, sup = estructura(resultado, recursos)
    tot = {k: round(sum(f[k] for f in filas), 2) for k in ("ventas", "cv", "margen_contribucion", "cf_controlable", "cf_no_controlable", "utilidad_operativa")}
    return {"er_gerencial": {"productos": filas, "total": tot}, "punto_equilibrio": punto_equilibrio(filas),
            "relevancia": relevancia_10(resultado), "recursos_supuestos": sup,
            "nota": "Clasificación SUPUESTA en los recursos listados: declara REC_COMPORT, REC_CTRL y REC_EVIT en el libro para precisarla."}
