"""Recetas parametrizadas de pedido, independientes de la interfaz.

El libro puede incluir una hoja opcional ``FAMILIA_PARAM``. La ausencia de esa
hoja no altera libros existentes. Los coeficientes se obtienen con mínimos
cuadrados lineales implementados aquí, sin dependencias estadísticas externas.
"""
from __future__ import annotations

import math
import json


HOJA_FAMILIA_PARAM = "FAMILIA_PARAM"
COLUMNAS_FAMILIA_PARAM = (
    "FAM_COD", "IND_COD", "PAR_COD", "PAR_NOMBRE", "PAR_UNIDAD",
    "PAR_MIN", "PAR_MAX", "REC_BASE", "REC_COEF", "REC_N",
)
HOJA_FAMILIA_PRED = "FAMILIA_PRED"
COLUMNAS_FAMILIA_PRED = ("FAM_COD", "IND_COD", "ESTADISTICA_JSON")


def _numero(valor, etiqueta):
    if isinstance(valor, bool):
        raise ValueError(f"{etiqueta} debe ser numérico")
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        raise ValueError(f"{etiqueta} debe ser numérico") from None
    if not math.isfinite(numero):
        raise ValueError(f"{etiqueta} debe ser finito")
    return numero


def _definiciones(parametros):
    if isinstance(parametros, dict):
        items = []
        for clave, valor in parametros.items():
            item = dict(valor)
            item.setdefault("codigo", clave)
            items.append(item)
    elif isinstance(parametros, (list, tuple)):
        items = [dict(item) for item in parametros]
    else:
        raise ValueError("Los parámetros de familia deben ser una lista o mapa")
    salida = {}
    for item in items:
        codigo = str(item.get("codigo", "")).strip()
        nombre = str(item.get("nombre", "")).strip()
        unidad = str(item.get("unidad", "")).strip()
        if not codigo or not nombre or not unidad:
            raise ValueError("Cada parámetro requiere código, nombre y unidad")
        minimo = item.get("minimo")
        maximo = item.get("maximo")
        minimo = None if minimo in (None, "") else _numero(minimo, f"Mínimo de {nombre}")
        maximo = None if maximo in (None, "") else _numero(maximo, f"Máximo de {nombre}")
        if minimo is not None and maximo is not None and minimo > maximo:
            raise ValueError(f"Rango inválido para {nombre}: mínimo mayor que máximo")
        if codigo in salida:
            raise ValueError(f"Parámetro duplicado: {codigo}")
        salida[codigo] = {"codigo": codigo, "nombre": nombre, "unidad": unidad,
                          "minimo": minimo, "maximo": maximo, "obligatorio": True}
    if not salida:
        raise ValueError("La familia requiere al menos un parámetro")
    return salida


def validar_parametros(definiciones, valores):
    """Valida presencia y rango; devuelve valores numéricos por código."""
    defs = _definiciones(definiciones)
    if not isinstance(valores, dict):
        raise ValueError("Los valores del pedido deben ser un mapa")
    faltantes = [d["nombre"] for codigo, d in defs.items()
                 if d["obligatorio"] and (codigo not in valores or valores[codigo] in (None, ""))]
    if faltantes:
        raise ValueError("Falta parámetro obligatorio: " + ", ".join(faltantes))
    desconocidos = sorted(set(map(str, valores)) - set(defs))
    if desconocidos:
        raise ValueError("Parámetro no declarado: " + ", ".join(desconocidos))
    salida = {}
    for codigo, definicion in defs.items():
        valor = _numero(valores[codigo], definicion["nombre"])
        if definicion["minimo"] is not None and valor < definicion["minimo"]:
            raise ValueError(f"{definicion['nombre']} está debajo del mínimo válido ({definicion['minimo']:g} {definicion['unidad']})")
        if definicion["maximo"] is not None and valor > definicion["maximo"]:
            raise ValueError(f"{definicion['nombre']} supera el máximo válido ({definicion['maximo']:g} {definicion['unidad']})")
        salida[codigo] = valor
    return salida


