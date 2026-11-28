"""Pieza 24: genera libros_hostiles/ a partir de SERVITEC_sintetico.xlsx (no modifica el original).
Uso: python hacer_hostiles.py <SERVITEC_sintetico.xlsx> <carpeta_salida>"""
import shutil
import sys
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill

BASE, OUT = Path(sys.argv[1]), Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)


def fila_de(ws, pred):
    for i, r in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if pred(r):
            return i
    raise KeyError("fila no encontrada")


def col(ws, nombre):
    return [c.value for c in ws[1]].index(nombre) + 1


CASOS = []


def caso(num, slug, defecto, que_se_toco, esperado, detecta_hoy, fuente_msg):
    def deco(f):
        CASOS.append(dict(num=num, slug=slug, defecto=defecto, toco=que_se_toco, esperado=esperado,
                          detecta=detecta_hoy, fuente=fuente_msg, f=f))
        return f
    return deco


@caso("00", "control_sin_defecto", "Ninguno: copia del libro base con la hoja LEEME añadida.",
      "Solo se agrega la hoja LEEME.", "Sin errores; el cálculo de julio da REB 22,975 y MPR 5,165 (verificado con calcular() del motor completo, 28/11/2026).",
      "SÍ (acepta)", "Control: demuestra que la hoja LEEME y el guardado con openpyxl no rompen el libro.")
def c00(wb):
    return []


@caso("01", "hoja_obligatoria_borrada", "Se borró una hoja obligatoria: CRITERIO.",
      "Hoja CRITERIO eliminada completa.",
      "Falta la hoja CRITERIO. Inductores (unidad de medida).",
      "SÍ", "libro_dbd.validar(): «Falta la hoja {n}. {DESCRIPCION}».")
def c01(wb):
    del wb["CRITERIO"]
    return ["CRITERIO: hoja eliminada"]


@caso("02", "celdas_vacias_MEDIDA", "Celdas vacías en MEDIDA: la cantidad de HORAS_MOD de julio quedó en blanco.",
      "MEDIDA, filas 184–186 (2025-07, HORAS_MOD → DES, BOB, PRU): MED_CAN 300/500/200 → vacío.",
      "Hoja MEDIDA, fila 184: la cantidad debe ser un número ≥ 0. (y lo mismo para las filas 185 y 186)",
      "SÍ", "libro_dbd.validar(): revisa MED_CAN con _num() y ≥ 0.")
def c02(wb):
    ws = wb["MEDIDA"]
    c = col(ws, "MED_CAN")
    cambios = []
    for dest in ("DES", "BOB", "PRU"):
        i = fila_de(ws, lambda r: r[0] == "2025-07" and r[2] == "HORAS_MOD" and r[4] == dest)
        cambios.append(f"MEDIDA fila {i}: MED_CAN {ws.cell(i, c).value} → vacío")
        ws.cell(i, c).value = None
    return cambios


@caso("03", "texto_en_monto", "Texto en un monto: el ingreso de julio de REB se escribió «30,000» (texto con coma).",
      "VENTA, fila 14 (2025-07, REB): VTA_ING 30000 → «30,000» (texto).",
      "Hoja VENTA, fila 14: el ingreso (VTA_ING) debe ser un número.",
      "SÍ", "libro_dbd.validar(): revisa VTA_ING con _num(). Ojo: «30000» como texto SÍ pasa, porque float('30000') funciona; "
            "y LINEA.LIN_MTO no se revisa (ver hallazgos).")
def c03(wb):
    ws = wb["VENTA"]
    i = fila_de(ws, lambda r: r[2] == "2025-07" and r[4] == "REB")
    c = col(ws, "VTA_ING")
    antes = ws.cell(i, c).value
    ws.cell(i, c).value = "30,000"
    ws.cell(i, c).data_type = "s"
    return [f"VENTA fila {i}: VTA_ING {antes} → '30,000' (texto)"]


