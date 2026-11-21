# -*- coding: utf-8 -*-
"""TRADUCTOR SEMÁNTICO ÚNICO (OT-022). Lee la capa semántica de DBD_4 y traduce en las dos direcciones:
    resolver(entidad, concepto) -> (tabla, columna)      concepto MCD -> columna física
    concepto_de(tabla, columna) -> (entidad, concepto)   columna física -> concepto MCD
Ningún otro módulo resuelve por su cuenta: los métodos declaran CONSUME por entidad/concepto y este módulo
hace la traducción. La ruta del DBD sale de rutas.FUENTE (nunca una ruta literal).

Columnas de DBD_4 que OT-021 dejó en dudas (sin Concepto) se pueden usar por su nombre físico como RESPALDO,
pero se marcan como OBSOLETAS: un método que las usa sigue atado al nombre de la columna. Igual pasa con una
columna cuya Naturaleza es RESULTADO: consumirla como hecho es una deuda (V6), no un concepto de entrada.
"""
import os

from openpyxl import load_workbook

import rutas

HOJA = "DBD_4_Modelo_Interno"
COL_TABLA = "Tabla"
COL_COLUMNA = "Columna"
COL_ENTIDAD = "Entidad MCD"
COL_CONCEPTO = "Concepto"
COL_NATURALEZA = "Naturaleza"
NAT_RESULTADO = "RESULTADO"

_CACHE = {}


class ErrorSemantico(ValueError):
    """La entidad, el concepto o la columna no existen en la capa semántica del DBD."""


def ruta_dbd(dbd=None):
    """Ruta del DBD_Fuente: la del argumento o la de rutas.FUENTE. Sin rutas literales."""
    return os.path.abspath(dbd or os.path.join(rutas.FUENTE, "DBD_Fuente.xlsx"))


def _texto(v):
    return "" if v is None else str(v).strip()


def _leer(dbd=None):
    """Carga (y cachea por ruta) el mapa semántico de DBD_4."""
    ruta = ruta_dbd(dbd)
    if ruta in _CACHE:
        return _CACHE[ruta]
    if not os.path.exists(ruta):
        raise ErrorSemantico(f"No existe el DBD en {ruta} (defina REYNA_FUENTE o revise rutas.FUENTE)")
    wb = load_workbook(ruta, read_only=True, data_only=True)
    try:
        if HOJA not in wb.sheetnames:
            raise ErrorSemantico(f"{ruta}: falta la hoja {HOJA}")
        ws = wb[HOJA]
        filas = list(ws.iter_rows(min_row=1, max_row=ws.max_row, values_only=True))
    finally:
        wb.close()

    # Encabezado en la primera fila que traiga Tabla y Columna (hoy es la fila 4).
    i_hdr = None
    for i, fila in enumerate(filas):
        textos = {_texto(x).upper() for x in (fila or ())}
        if COL_TABLA.upper() in textos and COL_COLUMNA.upper() in textos:
            i_hdr = i
            break
    if i_hdr is None:
        raise ErrorSemantico(f"{ruta}: no encuentro el encabezado {COL_TABLA}/{COL_COLUMNA} en {HOJA}")
    hdr = {_texto(x).upper(): j for j, x in enumerate(filas[i_hdr] or ()) if _texto(x)}
    for nombre in (COL_TABLA, COL_COLUMNA, COL_ENTIDAD, COL_CONCEPTO, COL_NATURALEZA):
        if nombre.upper() not in hdr:
            raise ErrorSemantico(f"{ruta}: falta la columna «{nombre}» en {HOJA}")

    entidades = {}   # entidad -> {tabla, conceptos: {concepto: {columna, naturaleza}}, columnas: {...}}
    por_tabla = {}   # tabla -> {entidad, conceptos, columnas}
    columnas = 0
    for fila in filas[i_hdr + 1:]:
        if not fila:
            continue
        tabla = _texto(fila[hdr[COL_TABLA.upper()]]) if hdr[COL_TABLA.upper()] < len(fila) else ""
        columna = _texto(fila[hdr[COL_COLUMNA.upper()]]) if hdr[COL_COLUMNA.upper()] < len(fila) else ""
        if not tabla or not columna:
            continue
        entidad = _texto(fila[hdr[COL_ENTIDAD.upper()]]) if hdr[COL_ENTIDAD.upper()] < len(fila) else ""
        concepto = _texto(fila[hdr[COL_CONCEPTO.upper()]]) if hdr[COL_CONCEPTO.upper()] < len(fila) else ""
        naturaleza = _texto(fila[hdr[COL_NATURALEZA.upper()]]) if hdr[COL_NATURALEZA.upper()] < len(fila) else ""
        naturaleza = naturaleza.upper() or None
        if not entidad:                       # la capa de OT-021 la exige en todas las filas; no la inventamos
            raise ErrorSemantico(f"{tabla}.{columna}: falta Entidad MCD en {HOJA}")
        columnas += 1
        e = entidades.setdefault(entidad, {"tabla": tabla, "conceptos": {}, "columnas": {}})
        if e["tabla"] != tabla:
            raise ErrorSemantico(f"La entidad {entidad} aparece en dos tablas: {e['tabla']} y {tabla}")
        col = {"columna": columna, "concepto": concepto or None, "naturaleza": naturaleza}
        e["columnas"][columna] = col
        t = por_tabla.setdefault(tabla, {"entidad": entidad, "conceptos": {}, "columnas": {}})
        if t["entidad"] != entidad:
            raise ErrorSemantico(f"La tabla {tabla} aparece con dos entidades: {t['entidad']} y {entidad}")
        t["columnas"][columna] = col
        if concepto:
            if concepto in e["conceptos"]:
                raise ErrorSemantico(f"Concepto repetido en {entidad}: {concepto}")
            e["conceptos"][concepto] = {"columna": columna, "naturaleza": naturaleza}

    mapa = {
        "ruta": ruta,
        "entidades": entidades,
        "por_tabla": por_tabla,
        # alias: el nombre de la tabla siempre lleva a la entidad VIGENTE (hoy «(sin MCD) X»; OT-030 puede cambiarla)
        "alias": {t: v["entidad"] for t, v in por_tabla.items()},
        "columnas": columnas,
        "declaradas": sum(len(e["conceptos"]) for e in entidades.values()),
        "sin_concepto": sum(1 for e in entidades.values() for c in e["columnas"].values() if not c["concepto"]),
    }
    _CACHE[ruta] = mapa
    return mapa


