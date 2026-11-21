# -*- coding: utf-8 -*-
"""Utilidades comunes de las cargas de casos (ARQUITECTURA_V4_1 §8.5). Una carga produce un ESTADO DE HECHOS: un libro con
una hoja por tabla física (columnas en el orden de DBD_4), legible por kit/puerto_lectura.py, más un archivo de rechazos.
Validación defensiva (PR-4): lo inválido va a rechazos con su motivo; nunca se corrige en silencio."""
import csv, os, re
from collections import OrderedDict
from openpyxl import Workbook, load_workbook

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DBD = os.path.join(RAIZ, "fuente", "DBD_Fuente.xlsx")
DATOS = os.path.join(RAIZ, "fuente", "Datos_Iniciales.xlsx")


def norm(s):
    """R-50: los códigos se normalizan quitando espacios ('OT 1480' → 'OT1480')."""
    return re.sub(r"\s+", "", str(s)) if s is not None else None


def num(v):
    return float(v) if isinstance(v, (int, float)) else 0.0


def columnas_dbd():
    t = OrderedDict()
    for r in load_workbook(DBD, read_only=True)["DBD_4_Modelo_Interno"].iter_rows(min_row=5, values_only=True):
        if r and r[0]: t.setdefault(r[0], []).append(r[3])
    return t


# Tablas que todo estado de caso trae (aunque estén vacías), para que el puerto de lectura las encuentre (§8.2).
TABLAS_CASO = ["EMPRESA", "PERIODO", "TIPO_RECURSO", "RECURSO", "CENTRO", "ACTIVIDAD", "OBJETO", "CLIENTE", "CRITERIO",
               "REGLA_REPARTO", "MEDIDA", "EVENTO", "LINEA", "KARDEX", "VENTA", "INV_PROCESO", "ESTIMACION", "LIN_ESTIM",
               "PARAMETRO", "METODO_REGISTRADO", "EJE", "RESULTADO_METODO", "ALERTA", "PARAM_CAMBIO"]


class Estado:
    """Acumula filas por tabla física (dict columna → valor), valida y guarda."""
    def __init__(self, emp):
        self.emp = emp; self.cols = columnas_dbd(); self.filas = OrderedDict(); self.rechazos = []; self.avisos = []
        self._eve = 0

    def fila(self, tabla, **v):
        if tabla not in self.cols: raise KeyError(f"tabla {tabla} no existe en DBD_4")
        malas = [k for k in v if k not in self.cols[tabla]]
        if malas: raise KeyError(f"{tabla}: columnas inexistentes {malas}")
        self.filas.setdefault(tabla, []).append(v)

    def evento(self, trx, per, fec, obj=None, cen=None):
        self._eve += 1
        self.fila("EVENTO", EVE_NUM=self._eve, EVE_TRX=trx, EVE_FEC=fec, EVE_EMP=self.emp, EVE_PER=per, EVE_OBJ=obj, EVE_CEN=cen, EVE_MON="PEN", EVE_TC=1)
        return self._eve

    def rechazo(self, origen, motivo):
        self.rechazos.append((origen, motivo))

    def aviso(self, origen, motivo):
        self.avisos.append((origen, motivo))

    def copiar_catalogo(self, tabla):
        """Copia las filas de Datos_Iniciales (D_<tabla>): parámetros, métodos, tipos de recurso…"""
        wd = load_workbook(DATOS, read_only=True); h = ("D_" + tabla)[:31]
        if h not in wd.sheetnames: return
        rows = list(wd[h].iter_rows(values_only=True))
        cab = list(rows[0])
        for r in rows[1:]:
            if r and r[0] not in (None, ""): self.fila(tabla, **{c: x for c, x in zip(cab, r) if c in self.cols[tabla]})

    def guardar(self, ruta):
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        wb = Workbook(); wb.remove(wb.active)
        for t in TABLAS_CASO: self.filas.setdefault(t, [])
        for t, fs in self.filas.items():
            ws = wb.create_sheet(t[:31]); ws.append(self.cols[t])
            for f in fs: ws.append([f.get(c) for c in self.cols[t]])
        wb.save(ruta)
        with open(ruta.replace(".xlsx", "_rechazos.csv"), "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh); w.writerow(["tipo", "origen", "motivo"])
            for o, m in self.rechazos: w.writerow(["RECHAZO", o, m])
            for o, m in self.avisos: w.writerow(["AVISO", o, m])
        return ruta


def matriz(ws, prefijo_destino, col_clave=2):
    """Matriz de Oria: fila de cabecera con los códigos destino (≥ 3 que empiezan con el prefijo); filas origen con su código
    en col_clave. Devuelve (destinos en orden, {origen: {'criterio': str|None, 'costo': float|None, 'vals': {dest: v}}})."""
    for r in range(1, 12):
        dest = OrderedDict((c, norm(ws.cell(r, c).value)) for c in range(1, ws.max_column + 1)
                           if norm(ws.cell(r, c).value) and norm(ws.cell(r, c).value).startswith(prefijo_destino) and norm(ws.cell(r, c).value) != "Codigo")
        if len(dest) >= 3: hr = r; break
    else:
        raise ValueError(f"{ws.title}: sin fila de destinos {prefijo_destino}")
    col_crit = next((c for r in range(1, min(ws.max_row, 14) + 1) for c in range(1, ws.max_column + 1)
                     if str(ws.cell(r, c).value or "").strip() == "Criterio"), None)
    out = OrderedDict()
    for r in range(hr + 1, ws.max_row + 1):
        k = norm(ws.cell(r, col_clave).value)
        if not k or not re.match(r"^(EC|MD|SD|P0|CC)\d+", k): continue
        crit = ws.cell(r, col_crit).value if col_crit else None
        out[k] = {"criterio": str(crit).strip() if crit else None, "vals": OrderedDict((d, num(ws.cell(r, c).value)) for c, d in dest.items())}
    return list(dest.values()), out
