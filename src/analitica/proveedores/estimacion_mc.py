# -*- coding: utf-8 -*-
"""OT-017 · Proveedor ESTIMACION ex-ante (cotizacion con intervalo), Monte Carlo con semilla.

Costo de una orden ANTES de existir:
    C = sum_i  Q_i * (1 + M_i) * T_i   +   H * R
con Q_i = cantidad de receta (dato), M_i = merma esperada, T_i = tarifa/precio estimado del insumo i,
H = tiempo de la orden, R = tasa por unidad de tiempo.
Flujo de datos (E-157): T_i y R llegan del proveedor PRONOSTICO (valor, p05, p95); M_i y H toman su
distribucion de la HISTORIA del extracto (normal con media y desviacion muestrales). Nada se inventa:
sin pronostico o sin historia suficiente -> ValueError (Horngren cap. 7; Hyndman para el pronostico).
Insumos independientes => la varianza total es la suma de las de cada termino; el peso de cada insumo
en la varianza es su parte de esa suma. Puro: sin archivos, sin hora, azar solo con `semilla`.

Conceptos del extracto (fila canonica {fecha, entidad, clave, concepto, valor, unidad}):
  CANTIDAD_RECETA   clave=<producto>|<insumo>   valor
  MERMA_HISTORICA   clave=<producto>|<insumo>   una fila por periodo (fraccion, p. ej. 0.03)
  TARIFA_ESTIMADA   clave=<producto>|<insumo>   valor y p05/p95 (salida de PRONOSTICO)
  TIEMPO_HISTORICO  clave=<producto>            una fila por periodo
  TASA_ESTIMADA     clave=<producto>            valor y p05/p95 (salida de PRONOSTICO)
Salida: COSTO_ESTIMADO (clave=<producto>; media, p05, p95, conf) y PESO_VARIANZA (clave=<producto>|<insumo>
o <producto>|TIEMPO). Marca ESTIMADO (R46): el concepto lo declara, no es un hecho.
OT-100 (L-3, cola de riesgo; estrategia inspirada en Oria Chavarria 2026): DESPUES de todas las filas anteriores,
por producto, `CVAR95` (media del 5 % de corridas de MAYOR costo, k = ceil(0.05 n), minimo 1) y, si el parametro
opcional `umbral` (numero o {producto: numero}) cubre al producto, `PROB_SUPERA` (fraccion de corridas con costo
> umbral, estricto). Se calculan con las MISMAS corridas: no consumen numeros del generador."""
import math
import random

FICHA = {
    "nombre": "ESTIMACION_MC", "version": "1.0", "familia": "ESTIMACION",
    "pregunta": "¿Cuánto costará esta orden antes de existir, con qué intervalo y qué insumo pesa más en la incertidumbre?",
    "consume": ["CANTIDAD_RECETA", "MERMA_HISTORICA", "TARIFA_ESTIMADA", "TIEMPO_HISTORICO", "TASA_ESTIMADA"],
    "produce": ["COSTO_ESTIMADO", "PESO_VARIANZA", "CVAR95", "PROB_SUPERA"],
    "semilla": True,
}

PARAMETROS = {
    "semilla": 12345,        # reproducibilidad
    "n_sim": 20000,          # corridas Monte Carlo
    "nivel": 0.90,           # nivel del intervalo (P05-P95)
    "min_historia": 3,       # periodos minimos para estimar media y desviacion (n-1 > 0)
}

Z95 = 1.6448536269514722     # cuantil 0.95 de la normal estandar


def _fila(clave, concepto, valor, p05, p95, conf, unidad):
    return {"clave": clave, "concepto": concepto, "valor": round(valor, 6), "p05": round(p05, 6),
            "p95": round(p95, 6), "conf": conf, "unidad": unidad}


def _media_sd(xs):
    n = len(xs)
    m = sum(xs) / n
    return m, math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))


