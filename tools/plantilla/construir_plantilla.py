"""Construye casos/plantilla_dbd.xlsx: la plantilla ÚNICA del DBD (D-6) para operar y costear en el mismo libro.
Parte del modelo operativo completo (tablas, transacciones, usuarios, cierre) y deja vacías todas las tablas de datos de
empresa: no queda ningún dato de casos anteriores. El catálogo TIPO_RECURSO y los métodos registrados vienen de la plantilla
de costeo. Uso: python tools/plantilla/construir_plantilla.py"""
import shutil, sys
from pathlib import Path
from openpyxl import load_workbook

R = Path(__file__).resolve().parents[2]
ORIGEN = R / "tests/fixtures/ola1/Sistema_Costos.xlsx"      # modelo operativo (configuración del motor)
COSTEO = R / "casos/plantilla_caso.xlsx"                    # catálogos del costeo
DESTINO = R / "casos/plantilla_dbd.xlsx"

# Configuración del método y del motor: se conserva. Todo lo demás es dato de una empresa y se vacía.
CONFIG = {"PERFIL_TRX", "MENSAJE", "REGLA", "PARAMETRO", "IMPUESTO", "CAUSA_DIF", "UMBRAL", "USUARIO", "USUARIO_PERFIL",
          "REGLA_OFICIAL", "REGLA_IMPL", "CIERRE_PASO", "TRX_MODULO", "DATO_REF", "TRX_KARDEX", "METODO_REGISTRADO", "EJE",
          "EJE_PUNTO", "METODO_SRV", "METODO_PAS", "TRX", "TRX_CAMPO", "TOP", "OME", "MET", "MCA", "FRM", "CND", "ALG", "PAL",
          "TABLAS_LOGICAS", "MODELO_FISICO", "CAUSA_INEF", "TIPO_RECURSO"}
DE_COSTEO = ("TIPO_RECURSO", "METODO_REGISTRADO", "EJE")          # se toman de la plantilla de costeo (más recientes)


def construir():
    shutil.copy(ORIGEN, DESTINO); wb = load_workbook(DESTINO); cst = load_workbook(COSTEO)
    for ws in wb.worksheets:
        if ws.title not in CONFIG or ws.title in DE_COSTEO:
            if ws.max_row > 1: ws.delete_rows(2, ws.max_row - 1)
    for n in DE_COSTEO:
        cab = [c.value for c in wb[n][1]]; ccab = [c.value for c in cst[n][1]]
        for fila in cst[n].iter_rows(min_row=2, values_only=True):
            if fila and any(v is not None for v in fila):
                d = dict(zip(ccab, fila))
                if n == "TIPO_RECURSO":                 # vocabulario de elementos del motor operativo (columnas COP_MAT, COP_MOD…);
                    d["TRE_ELE"] = {"MD": "MAT", "PD": "MOD"}.get(d.get("TRE_ELE"), d.get("TRE_ELE"))   # el costeo lo traduce (ELEM)
                wb[n].append([d.get(c) for c in cab])
    # REGLA_IMPL: el motor Python ejecuta DIRECTO, ESCALONADO y RECIPROCO (tarea 1.3, 23-nov)
    act = wb["ACTIVIDAD"]                                                  # Modelo 3 (Oria): nivel E/A/O de la actividad
    if "ACT_NIVEL" not in [c.value for c in act[1]]: act.cell(1, act.max_column + 1, "ACT_NIVEL")
    for sheet, names in (("RECURSO", ("REC_COQ",)), ("CRITERIO", ("CRI_RESP", "CRI_EVID"))):
        ws = wb[sheet]
        for name in names:
            if name not in [c.value for c in ws[1]]: ws.cell(1, ws.max_column + 1, name)
    tc = wb["TIPO_CAMBIO"]; tc.append(["PEN", 19000101, 1])              # moneda funcional por defecto
    for u in wb["USUARIO"].iter_rows(min_row=2):                          # los usuarios se asignan a la empresa al cargarla
        u[3].value = None
    wb.save(DESTINO); return DESTINO


if __name__ == "__main__":
    print(construir())
