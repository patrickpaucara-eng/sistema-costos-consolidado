# -*- coding: utf-8 -*-
"""Familias de componentes con lógica de bloques (DBCA) — sección G de docs/diseno/OLA2_REVISION_DUENO.md (decisión 25-nov).
La familia es el «bloque»: dentro de ella las cantidades por unidad varían al azar (normal) pero el efecto es el mismo.
Estadística en Python puro (el EXE no lleva scipy): beta incompleta regularizada → t de Student y F de Fisher."""
import math


def _betacf(a, b, x):
    m_max, eps = 300, 3e-14
    qab, qap, qam = a + b, a + 1, a - 1
    c, d = 1.0, 1 - qab * x / qap
    d = 1 / (d if abs(d) > 1e-300 else 1e-300); h = d
    for m in range(1, m_max + 1):
        m2 = 2 * m; aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1 + aa * d; d = 1 / (d if abs(d) > 1e-300 else 1e-300); c = 1 + aa / c if abs(c) > 1e-300 else 1 + aa / 1e-300; h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1 + aa * d; d = 1 / (d if abs(d) > 1e-300 else 1e-300); c = 1 + aa / c if abs(c) > 1e-300 else 1 + aa / 1e-300; dl = d * c; h *= dl
        if abs(dl - 1) < eps: break
    return h


def betai(a, b, x):
    """Beta incompleta regularizada I_x(a, b)."""
    if x <= 0: return 0.0
    if x >= 1: return 1.0
    bt = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log(1 - x))
    return bt * _betacf(a, b, x) / a if x < (a + 1) / (a + b + 2) else 1 - bt * _betacf(b, a, 1 - x) / b


def t_cdf(t, v):
    p = 0.5 * betai(v / 2, 0.5, v / (v + t * t))
    return 1 - p if t > 0 else p


def t_cuantil(q, v):
    lo, hi = -1e3, 1e3
    for _ in range(200):
        mid = (lo + hi) / 2
        if t_cdf(mid, v) < q: lo = mid
        else: hi = mid
    return (lo + hi) / 2


def f_pvalor(f, d1, d2):
    return betai(d2 / 2, d1 / 2, d2 / (d2 + d1 * f)) if f > 0 else 1.0


def receta(valores, confianza=0.95):
    """Receta aprendida de un inductor: media, desviación e intervalo de predicción al 95 % para una unidad nueva."""
    x = [float(v) for v in valores]; n = len(x)
    if n < 3: raise ValueError("Se necesitan al menos 3 órdenes de la familia")
    m = sum(x) / n; s = math.sqrt(sum((v - m) ** 2 for v in x) / (n - 1))
    h = t_cuantil(1 - (1 - confianza) / 2, n - 1) * s * math.sqrt(1 + 1 / n)
    return {"media": m, "desviacion": s, "n": n, "minimo": m - h, "maximo": m + h}


def pertenece(cantidades, familia):
    """¿El componente pertenece a la familia? Cada inductor debe caer en su intervalo de predicción."""
    fuera = [k for k, v in cantidades.items() if k not in familia or not familia[k]["minimo"] <= float(v) <= familia[k]["maximo"]]
    return {"pertenece": not fuera, "fuera_de_rango": fuera}


def anova(a, b):
    """ANOVA de un factor entre dos familias (mismo inductor). p > 0.05 → mismo efecto → sugerir fusionar."""
    grupos = [[float(v) for v in a], [float(v) for v in b]]; todos = grupos[0] + grupos[1]; N, k = len(todos), 2
    m = sum(todos) / N
    ssb = sum(len(g) * (sum(g) / len(g) - m) ** 2 for g in grupos)
    ssw = sum(sum((v - sum(g) / len(g)) ** 2 for v in g) for g in grupos)
    f = (ssb / (k - 1)) / (ssw / (N - k)) if ssw else float("inf")
    p = f_pvalor(f, k - 1, N - k) if math.isfinite(f) else 0.0
    return {"F": f, "p": p, "mismo_efecto": p > 0.05}


def explotar(familia_receta, unidades):
    """Componentes × receta → cantidades por actividad/insumo (con su rango al 95 %)."""
    return {k: {"cantidad": r["media"] * unidades, "minimo": max(0.0, r["minimo"]) * unidades, "maximo": r["maximo"] * unidades}
            for k, r in familia_receta.items()}