def _sd_desde_intervalo(f, clave):
    if f.get("p05") is None or f.get("p95") is None:
        raise ValueError("%s sin intervalo p05/p95 del pronostico: no se inventa una dispersion" % clave)
    if f["p95"] < f["p05"]:
        raise ValueError("%s con p95 < p05" % clave)
    return (f["p95"] - f["p05"]) / (2 * Z95)


def preparar(extracto, parametros=None):
    """Agrupa el extracto por producto. Devuelve {producto: {'insumos': {...}, 'tiempo': (m, sd), 'tasa': (mu, sd), 'unidad'}}."""
    par = dict(PARAMETROS)
    par.update(parametros or {})
    k = par["min_historia"]
    prod = {}

    def p(clave):
        return prod.setdefault(clave.split("|")[0], {"rec": {}, "mer": {}, "tar": {}, "tie": [], "tasa": None, "uni": ""})
    for f in extracto:
        c, cl = f["concepto"], f["clave"]
        if c == "CANTIDAD_RECETA":
            p(cl)["rec"][cl.split("|", 1)[1]] = f["valor"]
        elif c == "MERMA_HISTORICA":
            p(cl)["mer"].setdefault(cl.split("|", 1)[1], []).append(f["valor"])
        elif c == "TARIFA_ESTIMADA":
            p(cl)["tar"][cl.split("|", 1)[1]] = (f["valor"], _sd_desde_intervalo(f, cl))
            p(cl)["uni"] = f["unidad"]
        elif c == "TIEMPO_HISTORICO":
            p(cl)["tie"].append(f["valor"])
        elif c == "TASA_ESTIMADA":
            p(cl)["tasa"] = (f["valor"], _sd_desde_intervalo(f, cl))
    if not prod:
        raise ValueError("extracto sin datos de estimacion: no hay historia ni pronostico")
    out = {}
    for nom, d in prod.items():
        if not d["rec"]:
            raise ValueError("%s sin CANTIDAD_RECETA" % nom)
        if d["tasa"] is None:
            raise ValueError("%s sin TASA_ESTIMADA (pronostico)" % nom)
        if len(d["tie"]) < k:
            raise ValueError("%s: historia de tiempo insuficiente (%d < %d)" % (nom, len(d["tie"]), k))
        ins = {}
        for i, q in d["rec"].items():
            if i not in d["tar"]:
                raise ValueError("%s|%s sin TARIFA_ESTIMADA (pronostico)" % (nom, i))
            h = d["mer"].get(i, [])
            if len(h) < k:
                raise ValueError("%s|%s: historia de merma insuficiente (%d < %d)" % (nom, i, len(h), k))
            ins[i] = {"q": q, "merma": _media_sd(h), "tarifa": d["tar"][i]}
        out[nom] = {"insumos": ins, "tiempo": _media_sd(d["tie"]), "tasa": d["tasa"], "unidad": d["uni"]}
    return out


def analitico(modelo):
    """Media y varianza exactas (insumos independientes). Var(XY) = (sx2+mx2)(sy2+my2) - mx2*my2.
    Devuelve (media, varianza, {termino: varianza}). Sirve de oraculo del Monte Carlo."""
    var_t, media = {}, 0.0
    for i, d in modelo["insumos"].items():
        mm, sm = d["merma"]
        mt, st = d["tarifa"]
        mx, vx = d["q"] * (1 + mm), (d["q"] * sm) ** 2          # X = Q(1+M)
        media += mx * mt
        var_t[i] = (vx + mx ** 2) * (st ** 2 + mt ** 2) - (mx * mt) ** 2
    ht, sh = modelo["tiempo"]
    rt, sr = modelo["tasa"]
    media += ht * rt
    var_t["TIEMPO"] = (sh ** 2 + ht ** 2) * (sr ** 2 + rt ** 2) - (ht * rt) ** 2
    return media, sum(var_t.values()), var_t


