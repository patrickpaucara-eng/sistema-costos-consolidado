# -*- coding: utf-8 -*-
"""CASO DE VALIDACIÓN EN EXCEL → CASOS del método (estándar v3, E-109 + OT-022). SIN hojas duplicadas.
El libro solo tiene datos elementales y el cálculo; la máquina los lee con dos marcas en las MISMAS hojas humanas:
  01_Datos   bloques  «#TABLA <ENTIDAD_MCD>>» / columnas por CONCEPTO / filas (celdas amarillas) / fila vacía
             y un bloque «#PARAMETROS» / PARAMETRO | VALOR
  R##_*      el resultado del paso en un bloque «#RESULTADO» / TIPO | CLAVE | CONCEPTO | VALOR  (VALOR = FÓRMULA de Excel)
OT-022: #TABLA acepta la Entidad MCD y las columnas por concepto; semantica traduce a la columna física. Los hechos
que entrega quedan por entidad/concepto y, para convivir con los métodos aún no migrados, conservan también la forma
física {tabla: [{columna: valor}]}. El esperado es el VALOR que calcula Excel (no el código Python): si el libro no
trae valores calculados en caché, se recalcula una vez con LibreOffice.
Uso: python -m metodos.caso_excel casos/Caso_X_7.xlsx metodos/x.py"""
import os
import subprocess
import sys
import tempfile

from openpyxl import load_workbook

AQUI = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(AQUI)
if KIT not in sys.path:
    sys.path.insert(0, KIT)

try:
    from . import semantica
except ImportError:
    import semantica


def _ruta(libro):
    return libro if os.path.isabs(libro) or os.path.exists(libro) else os.path.join(AQUI, "casos", libro)


def _bloques(ws):
    """Devuelve [(marca, nombre, columnas, filas)] de una hoja con bloques «#...»."""
    out, cur = [], None
    for r in ws.iter_rows(values_only=True):
        v = list(r)
        if not any(x not in (None, "") for x in v):
            cur = None
            continue
        txt = next((x for x in v if x not in (None, "")), None)
        if isinstance(txt, str) and txt.startswith("#"):
            p = txt[1:].split(None, 1)
            cur = [p[0].upper(), p[1].strip() if len(p) > 1 else "", None, []]
            out.append(cur)
            continue
        if cur is None:
            continue
        i0 = next(i for i, x in enumerate(v) if x not in (None, ""))
        if cur[2] is None:
            cur[2] = [(i, c) for i, c in enumerate(v) if c not in (None, "")]
            continue
        cur[3].append({c: v[i] if i < len(v) else None for i, c in cur[2]})
    return out


def _recalcular(ruta):
    tmp = tempfile.mkdtemp()
    subprocess.run(["soffice", "--headless", "--convert-to", "xlsx", "--outdir", tmp, ruta],
                   capture_output=True, timeout=180)
    return os.path.join(tmp, os.path.basename(ruta))


def _fila_conceptos(entidad, fila, dbd=None):
    """Una fila del #TABLA -> {concepto: valor, columna_física: valor}. Acepta encabezados por concepto o por columna."""
    tabla = semantica.tabla_de(entidad, dbd=dbd)
    out = {}
    for clave, valor in fila.items():
        k = str(clave).strip()
        if semantica.es_concepto(entidad, k, dbd=dbd):
            _, col = semantica.resolver(entidad, k, dbd=dbd)
            out[k] = valor
            out[col] = valor
        elif semantica.es_columna(entidad, k, dbd=dbd):
            _, con = semantica.concepto_de(tabla, k, dbd=dbd)
            out[k] = valor
            out[con] = valor
        else:
            raise ValueError(f"#TABLA {entidad}: la columna «{k}» no es un concepto ni una columna de DBD_4")
    return out


def _agregar_tabla(hechos, nombre, filas, dbd=None):
    """Agrega un bloque #TABLA por entidad/concepto y, por compatibilidad, por tabla/columna."""
    if not filas:
        return
    if semantica.es_entidad(nombre, dbd=dbd):
        entidad = semantica.entidad_de(semantica.tabla_de(nombre, dbd=dbd), dbd=dbd)
        tabla = semantica.tabla_de(entidad, dbd=dbd)
        nuevas = [_fila_conceptos(entidad, f, dbd=dbd) for f in filas]
        # El método lee la clave que declaró en CONSUME: «(sin MCD) X», «X» o la entidad actual. Se entregan las tres
        # (sin duplicar) para que OT-030 pueda cambiar la Entidad MCD sin tocar el método.
        claves = [nombre]
        for k in (entidad, tabla):
            if k not in claves:
                claves.append(k)
        for k in claves:
            hechos.setdefault(k, []).extend(nuevas)
        return
    if semantica.es_tabla(nombre, dbd=dbd):
        entidad = semantica.entidad_de(nombre, dbd=dbd)
        nuevas = [_fila_conceptos(entidad, f, dbd=dbd) for f in filas]
        claves = [nombre]
        for k in (entidad, nombre):
            if k not in claves:
                claves.append(k)
        for k in claves:
            hechos.setdefault(k, []).extend(nuevas)
        return
    hechos.setdefault(nombre, []).extend(filas)         # bloque legacy sin capa semántica


def cargar(libro, metodo=None, dbd=None):
    ruta = _ruta(libro)
    wb = load_workbook(ruta, data_only=True, read_only=True)
    if "01_Datos" not in wb.sheetnames:
        raise ValueError(f"{libro}: falta 01_Datos (CONTEXTO_CONSTRUCTOR.md §6)")
    hechos, parametros, espera = {}, {}, []
    for marca, nom, _, filas in _bloques(wb["01_Datos"]):
        if marca == "TABLA":
            _agregar_tabla(hechos, nom, filas, dbd=dbd)
        elif marca == "PARAMETROS":
            parametros = {f["PARAMETRO"]: f["VALOR"] for f in filas if f.get("PARAMETRO")}

    def leer_res(w):
        return [(f["TIPO"], f["CLAVE"], f["CONCEPTO"], f["VALOR"]) for n in w.sheetnames if n[:1] == "R"
                for marca, _, _, fs in _bloques(w[n]) if marca == "RESULTADO" for f in fs if f.get("TIPO")]

    espera = leer_res(wb)
    if any(v is None for *_, v in espera):                      # sin caché de fórmulas: Excel/LibreOffice calcula
        wb = load_workbook(_recalcular(ruta), data_only=True, read_only=True)
        espera = leer_res(wb)
    if not hechos:
        raise ValueError(f"{libro}: 01_Datos no tiene bloques #TABLA")
    if not espera:
        raise ValueError(f"{libro}: ninguna hoja R## tiene bloque #RESULTADO")
    if any(v is None for *_, v in espera):
        raise ValueError(f"{libro}: hay VALOR sin calcular en #RESULTADO")
    return [dict(nombre=os.path.basename(libro), hechos=hechos, parametros=parametros, previos={},
                 espera=[(t, k, c, float(v)) for t, k, c, v in espera])]


if __name__ == "__main__":
    from metodos import validar_metodo as VM
    m = VM.cargar(sys.argv[2])
    m.CASOS = cargar(sys.argv[1], m.FICHA["nombre"])
    f = VM.validar(m, None)
    print("CASO OK: el método reproduce lo que calcula Excel" if not f else "FALLA:\n  " + "\n  ".join(f))
    sys.exit(1 if f else 0)