def _resolver_qr(matriz, respuesta):
    """Resuelve mínimos cuadrados por QR de Householder para matriz alta."""
    a = [list(map(float, fila)) for fila in matriz]
    y = list(map(float, respuesta))
    n = len(a)
    p = len(a[0]) if n else 0
    if n < p or p == 0 or any(len(fila) != p for fila in a) or len(y) != n:
        raise ValueError("No hay suficientes órdenes para aprender la receta")
    for k in range(p):
        norma = math.sqrt(sum(a[i][k] ** 2 for i in range(k, n)))
        if norma <= 1e-12:
            raise ValueError("Las órdenes históricas no permiten distinguir todos los parámetros")
        alfa = -math.copysign(norma, a[k][k] if a[k][k] else 1.0)
        vector = [a[i][k] for i in range(k, n)]
        vector[0] -= alfa
        vv = sum(v * v for v in vector)
        if vv <= 1e-24:
            raise ValueError("Las órdenes históricas no permiten distinguir todos los parámetros")
        factor = 2.0 / vv
        for j in range(k, p):
            escala = factor * sum(vector[i - k] * a[i][j] for i in range(k, n))
            for i in range(k, n):
                a[i][j] -= escala * vector[i - k]
        escala_y = factor * sum(vector[i - k] * y[i] for i in range(k, n))
        for i in range(k, n):
            y[i] -= escala_y * vector[i - k]
        a[k][k] = alfa
        for i in range(k + 1, n):
            a[i][k] = 0.0
    beta = [0.0] * p
    for i in range(p - 1, -1, -1):
        divisor = a[i][i]
        if abs(divisor) <= 1e-12:
            raise ValueError("Las órdenes históricas no permiten distinguir todos los parámetros")
        beta[i] = (y[i] - sum(a[i][j] * beta[j] for j in range(i + 1, p))) / divisor
    return beta


def _inversa(matriz):
    """Inversa por Gauss-Jordan; entradas estandarizadas evitan mala escala."""
    n = len(matriz)
    ampliada = [list(map(float, fila)) + [1.0 if i == j else 0.0 for j in range(n)]
                for i, fila in enumerate(matriz)]
    for col in range(n):
        pivote = max(range(col, n), key=lambda fila: abs(ampliada[fila][col]))
        if abs(ampliada[pivote][col]) <= 1e-12:
            raise ValueError("Las órdenes históricas no permiten estimar la incertidumbre")
        ampliada[col], ampliada[pivote] = ampliada[pivote], ampliada[col]
        divisor = ampliada[col][col]
        ampliada[col] = [valor / divisor for valor in ampliada[col]]
        for fila in range(n):
            if fila == col:
                continue
            factor = ampliada[fila][col]
            ampliada[fila] = [a - factor * b for a, b in zip(ampliada[fila], ampliada[col])]
    return [fila[n:] for fila in ampliada]


def _ajustar_lineal(observaciones, codigos_parametro):
    """Ajusta cantidad = base + Σ coeficiente×parámetro."""
    codigos = list(codigos_parametro)
    n = len(observaciones)
    if n < len(codigos) + 1:
        raise ValueError(f"Se requieren al menos {len(codigos) + 1} OT reales para aprender esta receta")
    columnas = [[_numero(o["parametros"][codigo], codigo) for o in observaciones]
                for codigo in codigos]
    medias = [sum(columna) / n for columna in columnas]
    escalas = [max((abs(x - media) for x in columna), default=0.0)
               for columna, media in zip(columnas, medias)]
    if any(escala <= 1e-12 for escala in escalas):
        raise ValueError("Las órdenes históricas no permiten distinguir todos los parámetros")
    matriz = [[(columnas[j][i] - medias[j]) / escalas[j] for j in range(len(codigos))]
              for i in range(n)]
    cantidades = [_numero(o["cantidad"], "Cantidad histórica") for o in observaciones]
    media_cantidad = sum(cantidades) / n
    beta_escalada = _resolver_qr(matriz, [y - media_cantidad for y in cantidades])
    coeficientes = {codigo: beta_escalada[i] / escalas[i] for i, codigo in enumerate(codigos)}
    base = media_cantidad - sum(coeficientes[codigo] * medias[i] for i, codigo in enumerate(codigos))
    gl = n - len(codigos) - 1
    estadistica = {"grados_libertad": gl, "desviacion_residual": None,
                   "medias": dict(zip(codigos, medias)), "escalas": dict(zip(codigos, escalas)),
                   "inversa_grama": None}
    if gl > 0:
        residuos = [cantidad - (base + sum(coeficientes[codigo] * obs["parametros"][codigo]
                                           for codigo in codigos))
                    for obs, cantidad in zip(observaciones, cantidades)]
        estadistica["desviacion_residual"] = math.sqrt(sum(r * r for r in residuos) / gl)
        gram = [[sum(fila[i] * fila[j] for fila in matriz) for j in range(len(codigos))]
                for i in range(len(codigos))]
        estadistica["inversa_grama"] = _inversa(gram)
    return {"base": base, "coeficientes": coeficientes, "n": n, "estadistica": estadistica}


