"""Operaciones preliminares de OT-C27 B; no conectadas a registro ni cotización."""
from decimal import Decimal, ROUND_HALF_UP
from statistics import median


def _positivo(valor):
    try:
        d = Decimal(str(valor))
    except Exception:
        raise ValueError('Se requiere un número válido.') from None
    if not d.is_finite() or d < 0:
        raise ValueError('Se requiere un número finito no negativo.')
    return d


def sugerir_intervalo(precios, tolerancia):
    """Mayor intervalo con historia suficiente cuya mediana de rangos no excede tolerancia."""
    valores = [_positivo(x) for x in precios]
    limite = _positivo(tolerancia)
    if any(x == 0 for x in valores):
        raise ValueError('Los precios deben ser positivos para medir volatilidad.')
    if not valores:
        raise ValueError('No hay precios para sugerir un intervalo.')
    opciones = []
    for largo in (1, 2, 3, 6, 12):
        if largo > len(valores):
            continue
        rangos = [(max(valores[i:i+largo]) / min(valores[i:i+largo]) - 1)
                  for i in range(len(valores)-largo+1)]
        if median(rangos) <= limite:
            opciones.append(largo)
    if not opciones:
        raise ValueError('No hay intervalo que cumpla la tolerancia.')
    return max(opciones)


def importe_intervalos(filas):
    """Multiplica cantidades explícitas por tasas explícitas, sin pronosticar ni aprobar reglas."""
    total = Decimal(0)
    subtotales = []
    for fila in filas:
        subtotal = sum((_positivo(x['cantidad']) * _positivo(x['tasa']) for x in fila), Decimal(0))
        subtotal = subtotal.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
        subtotales.append(subtotal); total += subtotal
    return subtotales, total


def variaciones(cantidad_proyectada, tasa_proyectada, cantidad_real, tasa_real):
    qp, tp, qr, tr = map(_positivo, (cantidad_proyectada, tasa_proyectada, cantidad_real, tasa_real))
    return {'tasa': (tr-tp)*qr, 'cantidad': (qr-qp)*tp, 'total': qr*tr-qp*tp}