def recargar():
    """Vacía la caché (pruebas de renombrado con una copia temporal del DBD)."""
    _CACHE.clear()


def _entidad(nombre, dbd=None):
    m = _leer(dbd)
    s = _texto(nombre)
    if s in m["entidades"]:
        return s
    # Clave estable del método: «(sin MCD) X» apunta a la TABLA X y a la entidad que el DBD tenga HOY para X.
    # Así OT-030 puede asignar la entidad MCD sin tocar el método (que sigue escribiendo «(sin MCD) X»).
    if s.startswith("(sin MCD) "):
        tabla = s[len("(sin MCD) "):].strip()
        if tabla in m["por_tabla"]:
            return m["por_tabla"][tabla]["entidad"]
    if s in m["alias"]:
        return m["alias"][s]
    raise ErrorSemantico(f"La entidad MCD «{s}» no existe en DBD_4")


def _tabla(nombre, dbd=None):
    m = _leer(dbd)
    s = _texto(nombre)
    if s in m["por_tabla"]:
        return s
    raise ErrorSemantico(f"La tabla «{s}» no existe en DBD_4")


def es_entidad(nombre, dbd=None):
    """True si es una Entidad MCD exacta o el alias de una entidad «(sin MCD) TABLA»."""
    try:
        _entidad(nombre, dbd)
        return True
    except ErrorSemantico:
        return False


def es_tabla(nombre, dbd=None):
    try:
        _tabla(nombre, dbd)
        return True
    except ErrorSemantico:
        return False


def entidad_de(tabla, dbd=None):
    return _leer(dbd)["por_tabla"][_tabla(tabla, dbd)]["entidad"]


def tabla_de(entidad, dbd=None):
    return _leer(dbd)["entidades"][_entidad(entidad, dbd)]["tabla"]


def columnas_de(entidad, dbd=None):
    """Columnas físicas de la entidad, en el orden del DBD."""
    return list(_leer(dbd)["entidades"][_entidad(entidad, dbd)]["columnas"])


def conceptos_de(entidad, dbd=None):
    """Conceptos declarados de la entidad, en el orden del DBD."""
    return list(_leer(dbd)["entidades"][_entidad(entidad, dbd)]["conceptos"])


def es_concepto(entidad, concepto, dbd=None):
    """True solo si el concepto está declarado en DBD_4 para esa entidad."""
    e = _leer(dbd)["entidades"][_entidad(entidad, dbd)]
    return _texto(concepto) in e["conceptos"]


def es_columna(entidad, columna, dbd=None):
    """True si la columna física existe en la tabla de esa entidad."""
    e = _leer(dbd)["entidades"][_entidad(entidad, dbd)]
    return _texto(columna) in e["columnas"]


def resolver(entidad, concepto, dbd=None):
    """Concepto MCD -> (tabla, columna). Si el nombre no es un concepto declarado, acepta la columna física
    como respaldo (deuda de OT-021) para que la migración no invente semántica."""
    m = _leer(dbd)
    e = m["entidades"][_entidad(entidad, dbd)]
    c = _texto(concepto)
    if c in e["conceptos"]:
        return e["tabla"], e["conceptos"][c]["columna"]
    if c in e["columnas"]:
        return e["tabla"], c
    raise ErrorSemantico(f"El concepto «{c}» no existe en la entidad «{_entidad(entidad, dbd)}» de DBD_4")


