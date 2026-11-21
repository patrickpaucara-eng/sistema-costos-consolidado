"""Construye el CONTRATO de resultados (contrato.py) desde el cálculo publicado del caso. Las pantallas solo leen esto.
Etapa 1: síntesis REAL, ABC de producción (MD, MOD, CIF) y serie histórica. Etapas 2-3 agregan admin/ventas/financieros
(NIIF 18), relevancia, hallazgos, proyección, escenarios y propuestas sin cambiar la forma."""
import csv, os
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


def construir(libro, emp="FRE", nombre="Frenosa", periodo=None, ventas_csv=None, sintesis="REAL", _cache=None):
    """Síntesis (D-8/D-9, reglas por tipo de síntesis):
    REAL     costo integral del objeto = MD + MOD + CIF + administración + ventas + financieros (gerencial, precio objetivo).
    CONTABLE costo del inventario = MD + MOD + CIF (NIC 2 §10-16): administración, ventas y financieros son gastos del periodo;
             estado de resultados NIIF 18: Operación (ventas, costo de ventas, administración, ventas) y Financiación (financieros)."""
    if sintesis not in ("REAL", "CONTABLE"): raise ValueError("síntesis ESTIMADO: Etapa 3")
    por_per, h = _cache or calcular_periodos(libro, emp)
    pers = sorted(por_per); periodo = periodo or pers[-1]
    can = {str(r["NUMERO"]): float(r.get("CANTIDAD") or 0) for r in P.leer(libro, ["OBJETO"])["OBJETO"] for r in [dict(NUMERO=r["OBJ_NUM"], CANTIDAD=r["OBJ_CAN"], PRO=r["OBJ_PRO"])]}
    pro = {r["OBJ_NUM"]: r["OBJ_PRO"] for r in P.leer(libro, ["OBJETO"])["OBJETO"]}
    ventas = {}
    if ventas_csv:
        for r in csv.DictReader(open(ventas_csv, encoding="utf-8")):
            ventas[(r["periodo"], r["ot_id"])] = float(r["ventas_netas_soles"])
    def ingreso(p, ot):   # ventas por OT del periodo (ot_id OT00n dentro del código)
        idx = {"SW50": "OT001", "FRE9000": "OT002", "FRE9002": "OT003"}
        clave = next((v for k, v in idx.items() if f"-{k}-" in ot), None)
        return ventas.get((p, clave), 0.0)
    objetos = []
    for o, v in sorted(por_per[periodo].items()):
        md, mod, cif = _f(v.get("MD", 0)), _f(v.get("PD", 0)) + _f(v.get("SD", 0)), _f(v.get("CIF", 0))
        gad, gvt, gfi = (_f(v.get(k, 0)) for k in ("GAD", "GVT", "GFI"))
        if sintesis == "CONTABLE": gad = gvt = gfi = 0.0          # gastos del periodo, nunca inventario (NIC 2 §16)
        ct = round(md + mod + cif + gad + gvt + gfi, 2); ing = ingreso(periodo, o)
        objetos.append(dict(codigo=o, producto=pro.get(o, o), cantidad=can.get(o, 0), md=md, mod=mod, cif=cif, admin=gad, gasto_venta=gvt,
                            financiero=gfi, costo_total=ct, costo_unitario=round(ct / can[o], 4) if can.get(o) else 0, ingreso=ing, margen=round(ing - ct, 2)))
    serie = []
    for p in pers:
        ct = sum(_f(sum(v.values())) for v in por_per[p].values()); vt = sum(ingreso(p, o) for o in por_per[p])
        serie.append(dict(periodo=p, tipo="ACTUAL" if p == periodo else "HISTORICO", ventas=round(vt, 2), costo_total=round(ct, 2), margen=round(vt - ct, 2)))
    vt = sum(o["ingreso"] for o in objetos); ct = sum(o["costo_total"] for o in objetos); q = sum(o["cantidad"] for o in objetos)
    tot = {k: round(sum(_f(v.get(k, 0)) for v in por_per[periodo].values()), 2) for k in ("MD", "PD", "SD", "CIF", "GAD", "GVT", "GFI")}
    cventas = round(tot["MD"] + tot["PD"] + tot["SD"] + tot["CIF"], 2)
    er = [dict(categoria="OPERACION", concepto="Ventas netas", importe=round(vt, 2)),
          dict(categoria="OPERACION", concepto="Costo de ventas (MD + MOD + CIF)", importe=-cventas),
          dict(categoria="OPERACION", concepto="Gastos de administración", importe=-tot["GAD"]),
          dict(categoria="OPERACION", concepto="Gastos de ventas", importe=-tot["GVT"]),
          dict(categoria="FINANCIACION", concepto="Gastos financieros", importe=-tot["GFI"])]
    r_oper = round(vt - cventas - tot["GAD"] - tot["GVT"], 2)
    acts = []
    for (tipo, clave, conc, val) in R.calcular(h, dict(PER=periodo, EMP=emp), {"VALUACION_PROMEDIO": valuacion_alg01(libro)})[0]:
        if tipo == "ACTIVIDAD": acts.append(dict(codigo=clave, nombre=clave, costo=round(val, 2), inductor="", tasa=0.0))
    return dict(empresa=dict(codigo=emp, nombre=nombre), periodo_actual=periodo, sintesis=sintesis, moneda="PEN",
                kpi=dict(ventas=round(vt, 2), costo_total=round(ct, 2), margen_operativo=r_oper,
                         rentabilidad=round(r_oper / vt, 4) if vt else 0, costo_unitario_prom=round(ct / q, 4) if q else 0,
                         resultado_antes_impuestos=round(r_oper - tot["GFI"], 2)),
                objetos=objetos, actividades=acts, serie=serie, estado_resultados=er, relevancia=[], hallazgos=[], propuestas=[], escenarios=[])