@caso("04", "fechas_al_reves", "Fechas al revés: el periodo 2025-07 empieza después de terminar.",
      "PERIODO, fila 8 (2025-07): PER_INI 20250701 ↔ PER_FIN 20250731 intercambiados.",
      "PROPUESTO: «Hoja PERIODO, fila 8: PER_INI (20250731) es posterior a PER_FIN (20250701).»",
      "NO (hallazgo)", "libro_dbd.validar() solo revisa que PER_COD tenga la forma AAAA-MM; no compara PER_INI con PER_FIN. "
                       "calcular() 2025-07 tampoco avisa y da los mismos costos (REB 22,975 / MPR 5,165): el error pasa en silencio.")
def c04(wb):
    ws = wb["PERIODO"]
    i = fila_de(ws, lambda r: r[0] == "2025-07")
    ci, cf = col(ws, "PER_INI"), col(ws, "PER_FIN")
    a, b = ws.cell(i, ci).value, ws.cell(i, cf).value
    ws.cell(i, ci).value, ws.cell(i, cf).value = b, a
    return [f"PERIODO fila {i}: PER_INI {a} → {b}; PER_FIN {b} → {a}"]


@caso("05", "codigo_duplicado", "Código duplicado: la orden OT-SRV-REB-2025-07 aparece dos veces en OBJETO con cantidades distintas.",
      "OBJETO: se agrega la fila 18, copia de la fila 14 (OT-SRV-REB-2025-07) con OBJ_CAN 12 en vez de 10.",
      "PROPUESTO: «Hoja OBJETO, fila 18: OBJ_NUM «OT-SRV-REB-2025-07» está repetido (ya está en la fila 14).»",
      "NO (hallazgo GRAVE)", "libro_dbd.validar() guarda OBJETO en un diccionario por OBJ_NUM: la segunda fila pisa a la primera sin aviso. "
                       "calcular() 2025-07 lo acepta: REB queda con cantidad 12, costo total 22,975 y costo unitario 1,914.58 "
                       "(correcto: 2,297.50, −16.7 %); el margen del mes sube de 9,860 a 13,422.33. Nada avisa.")
def c05(wb):
    ws = wb["OBJETO"]
    i = fila_de(ws, lambda r: r[0] == "OT-SRV-REB-2025-07")
    vals = [c.value for c in ws[i]]
    vals[col(ws, "OBJ_CAN") - 1] = 12
    ws.append(vals)
    return [f"OBJETO fila {ws.max_row}: copia de la fila {i} con OBJ_CAN 12"]


@caso("06", "criterio_suma_cero", "Criterio que suma 0: el inductor DES_OT de julio quedó en cero para las dos órdenes.",
      "MEDIDA, filas 190–191 (2025-07, DES_OT → OT-SRV-REB-2025-07 / OT-SRV-MPR-2025-07): MED_CAN 200/100 → 0.",
      "Al calcular: «I8: P4C DES tiene monto 5700.00 y su criterio DES_OT suma cero» (validar() lo acepta porque 0 es ≥ 0).",
      "PARCIAL: validar() NO; calcular() SÍ lo rechaza (verificado)",
      "metodos/reparto_etapas.py, línea 290: Rechazo I8. Mensaje real de calcular(): «I8: P4C DES tiene monto 5700.00 y su "
      "criterio DES_OT suma cero». El usuario solo se entera al calcular, no al cargar el libro.")
def c06(wb):
    ws = wb["MEDIDA"]
    c = col(ws, "MED_CAN")
    cambios = []
    for ot in ("OT-SRV-REB-2025-07", "OT-SRV-MPR-2025-07"):
        i = fila_de(ws, lambda r: r[0] == "2025-07" and r[2] == "DES_OT" and r[4] == ot)
        cambios.append(f"MEDIDA fila {i}: MED_CAN {ws.cell(i, c).value} → 0")
        ws.cell(i, c).value = 0
    return cambios


@caso("07", "archivo_truncado", "Archivo truncado: se cortó el archivo a la mitad de sus bytes (descarga o copia interrumpida).",
      "Archivo completo → primeros 50 % de los bytes. La hoja LEEME existía antes del corte pero ya no se puede abrir: "
      "ver 07_archivo_truncado_LEEME.md.",
      "El archivo no es un libro Excel (.xlsx) legible.",
      "SÍ", "libro_dbd.validar(): cualquier excepción al abrir el libro devuelve ese mensaje.")
def c07(wb):
    return ["(se trunca después de guardar)"]


