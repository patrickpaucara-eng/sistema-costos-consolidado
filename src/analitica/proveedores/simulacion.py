# -*- coding: utf-8 -*-
"""OT-020 · Proveedor SIMULAR (qué pasa si sobre lo REAL, con Monte Carlo y semilla). Contrato común de OT-017/E-158.

Entrada (extracto, filas canónicas {fecha, entidad, clave, concepto, valor, unidad}):
  por producto (clave `P:<id>`): PRECIO_VENTA, VOLUMEN (vendido), COSTO_VARIABLE_UNIT (de producción),
                                 VOLUMEN_PRODUCIDO (unidades producidas en el periodo),
                                 COSTO_VARIABLE_VENTA_UNIT (opcional: comisiones, fletes; si falta vale 0 y se declara)
  COSTO_FIJO_PRODUCCION  (se suman todos; se absorbe en las unidades producidas: es DATO, no supuesto)
  COSTO_FIJO_PERIODO     (administración y ventas: NO entra en el margen bruto)
Parámetros (nada fijo en el código):
  semilla, n          (obligatorios: reproducible y con tamaño dado)
  producido_igual_vendido  bool, defecto False. Si falta VOLUMEN_PRODUCIDO: False -> error explícito;
                      True -> «producido = vendido» DESPUÉS de aplicar los factores de volumen (queda en `detalle`)
  vendido_sobre_producido  bool, defecto False. Si en algún producto lo vendido supera lo producido y no hay dato de
                      inventario inicial: False -> ValueError; True -> supuesto declarado: inventario inicial
                      suficiente, valuado a la tasa del periodo (queda en `detalle`)
  escenario           {eje: factor | {clave: factor}}   qué pasa si (determinista)
  incertidumbre       {eje: [min, moda, max]}  factor multiplicativo triangular (Montgomery/PERT, §8d: sin medida
                      ni historia se trata como incertidumbre); un sorteo por eje y corrida.
  ejes: precio, volumen, volumen_producido, costo_variable, costo_variable_venta, costo_fijo_produccion,
        costo_fijo_periodo, costo_fijo (= ambos fijos)
Definiciones (Horngren cap. 9): contribución = Σ q_vendida (p − cv − cvv) (TODOS los variables, incluidos los de venta);
  margen bruto por absorción = Σ q_vendida (p − cv) − CF_prod · Q_vendida/Q_producida (no resta los variables de venta
  ni los gastos fijos del periodo); resultado operativo = margen bruto − cvv·q − CF_periodo; efecto inventario = CF_prod (Q_prod − Q_vend)/Q_prod
  (fijo diferido en inventario; resultado por costeo variable = resultado operativo − efecto inventario).
Salida: por concepto la fila de la media (P05/P95, conf = 0.90 nominal o None sin incertidumbre) y `<concepto>|EE`
  (error estándar de la media); `detalle` (opcional) con base determinista, n y supuestos.
OT-100 (L-4, números aleatorios comunes; estrategia inspirada en Oria Chavarría 2026):
  comparar            {nombre: escenario} (mismos ejes que `escenario`; cada uno REEMPLAZA al escenario base al evaluarse).
                      En cada corrida se usan los MISMOS multiplicadores sorteados para la base y para cada escenario
                      (no se sortea nada más: la secuencia del generador no cambia). Filas nuevas al final, por nombre y
                      concepto: clave = <nombre>, `<concepto>|DIF` (media de escenario − base, P05/P95 de la diferencia) y
                      `<concepto>|DIF_EE` (error estándar de la diferencia pareada)."""
import math
import random

FICHA = {
    "nombre": "SIMULACION", "version": "1.2", "familia": "SIMULACION",
    "pregunta": "¿Qué pasa con el margen de contribución, el margen bruto por absorción y el resultado operativo si cambian precio, volumen, mezcla o costos, y con qué intervalo?",
    "consume": ["PRECIO_VENTA", "VOLUMEN", "VOLUMEN_PRODUCIDO", "COSTO_VARIABLE_UNIT", "COSTO_VARIABLE_VENTA_UNIT", "COSTO_FIJO_PRODUCCION", "COSTO_FIJO_PERIODO"],
    "produce": ["MARGEN_CONTRIBUCION", "MARGEN_ABSORCION", "RESULTADO_OPERATIVO", "EFECTO_INVENTARIO", "<concepto>|EE", "<concepto>|DIF", "<concepto>|DIF_EE"],
    "semilla": True,
}
EJES = ("precio", "volumen", "volumen_producido", "costo_variable", "costo_variable_venta", "costo_fijo_produccion", "costo_fijo_periodo", "costo_fijo")
CONCEPTOS = ("MARGEN_CONTRIBUCION", "MARGEN_ABSORCION", "RESULTADO_OPERATIVO", "EFECTO_INVENTARIO")
NIVEL = 0.90  # P05-P95


def _factor(spec, eje, clave):
    v = (spec or {}).get(eje, 1.0)
    if isinstance(v, dict):
        return float(v.get(clave, 1.0))
    return float(v)