def aprender_familia(codigo_familia, definiciones, ordenes_reales):
    """Aprende una receta por inductor; cada fila identifica una OT de síntesis REAL.

    Formato de fila: ``{"sintesis":"REAL", "parametros":{"kg": 1000},
    "inductores":{"SOLD_H": 60}}``. No acepta estimaciones ni observaciones
    sin la etiqueta REAL para evitar convertirlas silenciosamente en historia.
    """
    familia = str(codigo_familia or "").strip()
    if not familia:
        raise ValueError("La familia requiere un código")
    defs = _definiciones(definiciones)
    if not isinstance(ordenes_reales, (list, tuple)) or not ordenes_reales:
        raise ValueError("Se requieren órdenes históricas reales")
    for orden in ordenes_reales:
        if orden.get("sintesis") != "REAL":
            raise ValueError("Solo se aprende con órdenes de síntesis REAL")
        if orden.get("familia") not in (None, familia):
            raise ValueError("La orden histórica pertenece a otra familia")
        validar_parametros(defs, orden.get("parametros"))
        if not isinstance(orden.get("inductores"), dict) or not orden["inductores"]:
            raise ValueError("Cada orden real requiere cantidades históricas de inductores")
    codigos_inductor = set(ordenes_reales[0]["inductores"])
    if any(set(o["inductores"]) != codigos_inductor for o in ordenes_reales):
        raise ValueError("Las órdenes históricas deben declarar los mismos inductores, incluido cero cuando no se use")
    aprendidos = {}
    for inductor in sorted(codigos_inductor):
        observaciones = []
        for orden in ordenes_reales:
            parametros = validar_parametros(defs, orden["parametros"])
            observaciones.append({"parametros": parametros,
                                  "cantidad": _numero(orden["inductores"][inductor], f"Cantidad de {inductor}")})
        aprendidos[inductor] = _ajustar_lineal(observaciones, defs)
    return {"familia": familia, "parametros": defs, "inductores": aprendidos}


def calcular_cantidades(modelo, valores):
    """Explota la receta aprendida para los datos de un pedido nuevo."""
    if not isinstance(modelo, dict) or not isinstance(modelo.get("inductores"), dict):
        raise ValueError("Receta de familia inválida")
    parametros = validar_parametros(modelo.get("parametros", {}), valores)
    resultados = {}
    for codigo, receta in modelo["inductores"].items():
        coeficientes = receta.get("coeficientes") or {}
        if set(coeficientes) != set(parametros):
            raise ValueError(f"La receta de {codigo} no contiene todos los parámetros requeridos")
        cantidad = _numero(receta.get("base"), f"Base de {codigo}") + sum(
            _numero(coeficientes[param], f"Coeficiente de {codigo}/{param}") * valor
            for param, valor in parametros.items()
        )
        if not math.isfinite(cantidad) or cantidad < -1e-9:
            raise ValueError(f"La receta de {codigo} produce una cantidad negativa")
        resultados[codigo] = max(0.0, cantidad)
    return resultados


def intervalo_prediccion(modelo, codigo_inductor, valores, confianza=0.90):
    """Intervalo t de predicción para una OT nueva (P05–P95 por defecto).

    La incertidumbre queda como no estimable si la historia no aporta grados de
    libertad residuales. El intervalo es por inductor; sumar sus extremos para
    formar el rango del pedido presupone independencia entre errores.
    """
    defs = _definiciones(modelo.get("parametros", {}))
    parametros = validar_parametros(defs, valores)
    if isinstance(confianza, bool) or not isinstance(confianza, (int, float)) or not 0 < confianza < 1:
        raise ValueError("La confianza debe estar entre 0 y 1")
    receta = (modelo.get("inductores") or {}).get(codigo_inductor)
    if receta is None:
        raise ValueError(f"Inductor inexistente en la receta: {codigo_inductor}")
    media = calcular_cantidades({"parametros": defs, "inductores": {codigo_inductor: receta}}, parametros)[codigo_inductor]
    estadistica = receta.get("estadistica") or {}
    gl = estadistica.get("grados_libertad", 0)
    sigma = estadistica.get("desviacion_residual")
    inversa = estadistica.get("inversa_grama")
    if gl <= 0 or sigma is None or inversa is None:
        return {"estimable": False, "media": media, "p05": None, "p95": None,
                "motivo": "Historia insuficiente para estimar P05–P95."}
    codigos = list(defs)
    medias = estadistica.get("medias") or {}
    escalas = estadistica.get("escalas") or {}
    z = [(parametros[codigo] - float(medias[codigo])) / float(escalas[codigo]) for codigo in codigos]
    if len(inversa) != len(z) or any(len(fila) != len(z) for fila in inversa):
        raise ValueError(f"Estadística de predicción inválida para {codigo_inductor}")
    leverage = 1 / int(receta["n"]) + sum(z[i] * float(inversa[i][j]) * z[j]
                                            for i in range(len(z)) for j in range(len(z)))
    from .familias import t_cuantil
    t = t_cuantil((1 + float(confianza)) / 2, int(gl))
    radio = t * float(sigma) * math.sqrt(max(0.0, 1 + leverage))
    return {"estimable": True, "media": media, "p05": max(0.0, media - radio), "p95": media + radio,
            "confianza": float(confianza), "grados_libertad": int(gl)}


