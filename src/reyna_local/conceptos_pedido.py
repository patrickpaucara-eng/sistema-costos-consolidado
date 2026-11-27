"""Costo de lotes y conceptos de pedido que no pertenecen al ABC."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import math


CONCEPTOS_FIJOS = {"SUBCONTRATO", "TRANSPORTE", "GASTOS_GENERALES"}
CONCEPTO_PORCENTAJE = "CONTINGENCIA"


def _decimal(valor, etiqueta, minimo=Decimal("0")):
    if isinstance(valor, bool):
        raise ValueError(f"{etiqueta} debe ser numérico")
    try:
        numero = Decimal(str(valor))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"{etiqueta} debe ser numérico") from None
    if not numero.is_finite() or numero < minimo:
        raise ValueError(f"{etiqueta} debe ser finito y no negativo")
    return numero


def _moneda(valor):
    return float(valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _unitario(valor):
    return float(valor.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP))


def calcular_preparacion_lotes(cantidad, unidades_por_lote, preparacion_por_lote,
                               costo_variable_por_unidad):
    """Calcula fijo por lote + variable por unidad; lotes incompletos cuentan como lote."""
    q = _decimal(cantidad, "Cantidad", Decimal("0.000000001"))
    tamano = _decimal(unidades_por_lote, "Unidades por lote", Decimal("0.000000001"))
    fijo = _decimal(preparacion_por_lote, "Preparación por lote")
    variable = _decimal(costo_variable_por_unidad, "Costo variable por unidad")
    n_lotes = int(math.ceil(q / tamano))
    unidades = q * variable
    preparacion = Decimal(n_lotes) * fijo
    return {
        "cantidad": float(q),
        "unidades_por_lote": float(tamano),
        "numero_lotes": n_lotes,
        "costo_preparacion": _moneda(preparacion),
        "costo_variable": _moneda(unidades),
        "costo_total": _moneda(preparacion + unidades),
        "costo_unitario": _moneda((preparacion + unidades) / q),
    }


def calcular_conceptos_adicionales(costo_base, conceptos=()):
    """Añade importes fijos y contingencia sobre el costo previo a porcentajes.

    `SUBCONTRATO`, `TRANSPORTE` y `GASTOS_GENERALES` reciben un `importe`.
    `CONTINGENCIA` recibe un `porcentaje` entre 0 y 100. Si hay varios conceptos
    porcentuales, todos usan la misma base: costo ABC/lote más importes fijos;
    así no se componen ni dependen del orden de las líneas.
    """
    base = _decimal(costo_base, "Costo base")
    if conceptos is None:
        conceptos = ()
    if not isinstance(conceptos, (list, tuple)):
        raise ValueError("Los conceptos adicionales deben ser una lista")
    lineas_fijas = []
    lineas_porcentaje = []
    for indice, linea in enumerate(conceptos, 1):
        if not isinstance(linea, dict):
            raise ValueError(f"Concepto adicional {indice} inválido")
        codigo = str(linea.get("concepto", "")).strip().upper()
        nombre = str(linea.get("nombre") or codigo).strip()
        if codigo in CONCEPTOS_FIJOS:
            importe = _decimal(linea.get("importe"), f"Importe de {nombre}")
            lineas_fijas.append({"concepto": codigo, "nombre": nombre, "importe": importe})
        elif codigo == CONCEPTO_PORCENTAJE:
            porcentaje = _decimal(linea.get("porcentaje"), f"Porcentaje de {nombre}")
            if porcentaje > 100:
                raise ValueError(f"Porcentaje de {nombre} no puede superar 100")
            lineas_porcentaje.append({"concepto": codigo, "nombre": nombre, "porcentaje": porcentaje})
        else:
            raise ValueError(f"Concepto adicional no reconocido: {codigo or '(vacío)'}")
    base_porcentual = base + sum((linea["importe"] for linea in lineas_fijas), Decimal("0"))
    salida = [{"concepto": linea["concepto"], "nombre": linea["nombre"], "tipo": "importe",
               "importe": _moneda(linea["importe"])} for linea in lineas_fijas]
    for linea in lineas_porcentaje:
        importe = base_porcentual * linea["porcentaje"] / Decimal("100")
        salida.append({"concepto": linea["concepto"], "nombre": linea["nombre"], "tipo": "porcentaje",
                       "porcentaje": float(linea["porcentaje"]), "base_porcentual": _moneda(base_porcentual),
                       "importe": _moneda(importe)})
    fijo = sum((linea["importe"] for linea in lineas_fijas), Decimal("0"))
    porcentaje = base_porcentual * sum((linea["porcentaje"] for linea in lineas_porcentaje), Decimal("0")) / Decimal("100")
    return {"costo_base": _moneda(base), "base_porcentual": _moneda(base_porcentual),
            "lineas": salida, "costo_adicionales": _moneda(fijo + porcentaje),
            "costo_total": _moneda(base + fijo + porcentaje)}


def cotizar_lote(cantidad, unidades_por_lote, preparacion_por_lote,
                 costo_variable_por_unidad, conceptos=()):
    """Resultado unificado para que Pedido consuma costos ABC y no ABC."""
    lote = calcular_preparacion_lotes(cantidad, unidades_por_lote,
                                      preparacion_por_lote, costo_variable_por_unidad)
    adicionales = calcular_conceptos_adicionales(lote["costo_total"], conceptos)
    return {**lote, "conceptos_adicionales": adicionales["lineas"],
            "costo_adicionales": adicionales["costo_adicionales"],
            "costo_pedido": adicionales["costo_total"],
            "costo_unitario_final": _unitario(Decimal(str(adicionales["costo_total"])) /
                                               _decimal(cantidad, "Cantidad", Decimal("0.000000001")))}


def comparar_tamanos_lote(cantidad, tamanos_lote, preparacion_por_lote,
                          costo_variable_por_unidad, conceptos=()):
    """Compara alternativas de lote y deja visible el efecto monetario de preparación."""
    if not isinstance(tamanos_lote, (list, tuple)) or not tamanos_lote:
        raise ValueError("Indica al menos un tamaño de lote")
    alternativas = [cotizar_lote(cantidad, tamano, preparacion_por_lote,
                                 costo_variable_por_unidad, conceptos)
                    for tamano in tamanos_lote]
    referencia = alternativas[0]["costo_pedido"]
    for alternativa in alternativas:
        alternativa["diferencia_vs_primera"] = _moneda(
            Decimal(str(alternativa["costo_pedido"])) - Decimal(str(referencia)))
    return {"alternativas": alternativas,
            "diferencia_max_min": _moneda(Decimal(str(max(x["costo_pedido"] for x in alternativas))) -
                                          Decimal(str(min(x["costo_pedido"] for x in alternativas))))}