@caso("08", "columnas_otro_orden", "Columnas en otro orden: MEDIDA y OBJETO tienen sus columnas invertidas (mismos nombres, mismos datos).",
      "MEDIDA y OBJETO: orden de columnas invertido (la última pasa a ser la primera).",
      "Sin errores: el sistema lee por nombre de columna, no por posición. El cálculo de julio debe dar lo mismo que el control "
      "(REB 22,975 / MPR 5,165).",
      "SÍ (acepta)", "libro_dbd._tablas(): arma cada fila con dict(zip(cabecera, fila)). calcular() 2025-07 da REB 22,975 / MPR 5,165, igual que el control (verificado).")
def c08(wb):
    cambios = []
    for n in ("MEDIDA", "OBJETO"):
        ws = wb[n]
        filas = [list(r) for r in ws.iter_rows(values_only=True)]
        ws.delete_rows(1, ws.max_row)
        for f in filas:
            ws.append(list(reversed(f)))
        cambios.append(f"{n}: {len(filas[0])} columnas invertidas")
    return cambios


def leeme(wb, c, cambios, actual):
    ws = wb.create_sheet("LEEME", 0)
    neg = Font(name="Arial", bold=True)
    ws["A1"] = f"Libro hostil {c['num']} · {c['slug']}"
    ws["A1"].font = Font(name="Arial", bold=True, size=13)
    filas = [
        ("Defecto", c["defecto"]),
        ("Qué se tocó", c["toco"]),
        ("Cambios exactos", " | ".join(cambios)),
        ("Mensaje que debería dar el sistema", c["esperado"]),
        ("¿Lo detecta hoy validar()?", c["detecta"]),
        ("Mensaje real de validar() en esta copia", " | ".join(actual) if actual else "(ninguno: libro aceptado)"),
        ("De dónde sale", c["fuente"]),
        ("Libro base", "SERVITEC_sintetico.xlsx (sintético, sin datos reales). validar() y calcular() del repo con fuente/DBD_Fuente.xlsx, 28/11/2026."),
        ("Cómo probarlo", "En el sistema: subir este archivo en «Cargar libro» (calculo_local.registrar) y, si se acepta, calcular "
                          "2025-07 REAL. Anotar el mensaje y compararlo con la fila «Mensaje que debería dar»."),
    ]
    for k, (a, b) in enumerate(filas, start=3):
        ws.cell(k, 1, a).font = neg
        ws.cell(k, 2, b).font = Font(name="Arial")
        ws.cell(k, 2).alignment = Alignment(wrap_text=True, vertical="top")
        ws.cell(k, 1).alignment = Alignment(wrap_text=True, vertical="top")
        if a.startswith("Mensaje que"):
            ws.cell(k, 2).fill = PatternFill("solid", fgColor="FFE9B8")
    ws.column_dimensions["A"].width = 34
    ws.column_dimensions["B"].width = 110


if __name__ == "__main__":
    import json
    sys.path.insert(0, sys.argv[3])                       # repo/src para validar()
    import reyna_local.libro_dbd as B
    B.PLANTILLA = Path(sys.argv[4])
    resumen = []
    for c in CASOS:
        nombre = f"{c['num']}_{c['slug']}.xlsx"
        wb = load_workbook(BASE)
        cambios = c["f"](wb)
        tmp = OUT / f"_tmp_{nombre}"
        wb.save(tmp)
        actual = B.validar(tmp)
        wb = load_workbook(tmp)
        leeme(wb, c, cambios, actual)
        destino = OUT / nombre
        wb.save(destino)
        tmp.unlink()
        despues = B.validar(destino)                       # la hoja LEEME no debe cambiar el resultado
        assert despues == actual, (nombre, actual, despues)
        if c["num"] == "07":
            datos = destino.read_bytes()
            destino.write_bytes(datos[: len(datos) // 2])
            actual = B.validar(destino)
        resumen.append(dict(archivo=nombre, defecto=c["defecto"], esperado=c["esperado"], detecta=c["detecta"],
                            actual=actual, cambios=cambios, fuente=c["fuente"]))
    (OUT / "_resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps([(r["archivo"], r["actual"][:3]) for r in resumen], ensure_ascii=False, indent=1))