def _leer(extracto, producido_igual_vendido):
    prod, cf_prod, cf_per = {}, 0.0, 0.0
    hay_prod = hay_per = False
    for f in extracto:
        for c in ("clave", "concepto", "valor"):
            if f.get(c) is None:
                raise ValueError(f"fila sin '{c}': {f}")
        c = f["concepto"]
        if c in ("PRECIO_VENTA", "VOLUMEN", "COSTO_VARIABLE_UNIT", "VOLUMEN_PRODUCIDO", "COSTO_VARIABLE_VENTA_UNIT"):
            d = prod.setdefault(f["clave"], {})
            if c in d:
                raise ValueError(f"dato duplicado {f['clave']}/{c}")
            d[c] = float(f["valor"])
        elif c == "COSTO_FIJO_PRODUCCION":
            cf_prod += float(f["valor"]); hay_prod = True
        elif c == "COSTO_FIJO_PERIODO":
            cf_per += float(f["valor"]); hay_per = True
    if not prod:
        raise ValueError("sin productos en el extracto")
    supuestos, sin_venta = [], []
    for k, d in prod.items():
        faltan = {"PRECIO_VENTA", "VOLUMEN", "COSTO_VARIABLE_UNIT"} - set(d)
        if faltan:
            raise ValueError(f"producto {k}: faltan {sorted(faltan)}")
        if "VOLUMEN_PRODUCIDO" not in d:
            if not producido_igual_vendido:
                raise ValueError(f"producto {k}: falta VOLUMEN_PRODUCIDO (o declare el parámetro producido_igual_vendido=True)")
            d["VOLUMEN_PRODUCIDO"] = d["VOLUMEN"]
            d["_asumido"] = True   # producido = vendido DESPUÉS de los factores (ver `margenes`)
            supuestos.append(f"{k}: producido = vendido (parámetro producido_igual_vendido)")
        if "COSTO_VARIABLE_VENTA_UNIT" not in d:
            d["COSTO_VARIABLE_VENTA_UNIT"] = 0.0
            sin_venta.append(k)
    if not hay_prod:
        raise ValueError("falta COSTO_FIJO_PRODUCCION: sin él no hay margen de absorción")
    if not hay_per:
        raise ValueError("falta COSTO_FIJO_PERIODO: sin él no hay resultado operativo")
    if sin_venta:
        supuestos.append(f"COSTO_VARIABLE_VENTA_UNIT ausente en {', '.join(sorted(sin_venta))}: se toma 0")
    return prod, cf_prod, cf_per, supuestos


def margenes(prod, cf_prod, cf_per, esc, mult, vendido_sobre_producido=False):
    """esc: escenario determinista; mult: {eje: factor sorteado}.
    Devuelve {contribución, margen bruto por absorción, resultado operativo, efecto inventario}."""
    contrib_prod = cvv_total = qv = qp = 0.0
    for k, d in prod.items():
        p = d["PRECIO_VENTA"] * _factor(esc, "precio", k) * mult.get("precio", 1.0)
        q = d["VOLUMEN"] * _factor(esc, "volumen", k) * mult.get("volumen", 1.0)
        cv = d["COSTO_VARIABLE_UNIT"] * _factor(esc, "costo_variable", k) * mult.get("costo_variable", 1.0)
        cvv = d["COSTO_VARIABLE_VENTA_UNIT"] * _factor(esc, "costo_variable_venta", k) * mult.get("costo_variable_venta", 1.0)
        # producido asumido = vendido: se iguala DESPUÉS de aplicar los factores de volumen
        qpi = q if d.get("_asumido") else d["VOLUMEN_PRODUCIDO"] * _factor(esc, "volumen_producido", k) * mult.get("volumen_producido", 1.0)
        if q > qpi + 1e-9 and not vendido_sobre_producido:
            raise ValueError(f"producto {k}: lo vendido ({q:g}) supera lo producido ({qpi:g}) y no hay dato de inventario inicial "
                             "(declare el parámetro vendido_sobre_producido=True para asumir inventario inicial suficiente)")
        contrib_prod += (p - cv) * q
        cvv_total += cvv * q
        qv += q
        qp += qpi
    if qp <= 0:
        raise ValueError("el volumen producido total debe ser > 0 (no hay base para absorber el fijo)")
    cfp = cf_prod * _factor(esc, "costo_fijo_produccion", None) * _factor(esc, "costo_fijo", None) \
        * mult.get("costo_fijo_produccion", 1.0) * mult.get("costo_fijo", 1.0)
    cfe = cf_per * _factor(esc, "costo_fijo_periodo", None) * _factor(esc, "costo_fijo", None) \
        * mult.get("costo_fijo_periodo", 1.0) * mult.get("costo_fijo", 1.0)
    absorbido = cfp * qv / qp
    mb = contrib_prod - absorbido            # margen bruto: sin variables de venta ni gastos del periodo
    return {"MARGEN_CONTRIBUCION": contrib_prod - cvv_total, "MARGEN_ABSORCION": mb,
            "RESULTADO_OPERATIVO": mb - cvv_total - cfe, "EFECTO_INVENTARIO": cfp - absorbido}


