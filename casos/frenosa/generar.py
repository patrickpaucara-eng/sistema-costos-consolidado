"""Caso Frenosa 2010 (12 meses) desde los CSV normalizados (OT-C03) al libro por tabla del motor.
Solo datos. Reglas aplicadas (decisiones del dueño):
- D-10 material por kardex: compras (T14), consumos a la orden (T15), devoluciones a proveedor (T14.1); promedio ponderado continuo
  desde el saldo inicial de enero; los «saldo inicial» de los meses siguientes se usan solo para comprobar el encadenamiento.
- D-11 costo de adquisición directo: costo unitario = precio con IGV / (1 + IGV) + flete del documento / cantidad del documento.
- Mano de obra → actividades por minutos estándar Te × kg (Fd común se cancela); otros recursos y soporte → actividades;
  actividades → órdenes con pesos de producción y de soporte.
Uso: python casos/frenosa/generar.py casos/plantilla_caso.xlsx <salida.xlsx>"""
import csv, os, shutil, sys
from collections import defaultdict
from openpyxl import load_workbook
DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "datos", "frenosa")
EMP = "FRE"
MAT = {"MAT001": "MAT_SW50", "MAT002": "MAT_FRE9000", "MAT003": "MAT_FRE9002"}


def leer(nombre):
    return list(csv.DictReader(open(os.path.join(DIR, nombre), encoding="utf-8")))


def num(x):
    return float(str(x).replace(",", "")) if str(x).strip() not in ("", "None") else 0.0


def _fec(s):
    return int(str(s).replace("-", "")[:8])


