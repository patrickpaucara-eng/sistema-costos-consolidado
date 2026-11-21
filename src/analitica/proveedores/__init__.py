# -*- coding: utf-8 -*-
"""Contrato común de proveedor analítico (OT-017, vale para OT-017…020).

Un proveedor es un módulo `kit/analitica/proveedores/<nombre>.py` con `FICHA` y `ejecutar(extracto, parametros)`.
Este paquete solo VALIDA la forma: no tiene lógica de negocio. Puro: sin archivos, sin red, sin hora."""
import importlib

FAMILIAS = ("ESTIMACION", "PRONOSTICO", "VARIACION", "SIMULACION", "OPTIMIZACION")
CLAVES_FICHA = ("nombre", "version", "familia", "pregunta", "consume", "produce", "semilla")
CLAVES_ENTRADA = ("fecha", "entidad", "clave", "concepto", "valor", "unidad")
CLAVES_SALIDA = ("clave", "concepto", "valor", "p05", "p95", "conf", "unidad")


def validar_ficha(ficha):
    """Lanza ValueError si la FICHA no cumple el contrato. Devuelve la ficha."""
    faltan = [k for k in CLAVES_FICHA if not isinstance(ficha, dict) or k not in ficha]
    if faltan:
        raise ValueError("FICHA sin: " + ", ".join(faltan))
    if ficha["familia"] not in FAMILIAS:
        raise ValueError("familia invalida: %r (validas: %s)" % (ficha["familia"], ", ".join(FAMILIAS)))
    if not all(isinstance(ficha[k], str) and ficha[k].strip() for k in ("nombre", "version", "pregunta")):
        raise ValueError("FICHA: nombre, version y pregunta deben ser texto no vacio")
    for k in ("consume", "produce"):
        if not isinstance(ficha[k], (list, tuple)) or not ficha[k] or not all(isinstance(c, str) for c in ficha[k]):
            raise ValueError("FICHA[%s] debe ser una lista no vacia de conceptos" % k)
    if not isinstance(ficha["semilla"], bool):
        raise ValueError("FICHA[semilla] debe ser bool")
    return ficha


def validar_entrada(extracto):
    """Cada fila del extracto trae fecha, entidad, clave, concepto, valor, unidad (E-156). Devuelve el extracto."""
    if not isinstance(extracto, (list, tuple)):
        raise ValueError("el extracto debe ser una lista de filas")
    for i, f in enumerate(extracto):
        if not isinstance(f, dict):
            raise ValueError("fila %d del extracto no es un diccionario" % i)
        faltan = [k for k in CLAVES_ENTRADA if k not in f]
        if faltan:
            raise ValueError("fila %d del extracto sin: %s" % (i, ", ".join(faltan)))
        v = f["valor"]
        if isinstance(v, bool) or not isinstance(v, (int, float)) or v != v:
            raise ValueError("fila %d del extracto: valor no numerico" % i)
    return extracto


def validar_salida(filas):
    """Cada fila de salida trae clave, concepto, valor, p05, p95, conf, unidad; p05 <= valor <= p95."""
    if not isinstance(filas, (list, tuple)):
        raise ValueError("la salida debe ser una lista de filas")
    for i, f in enumerate(filas):
        faltan = [k for k in CLAVES_SALIDA if k not in f]
        if faltan:
            raise ValueError("fila %d de salida sin: %s" % (i, ", ".join(faltan)))
        for k in ("valor", "p05", "p95"):
            if isinstance(f[k], bool) or not isinstance(f[k], (int, float)) or f[k] != f[k]:
                raise ValueError("fila %d de salida: %s no numerico" % (i, k))
        if not (f["p05"] - 1e-9 <= f["valor"] <= f["p95"] + 1e-9):
            raise ValueError("fila %d de salida: valor fuera de [p05, p95]" % i)
        if f["conf"] is not None and not (0 <= f["conf"] <= 1):
            raise ValueError("fila %d de salida: conf fuera de [0, 1]" % i)
    return filas


def cargar(nombre):
    """Importa el proveedor `nombre` y valida su FICHA y que traiga `ejecutar`."""
    m = importlib.import_module("%s.%s" % (__name__, nombre))
    validar_ficha(getattr(m, "FICHA", None))
    if not callable(getattr(m, "ejecutar", None)):
        raise ValueError("el proveedor %s no define ejecutar()" % nombre)
    return m


def ejecutar_validado(modulo, extracto, parametros=None):
    """Corre un proveedor validando ficha, entrada y salida contra el contrato."""
    validar_ficha(modulo.FICHA)
    return validar_salida(modulo.ejecutar(validar_entrada(extracto), dict(parametros or {})))
