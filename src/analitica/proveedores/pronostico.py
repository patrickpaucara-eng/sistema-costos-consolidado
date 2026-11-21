# -*- coding: utf-8 -*-
"""OT-018 · Proveedor PRONÓSTICO y aprendizaje (contrato común de OT-017).

Pronostica el siguiente periodo de TARIFA o PRECIO por serie (clave, concepto) con cuatro métodos
(Hyndman y Athanasopoulos): ingenuo, media, suavización exponencial simple (SES) y Holt (tendencia).
Elige por validación de ORIGEN MÓVIL (rolling origin), no por ajuste en la muestra.
Intervalo P05/P95: valor + cuantil de los errores de validación, ampliado para contener siempre el valor
(p05 = valor + min(q05, 0); p95 = valor + max(q95, 0)). conf: nivel nominal del intervalo; el MASE va en su fila.
Aprende: `evaluar` mide pronósticos pasados contra reales; si el MASE de las últimas k ventanas es >= 1
el proveedor se declara en RESPALDO (devuelve el ingenuo). Deriva: CUSUM tabular (Montgomery, fase I / fase II)
sobre los errores de un modelo CONGELADO en la fase I (nivel o recta), que no se reajusta al vigilar.
Puro: sin archivos, sin hora, sin azar. Nada de política fijo: todo es parámetro con su valor por defecto.
OT-100 (L-6; estrategia inspirada en Oria Chavarría 2026): `<concepto>|SESGO` por serie = promedio(real − previsto)
en las MISMAS ventanas de validación del MASE (las del modelo elegido); positivo = el método subestima. Sin ventanas
no se publica. Las filas SESGO van DESPUÉS de todas las anteriores (la salida previa no cambia).
Ojo: `evaluar()` reporta `sesgo` con el signo contrario (pronóstico − real); no se cambió para no romper a quien la usa."""
import math

FICHA = {
    "nombre": "PRONOSTICO", "version": "1.0", "familia": "PRONOSTICO",
    "pregunta": "¿Cuánto costará la tarifa o el insumo el próximo periodo, con qué intervalo y con qué confianza?",
    "consume": ["TARIFA", "PRECIO_INSUMO"],
    "produce": ["<concepto>|PRONOSTICO", "<concepto>|MASE", "<concepto>|DERIVA", "<concepto>|SESGO"],
    "semilla": False,
}

MODELOS = ("INGENUO", "MEDIA", "SES", "HOLT")
MODELOS_DEFECTO = MODELOS

PARAMETROS = {
    "min_entrenamiento": 6,   # observaciones mínimas para el primer origen de validación
    "k_respaldo": 4,          # ventanas recientes en las que se vigila el MASE
    "umbral_mase": 1.0,       # MASE >= umbral en las k ventanas -> RESPALDO (Hyndman: >1 peor que el ingenuo)
    "malla_alfa": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
    "malla_beta": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
    "cusum_k": 0.75,          # holgura en desviaciones (Montgomery, cap. 9; 0,75 con modelo congelado y sigma estimada)
    "cusum_h": 8.0,           # límite en desviaciones: calibrado con series sintéticas (falsas alarmas < 3 % en estacionarias)
    "cusum_fase1": 30,        # puntos de la fase I: fijan el modelo en control (nivel o recta) y la sigma; el resto es fase II
    "cusum_t": 3.0,           # |t| de la pendiente en fase I para congelar una recta; menos -> nivel constante
    "modelos": list(MODELOS_DEFECTO),  # candidatos a elegir; el ingenuo se calcula siempre como base del MASE
    "nivel": 0.90,            # nivel nominal del intervalo (y valor de `conf`); q_inf = (1-nivel)/2, q_sup = (1+nivel)/2
}


# ----------------------------------------------------------------------------- métodos de pronóstico
def pron_ingenuo(y):
    return y[-1]


def pron_media(y):
    return sum(y) / len(y)


def ses_niveles(y, alfa):
    """Niveles L_t: L_1 = y_1; L_t = alfa*y_t + (1-alfa)*L_(t-1). El pronóstico a un paso desde t es L_t."""
    n = [y[0]]
    for v in y[1:]:
        n.append(alfa * v + (1 - alfa) * n[-1])
    return n


