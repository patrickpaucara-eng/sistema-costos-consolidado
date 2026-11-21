"""Construye el CONTRATO de resultados (contrato.py) desde el cálculo publicado del caso. Las pantallas solo leen esto.
Etapa 1: síntesis REAL, ABC de producción (MD, MOD, CIF) y serie histórica. Etapas 2-3 agregan admin/ventas/financieros
(NIIF 18), relevancia, hallazgos, proyección, escenarios y propuestas sin cambiar la forma."""
import csv, math, os
from decimal import Decimal as D
import puerto_lectura as P
from metodos import reparto_etapas as R
from integra_env import valuacion_alg01

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _f(x): return float(round(D(x), 2))


def calcular_periodos(libro, emp):
    val = valuacion_alg01(libro); h = P.leer_conceptos(libro, R.CONSUME)
    pers = sorted({str(r["CODIGO"]) for r in h.get("PERIODO", [])})
    return {p: R.interno(h, dict(PER=p, EMP=emp), {"VALUACION_PROMEDIO": val}) for p in pers}, h


PROD = ("MD", "PD", "SD", "CIF"); OPER = ("GAD", "GVT"); FIN = ("GFI",)


def _incluidos(sintesis):
    """Reglas por tipo de síntesis (D-8/D-9): qué elementos forman el costo del objeto."""
    return PROD + OPER + FIN if sintesis in ("REAL", "ESTIMADO") else PROD


def construir(libro, emp="FRE", nombre="Frenosa", periodo=None, ventas_csv=None, sintesis="REAL", _cache=None):
    """REAL     costo integral = MD + MOD + CIF + administración + ventas + financieros (gerencial, precio objetivo).
    CONTABLE costo del inventario = MD + MOD + CIF (NIC 2 §10-16); el resto es gasto del periodo; estado de resultados NIIF 18.
    ESTIMADO costo más fiel según la historia (estadística, fuera de muestra), con banda; no es un estándar.
    En las tres: descriptivo, diagnóstico, relevancia, proyección 6 meses (determinística y estocástica), escenarios y propuestas."""
    from reyna_local import analisis as A
    if sintesis not in ("REAL", "CONTABLE", "ESTIMADO"): raise ValueError("síntesis desconocida")
    por_per, h = _cache or calcular_periodos(libro, emp)
    pers = sorted(por_per); periodo = periodo or pers[-1]
    objs = P.leer(libro, ["OBJETO"])["OBJETO"]
    can = {r["OBJ_NUM"]: float(r["OBJ_CAN"] or 0) for r in objs}; pro = {r["OBJ_NUM"]: r["OBJ_PRO"] for r in objs}
    ventas = {}
    if ventas_csv:
        for r in csv.DictReader(open(ventas_csv, encoding="utf-8")): ventas[(r["periodo"], r["ot_id"])] = float(r["ventas_netas_soles"])
    idx = {"SW50": "OT001", "FRE9000": "OT002", "FRE9002": "OT003"}
    def ingreso(p, ot): return ventas.get((p, idx.get(A._producto(ot))), 0.0)
    inc = _incluidos(sintesis)
    series = A.serie_producto(por_per, can)
    est = A.estimado(series, periodo) if sintesis == "ESTIMADO" else {}
    objetos = []
    for o, v in sorted(por_per[periodo].items()):
        el = {e: _f(v.get(e, 0)) for e in PROD + OPER + FIN}
        if sintesis == "ESTIMADO" and A._producto(o) in est:
            el = {e: round(est[A._producto(o)]["cu_elementos"][e] * can[o], 2) for e in el}
        el = {e: (x if e in inc else 0.0) for e, x in el.items()}
        ct = round(sum(el.values()), 2); ing = ingreso(periodo, o)
        objetos.append(dict(codigo=o, producto=A._producto(o), cantidad=can.get(o, 0), md=el["MD"], mod=round(el["PD"] + el["SD"], 2), cif=el["CIF"],
                            admin=el["GAD"], gasto_venta=el["GVT"], financiero=el["GFI"], costo_total=ct,
                            costo_unitario=round(ct / can[o], 4) if can.get(o) else 0, ingreso=ing, margen=round(ing - ct, 2)))
    def tot_per(p): return {e: round(sum(_f(v.get(e, 0)) for v in por_per[p].values()), 2) for e in PROD + OPER + FIN}
    def vta_per(p): return round(sum(ingreso(p, o) for o in por_per[p]), 2)
    serie = []
    for p in [x for x in pers if x <= periodo]:
        t = tot_per(p); ct = round(sum(t[e] for e in inc), 2); vt = vta_per(p)
        serie.append(dict(periodo=p, tipo="ACTUAL" if p == periodo else "HISTORICO", ventas=vt, costo_total=ct, margen=round(vt - ct, 2)))
    proy, info = A.proyectar([(x["periodo"], x["ventas"], x["costo_total"]) for x in serie])
    serie += proy
    t = tot_per(periodo); vt = vta_per(periodo)
    cventas = round(sum(t[e] for e in PROD), 2)
    er = [dict(categoria="OPERACION", concepto="Ventas netas", importe=vt),
          dict(categoria="OPERACION", concepto="Costo de ventas (MD + MOD + CIF)", importe=-cventas),
          dict(categoria="OPERACION", concepto="Gastos de administración", importe=-t["GAD"]),
          dict(categoria="OPERACION", concepto="Gastos de ventas", importe=-t["GVT"]),
          dict(categoria="FINANCIACION", concepto="Gastos financieros", importe=-t["GFI"])]
    r_oper = round(vt - cventas - t["GAD"] - t["GVT"], 2)
    hall = A.diagnostico(series, periodo)
    rel = A.relevancia({e: t[e] for e in inc})
    esc = A.escenarios(dict(ventas=vt, **t))
    prop = A.propuestas(series, periodo, hall, rel)
    acts = []
    for (tipo, clave, conc, val) in R.calcular(h, dict(PER=periodo, EMP=emp), {"VALUACION_PROMEDIO": valuacion_alg01(libro)})[0]:
        if tipo == "ACTIVIDAD": acts.append(dict(codigo=clave, nombre=clave, costo=round(val, 2), inductor="", tasa=0.0))
    ct = sum(o["costo_total"] for o in objetos); q = sum(o["cantidad"] for o in objetos)
    r = dict(empresa=dict(codigo=emp, nombre=nombre), periodo_actual=periodo, sintesis=sintesis, moneda="PEN",
             kpi=dict(ventas=vt, costo_total=round(ct, 2), margen_operativo=r_oper, rentabilidad=round(r_oper / vt, 4) if vt else 0,
                      costo_unitario_prom=round(ct / q, 4) if q else 0, resultado_antes_impuestos=round(r_oper - t["GFI"], 2)),
             objetos=objetos, actividades=acts, serie=serie, estado_resultados=er, relevancia=rel, hallazgos=hall, propuestas=prop,
             escenarios=esc, proyeccion_info=info)
    if est:
        r["estimacion"] = {k: dict(cu_total=round(v["cu_total"], 4), p05=round(v["p05"], 4), p95=round(v["p95"], 4), metodo=v["metodo"],
                                   mase=None if v["mase"] in (None, math.inf) else round(v["mase"], 3)) for k, v in est.items()}
    return r