def generar(plantilla, salida, periodos=None):
    shutil.copy(plantilla, salida); wb = load_workbook(salida)
    for s in ["EMPRESA", "PERIODO", "OBJETO", "RECURSO", "EVENTO", "LINEA", "KARDEX", "REGLA_REPARTO", "CRITERIO", "MEDIDA", "CENTRO", "ACTIVIDAD"]:
        if wb[s].max_row > 1: wb[s].delete_rows(2, wb[s].max_row - 1)
    ot = leer("Ordenes_Trabajo.csv"); pers = sorted({r["periodo"] for r in ot})
    pers = [p for p in pers if periodos is None or p in periodos]
    wb["EMPRESA"].append([EMP, "Frenosa (caso de desarrollo)", "PEN"])
    eve, lin, kdx, rec, rr, cri, med = (wb[s] for s in ["EVENTO", "LINEA", "KARDEX", "RECURSO", "REGLA_REPARTO", "CRITERIO", "MEDIDA"])
    n = [0]
    def evento(trx, per, fec, obj=None):
        n[0] += 1; eve.append([n[0], trx, fec, EMP, per, obj, None, "PEN", 1, None]); return n[0]
    for c, d in MAT.items():
        rec.append([d, f"Material {d[4:]}", "MAT_DIR", "kg", None, "S"]); rr.append(["P1", d, "CONSUMO", 19000101, "Material por kardex (D-10)"])
    for p in pers:
        a, m = p.split("-"); fin = 20000000 + 0  # placeholder
        wb["PERIODO"].append([p, EMP, int(a + m + "01"), int(a + m + "31"), "A"])
    for r in ot:
        if r["periodo"] in pers: wb["OBJETO"].append([r["codigo_ot"], EMP, r["objeto_costo_id"], num(r["cantidad_producida"]), "T", None, None, None, None])
    # --- kardex continuo (D-10, D-11) ---
    saldos = []                                   # (periodo, material, cantidad, importe) de «saldo inicial» para comprobar encadenamiento
    primero = True
    for r in sorted(leer("Compras.csv"), key=lambda r: (r["fecha"], r["compra_id"])):
        if r["periodo"] not in pers: continue
        mat = MAT[r["item_codigo"]]; q = num(r["cantidad"]); t = r["tipo_movimiento"]; f = _fec(r["fecha"])
        if t == "Saldo inicial":
            saldos.append((r["periodo"], mat, q, num(r["importe_soles"])))
            if r["periodo"] != pers[0]: continue
            cu = num(r["importe_soles"]) / q if q else 0
            e = evento("T14", r["periodo"], f); lin.append([e, 1, mat, q, cu, None, None, round(num(r["importe_soles"]), 2), None, None])
            kdx.append([e, 1, "ALM_FRE", r["periodo"], f, "T14", None, "SALDO", mat, q, round(num(r["importe_soles"]), 2)])
        elif t == "Compra":
            igv = num(r["igv_pct"]); cu = num(r["precio_unitario_con_igv"]) / (1 + igv) + num(r["flete_soles"]) / q
            val = round(q * cu, 2)
            e = evento("T14", r["periodo"], f); lin.append([e, 1, mat, q, cu, None, None, val, None, None])
            kdx.append([e, 1, "ALM_FRE", r["periodo"], f, "T14", None, r["documento"], mat, q, val])
        elif t == "Consumo":
            e = evento("T15", r["periodo"], f, r["destino"]); lin.append([e, 1, mat, q, None, None, None, None, None, None])
            kdx.append([e, 1, "ALM_FRE", r["periodo"], f, "T15", None, r["documento"], mat, -q])
        elif t.startswith("Devolucion"):
            e = evento("T14.1", r["periodo"], f); lin.append([e, 1, mat, q, None, None, None, None, None, None])
            kdx.append([e, 1, "ALM_FRE", r["periodo"], f, "T14.1", None, r["documento"], mat, -q])
    # --- mano de obra, otros recursos y soporte por periodo ---
    acts = []
    for r in leer("Actividades.csv"):
        if r["periodo"] == pers[0]: acts.append(r["codigo_actividad"]); wb["ACTIVIDAD"].append([r["codigo_actividad"], r["nombre_actividad"], "kg"]); wb["ACTIVIDAD"].append(["S-" + r["codigo_actividad"], "Soporte de " + r["nombre_actividad"], "S/"])
    rec.append(["MOD", "Personal directo (operarios)", "PERS_DIR", "S/", None, "S"]); rr.append(["P2", "MOD", "MIN_STD", 19000101, "Minutos estándar Te×kg"]); cri.append(["MIN_STD", "Minutos estándar", "min", "S"])
    otros = {r["codigo_recurso"]: r["nombre_recurso"] for r in leer("costo_otros_recursos(CI).csv")}
    for c, nom in otros.items():
        rec.append([c, nom, "INDIRECTO", "S/", None, "S"]); rr.append(["P4A", c, "EC_" + c, 19000101, "Cuadro 6"]); cri.append(["EC_" + c, "Inductor de " + nom, "%", "S"])
    for c, nom, k in [("MANT", "Mantenimiento", "SOP_MANT"), ("CC", "Control de calidad", "SOP_CC"), ("ING", "Ingeniería y desarrollo", "SOP_ING")]:
        rec.append([c, nom, "INDIRECTO", "S/", None, "S"]); rr.append(["P4A", c, k, 19000101, "Cuadros 7-9 y 12"]); cri.append([k, "Distribución de " + nom, "", "S"])
    for k in ("AC_PROD", "AC_SOP", "CONSUMO"): cri.append([k, k, "", "S"])
    for a in acts: rr.append(["P4C", a, "AC_PROD", 19000101, "Pesos AC-OT producción"]); rr.append(["P4C", "S-" + a, "AC_SOP", 19000101, "Pesos AC-OT soporte"])
    codot = {(r["periodo"], r["ot_id"]): r["codigo_ot"] for r in ot}
    for p in pers:
        pd = [r for r in leer("Personal_directos.csv") if r["periodo"] == p]
        total = num(pd[0]["cantidad_operarios"]) * num(pd[0]["salario_mensual_operario_soles"])
        e = evento("T25.3", p, int(p.replace("-", "") + "28")); lin.append([e, 1, "MOD", 1, total, None, None, total, None, None])
        for r in pd:
            ts = sum(num(r[k]) for k in ("tolerancia_personal_pct", "tolerancia_fatiga_pct", "tolerancia_pie_pct", "tolerancia_encorvado_pct"))
            te = round(num(r["tiempo_normal_min_kg"]) * (1 + ts), int(num(r["redondear_te_decimales"])))
            med.append([p, EMP, "MIN_STD", "ACT", r["codigo_actividad"], te * num(r["kg_producidos_periodo"])])
        for r in [r for r in leer("costo_otros_recursos(CI).csv") if r["periodo"] == p]:
            e = evento("T17", p, int(p.replace("-", "") + "28")); lin.append([e, 1, r["codigo_recurso"], 1, num(r["importe_soles"]), None, None, num(r["importe_soles"]), None, None])
        for r in [r for r in leer("EC_AC_Inductores.csv") if r["periodo"] == p]:
            med.append([p, EMP, "EC_" + r["codigo_recurso"], "ACT", r["codigo_actividad"], num(r["porcentaje_inductor"])])
        mant = defaultdict(float)
        for r in [r for r in leer("Soporte_Mantenimiento(CI).csv") if r["periodo"] == p]: mant[r["codigo_actividad_destino"]] += num(r["costo_equipo_soles"])
        cc = sum(num(r["cantidad"]) * num(r["costo_unitario_soles"]) for r in leer("Soporte_Control_Calidad(CI).csv") if r["periodo"] == p)
        ing = sum(num(r["cantidad"]) * num(r["costo_unitario_soles"]) for r in leer("Soporte_Ingenieria(CI).csv") if r["periodo"] == p)
        for c, imp in (("MANT", sum(mant.values())), ("CC", cc), ("ING", ing)):
            e = evento("T17", p, int(p.replace("-", "") + "28")); lin.append([e, 1, c, 1, imp, None, None, imp, None, None])
        for a, v in mant.items(): med.append([p, EMP, "SOP_MANT", "ACT", "S-" + a, v])
        for r in [r for r in leer("Soporte_CC_ING_Inductores.csv") if r["periodo"] == p]:
            med.append([p, EMP, "SOP_CC" if r["proceso_soporte"].startswith("Control") else "SOP_ING", "ACT", "S-" + r["codigo_actividad"], num(r["porcentaje_distribucion"])])
        for hoja, k in (("AC_OT_Pesos_Produccion.csv", "AC_PROD"), ("AC_OT_Pesos_Soporte.csv", "AC_SOP")):
            agg = defaultdict(float)
            for r in [r for r in leer(hoja) if r["periodo"] == p]: agg[codot[(p, r["ot_id"])]] = num(r["porcentaje_inductor"])
            for o, v in agg.items(): med.append([p, EMP, k, "OBJ", o, v])
    wb.save(salida); return salida, saldos


if __name__ == "__main__":
    print(generar(sys.argv[1], sys.argv[2])[0])
