"""Caso Frenosa, julio 2010 (Cherres Juárez 2010, PUCP), en el formato de libro por tabla del motor (igual que P10).
Solo DATOS del caso; cero código del proyecto pasado. Uso: python casos/frenosa/generar_julio.py casos/plantilla_caso.xlsx <salida.xlsx>"""
import sys, shutil
from openpyxl import load_workbook
EMP, PER = "FRE", "2010-07"
OTS = [("OT001", "FEF0014P_SW50", 38174, "MAT_SW50", 3.2045), ("OT002", "FEF0014P_FRE9000", 44039, "MAT_FRE9000", 5.481),
       ("OT003", "FEF0011P_FRE9002", 15807, "MAT_FRE9002", 5.0792)]
ACT = [("FO-1", "Impregnación", 1.0), ("FO-2", "Enrollado", 0.31), ("FO-3", "Prensado", 0.65), ("FO-4", "Horneado", 1.05),
       ("FO-5", "Lijado", 0.17), ("FO-6", "Taladrado", 0.39), ("FO-7", "Acabado", 0.27)]
TOL, KG, OPERARIOS, SALARIO = 0.13, 98020, 59, 1350          # Cuadros 2 y 3: tolerancias 5+4+2+2 %; Te redondeado a 2 decimales
OTROS = [("REC001", "Personal indirecto", 5724, [.14, .19, .49, .09, .03, .03, .03]), ("REC002", "Servicios", 8199, [.17, .09, .16, .22, .14, .10, .11]),
         ("REC003", "Operacionales", 49769, [.25, .14, .13, .15, .13, .12, .09]), ("REC004", "No operacionales", 2829, [.25, .14, .13, .15, .13, .12, .09]),
         ("REC005", "Instalaciones", 25617, [.17, .09, .16, .22, .14, .10, .11])]          # Cuadros 4-6
MANT = [463 + 974, 137, 4371, 1258, 5672, 1425, 238]                                             # Cuadro 7, por actividad
CC = 12 * 147 + 10 * 34 + 11 * 161 + 8 * 29 + 8 * 27 + 16 * 94                                   # Cuadro 8 = 5827
ING = 23 * 147 + 2 * 34 + 8 * 161                                                                 # Cuadro 9 = 4737
PCT_SOP = [.23, .11, .17, .22, .09, .10, .08]                                                     # Cuadro 12
AC_OT_PROD, AC_OT_SOP = [.45, .52, .03], [.39, .45, .16]                                          # pesos AC→OT
VENTAS = [324479, 453602, 110649]                                                                 # Cuadro 18


def limpiar(ws):
    if ws.max_row > 1: ws.delete_rows(2, ws.max_row - 1)