def ses_a_un_paso(y, alfa):
    """Pronósticos a un paso para t=2..n: f_t = L_(t-1)."""
    return ses_niveles(y, alfa)[:-1]


def _holt_serie(y, alfa, beta):
    L, T = [y[0]], [y[1] - y[0]]
    pron = []
    for v in y[1:]:
        pron.append(L[-1] + T[-1])
        l = alfa * v + (1 - alfa) * (L[-1] + T[-1])
        T.append(beta * (l - L[-1]) + (1 - beta) * T[-1])
        L.append(l)
    return pron, L, T


def holt_a_un_paso(y, alfa, beta):
    return _holt_serie(y, alfa, beta)[0]


def holt_pronostico(y, alfa, beta):
    _, L, T = _holt_serie(y, alfa, beta)
    return L[-1] + T[-1]


def _sse(real, pron):
    return sum((r - p) ** 2 for r, p in zip(real, pron))


def ajustar(modelo, y, par):
    """Devuelve (parametros_elegidos, pronostico_siguiente). Los parámetros se eligen por SSE a un paso en la muestra
    de entrenamiento (nunca en la validación)."""
    if modelo == "INGENUO":
        return {}, pron_ingenuo(y)
    if modelo == "MEDIA":
        return {}, pron_media(y)
    if modelo == "SES":
        if len(y) < 2:
            raise ValueError("SES necesita al menos 2 observaciones")
        a = min(par["malla_alfa"], key=lambda a: (_sse(y[1:], ses_a_un_paso(y, a)), a))
        return {"alfa": a}, ses_niveles(y, a)[-1]
    if modelo == "HOLT":
        if len(y) < 3:
            raise ValueError("Holt necesita al menos 3 observaciones")
        # con T0 = y1 - y0 el primer pronóstico a un paso es exactamente y1 (error 0): el SSE empieza en t = 2
        mejor = min(((_sse(y[2:], holt_a_un_paso(y, a, b)[1:]), a, b) for a in par["malla_alfa"] for b in par["malla_beta"]))
        _, a, b = mejor
        return {"alfa": a, "beta": b}, holt_pronostico(y, a, b)
    raise ValueError(f"modelo desconocido: {modelo}")


# ----------------------------------------------------------------------------- validación y métricas
def origen_movil(y, modelo, par):
    """Para cada origen t (desde min_entrenamiento): ajusta con y[:t] y pronostica y[t]. Devuelve lista de (real, pron)."""
    m = par["min_entrenamiento"]
    if len(y) <= m:
        raise ValueError(f"serie de {len(y)} puntos: se necesitan más de {m} para validar por origen móvil")
    return [(y[t], ajustar(modelo, y[:t], par)[1]) for t in range(m, len(y))]


def mase(real, pron, base):
    """MASE = MAE del modelo / MAE del ingenuo, ambos sobre los mismos puntos."""
    mae = sum(abs(r - p) for r, p in zip(real, pron)) / len(real)
    mae_b = sum(abs(r - p) for r, p in zip(real, base)) / len(real)
    if mae_b == 0:
        return 0.0 if mae == 0 else math.inf
    return mae / mae_b


def cuantil(xs, q):
    """Cuantil por interpolación lineal (tipo 7, igual a PERCENTILE.INC de Excel)."""
    s = sorted(xs)
    if not s:
        raise ValueError("sin datos para el cuantil")
    h = (len(s) - 1) * q
    lo = int(math.floor(h))
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (h - lo) * (s[hi] - s[lo])


def evaluar(pronosticos_pasados, reales):
    """pronosticos_pasados: lista de {valor, p05, p95} (o números); reales: lista de números, mismo orden.
    Devuelve {MAPE (%), sesgo (media pronóstico-real; >0 = sobrestima), MASE (vs. ingenuo = real anterior), cobertura}.
    MASE usa los puntos 2..n porque el ingenuo necesita el real anterior."""
    if len(pronosticos_pasados) != len(reales) or not reales:
        raise ValueError("pronósticos y reales deben tener la misma longitud (>0)")
    vals = [p["valor"] if isinstance(p, dict) else p for p in pronosticos_pasados]
    if any(r == 0 for r in reales):
        raise ValueError("MAPE no definido: hay reales iguales a cero")
    out = {"MAPE": 100 * sum(abs(r - p) / abs(r) for r, p in zip(reales, vals)) / len(reales),
           "sesgo": sum(p - r for r, p in zip(reales, vals)) / len(reales)}
    out["MASE"] = mase(reales[1:], vals[1:], reales[:-1]) if len(reales) > 1 else None
    cub = [(p["p05"] <= r <= p["p95"]) for p, r in zip(pronosticos_pasados, reales) if isinstance(p, dict)]
    out["cobertura"] = sum(cub) / len(cub) if cub else None
    return out