def simular(modelo, n, rng):
    """Monte Carlo: devuelve (lista de costos, {termino: lista de contribuciones})."""
    contrib = {t: [] for t in list(modelo["insumos"]) + ["TIEMPO"]}
    costos = []
    for _ in range(n):
        tot = 0.0
        for i, d in modelo["insumos"].items():
            m = rng.gauss(*d["merma"])
            t = rng.gauss(*d["tarifa"])
            v = d["q"] * (1 + m) * t
            contrib[i].append(v)
            tot += v
        v = rng.gauss(*modelo["tiempo"]) * rng.gauss(*modelo["tasa"])
        contrib["TIEMPO"].append(v)
        costos.append(tot + v)
    return costos, contrib


def _cuantil(xs_ordenados, q):
    pos = q * (len(xs_ordenados) - 1)
    lo = int(math.floor(pos))
    hi = min(lo + 1, len(xs_ordenados) - 1)
    return xs_ordenados[lo] + (pos - lo) * (xs_ordenados[hi] - xs_ordenados[lo])


def _varianza(xs):
    return _media_sd(xs)[1] ** 2


def cvar95(costos):
    """Media de las k = ceil(0.05 n) corridas de mayor costo (k >= 1). Cola superior: el riesgo es pagar de mas."""
    k = max(1, int(math.ceil(0.05 * len(costos))))
    return sum(sorted(costos, reverse=True)[:k]) / k


def prob_supera(costos, umbral):
    """Fraccion de corridas con costo ESTRICTAMENTE mayor que el umbral."""
    return sum(1 for c in costos if c > umbral) / len(costos)


def _umbral_de(umbral, modelo):
    if umbral is None:
        return None
    if isinstance(umbral, dict):
        u = umbral.get(modelo)
    else:
        u = umbral
    if u is None:
        return None
    if isinstance(u, bool) or not isinstance(u, (int, float)) or u != u:
        raise ValueError("umbral de %s no numerico: %r" % (modelo, u))
    return float(u)


def ejecutar(extracto, parametros):
    par = dict(PARAMETROS)
    par.update(parametros or {})
    n = int(par["n_sim"])
    if n < 100 or not 0 < par["nivel"] < 1:
        raise ValueError("n_sim < 100 o nivel fuera de (0, 1)")
    rng = random.Random(par["semilla"])
    filas, modelos = [], preparar(extracto, par)
    umbral = par.get("umbral")
    if isinstance(umbral, dict):
        ajenos = sorted(set(umbral) - set(modelos))
        if ajenos:
            raise ValueError("umbral para modelos inexistentes: %s" % ", ".join(map(str, ajenos)))
    cola = []                                    # L-3: filas nuevas, van DESPUES de todas las actuales
    for nom in sorted(modelos):
        mod = modelos[nom]
        costos, contrib = simular(mod, n, rng)
        ord_ = sorted(costos)
        a = (1 - par["nivel"]) / 2
        media = sum(costos) / n
        filas.append(_fila(nom, "COSTO_ESTIMADO", media, _cuantil(ord_, a), _cuantil(ord_, 1 - a), par["nivel"], mod["unidad"]))
        vt = {t: _varianza(x) for t, x in contrib.items()}
        s = sum(vt.values())
        for t in sorted(vt):
            peso = vt[t] / s if s > 0 else 0.0
            filas.append(_fila("%s|%s" % (nom, t), "PESO_VARIANZA", peso, peso, peso, None, "fraccion"))
        cv = cvar95(costos)
        cola.append(_fila(nom, "CVAR95", cv, cv, cv, None, mod["unidad"]))   # [ARQ] misma unidad que COSTO_ESTIMADO
        u = _umbral_de(umbral, nom)
        if u is not None:
            pr = prob_supera(costos, u)
            cola.append(_fila(nom, "PROB_SUPERA", pr, pr, pr, None, "fraccion"))
    return filas + cola
