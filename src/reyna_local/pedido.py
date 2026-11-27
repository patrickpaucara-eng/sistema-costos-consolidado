"""Orquestación del pedido: receta, costo, rango, adicionales, plazo y precio."""
from __future__ import annotations

from datetime import date
import math

from .conceptos_pedido import comparar_tamanos_lote, cotizar_lote
from .plazo_pedido import calcular_plazo_actividades
from .recetas_pedido import calcular_cantidades, intervalo_prediccion


def _number(value, label, allow_zero=True):
    if isinstance(value, bool):
        raise ValueError(f"{label} debe ser numérico")
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label} debe ser numérico") from None
    if not math.isfinite(value) or value < 0 or (not allow_zero and value == 0):
        raise ValueError(f"{label} debe ser finito y {'positivo' if not allow_zero else 'no negativo'}")
    return value


def _mapear_inductores(cantidades, resultado):
    actividades_disponibles = {str(fila.get("codigo")) for fila in resultado.get("actividades", [])}
    materiales_disponibles = {str(fila.get("material")) for fila in resultado.get("kardex", []) if fila.get("material")}
    reglas = (resultado.get("modelo") or {}).get("reglas", [])
    actividades = {}
    materiales = {}
    for codigo, cantidad in cantidades.items():
        if codigo in actividades_disponibles:
            actividades[codigo] = cantidad
        elif codigo in materiales_disponibles:
            materiales[codigo] = cantidad
        else:
            asociadas = sorted({str(regla.get("origen")) for regla in reglas
                                if regla.get("etapa") == "P4C" and str(regla.get("inductor")) == codigo
                                and str(regla.get("origen")) in actividades_disponibles})
            if len(asociadas) != 1:
                detalle = "no tiene" if not asociadas else "tiene más de una"
                raise ValueError(f"El inductor {codigo} {detalle} actividad de costo única en el resultado REAL")
            actividades[asociadas[0]] = actividades.get(asociadas[0], 0.0) + cantidad
    return actividades, materiales


def _cotizar_base(libro, empresa, resultado, medidas, actividades, materiales,
                  precio, margen, meses, intervalo, curva, contrato, producto):
    if meses:
        from .cotizador import cotizar_proyectado
        return cotizar_proyectado(libro, empresa, resultado, medidas, actividades, materiales,
                                  precio, margen, meses, intervalo, curva, contrato)
    from .cotizador import cotizar
    return cotizar(resultado, medidas, actividades, materiales, precio, margen, producto=producto)


def _costo_con_adicionales(costo_abc, cantidad, pedido):
    unidades_lote = pedido.get("unidades_por_lote")
    if unidades_lote in (None, ""):
        unidades_lote = cantidad
    return cotizar_lote(cantidad, unidades_lote,
                        pedido.get("preparacion_por_lote", 0),
                        costo_abc / cantidad,
                        pedido.get("conceptos_adicionales") or [])


def _plazo(cargas, pedido):
    capacidad = pedido.get("capacidad_practica_diaria") or {}
    comprometidas = pedido.get("ot_comprometidas_por_dia") or {}
    codigos = set(cargas)
    if not codigos or codigos - set(capacidad) or codigos - set(comprometidas):
        return {"estado": "NO_DISPONIBLE", "dias_earliest": None, "dias_tarde": None,
                "motivo": "Indica capacidad práctica y carga diaria ya comprometida para cada inductor."}
    return calcular_plazo_actividades(cargas, capacidad, comprometidas,
                                      pedido.get("dias_solicitados"))