def _cuantil(xs, q):
    s = sorted(xs)
    h = (len(s) - 1) * q
    lo = int(math.floor(h)); hi = min(lo + 1, len(s) - 1)
    return s[lo] + (h - lo) * (s[hi] - s[lo])


def ejecutar(extracto, parametros):
    par = parametros or {}
    for obligatorio in ("semilla", "n"):
        if par.get(obligatorio) is None:
            raise ValueError(f"falta el parámetro '{obligatorio}'")
    n = int(par["n"])
    if n < 2:
        raise ValueError("n debe ser >= 2")
    esc = par.get("escenario") or {}
    inc = par.get("incertidumbre") or {}
    for e in list(esc) + list(inc):
        if e not in EJES:
            raise ValueError(f"eje desconocido: {e}")
    comparar = par.get("comparar") or {}
    if not isinstance(comparar, dict):
        raise ValueError("comparar debe ser {nombre: escenario}")
    for nom, ce in comparar.items():
        if not isinstance(ce, dict):
            raise ValueError(f"comparar[{nom}] debe ser un escenario {{eje: factor | {{clave: factor}}}}")
        for e in ce:
            if e not in EJES:
                raise ValueError(f"eje desconocido en comparar[{nom}]: {e}")
    for e, tri in inc.items():
        if len(tri) != 3 or not (tri[0] <= tri[1] <= tri[2]):
            raise ValueError(f"incertidumbre[{e}] debe ser [min, moda, max] con min<=moda<=max")
    prod, cf_prod, cf_per, supuestos = _leer(extracto, bool(par.get("producido_igual_vendido", False)))
    vsp = bool(par.get("vendido_sobre_producido", False))
    if vsp:
        supuestos.append("vendido > producido permitido: se asume inventario inicial suficiente, valuado a la tasa del periodo (parámetro vendido_sobre_producido)")
    if any(d.get("_asumido") for d in prod.values()) and ("volumen_producido" in esc or "volumen_producido" in inc
                                                          or any("volumen_producido" in ce for ce in comparar.values())):
        raise ValueError("el eje volumen_producido no aplica a productos con producido = vendido (supuesto declarado)")
    base = margenes(prod, cf_prod, cf_per, esc, {}, vsp)
    rng = random.Random(par["semilla"])
    xs = {c: [] for c in CONCEPTOS}
    nombres = sorted(comparar)
    difs = {nom: {c: [] for c in CONCEPTOS} for nom in nombres}
    for _ in range(n):
        mult = {e: rng.triangular(t[0], t[2], t[1]) for e, t in sorted(inc.items())}
        m = margenes(prod, cf_prod, cf_per, esc, mult, vsp)
        for c in CONCEPTOS:
            xs[c].append(m[c])
        for nom in nombres:                      # L-4: mismos multiplicadores (CRN), sin sorteos nuevos
            me = margenes(prod, cf_prod, cf_per, comparar[nom], mult, vsp)
            for c in CONCEPTOS:
                difs[nom][c].append(me[c] - m[c])
    out = []
    for conc in CONCEPTOS:
        v = xs[conc]
        media = sum(v) / n
        sd = math.sqrt(sum((x - media) ** 2 for x in v) / (n - 1))
        ee = sd / math.sqrt(n)
        if not inc:
            p05 = p95 = base[conc]
        else:
            p05, p95 = _cuantil(v, 0.05), _cuantil(v, 0.95)
        out.append({"clave": "TOTAL", "concepto": conc, "valor": media, "p05": p05, "p95": p95,
                    "conf": NIVEL if inc else None, "unidad": "S/",
                    "detalle": {"base_determinista": base[conc], "n": n, "supuestos": list(supuestos),
                                "ee_relativo": (ee / abs(media)) if media else None}})
        out.append({"clave": "TOTAL", "concepto": f"{conc}|EE", "valor": ee, "p05": ee, "p95": ee,
                    "conf": None, "unidad": "S/"})
    for nom in nombres:
        base_e = margenes(prod, cf_prod, cf_per, comparar[nom], {}, vsp)
        for conc in CONCEPTOS:
            v = difs[nom][conc]
            media = sum(v) / n
            ee = math.sqrt(sum((x - media) ** 2 for x in v) / (n - 1)) / math.sqrt(n)
            if not inc:
                p05 = p95 = base_e[conc] - base[conc]
            else:
                p05, p95 = _cuantil(v, 0.05), _cuantil(v, 0.95)
            out.append({"clave": nom, "concepto": f"{conc}|DIF", "valor": media, "p05": p05, "p95": p95,
                        "conf": NIVEL if inc else None, "unidad": "S/"})
            out.append({"clave": nom, "concepto": f"{conc}|DIF_EE", "valor": ee, "p05": ee, "p95": ee,
                        "conf": None, "unidad": "S/"})
    return out