def crear_hoja_familia_param(libro):
    """Crea la hoja opcional si falta y valida su cabecera sin cambiar otras hojas."""
    hoja = libro[HOJA_FAMILIA_PARAM] if HOJA_FAMILIA_PARAM in libro.sheetnames else libro.create_sheet(HOJA_FAMILIA_PARAM)
    actual = tuple(hoja.cell(1, i + 1).value for i in range(len(COLUMNAS_FAMILIA_PARAM)))
    if all(valor is None for valor in actual):
        for i, encabezado in enumerate(COLUMNAS_FAMILIA_PARAM, 1):
            hoja.cell(1, i, encabezado)
    elif actual != COLUMNAS_FAMILIA_PARAM:
        raise ValueError(f"La hoja {HOJA_FAMILIA_PARAM} tiene una cabecera incompatible")
    return hoja


def guardar_familias_en_libro(libro, modelos):
    """Persiste los modelos en la hoja propia; no modifica las demás hojas."""
    hoja = crear_hoja_familia_param(libro)
    if hoja.max_row > 1:
        hoja.delete_rows(2, hoja.max_row - 1)
    for familia, modelo in sorted(modelos.items()):
        defs = _definiciones(modelo.get("parametros", {}))
        for inductor, receta in sorted(modelo.get("inductores", {}).items()):
            coeficientes = receta.get("coeficientes") or {}
            if set(coeficientes) != set(defs):
                raise ValueError(f"La receta de {inductor} no contiene todos los parámetros de {familia}")
            base = _numero(receta.get("base"), f"Base de {inductor}")
            n = receta.get("n", "")
            for parametro, definicion in defs.items():
                hoja.append((familia, inductor, parametro, definicion["nombre"], definicion["unidad"],
                             definicion["minimo"], definicion["maximo"], base,
                             _numero(coeficientes[parametro], f"Coeficiente de {inductor}/{parametro}"), n))
    predicciones = []
    for familia, modelo in sorted(modelos.items()):
        for inductor, receta in sorted(modelo.get("inductores", {}).items()):
            if receta.get("estadistica"):
                predicciones.append((familia, inductor,
                                     json.dumps(receta["estadistica"], ensure_ascii=False, sort_keys=True)))
    if predicciones or HOJA_FAMILIA_PRED in libro.sheetnames:
        hoja_pred = libro[HOJA_FAMILIA_PRED] if HOJA_FAMILIA_PRED in libro.sheetnames else libro.create_sheet(HOJA_FAMILIA_PRED)
        encabezados = tuple(hoja_pred.cell(1, i + 1).value for i in range(len(COLUMNAS_FAMILIA_PRED)))
        if all(valor is None for valor in encabezados):
            for i, encabezado in enumerate(COLUMNAS_FAMILIA_PRED, 1):
                hoja_pred.cell(1, i, encabezado)
        elif encabezados != COLUMNAS_FAMILIA_PRED:
            raise ValueError(f"La hoja {HOJA_FAMILIA_PRED} tiene una cabecera incompatible")
        if hoja_pred.max_row > 1:
            hoja_pred.delete_rows(2, hoja_pred.max_row - 1)
        # También vacía estadísticas antiguas si se reemplaza una receta por
        # otra sin historia suficiente; no deben sobrevivir intervalos obsoletos.
        for fila in predicciones:
            hoja_pred.append(fila)
    return hoja