def generar(plantilla, salida):
    shutil.copy(plantilla, salida); wb = load_workbook(salida)
    for s in ["EMPRESA", "PERIODO", "OBJETO", "RECURSO", "EVENTO", "LINEA", "KARDEX", "REGLA_REPARTO", "CRITERIO", "MEDIDA", "CENTRO", "ACTIVIDAD"]:
        limpiar(wb[s])
    wb["EMPRESA"].append([EMP, "Frenosa (caso de desarrollo)", "PEN"])
    wb["PERIODO"].append([PER, EMP, 20100701, 20100731, "A"])
    rec, eve, lin, kdx, rr, cri, med = wb["RECURSO"], wb["EVENTO"], wb["LINEA"], wb["KARDEX"], wb["REGLA_REPARTO"], wb["CRITERIO"], wb["MEDIDA"]
    n = 0
    def evento(trx, obj=None):
        nonlocal n; n += 1; eve.append([n, trx, 20100731 if trx != "T14" else 20100701, EMP, PER, obj, None, "PEN", 1, None]); return n
    for ot, pro, q, mat, cu in OTS:
        wb["OBJETO"].append([ot, EMP, pro, q, "T", None, None, None, None])
        rec.append([mat, f"Material {mat[4:]}", "MAT_DIR", "kg", None, "S"])
        e = evento("T14"); lin.append([e, 1, mat, q, cu, None, None, round(q * cu, 2), None, None]); kdx.append([e, 1, "ALM_FRE", PER, 20100701, "T14", None, None, mat, q, round(q * cu, 2)])
        e = evento("T15", ot); lin.append([e, 1, mat, q, None, None, None, None, None, None]); kdx.append([e, 1, "ALM_FRE", PER, 20100731, "T15", None, None, mat, -q])
        rr.append(["P1", mat, "CONSUMO", 19000101, "Material directo por kardex (D-10)"])
    # Mano de obra → actividades por minutos estándar (Te × kg; el factor de distribución Fd es común a todas y se cancela)
    rec.append(["MOD", "Personal directo (operarios)", "PERS_DIR", "S/", None, "S"])
    e = evento("T25.3"); lin.append([e, 1, "MOD", 1, OPERARIOS * SALARIO, None, None, OPERARIOS * SALARIO, None, None])
    rr.append(["P2", "MOD", "MIN_STD", 19000101, "Minutos estándar por actividad (Cuadros 2-3)"]); cri.append(["MIN_STD", "Minutos estándar Te×kg", "min", "S"])
    for cod, nom, tn in ACT:
        wb["ACTIVIDAD"].append([cod, nom, "kg"]); wb["ACTIVIDAD"].append(["S-" + cod, f"Soporte de {nom}", "S/"])
        med.append([PER, EMP, "MIN_STD", "ACT", cod, round(tn * (1 + TOL), 2) * KG])
    for cod, nom, imp, pct in OTROS:
        rec.append([cod, nom, "INDIRECTO", "S/", None, "S"]); e = evento("T17"); lin.append([e, 1, cod, 1, imp, None, None, imp, None, None])
        c = "EC_" + cod; rr.append(["P4A", cod, c, 19000101, "Cuadro 6"]); cri.append([c, f"Inductor de {nom}", "%", "S"])
        for (a, _, _), p in zip(ACT, pct): med.append([PER, EMP, c, "ACT", a, p])
    for cod, nom, imp, cri_cod, pesos in [("MANT", "Mantenimiento", sum(MANT), "SOP_MANT", MANT), ("CC", "Control de calidad", CC, "SOP_CC", PCT_SOP), ("ING", "Ingeniería y desarrollo", ING, "SOP_ING", PCT_SOP)]:
        rec.append([cod, nom, "INDIRECTO", "S/", None, "S"]); e = evento("T17"); lin.append([e, 1, cod, 1, imp, None, None, imp, None, None])
        rr.append(["P4A", cod, cri_cod, 19000101, "Cuadros 7-9 y 12"]); cri.append([cri_cod, f"Distribución de {nom}", "", "S"])
        for (a, _, _), p in zip(ACT, pesos): med.append([PER, EMP, cri_cod, "ACT", "S-" + a, p])
    cri.append(["AC_PROD", "Peso actividad→OT (producción)", "%", "S"]); cri.append(["AC_SOP", "Peso actividad→OT (soporte)", "%", "S"])
    for a, _, _ in ACT:
        rr.append(["P4C", a, "AC_PROD", 19000101, "Pesos AC-OT producción"]); rr.append(["P4C", "S-" + a, "AC_SOP", 19000101, "Pesos AC-OT soporte"])
    for (ot, *_), pp, ps in zip(OTS, AC_OT_PROD, AC_OT_SOP):
        med.append([PER, EMP, "AC_PROD", "OBJ", ot, pp]); med.append([PER, EMP, "AC_SOP", "OBJ", ot, ps])
    cri.append(["CONSUMO", "Consumo", "kg", "S"])
    wb.save(salida); return salida


if __name__ == "__main__":
    print(generar(sys.argv[1], sys.argv[2]))