def deriva(y, k=0.75, h=8.0, fase1=30, t_pend=3.0, escala=1.0):
    """Detección de cambio de nivel: CUSUM tabular (Montgomery, cap. 9) con fase I / fase II.
    Fase I (los primeros `fase1` puntos): se congela el modelo EN CONTROL, nivel constante o recta (OLS) si la
    pendiente tiene |t| >= t_pend, y la sigma de sus residuos. Fase II (el resto): se vigilan los errores de ESE modelo
    congelado (sin reajustarlo, para que un salto no sea absorbido). Devuelve el índice (base 0, en `y`) de la
    primera alarma, o None. Sin fase II (len(y) <= fase1) no hay vigilancia. `escala` fija un piso de sigma."""
    if fase1 < 6:
        raise ValueError("cusum_fase1 debe ser >= 6")
    n = len(y)
    if n <= fase1:
        return None
    y1 = y[:fase1]
    tb, yb = (fase1 - 1) / 2, sum(y1) / fase1
    sxx = sum((t - tb) ** 2 for t in range(fase1))
    b = sum((t - tb) * (y1[t] - yb) for t in range(fase1)) / sxx
    a = yb - b * tb
    s2 = sum((y1[t] - a - b * t) ** 2 for t in range(fase1)) / (fase1 - 2)
    recta = s2 > 0 and abs(b) / math.sqrt(s2 / sxx) >= t_pend
    if recta:
        sigma = math.sqrt(s2)
    else:
        a, b = yb, 0.0
        sigma = math.sqrt(sum((v - yb) ** 2 for v in y1) / (fase1 - 1))
    sigma = max(sigma, 1e-6 * max(abs(escala), 1e-12))
    sp = sn = 0.0
    for t in range(fase1, n):
        z = (y[t] - (a + b * t)) / sigma
        sp = max(0.0, sp + z - k)
        sn = max(0.0, sn - z - k)
        if sp > h or sn > h:
            return t
    return None


# ----------------------------------------------------------------------------- contrato común
def _pronosticar_serie(y, par):
    cand = list(par["modelos"])
    malos = [c for c in cand if c not in MODELOS]
    if malos or not cand:
        raise ValueError(f"modelos inválidos: {malos or 'lista vacía'} (válidos: {', '.join(MODELOS)})")
    val = {"INGENUO": origen_movil(y, "INGENUO", par)}  # el ingenuo siempre: es la base del MASE
    for mod in cand:
        if mod in val:
            continue
        try:
            val[mod] = origen_movil(y, mod, par)
        except ValueError:
            if mod == "MEDIA":
                raise
    cand = [c for c in cand if c in val]
    if not cand:
        raise ValueError("ningún modelo candidato tiene datos suficientes")
    base = [p for _, p in val["INGENUO"]]
    mae = {mod: sum(abs(r - p) for r, p in val[mod]) / len(val[mod]) for mod in cand}
    elegido = min(mae, key=lambda mod: (mae[mod], MODELOS.index(mod)))
    pares = val[elegido]
    real = [r for r, _ in pares]
    pron = [p for _, p in pares]
    errores = [r - p for r, p in pares]
    mase_tot = mase(real, pron, base)
    sesgo = sum(errores) / len(errores) if errores else None   # L-6: real − previsto, mismas ventanas del MASE
    k = min(par["k_respaldo"], len(pares))
    mase_k = mase(real[-k:], pron[-k:], base[-k:])
    # RESPALDO = volver al ingenuo cuando el elegido era OTRO y falla; si el mejor ya es el ingenuo, es OK
    respaldo = elegido != "INGENUO" and mase_k >= par["umbral_mase"]
    usado = "INGENUO" if respaldo else elegido
    pars, valor = ajustar(usado, y, par)
    # el intervalo sale de los errores del modelo USADO (en respaldo, los del ingenuo)
    err_u = [r - b for r, b in zip(real, base)] if respaldo else errores
    if not 0 < par["nivel"] < 1:
        raise ValueError("nivel debe estar en (0, 1)")
    q_inf, q_sup = round((1 - par["nivel"]) / 2, 12), round((1 + par["nivel"]) / 2, 12)
    # el intervalo siempre contiene el valor (E-159): errores de un solo signo no lo dejan fuera
    p05 = valor + min(cuantil(err_u, q_inf), 0.0)
    p95 = valor + max(cuantil(err_u, q_sup), 0.0)
    escala = sum(abs(v) for v in y) / len(y)
    i_deriva = deriva(y, par["cusum_k"], par["cusum_h"], par["cusum_fase1"], par["cusum_t"], escala)
    return {"valor": valor, "p05": p05, "p95": p95, "elegido": elegido, "usado": usado, "pars": pars,
            "mase": mase_tot, "mase_k": mase_k, "sesgo": sesgo, "respaldo": respaldo, "n_val": len(pares),
            "deriva": i_deriva}