def leer_familias_de_libro(libro):
    """Lee la hoja opcional; libros previos que no la tengan devuelven mapa vacío."""
    if HOJA_FAMILIA_PARAM not in libro.sheetnames:
        return {}
    hoja = libro[HOJA_FAMILIA_PARAM]
    encabezados = tuple(hoja.cell(1, i + 1).value for i in range(len(COLUMNAS_FAMILIA_PARAM)))
    if encabezados != COLUMNAS_FAMILIA_PARAM:
        raise ValueError(f"La hoja {HOJA_FAMILIA_PARAM} tiene una cabecera incompatible")
    salida = {}
    for numero_fila, fila in enumerate(hoja.iter_rows(min_row=2, values_only=True), 2):
        if not any(valor is not None for valor in fila[:len(COLUMNAS_FAMILIA_PARAM)]):
            continue
        datos = dict(zip(COLUMNAS_FAMILIA_PARAM, fila[:len(COLUMNAS_FAMILIA_PARAM)]))
        familia, inductor, parametro = (str(datos[campo] or "").strip()
                                         for campo in ("FAM_COD", "IND_COD", "PAR_COD"))
        if not familia or not inductor or not parametro:
            raise ValueError(f"Fila {numero_fila}: faltan familia, inductor o parámetro")
        definicion = {"codigo": parametro, "nombre": datos["PAR_NOMBRE"], "unidad": datos["PAR_UNIDAD"],
                      "minimo": datos["PAR_MIN"], "maximo": datos["PAR_MAX"]}
        definicion = _definiciones([definicion])[parametro]
        modelo = salida.setdefault(familia, {"familia": familia, "parametros": {}, "inductores": {}})
        previa = modelo["parametros"].get(parametro)
        if previa is not None and previa != definicion:
            raise ValueError(f"Fila {numero_fila}: definición inconsistente para {parametro}")
        modelo["parametros"][parametro] = definicion
        receta = modelo["inductores"].setdefault(inductor, {"base": _numero(datos["REC_BASE"], "Base de receta"),
                                                                  "coeficientes": {}, "n": datos["REC_N"]})
        if not math.isclose(receta["base"], _numero(datos["REC_BASE"], "Base de receta"), rel_tol=0, abs_tol=1e-9):
            raise ValueError(f"Fila {numero_fila}: bases inconsistentes para {inductor}")
        if parametro in receta["coeficientes"]:
            raise ValueError(f"Fila {numero_fila}: coeficiente duplicado para {inductor}/{parametro}")
        receta["coeficientes"][parametro] = _numero(datos["REC_COEF"], "Coeficiente de receta")
    for familia, modelo in salida.items():
        requeridos = set(modelo["parametros"])
        for inductor, receta in modelo["inductores"].items():
            if set(receta["coeficientes"]) != requeridos:
                raise ValueError(f"La receta de {familia}/{inductor} está incompleta")
    if HOJA_FAMILIA_PRED in libro.sheetnames:
        hoja_pred = libro[HOJA_FAMILIA_PRED]
        encabezados = tuple(hoja_pred.cell(1, i + 1).value for i in range(len(COLUMNAS_FAMILIA_PRED)))
        if encabezados != COLUMNAS_FAMILIA_PRED:
            raise ValueError(f"La hoja {HOJA_FAMILIA_PRED} tiene una cabecera incompatible")
        vistos = set()
        for numero_fila, fila in enumerate(hoja_pred.iter_rows(min_row=2, values_only=True), 2):
            if not any(valor is not None for valor in fila[:len(COLUMNAS_FAMILIA_PRED)]):
                continue
            familia, inductor, texto = fila[:len(COLUMNAS_FAMILIA_PRED)]
            clave = (str(familia or "").strip(), str(inductor or "").strip())
            if clave in vistos or clave[0] not in salida or clave[1] not in salida[clave[0]]["inductores"]:
                raise ValueError(f"Fila {numero_fila}: estadística de predicción duplicada o sin receta")
            try:
                estadistica = json.loads(texto)
            except (TypeError, json.JSONDecodeError):
                raise ValueError(f"Fila {numero_fila}: estadística de predicción inválida") from None
            if not isinstance(estadistica, dict):
                raise ValueError(f"Fila {numero_fila}: estadística de predicción inválida")
            salida[clave[0]]["inductores"][clave[1]]["estadistica"] = estadistica
            vistos.add(clave)
    return salida
