# -*- coding: utf-8 -*-
"""PUERTO DE LECTURA de la base (E-098): única vía para que un sistema externo (almacén, data warehouse, presupuesto)
lea la base. Las tablas excluidas las define la propia base (parámetro PUERTO_LECTURA_EXCLUIR), no quien lee.
OT-022: leer_conceptos() traduce la base física a hechos por entidad/concepto con el traductor único metodos.semantica;
ningún módulo de métodos resuelve columnas por su cuenta."""
from openpyxl import load_workbook


def excluidas(wb):
    ws = wb["PARAMETRO"]
    for r in ws.iter_rows(min_row=2, values_only=True):
        if r and r[0] == "PUERTO_LECTURA_EXCLUIR":
            return {x for x in str(r[1]).split("|") if x}
    return {"USUARIO", "USUARIO_PERFIL", "PERFIL_TRX", "BITACORA", "PARAM_CAMBIO"}   # por omisión, lo más restrictivo


def leer(libro, tablas):
    """{tabla: [filas como dict]} solo de tablas permitidas; error si se pide una excluida o inexistente."""
    wb = load_workbook(libro, read_only=True, data_only=True)
    try:
        no = excluidas(wb)
        out = {}
        for t in [x.strip() for x in tablas]:
            if t in no:
                raise PermissionError(f"La base no entrega la tabla {t} por el puerto de lectura")
            if t not in wb.sheetnames:
                raise KeyError(f"No existe la tabla {t}")
            filas = list(wb[t].iter_rows(values_only=True))
            h = [c for c in filas[0] if c is not None] if filas else []
            out[t] = [dict(zip(h, f)) for f in filas[1:] if f and f[0] not in (None, "")]
        return out
    finally:
        wb.close()


def leer_conceptos(libro, consume, dbd=None):
    """{entidad MCD: [{concepto: valor}]} a partir de la base física. El único traductor es semantica."""
    from metodos import semantica
    tablas = semantica.tablas_de(consume, dbd=dbd)
    fisicos = leer(libro, list(tablas))
    return semantica.traducir_hechos(fisicos, consume, dbd=dbd)