def cotizar_pedido(libro, empresa, resultado, medidas, modelo, pedido):
    """Calcula el pedido completo y conserva separados el costo y sus supuestos.

    Las cantidades de la receta son por unidad de producto; se multiplican por
    la cantidad solicitada. P05/P95 se estiman por inductor mediante OLS t y se
    suman como aproximación independiente de recursos.
    """
    if not isinstance(pedido, dict):
        raise ValueError("El pedido debe ser un mapa")
    producto = str(pedido.get("producto") or "").strip()
    cliente = str(pedido.get("cliente") or "").strip()
    fecha_requerida = str(pedido.get("fecha_requerida") or "").strip()
    if not producto or not cliente:
        raise ValueError("Indica producto y cliente")
    try:
        date.fromisoformat(fecha_requerida)
    except ValueError:
        raise ValueError("La fecha requerida debe tener formato AAAA-MM-DD") from None
    cantidad = _number(pedido.get("cantidad"), "Cantidad", allow_zero=False)
    precio = _number(pedido.get("precio_mercado"), "Precio de mercado")
    margen = _number(pedido.get("margen_objetivo"), "Margen objetivo")
    if margen >= 1:
        raise ValueError("El margen objetivo debe ser menor que 100 %")
    contrato = str(pedido.get("contrato") or "CERRADO").upper()
    if contrato not in {"CERRADO", "REAJUSTE"}:
        raise ValueError("El contrato debe ser CERRADO o REAJUSTE")
    meses = pedido.get("meses", 0)
    if isinstance(meses, bool) or not isinstance(meses, int) or not 0 <= meses <= 24:
        raise ValueError("La duración proyectada debe estar entre 0 y 24 meses")
    intervalo = pedido.get("intervalo", 3)
    if isinstance(intervalo, bool) or not isinstance(intervalo, int) or intervalo <= 0:
        raise ValueError("El intervalo debe ser entero positivo")
    curva = str(pedido.get("curva") or "s")
    if meses and curva not in {"pareja", "inicio", "final", "s"}:
        raise ValueError("Curva de proyección inválida")
    cantidades_unidad = calcular_cantidades(modelo, pedido.get("parametros") or {})
    cantidades = {codigo: valor * cantidad for codigo, valor in cantidades_unidad.items()}
    actividades, materiales = _mapear_inductores(cantidades, resultado)
    base = _cotizar_base(libro, empresa, resultado, medidas, actividades, materiales,
                         precio, margen, meses, intervalo, curva, contrato, producto)
    costo_abc = float(base.get("total", base.get("costo_pedido", 0)))
    costo = _costo_con_adicionales(costo_abc, cantidad, pedido)
    comparar_lote = pedido.get("comparar_unidades_por_lote")
    comparacion_lotes = None
    if comparar_lote not in (None, ""):
        comparar_lote = _number(comparar_lote, "Tamaño de lote alternativo", allow_zero=False)
        actual = pedido.get("unidades_por_lote")
        actual = cantidad if actual in (None, "") else _number(actual, "Unidades por lote", allow_zero=False)
        comparacion_lotes = comparar_tamanos_lote(
            cantidad, [actual, comparar_lote], pedido.get("preparacion_por_lote", 0),
            costo_abc / cantidad, pedido.get("conceptos_adicionales") or [],
        )

    intervalos = {codigo: intervalo_prediccion(modelo, codigo, pedido.get("parametros") or {})
                  for codigo in modelo.get("inductores", {})}
    rango = None
    if intervalos and all(x.get("estimable") for x in intervalos.values()):
        totales = []
        for extremo in ("p05", "p95"):
            cantidades_extremo = {codigo: fila[extremo] * cantidad for codigo, fila in intervalos.items()}
            act_extremo, mat_extremo = _mapear_inductores(cantidades_extremo, resultado)
            quote_extremo = _cotizar_base(libro, empresa, resultado, medidas, act_extremo, mat_extremo,
                                           precio, margen, meses, intervalo, curva, contrato, producto)
            abc_extremo = float(quote_extremo.get("total", quote_extremo.get("costo_pedido", 0)))
            totales.append(_costo_con_adicionales(abc_extremo, cantidad, pedido)["costo_pedido"])
        rango = {"p05": min(totales), "p95": max(totales),
                 "metodo": "Suma de intervalos t por inductor; supone errores independientes."}

    plazo = _plazo(cantidades, pedido)
    sugerido = round(costo["costo_pedido"] / (1 - margen), 2)
    brecha_mercado = round(precio - sugerido, 2)
    decision = ("REVISAR: el precio de mercado está por debajo del sugerido para el margen objetivo."
                if brecha_mercado < 0 else "El precio de mercado alcanza el sugerido; confirma plazo y supuestos.")
    if contrato == "CERRADO":
        recomendacion = "Precio cerrado: el proveedor asume el riesgo de costos durante la ejecución."
    else:
        recomendacion = "Con reajuste: el contrato debe definir cómo se actualizan los cambios de costo."
    avisos = list(base.get("avisos") or [])
    if rango is None:
        avisos.append("P05–P95 no estimable: faltan OTs reales suficientes para medir la variación.")
    if plazo.get("estado") == "NO_DISPONIBLE":
        avisos.append(plazo["motivo"])
    return {
        "producto": producto, "cliente": cliente, "fecha_requerida": fecha_requerida,
        "familia": modelo.get("familia"), "parametros": pedido.get("parametros"), "cantidad": cantidad,
        "costo_esperado": costo["costo_pedido"], "costo_pedido": costo["costo_pedido"],
        "total": costo["costo_pedido"], "costo_abc": round(costo_abc, 2),
        "rango_p05_p95": rango, "plazo": plazo, "costo_lote": costo,
        "comparacion_lotes": comparacion_lotes,
        "precio_mercado": precio, "precio_sugerido": sugerido,
        "margen_objetivo": margen, "brecha_mercado": brecha_mercado,
        "contrato": contrato, "decision": decision, "recomendacion": recomendacion,
        "avisos": avisos,
        "fundamento": {
            "formula": "Costo esperado = tarifa REAL × cantidad de inductores + preparación por lote + conceptos adicionales; precio sugerido = costo / (1 − margen objetivo).",
            "supuesto": "La receta es lineal en los parámetros declarados; la tarifa usa el último resultado REAL disponible y el contrato indicado.",
            "dato_usado": f"Familia {modelo.get('familia')}; cantidad {cantidad:g}; parámetros {pedido.get('parametros')}; precio de mercado S/ {precio:g}.",
            "limite": "P05/P95 suma intervalos t por inductor y supone independencia; plazo son días de capacidad. La fuente debe confirmar calendario y carga de OTs abiertas.",
        },
        "recomendacion_precio": recomendacion,
    }
