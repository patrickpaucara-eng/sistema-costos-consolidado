"""Tramos marginales opcionales para costos variables por cantidad."""
from __future__ import annotations

import math


HOJA_COSTO_TRAMO = "COSTO_TRAMO"
COLUMNAS_COSTO_TRAMO = ("COD_RECURSO", "DESDE", "HASTA", "TASA")


def _numero(valor, etiqueta):
    if isinstance(valor, bool):
        raise ValueError(f"{etiqueta} debe ser numérico")
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        raise ValueError(f"{etiqueta} debe ser numérico") from None
    if not math.isfinite(numero) or numero < 0:
        raise ValueError(f"{etiqueta} debe ser finito y no negativo")
    return numero


def validar_tramos(tramos):
    """Comprueba límites marginales contiguos que comienzan en cero."""
    if not isinstance(tramos, (list, tuple)) or not tramos:
        raise ValueError("La tabla de tramos no puede estar vacía")
    salida = []
    previo = 0.0
    for indice, fila in enumerate(tramos, 1):
        if not isinstance(fila, dict):
            raise ValueError(f"Tramo {indice} inválido")
        desde = _numero(fila.get("desde", 0 if indice == 1 else None), f"Desde del tramo {indice}")
        hasta_v = fila.get("hasta")
        hasta = None if hasta_v in (None, "") else _numero(hasta_v, f"Hasta del tramo {indice}")
        tasa = _numero(fila.get("tasa"), f"Tasa del tramo {indice}")
        if not math.isclose(desde, previo, rel_tol=0, abs_tol=1e-9):
            raise ValueError(f"Tramos discontinuos o desordenados en el tramo {indice}")
        if hasta is not None and hasta <= desde:
            raise ValueError(f"El límite superior del tramo {indice} debe ser mayor que el inferior")
        if salida and salida[-1]["hasta"] is None:
            raise ValueError("No puede haber tramos después de uno sin límite superior")
        salida.append({"desde": desde, "hasta": hasta, "tasa": tasa})
        previo = hasta if hasta is not None else math.inf
    return salida


def calcular_costo_recurso(cantidad, tasa_base, tramos=None):
    """Calcula cantidad×tasa o costo marginal progresivo según la tabla opcional.

    Si no hay tabla, la multiplicación conserva exactamente la ruta lineal previa.
    """
    q = _numero(cantidad, "Cantidad")
    tasa = _numero(tasa_base, "Tasa base")
    if tramos is None or tramos == [] or tramos == ():
        return q * tasa
    tabla = validar_tramos(tramos)
    if tabla[-1]["hasta"] is not None and q > tabla[-1]["hasta"]:
        raise ValueError("La tabla de tramos no cubre toda la cantidad")
    costo = 0.0
    for fila in tabla:
        if q <= fila["desde"]:
            break
        extremo = q if fila["hasta"] is None else min(q, fila["hasta"])
        costo += max(0.0, extremo - fila["desde"]) * fila["tasa"]
        if q <= extremo:
            break
    return costo


def calcular_costos_recursos(cantidades, tasas_base, tramos_por_recurso=None):
    """Aplica tramos solo a los recursos declarados; los demás mantienen la tasa base."""
    if not isinstance(cantidades, dict) or not isinstance(tasas_base, dict):
        raise ValueError("Cantidades y tasas deben ser mapas")
    tramos_por_recurso = tramos_por_recurso or {}
    desconocidos = set(tramos_por_recurso) - set(cantidades)
    if desconocidos:
        raise ValueError("Hay tramos para recursos no incluidos: " + ", ".join(sorted(desconocidos)))
    detalle = {}
    for recurso, cantidad in cantidades.items():
        if recurso not in tasas_base:
            raise ValueError(f"Falta la tasa base del recurso {recurso}")
        detalle[recurso] = calcular_costo_recurso(cantidad, tasas_base[recurso], tramos_por_recurso.get(recurso))
    return {"detalle": detalle, "total": sum(detalle.values())}


def crear_hoja_costo_tramo(libro):
    """Crea la hoja de tramos opcional y valida su cabecera."""
    hoja = libro[HOJA_COSTO_TRAMO] if HOJA_COSTO_TRAMO in libro.sheetnames else libro.create_sheet(HOJA_COSTO_TRAMO)
    actual = tuple(hoja.cell(1, i + 1).value for i in range(len(COLUMNAS_COSTO_TRAMO)))
    if all(valor is None for valor in actual):
        for i, encabezado in enumerate(COLUMNAS_COSTO_TRAMO, 1):
            hoja.cell(1, i, encabezado)
    elif actual != COLUMNAS_COSTO_TRAMO:
        raise ValueError(f"La hoja {HOJA_COSTO_TRAMO} tiene una cabecera incompatible")
    return hoja


def guardar_tramos_en_libro(libro, tramos_por_recurso):
    """Guarda la tabla opcional en la hoja propia, sin afectar otras hojas."""
    hoja = crear_hoja_costo_tramo(libro)
    if hoja.max_row > 1:
        hoja.delete_rows(2, hoja.max_row - 1)
    for recurso, tramos in sorted(tramos_por_recurso.items()):
        codigo = str(recurso).strip()
        if not codigo:
            raise ValueError("El código de recurso es obligatorio")
        for fila in validar_tramos(tramos):
            hoja.append((codigo, fila["desde"], fila["hasta"], fila["tasa"]))
    return hoja


def leer_tramos_de_libro(libro):
    """Los libros previos sin la hoja opcional no activan tramos."""
    if HOJA_COSTO_TRAMO not in libro.sheetnames:
        return {}
    hoja = libro[HOJA_COSTO_TRAMO]
    actual = tuple(hoja.cell(1, i + 1).value for i in range(len(COLUMNAS_COSTO_TRAMO)))
    if actual != COLUMNAS_COSTO_TRAMO:
        raise ValueError(f"La hoja {HOJA_COSTO_TRAMO} tiene una cabecera incompatible")
    agrupados = {}
    for numero_fila, fila in enumerate(hoja.iter_rows(min_row=2, values_only=True), 2):
        if not any(valor is not None for valor in fila[:len(COLUMNAS_COSTO_TRAMO)]):
            continue
        recurso, desde, hasta, tasa = fila[:len(COLUMNAS_COSTO_TRAMO)]
        recurso = str(recurso or "").strip()
        if not recurso:
            raise ValueError(f"Fila {numero_fila}: falta el recurso")
        agrupados.setdefault(recurso, []).append({"desde": desde, "hasta": hasta, "tasa": tasa})
    return {recurso: validar_tramos(filas) for recurso, filas in agrupados.items()}
