"""Entregable 13. Cada agente registra su trabajo en su propio CSV (docs/entrega/tiempos/<agente>.csv) para no chocar
en un binario; este script arma REGISTRO_TIEMPOS.xlsx. Columnas: fecha,inicio,termino,actividad,etapa,responsable,resultado"""
import csv, glob, pathlib
from openpyxl import load_workbook
R = pathlib.Path(__file__).resolve().parents[1]; X = R / "docs/entrega/REGISTRO_TIEMPOS.xlsx"
wb = load_workbook(X); ws = wb.active; ya = {tuple(str(c or "") for c in r) for r in ws.iter_rows(values_only=True)}
for f in sorted(glob.glob(str(R / "docs/entrega/tiempos/*.csv"))):
    for fila in csv.reader(open(f, encoding="utf-8")):
        if fila and fila[0] != "fecha" and tuple(fila) not in ya: ws.append(fila); ya.add(tuple(fila))
wb.save(X); print("registro actualizado:", ws.max_row - 1, "filas")
