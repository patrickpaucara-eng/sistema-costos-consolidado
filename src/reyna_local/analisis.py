"""Etapa 3 · Analítica sobre los resultados PUBLICADOS (nunca recalcula costos; lee lo que entregó el ABC por periodo).
- Descriptivo: qué pasó (serie mensual por producto y elemento).
- Diagnóstico: causa raíz de las variaciones del costo unitario (elemento que más explica el cambio contra su historia).
- Relevancia: Pareto de la estructura de costos; «crítico» = lo que acumula hasta el 80 %.
- Predictivo: 6 meses. Determinístico = el método que menos se equivoca fuera de muestra (proveedor PRONÓSTICO existente);
  estocástico = Monte Carlo con semilla remuestreando los errores fuera de muestra del MARGEN → P05 / P50 / P95.
- ESTIMADO (D-8): costo más fiel según la historia, por estadística (pronóstico con banda), NO un estándar.
- Escenarios (qué pasa si) y Monte Carlo de margen, sobre una COPIA de los resultados (la base nunca cambia).
- Prescriptivo: propuestas con impacto en S/ calculado desde la brecha contra la propia historia."""
import math, random
from analitica.proveedores import pronostico as PR

ELEMENTOS = [("MD", "Material directo"), ("PD", "Mano de obra directa"), ("SD", "Servicios directos"), ("CIF", "Costos indirectos de fabricación"),
             ("GAD", "Gastos de administración"), ("GVT", "Gastos de ventas"), ("GFI", "Gastos financieros")]
PARAM_PRON = dict(PR.PARAMETROS)


def _producto(ot):
    """OT-FRENOSA-SW50-2010-07 → SW50 (la orden es mensual; el producto se repite)."""
    partes = str(ot).split("-")
    return partes[2] if len(partes) >= 5 else str(ot)


def serie_producto(por_per, cantidades, productos=None):
    """{producto: [(periodo, {elemento: total}, cantidad)]} en orden de periodo. El producto de cada orden viene del libro
    (OBJETO.OBJ_PRO); sin él se deduce del código (compatibilidad)."""
    out = {}
    for p in sorted(por_per):
        for o, v in por_per[p].items():
            out.setdefault((productos or {}).get(o) or _producto(o), []).append((p, {e: float(v.get(e, 0)) for e, _ in ELEMENTOS}, cantidades.get(o, 0.0)))
    return out


def relevancia(totales, umbral=0.80):
    """Pareto: elementos ordenados por importe; crítico mientras el acumulado anterior no supere el umbral."""
    t = sum(v for v in totales.values() if v > 0)
    filas, acum = [], 0.0
    for e, nom in sorted(((e, n) for e, n in ELEMENTOS if totales.get(e, 0) > 0), key=lambda x: -totales[x[0]]):
        pct = totales[e] / t; critico = acum < umbral; acum += pct
        filas.append(dict(elemento=nom, importe=round(totales[e], 2), porcentaje=round(pct, 4), acumulado=round(acum, 4), critico=critico))
    return filas


def diagnostico(series, periodo, umbral=0.05, ventana=6):
    """Por producto: costo unitario del periodo frente al promedio de los `ventana` meses previos. Si la variación supera el
    umbral, la causa raíz es el elemento con mayor contribución a la variación del costo unitario."""
    hall = []
    for prod, pts in sorted(series.items()):
        idx = next((i for i, x in enumerate(pts) if x[0] == periodo), None)
        if idx is None or idx == 0: continue
        prev = pts[max(0, idx - ventana):idx]
        _, el, q = pts[idx]
        if not q: continue
        cu = {e: el[e] / q for e in el}
        base = {e: sum(x[1][e] / x[2] for x in prev if x[2]) / len(prev) for e in el}
        tot, tb = sum(cu.values()), sum(base.values())
        if not tb: continue
        var = (tot - tb) / tb
        contrib = {e: cu[e] - base[e] for e in el}
        causa = max(contrib, key=lambda e: abs(contrib[e]))
        nom = dict(ELEMENTOS)[causa]
        impacto = round((tot - tb) * q, 2)
        if abs(var) >= umbral:
            hall.append(dict(tipo="VARIACION_CU", referencia=prod,
                             mensaje=f"El costo unitario de {prod} varió {var:+.1%} frente a su promedio de {len(prev)} meses "
                                     f"(S/ {tot:,.4f} vs S/ {tb:,.4f}); la causa principal es {nom} ({contrib[causa]:+,.4f} por unidad).",
                             impacto=impacto, causa=causa, variacion=round(var, 4)))
    return hall


def _rutas(y, horizonte, par, n, semilla):
    """Determinístico (pronóstico recursivo con el método elegido) y rutas Monte Carlo (errores fuera de muestra remuestreados)."""
    r = PR._pronosticar_serie(list(y), par)
    modelo = r["usado"]
    pares = PR.origen_movil(list(y), modelo, par)
    errores = [a - b for a, b in pares] or [0.0]
    det, yy = [], list(y)
    for _ in range(horizonte):
        _, v = PR.ajustar(modelo, yy, par); det.append(v); yy.append(v)
    return det, errores, modelo, r


