# -*- coding: utf-8 -*-
"""OT-020 · Proveedor OPTIMIZAR (mezcla de productos con capacidad por centro). Contrato común de OT-017.
Apoyo a la DECISIÓN (Horngren cap. 12, restricciones); no calcula un costo: usa costos para decidir. Grupo PRESCRIPTIVO.

max Σ m_i x_i   s.a.   Σ_i h_ij x_i <= cap_j  (capacidad práctica del centro j)    x_i <= dem_i (demanda máxima)    x >= 0
Entrada (extracto): por producto `P:<id>`: MARGEN_UNITARIO, DEMANDA_MAXIMA;
  por (producto, centro) clave `P:<id>|C:<id>`: HORAS_UNIDAD;  por centro `C:<id>`: CAPACIDAD_PRACTICA.
  Si falta cualquiera -> ValueError (sin restricciones inventadas).
Salida: PLAN_OPTIMO (por producto), MARGEN_TOTAL, PRECIO_SOMBRA y HOLGURA (por centro, y por demanda `P:<id>|DEMANDA`).
Usa scipy.optimize.linprog (HiGHS) si existe; si no, un simplex propio (regla de Bland). Ambos coinciden (ver pruebas).
Puro y determinista."""
FICHA = {
    "nombre": "OPTIMIZACION", "version": "1.0", "familia": "OPTIMIZACION",
    "pregunta": "¿Qué mezcla de productos maximiza el margen dentro de la capacidad práctica y cuánto vale una hora más de cada centro?",
    "consume": ["MARGEN_UNITARIO", "DEMANDA_MAXIMA", "HORAS_UNIDAD", "CAPACIDAD_PRACTICA"],
    "produce": ["PLAN_OPTIMO", "MARGEN_TOTAL", "PRECIO_SOMBRA", "HOLGURA"],
    "semilla": False,
}
EPS = 1e-9


def _simplex_max(c, A, b):
    """max c.x s.a. A x <= b (b >= 0), x >= 0. Tableau con holguras, regla de Bland. Devuelve (x, obj, duales)."""
    m, n = len(A), len(c)
    T = [list(map(float, A[i])) + [1.0 if j == i else 0.0 for j in range(m)] + [float(b[i])] for i in range(m)]
    z = [-float(v) for v in c] + [0.0] * m + [0.0]
    base = [n + i for i in range(m)]
    for _ in range(10000):
        col = next((j for j in range(n + m) if z[j] < -EPS), None)
        if col is None:
            break
        filas = [(T[i][-1] / T[i][col], base[i], i) for i in range(m) if T[i][col] > EPS]
        if not filas:
            raise ValueError("problema no acotado")
        _, _, r = min(filas)
        p = T[r][col]
        T[r] = [v / p for v in T[r]]
        for i in range(m):
            if i != r and abs(T[i][col]) > 0:
                f = T[i][col]; T[i] = [a - f * bb for a, bb in zip(T[i], T[r])]
        f = z[col]; z = [a - f * bb for a, bb in zip(z, T[r])]
        base[r] = col
    x = [0.0] * n
    for i, bj in enumerate(base):
        if bj < n:
            x[bj] = T[i][-1]
    return x, z[-1], [z[n + i] for i in range(m)]


def resolver(c, A, b, motor="auto"):
    """Devuelve (x, objetivo, duales) con motor 'scipy' o 'simplex'."""
    if any(v < 0 for v in b):
        raise ValueError("capacidad o demanda negativa")
    if motor in ("auto", "scipy"):
        try:
            from scipy.optimize import linprog
            res = linprog([-v for v in c], A_ub=A, b_ub=b, bounds=[(0, None)] * len(c), method="highs")
            if res.status == 3:
                raise ValueError("problema no acotado")
            if res.status != 0:
                raise ValueError(f"sin solución: {res.message}")
            return [float(v) for v in res.x], float(-res.fun), [float(-v) for v in res.ineqlin.marginals]
        except ImportError:
            if motor == "scipy":
                raise
    return _simplex_max(c, A, b)


def ejecutar(extracto, parametros):
    par = parametros or {}
    dat = {}
    for f in extracto:
        for k in ("clave", "concepto", "valor"):
            if f.get(k) is None:
                raise ValueError(f"fila sin '{k}': {f}")
        kk = (f["concepto"], f["clave"])
        if kk in dat:
            raise ValueError(f"dato duplicado {kk}")
        dat[kk] = float(f["valor"])
    prods = sorted(k for (c, k) in dat if c == "MARGEN_UNITARIO")
    centros = sorted(k for (c, k) in dat if c == "CAPACIDAD_PRACTICA")
    if not prods or not centros:
        raise ValueError("faltan productos (MARGEN_UNITARIO) o centros (CAPACIDAD_PRACTICA)")
    A, b, nombres = [], [], []
    for cen in centros:
        fila = []
        for p in prods:
            if ("HORAS_UNIDAD", f"{p}|{cen}") not in dat:
                raise ValueError(f"falta HORAS_UNIDAD de {p}|{cen}")
            fila.append(dat[("HORAS_UNIDAD", f"{p}|{cen}")])
        A.append(fila); b.append(dat[("CAPACIDAD_PRACTICA", cen)]); nombres.append(cen)
    for i, p in enumerate(prods):
        if ("DEMANDA_MAXIMA", p) not in dat:
            raise ValueError(f"falta DEMANDA_MAXIMA de {p}")
        A.append([1.0 if j == i else 0.0 for j in range(len(prods))]); b.append(dat[("DEMANDA_MAXIMA", p)])
        nombres.append(f"{p}|DEMANDA")
    c = [dat[("MARGEN_UNITARIO", p)] for p in prods]
    x, obj, y = resolver(c, A, b, par.get("motor", "auto"))
    out = [{"clave": p, "concepto": "PLAN_OPTIMO", "valor": xi, "p05": xi, "p95": xi, "conf": None, "unidad": "u"} for p, xi in zip(prods, x)]
    out.append({"clave": "TOTAL", "concepto": "MARGEN_TOTAL", "valor": obj, "p05": obj, "p95": obj, "conf": None, "unidad": "S/"})
    for i, nom in enumerate(nombres):
        usado = sum(A[i][j] * x[j] for j in range(len(prods)))
        out.append({"clave": nom, "concepto": "PRECIO_SOMBRA", "valor": y[i], "p05": y[i], "p95": y[i], "conf": None, "unidad": "S/u"})
        out.append({"clave": nom, "concepto": "HOLGURA", "valor": b[i] - usado, "p05": b[i] - usado, "p95": b[i] - usado, "conf": None, "unidad": "u"})
    return out