def ejecutar(extracto, parametros):
    """extracto: filas {fecha, entidad, clave, concepto, valor, unidad}. Una serie por (clave, concepto),
    ordenada por fecha. Salida (contrato E-158): por serie, `<concepto>|PRONOSTICO` (conf = nivel nominal del
    intervalo, `detalle` informativo), `<concepto>|MASE` (valor = MASE) y, si hay cambio de nivel, `<concepto>|DERIVA`."""
    par = dict(PARAMETROS)
    par.update(parametros or {})
    series = {}
    for f in extracto:
        for c in ("fecha", "clave", "concepto", "valor"):
            if f.get(c) is None:
                raise ValueError(f"fila sin '{c}': {f}")
        series.setdefault((f["clave"], f["concepto"]), []).append(f)
    if not series:
        raise ValueError("extracto vacío: sin historia no hay pronóstico")
    filas, cola = [], []                     # cola: filas SESGO (L-6), al final
    for (clave, concepto) in sorted(series):
        pts = sorted(series[(clave, concepto)], key=lambda f: f["fecha"])
        fechas = [p["fecha"] for p in pts]
        if len(set(fechas)) != len(fechas):
            raise ValueError(f"fechas duplicadas en la serie {clave}/{concepto}")
        y = [float(p["valor"]) for p in pts]
        unidad = pts[-1].get("unidad")
        r = _pronosticar_serie(y, par)
        detalle = {"modelo": r["usado"], "modelo_elegido": r["elegido"], "parametros": r["pars"],
                   "n_validacion": r["n_val"], "mase_ventanas_recientes": r["mase_k"],
                   "estado": "RESPALDO" if r["respaldo"] else "OK"}
        filas.append({"clave": clave, "concepto": f"{concepto}|PRONOSTICO", "valor": r["valor"], "p05": r["p05"],
                      "p95": r["p95"], "conf": par["nivel"], "unidad": unidad, "detalle": detalle})
        filas.append({"clave": clave, "concepto": f"{concepto}|MASE", "valor": r["mase"], "p05": r["mase"],
                      "p95": r["mase"], "conf": None, "unidad": "razon"})
        if r["deriva"] is not None:
            d = float(r["deriva"] + 1)
            filas.append({"clave": clave, "concepto": f"{concepto}|DERIVA", "valor": d, "p05": d, "p95": d,
                          "conf": None, "unidad": "periodo",
                          "detalle": {"fecha": fechas[r["deriva"]], "indice_base_1": r["deriva"] + 1}})
        if r["sesgo"] is not None:
            cola.append({"clave": clave, "concepto": f"{concepto}|SESGO", "valor": r["sesgo"], "p05": r["sesgo"],
                         "p95": r["sesgo"], "conf": None, "unidad": unidad,
                         "detalle": {"n_validacion": r["n_val"], "modelo": r["elegido"]}})
    return filas + cola