MIN_ERRORES = 3      # errores reales mínimos para estimar la banda de un horizonte


def _errores_horizonte(y, modelo, par, h, m0):
    """Errores reales a h meses: para cada origen t ≥ m0, se ajusta con y[:t], se pronostica recursivamente h pasos y se compara
    con y[t+h-1]."""
    out = []
    for t in range(m0, len(y) - h + 1):
        yy = list(y[:t])
        for _ in range(h):
            _, f = PR.ajustar(modelo, yy, par); yy.append(f)
        out.append(y[t + h - 1] - yy[-1])
    return out


def proyectar(serie_meses, horizonte=6, n=2000, semilla=2010, par=None):
    """serie_meses: [(periodo, ventas, costo_total)] históricos → filas PROYECTADO_DET y PROYECTADO_EST del contrato.
    Determinístico: ventas y costo con el método que menos se equivoca fuera de muestra (cada uno el suyo).
    Estocástico: la banda se calcula sobre el MARGEN con los errores fuera de muestra de su propio pronóstico,
    remuestreados con semilla y acumulados en el horizonte (la incertidumbre crece mes a mes). Así no se rompe la
    correlación natural entre ventas y costo (error de la versión anterior: errores de series distintas desalineados)."""
    par = dict(PARAM_PRON, **(par or {}))
    pers = [p for p, _, _ in serie_meses]
    if len(pers) <= par.get("min_validacion", 6):                  # sin historia suficiente no se valida fuera de muestra: no se inventa
        return [], dict(aviso=f"Historia insuficiente para proyectar ({len(pers)} meses; se requieren al menos 7)")
    v = [x for _, x, _ in serie_meses]; c = [x for _, _, x in serie_meses]; mg = [a - b for a, b in zip(v, c)]
    dv, _, mv, _ = _rutas(v, horizonte, par, n, semilla); dc, _, mc, _ = _rutas(c, horizonte, par, n, semilla)
    _, _, mm_, rm = _rutas(mg, horizonte, par, n, semilla)
    # Banda calibrada por horizonte (tarea 1.4): para cada h, errores reales del pronóstico del MARGEN hecho h meses antes
    # (origen móvil, recursivo). Intervalo conformal: margen ± el error absoluto de rango ⌈(n+1)·0.9⌉ (incluye el sesgo real del
    # modelo; centrarlo subestimaba: 0 de 5 meses cubiertos). Con menos de MIN_ERRORES errores: «no estimable», no se publica.
    # La incertidumbre no disminuye con el horizonte: cada banda contiene a la anterior.
    m0 = max(3, par["min_entrenamiento"] - 2)
    lo_prev = hi_prev = 0.0; errores_h, no_est = [], []
    a, mm = map(int, pers[-1].split("-"))
    filas = []
    for h in range(1, horizonte + 1):
        mm += 1
        if mm > 12: a, mm = a + 1, 1
        per = f"{a}-{mm:02d}"
        det = dv[h - 1] - dc[h - 1]
        filas.append(dict(periodo=per, tipo="PROYECTADO_DET", ventas=round(dv[h - 1], 2), costo_total=round(dc[h - 1], 2), margen=round(det, 2)))
        e = _errores_horizonte(mg, mm_, par, h, m0); errores_h.append(len(e))
        if len(e) < MIN_ERRORES:
            no_est.append(per); continue
        ab = sorted(abs(x) for x in e); k = math.ceil((len(ab) + 1) * 0.90)       # conformal: rango finito-muestral del 90 %
        q = ab[min(k, len(ab)) - 1]                                               # con pocos errores, el mayor observado
        lo, hi = min(-q, lo_prev), max(q, hi_prev); lo_prev, hi_prev = lo, hi
        filas.append(dict(periodo=per, tipo="PROYECTADO_EST", ventas=round(dv[h - 1], 2), costo_total=round(dc[h - 1], 2), margen=round(det, 2),
                          p05=round(det + lo, 2), p50=round(det, 2), p95=round(det + hi, 2)))
    info = dict(modelo_ventas=mv, modelo_costo=mc, modelo_margen=mm_, mase_margen=None if rm["mase"] in (None, math.inf) else round(rm["mase"], 3),
                semilla=semilla, simulaciones=n, metodo_banda="conformal por horizonte (origen móvil, 90 %)",
                errores_por_horizonte=errores_h, banda_no_estimable=no_est)
    return filas, info


def estimado(series, periodo, par=None):
    """Síntesis ESTIMADO: para cada producto, costo unitario por elemento estimado con datos HASTA el mes anterior
    (fuera de muestra), con banda P05–P95 del total. Sirve para medir la variación real − estimado."""
    par = dict(PARAM_PRON, **(par or {}))
    out = {}
    for prod, pts in series.items():
        idx = next((i for i, x in enumerate(pts) if x[0] == periodo), None)
        if idx is None or idx < 7: continue                          # ESTIMADO exige historia validable fuera de muestra (≥ 7 meses)
        hist = pts[:idx]
        el = {}
        for e, _ in ELEMENTOS:
            y = [x[1][e] / x[2] for x in hist if x[2]]
            el[e] = PR._pronosticar_serie(y, par)["valor"] if any(y) else 0.0
        tot = [sum(x[1].values()) / x[2] for x in hist if x[2]]
        r = PR._pronosticar_serie(tot, par)
        out[prod] = dict(cu_elementos=el, cu_total=sum(el.values()), p05=r["p05"] * (sum(el.values()) / r["valor"]) if r["valor"] else r["p05"],
                         p95=r["p95"] * (sum(el.values()) / r["valor"]) if r["valor"] else r["p95"], metodo=r["usado"], mase=r["mase"])
    return out


