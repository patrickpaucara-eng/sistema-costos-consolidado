"""Plazo de pedido según carga nueva, capacidad práctica y OT ya comprometidas."""
import math


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


def calcular_plazo_actividades(cargas_nuevas, capacidad_practica_diaria,
                               ot_comprometidas_por_dia=None, plazo_solicitado_dias=None):
    """Calcula días de capacidad necesarios por actividad y el cuello de botella.

    `ot_comprometidas_por_dia` es `{actividad: [carga_día_1, ...]}` en las
    mismas unidades del inductor. Cada día, las OTs abiertas reservan capacidad
    primero y la orden nueva usa el saldo. No se asume que calendario y capacidad
    sean días corridos; la lista representa días hábiles/capacidad ya preparados
    por el llamador.
    """
    if not isinstance(cargas_nuevas, dict) or not cargas_nuevas:
        raise ValueError("Indica la carga nueva por actividad")
    if not isinstance(capacidad_practica_diaria, dict):
        raise ValueError("La capacidad práctica debe declararse por actividad")
    compromisos = ot_comprometidas_por_dia or {}
    if not isinstance(compromisos, dict):
        raise ValueError("La carga de OTs abiertas debe declararse por actividad")
    if plazo_solicitado_dias is not None:
        plazo = _numero(plazo_solicitado_dias, "Plazo solicitado")
    else:
        plazo = None
    por_actividad = {}
    for actividad, carga0 in cargas_nuevas.items():
        carga = _numero(carga0, f"Carga nueva de {actividad}")
        if actividad not in capacidad_practica_diaria:
            raise ValueError(f"Falta capacidad práctica de {actividad}")
        capacidad = _numero(capacidad_practica_diaria[actividad], f"Capacidad práctica de {actividad}")
        agenda = compromisos.get(actividad, [])
        if isinstance(agenda, (int, float)) and not isinstance(agenda, bool):
            reservada_diaria = _numero(agenda, f"Carga comprometida diaria de {actividad}")
            if reservada_diaria > capacidad + 1e-9:
                raise ValueError(f"La carga comprometida supera la capacidad práctica de {actividad} en un día")
            libre = max(0.0, capacidad - reservada_diaria)
            if carga > 0 and libre <= 0:
                raise ValueError(f"No hay capacidad práctica disponible para {actividad}")
            dias = math.ceil(carga / libre) if carga > 0 else 0
            por_actividad[actividad] = {"carga_nueva": carga, "capacidad_practica_diaria": capacidad,
                                       "dias": dias, "carga_comprometida_diaria": reservada_diaria,
                                       "carga_comprometida_total_estimada": reservada_diaria * dias}
            continue
        if not isinstance(agenda, (list, tuple)):
            raise ValueError(f"Las OTs abiertas de {actividad} requieren una agenda diaria")
        agenda = [_numero(valor, f"Carga comprometida de {actividad}") for valor in agenda]
        if any(valor > capacidad + 1e-9 for valor in agenda):
            raise ValueError(f"La carga comprometida supera la capacidad práctica de {actividad} en un día")
        if carga > 0 and capacidad <= 0:
            raise ValueError(f"No hay capacidad práctica disponible para {actividad}")
        restante = carga
        dias = 0
        limite = max(10000, len(agenda) + 1)
        while restante > 1e-9:
            if dias >= limite:
                raise ValueError(f"No se pudo calcular un plazo para {actividad}")
            reservada = agenda[dias] if dias < len(agenda) else 0.0
            libre = max(0.0, capacidad - reservada)
            restante -= libre
            dias += 1
        por_actividad[actividad] = {"carga_nueva": carga, "capacidad_practica_diaria": capacidad,
                                   "dias": dias, "carga_comprometida_total": sum(agenda)}
    dias_earliest = max((fila["dias"] for fila in por_actividad.values()), default=0)
    atraso = max(0.0, dias_earliest - plazo) if plazo is not None else None
    if atraso is None:
        estado = "PLAZO_NO_INDICADO"
    elif atraso > 0:
        estado = f"{int(atraso) if atraso.is_integer() else atraso:g} días tarde"
    else:
        estado = "LLEGA"
    return {"por_actividad": por_actividad, "dias_earliest": dias_earliest,
            "dias_solicitados": plazo, "dias_tarde": atraso, "estado": estado}