def concepto_de(tabla, columna, dbd=None):
    """Columna física -> (entidad, concepto). Si la columna no tiene Concepto en DBD_4, devuelve la columna
    como concepto de respaldo (se detecta con es_concepto(entidad, concepto))."""
    m = _leer(dbd)
    t = m["por_tabla"][_tabla(tabla, dbd)]
    c = _texto(columna)
    if c not in t["columnas"]:
        raise ErrorSemantico(f"La columna «{c}» no existe en la tabla «{_tabla(tabla, dbd)}» de DBD_4")
    return t["entidad"], (t["columnas"][c]["concepto"] or c)


def naturaleza(entidad, concepto, dbd=None):
    """Naturaleza del concepto (HECHO, RESULTADO, CLAVE, CATALOGO, CONTROL). None si es un respaldo físico."""
    e = _leer(dbd)["entidades"][_entidad(entidad, dbd)]
    c = _texto(concepto)
    if c in e["conceptos"]:
        return e["conceptos"][c]["naturaleza"]
    if c in e["columnas"]:
        return None
    raise ErrorSemantico(f"El concepto «{c}» no existe en la entidad «{_entidad(entidad, dbd)}» de DBD_4")


def naturaleza_de(tabla, columna, dbd=None):
    """Naturaleza declarada de la columna, aunque el Concepto esté vacío. None si no hay."""
    t = _leer(dbd)["por_tabla"][_tabla(tabla, dbd)]
    c = _texto(columna)
    if c not in t["columnas"]:
        raise ErrorSemantico(f"La columna «{c}» no existe en la tabla «{_tabla(tabla, dbd)}» de DBD_4")
    return t["columnas"][c]["naturaleza"]


def tablas_de(consume, dbd=None):
    """{entidad: [conceptos]} o {tabla: [columnas]} -> {tabla: [columnas físicas]}, sin repetir."""
    out = {}
    for clave, valores in (consume or {}).items():
        if not isinstance(valores, (list, tuple)):
            raise ErrorSemantico(f"CONSUME: los valores de «{clave}» deben ser una lista")
        if es_entidad(clave, dbd):
            tabla = tabla_de(clave, dbd)
            out.setdefault(tabla, [])
            for c in valores:
                _, col = resolver(clave, c, dbd)
                if col not in out[tabla]:
                    out[tabla].append(col)
        elif es_tabla(clave, dbd):
            out.setdefault(clave, [])
            for c in valores:
                if not es_columna(clave, c, dbd):
                    raise ErrorSemantico(f"CONSUME: {clave}.{c} no existe en DBD_4")
                if c not in out[clave]:
                    out[clave].append(c)
        else:
            raise ErrorSemantico(f"CONSUME: la entidad o tabla «{clave}» no existe en DBD_4")
    return out


def traducir_hechos(filas_por_tabla, consume, dbd=None):
    """{tabla: [{columna: valor}]} -> {clave_de_CONSUME: [{concepto: valor}]}.
    La clave de salida es la que declaró el método («(sin MCD) X», «X» o la entidad actual), para que el método
    no cambie cuando OT-030 asigne la Entidad MCD. Convive con el formato viejo: una clave que es tabla se copia."""
    out = {}
    for clave, valores in (consume or {}).items():
        if not isinstance(valores, (list, tuple)):
            raise ErrorSemantico(f"CONSUME: los valores de «{clave}» deben ser una lista")
        if es_entidad(clave, dbd):
            e = _entidad(clave, dbd)                     # entidad VIGENTE en DBD_4
            tabla = tabla_de(e, dbd)
            out[clave] = []
            for fila in filas_por_tabla.get(tabla, []):
                d = {}
                for c in valores:
                    if es_concepto(e, c, dbd):
                        _, col = resolver(e, c, dbd)
                        d[c] = fila.get(col)
                    elif es_columna(e, c, dbd):
                        d[c] = fila.get(c)
                    else:
                        raise ErrorSemantico(f"CONSUME: el concepto «{c}» no existe en «{e}»")
                out[clave].append(d)
        elif es_tabla(clave, dbd):
            out[clave] = [dict(f) for f in filas_por_tabla.get(clave, [])]
        else:
            raise ErrorSemantico(f"CONSUME: la entidad o tabla «{clave}» no existe en DBD_4")
    return out


def diagnostico(dbd=None):
    """Cifras de la capa semántica, para el informe (no decide nada)."""
    m = _leer(dbd)
    return {
        "ruta": m["ruta"],
        "entidades": len(m["entidades"]),
        "columnas": m["columnas"],
        "conceptos_declarados": m["declaradas"],
        "columnas_sin_concepto": m["sin_concepto"],
        "resultados": sum(1 for e in m["entidades"].values() for c in e["conceptos"].values()
                          if c["naturaleza"] == NAT_RESULTADO),
    }