ESCENARIOS = [("Base", {}), ("Precio del material +10 %", {"precio_material": 1.10}), ("Volumen −10 %", {"volumen": 0.90}),
              ("Salarios +5 %", {"salario": 1.05}), ("Precio de venta +3 %", {"precio_venta": 1.03})]


def margen_escenario(t, f):
    """t: totales del periodo {ventas, MD, PD, SD, CIF, GAD, GVT, GFI}. Reglas: MD y comisiones variables con el volumen;
    MOD, CIF, administración y financieros fijos en el mes (salvo el factor salario sobre MOD); ventas por volumen × precio."""
    vol, pm, pv, sal = f.get("volumen", 1), f.get("precio_material", 1), f.get("precio_venta", 1), f.get("salario", 1)
    ventas = t["ventas"] * vol * pv
    costo = t["MD"] * vol * pm + t["PD"] * sal + t["SD"] * vol + t["CIF"] + t["GAD"] + t["GVT"] * vol * pv + t["GFI"]
    return ventas - costo


def escenarios(t, n=2000, semilla=2010):
    """Determinístico por escenario + Monte Carlo (triangular) de margen y probabilidad de pérdida para cada uno."""
    rng = random.Random(semilla); out = []
    for nombre, f in ESCENARIOS:
        sims = []
        for _ in range(n):
            g = dict(f)
            g["precio_material"] = f.get("precio_material", 1) * rng.triangular(0.95, 1.08, 1.0)
            g["volumen"] = f.get("volumen", 1) * rng.triangular(0.85, 1.10, 1.0)
            g["precio_venta"] = f.get("precio_venta", 1) * rng.triangular(0.97, 1.03, 1.0)
            sims.append(margen_escenario(t, g))
        sims.sort()
        out.append(dict(nombre=nombre, supuestos=f, margen=round(margen_escenario(t, f), 2), margen_p50=round(PR.cuantil(sims, 0.5), 2),
                        margen_p05=round(PR.cuantil(sims, 0.05), 2), margen_p95=round(PR.cuantil(sims, 0.95), 2),
                        prob_perdida=round(sum(1 for s in sims if s < 0) / n, 4)))
    return out


def propuestas(series, periodo, hallazgos, rel):
    """Prescriptivo: brecha contra el promedio de 6 meses de la propia historia (no un estándar), anualizada (× 12).
    Cada propuesta guarda su línea base y su objetivo medibles (producto, elemento, costo unitario actual y objetivo): así la
    analítica autónoma puede medir después si se cumplió."""
    out = []
    def cu(prod, e):
        pts = series.get(prod, []); idx = next((i for i, x in enumerate(pts) if x[0] == periodo), None)
        if idx is None or idx == 0 or not pts[idx][2]: return None
        hist = [x for x in pts[max(0, idx - 6):idx] if x[2]]
        if not hist: return None
        return pts[idx][1][e] / pts[idx][2], sum(x[1][e] / x[2] for x in hist) / len(hist), pts[idx][2]
    for prod in sorted(series):
        v = cu(prod, "MD")
        if not v: continue
        base, ref, q = v; brecha = base - ref        # promedio de 6 meses (no el mejor mes: podría ser atípico)
        if brecha > 0:
            out.append(dict(codigo=f"P-MD-{prod}", descripcion=f"Material de {prod}: volver al costo unitario promedio de los últimos 6 meses "
                            f"(S/ {ref:,.4f}) con compras consolidadas y negociación de precio y flete",
                            impacto_anual=round(brecha * q * 12, 2), plazo="3 meses", responsable="Compras",
                            producto=prod, elemento="MD", cu_base=round(base, 6), cu_objetivo=round(ref, 6), cantidad_mes=q))
    for h in hallazgos:
        if h["impacto"] > 0 and h["causa"] in ("CIF", "PD"):
            v = cu(h["referencia"], h["causa"]) or (None, None, None)
            out.append(dict(codigo=f"P-{h['causa']}-{h['referencia']}", descripcion=f"{h['referencia']}: reducir {dict(ELEMENTOS)[h['causa']]} "
                            "al promedio histórico (programación de la carga, mantenimiento preventivo)",
                            impacto_anual=round(h["impacto"] * 12, 2), plazo="6 meses", responsable="Producción",
                            producto=h["referencia"], elemento=h["causa"], cu_base=v[0] and round(v[0], 6), cu_objetivo=v[1] and round(v[1], 6), cantidad_mes=v[2]))
    return sorted(out, key=lambda p: -p["impacto_anual"])
