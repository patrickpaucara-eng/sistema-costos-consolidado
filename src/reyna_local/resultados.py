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


def construir(libro, emp="FRE", nombre="Frenosa", periodo=None, ventas_csv=None):
    por_per, h = calcular_periodos(libro, emp)
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
        md, mod, cif = _f(v.get("MD", 0)), _f(v.get("PD", 0)), _f(v.get("CIF", 0))
        ct = round(md + mod + cif, 2); ing = ingreso(periodo, o)
        objetos.append(dict(codigo=o, producto=pro.get(o, o), cantidad=can.get(o, 0), md=md, mod=mod, cif=cif, admin=0.0, gasto_venta=0.0,
                            financiero=0.0, costo_total=ct, costo_unitario=round(ct / can[o], 4) if can.get(o) else 0, ingreso=ing, margen=round(ing - ct, 2)))
    serie = []
    for p in pers:
        ct = sum(_f(sum(v.values())) for v in por_per[p].values()); vt = sum(ingreso(p, o) for o in por_per[p])
        serie.append(dict(periodo=p, tipo="ACTUAL" if p == periodo else "HISTORICO", ventas=round(vt, 2), costo_total=round(ct, 2), margen=round(vt - ct, 2)))
    vt = sum(o["ingreso"] for o in objetos); ct = sum(o["costo_total"] for o in objetos); q = sum(o["cantidad"] for o in objetos)
    return dict(empresa=dict(codigo=emp, nombre=nombre), periodo_actual=periodo, sintesis="REAL", moneda="PEN",
                kpi=dict(ventas=round(vt, 2), costo_total=round(ct, 2), margen_operativo=round(vt - ct, 2),
                         rentabilidad=round((vt - ct) / vt, 4) if vt else 0, costo_unitario_prom=round(ct / q, 4) if q else 0),
                objetos=objetos, actividades=[], serie=serie, estado_resultados=[], relevancia=[], hallazgos=[], propuestas=[], escenarios=[])
