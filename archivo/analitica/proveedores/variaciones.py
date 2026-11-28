# -*- coding: utf-8 -*-
"""OT-019 · Proveedor VARIACIONES estimado vs. real (Horngren cap. 7: precio, cantidad, mezcla y rendimiento; Montgomery: Shewhart y EWMA).
Descompone REAL - ESTIMADO en precio, cantidad (eficiencia), mezcla, rendimiento, volumen y, en los centros,
gasto fijo, capacidad (ocio, por causa) y eficiencia fija. La division del CIF fijo es el analisis de 3 variaciones
(presupuesto, capacidad ociosa, eficiencia) de Polimeni, Fabozzi y Adelberg, Contabilidad de costos (costos estandar):
gasto = real - presupuesto; capacidad = tasa*(Hn-Hr); eficiencia = tasa*(Hr-Hp). Signo: + = desfavorable (el real cuesta mas).
Las partes DEBEN sumar el total (1e-6): si no cuadra lanza ValueError, nunca crea un residuo «otros».
No escribe nada: devuelve filas (las variaciones no son hechos, R42). Puro: sin archivos, hora ni azar.

Extracto (fila canonica {fecha, entidad, clave, concepto, valor, unidad}):
  Por insumo, clave=<orden>|<insumo>: CANT_REAL, PRECIO_REAL, CANT_UNIT_EST (por unidad de producto), PRECIO_EST
  Por orden, clave=<orden>: UNID_REAL, UNID_PRESUP (presupuesto estatico)
  Por centro, clave=<centro>: CIF_FIJO_REAL, CIF_FIJO_PRESUP, HORAS_NORMALES, HORAS_REALES, HORAS_PERMITIDAS
  Ocio por causa (E-142), concepto OCIO_CAPACIDAD, clave=CENTRO:<c>|CAUSA:<cod>: valor en dinero; sin filas -> CAUSA:SIN_REGISTRO
  Cartas, clave=<serie>, una fila por periodo: SERIE_VARIACION
Salida: centros con clave CENTRO:<c> y CENTRO:<c>|CAUSA:<cod> (E-142). Limites Shewhart en filas <serie>|LCI/LC/LCS (fijos).
Limites EWMA en filas <serie>|<fecha>|LCI/LC/LCS: son los de varianza variable, sigma_z(t)=sigma*sqrt(lam/(2-lam)*(1-(1-lam)^(2t))),
EXACTAMENTE los que se aplican a FUERA_DE_CONTROL|EWMA (Montgomery cap. 9). Unidad: la de las filas de entrada (PRECIO_REAL, CIF_FIJO_REAL,
SERIE_VARIACION); si una serie mezcla unidades, ValueError.
Parametros de la carta EWMA: lambda=0.2, L=2.7 dan ARL0 = 238 (calculo propio, cadena de Markov de Brook y Evans, con el limite
asintotico; el mismo calculo con L=2.962 da 500, valor tabulado por Montgomery/Lucas y Saccucci). Se dejan como PARAMETROS:
para ARL0 = 500 usar L_ewma = 2.962."""
import math

FICHA = {
    "nombre": "VARIACIONES", "version": "1.0", "familia": "VARIACION",
    "pregunta": "¿Por qué el costo real difiere del estimado, de qué causa y en qué periodo salió de control?",
    "consume": ["CANT_REAL", "PRECIO_REAL", "CANT_UNIT_EST", "PRECIO_EST", "UNID_REAL", "UNID_PRESUP", "CIF_FIJO_REAL",
                "CIF_FIJO_PRESUP", "HORAS_NORMALES", "HORAS_REALES", "HORAS_PERMITIDAS", "OCIO_CAPACIDAD", "SERIE_VARIACION"],
    "produce": ["VAR_PRECIO", "VAR_CANTIDAD", "VAR_MEZCLA", "VAR_RENDIMIENTO", "VAR_VOLUMEN", "VAR_GASTO_FIJO", "VAR_CAPACIDAD",
                "VAR_EFICIENCIA_FIJA", "VAR_TOTAL", "LIMITE_SHEWHART", "LIMITE_EWMA", "FUERA_DE_CONTROL"],
    "semilla": False,
}
PARAMETROS = {
    "insumos_mezcla": [],   # insumos sustituibles entre si (misma unidad): su cantidad se parte en mezcla y rendimiento
    "tolerancia": 1e-6,     # cuadre partes = total
    "L_shewhart": 3.0,      # Montgomery cap. 6 (limites 3 sigma); sigma = rango movil medio / 1.128
    "lambda_ewma": 0.2, "L_ewma": 2.7,   # Montgomery cap. 9; ARL0 = 238 (L = 2.962 -> 500)
    "n_base": 8,            # periodos iniciales que fijan media y sigma de la carta
}


def _f(clave, concepto, valor, unidad="PEN", p05=None, p95=None):
    v = round(valor, 6)
    return {"clave": clave, "concepto": concepto, "valor": v, "p05": v if p05 is None else round(p05, 6),
            "p95": v if p95 is None else round(p95, 6), "conf": None, "unidad": unidad}


def _agrupar(extracto):
    d = {}
    for f in extracto:
        d.setdefault(f["concepto"], {}).setdefault(f["clave"], []).append(f)
    return d


def _unidad(d, conceptos, claves=None):
    """Unidad unica de las filas de entrada de esos conceptos; error si se mezclan."""
    u = {f["unidad"] for c in conceptos for k, fs in d.get(c, {}).items() if claves is None or k in claves for f in fs}
    if len(u) > 1:
        raise ValueError("unidades mezcladas en %s: %s" % ("/".join(conceptos), sorted(map(str, u))))
    return u.pop() if u else "PEN"


def _uno(d, concepto, clave):
    filas = d.get(concepto, {}).get(clave)
    if not filas:
        raise ValueError("falta %s de %s" % (concepto, clave))
    if len(filas) > 1:
        raise ValueError("%s de %s duplicado" % (concepto, clave))
    return filas[0]["valor"]


def _materiales(d, par):
    out = []
    ordenes = sorted({k.split("|")[0] for k in d.get("CANT_REAL", {})})
    if not ordenes:
        return out
    mon = _unidad(d, ("PRECIO_REAL", "PRECIO_EST"))
    for o in ordenes:
        ur, up = _uno(d, "UNID_REAL", o), _uno(d, "UNID_PRESUP", o)
        ins = sorted(k.split("|", 1)[1] for k in d["CANT_REAL"] if k.split("|")[0] == o)
        v = {}
        for i in ins:
            k = "%s|%s" % (o, i)
            aq, ap, sq, sp = (_uno(d, c, k) for c in ("CANT_REAL", "PRECIO_REAL", "CANT_UNIT_EST", "PRECIO_EST"))
            v[i] = dict(aq=aq, ap=ap, sp=sp, sqf=sq * ur, sqb=sq * up)
        real = sum(x["ap"] * x["aq"] for x in v.values())
        est = sum(x["sp"] * x["sqb"] for x in v.values())
        mez = [i for i in ins if i in par["insumos_mezcla"]]
        aqt, sqt = sum(v[i]["aq"] for i in mez), sum(v[i]["sqf"] for i in mez)
        partes = 0.0
        for i in ins:
            x = v[i]
            filas = {"VAR_PRECIO": (x["ap"] - x["sp"]) * x["aq"], "VAR_VOLUMEN": (x["sqf"] - x["sqb"]) * x["sp"]}
            if i in mez:
                if sqt == 0:
                    raise ValueError("%s: cantidad estimada de la mezcla = 0" % o)
                ideal = aqt * x["sqf"] / sqt
                filas["VAR_MEZCLA"], filas["VAR_RENDIMIENTO"] = (x["aq"] - ideal) * x["sp"], (ideal - x["sqf"]) * x["sp"]
            else:
                filas["VAR_CANTIDAD"] = (x["aq"] - x["sqf"]) * x["sp"]
            for c, val in filas.items():
                out.append(_f("%s|%s" % (o, i), c, val, mon))
                partes += val
        if abs(partes - (real - est)) > par["tolerancia"]:
            raise ValueError("%s: las partes (%.6f) no suman el total (%.6f)" % (o, partes, real - est))
        out.append(_f(o, "VAR_TOTAL", real - est, mon))
    return out


def _centros(d, par):
    out = []
    centros = set(d.get("CIF_FIJO_REAL", {}))
    for k in d.get("OCIO_CAPACIDAD", {}):     # E-142: el ocio no se pierde en silencio
        cen, sep, causa = k.partition("|CAUSA:")
        if not k.startswith("CENTRO:") or not sep or not causa:
            raise ValueError("clave de ocio mal formada: %r (esperada CENTRO:<c>|CAUSA:<cod>)" % k)
        if cen[len("CENTRO:"):] not in centros:
            raise ValueError("ocio %r sin CIF_FIJO_REAL del centro %s: no se puede ubicar ni descartar" % (k, cen[len("CENTRO:"):]))
    mon = _unidad(d, ("CIF_FIJO_REAL", "CIF_FIJO_PRESUP", "OCIO_CAPACIDAD"))
    for c in sorted(centros):
        fr, fp, hn, hr, hp = (_uno(d, k, c) for k in ("CIF_FIJO_REAL", "CIF_FIJO_PRESUP", "HORAS_NORMALES", "HORAS_REALES", "HORAS_PERMITIDAS"))
        if hn <= 0:
            raise ValueError("%s: HORAS_NORMALES debe ser > 0" % c)
        tasa = fp / hn
        cap, partes = tasa * (hn - hr), []
        causas = {k.split("|CAUSA:")[1]: sum(f["valor"] for f in v) for k, v in d.get("OCIO_CAPACIDAD", {}).items()
                  if k.startswith("CENTRO:%s|" % c)}
        if not causas:
            causas = {"SIN_REGISTRO": cap}
        if abs(sum(causas.values()) - cap) > par["tolerancia"]:
            raise ValueError("%s: el ocio por causa (%.6f) no suma la capacidad no usada (%.6f)" % (c, sum(causas.values()), cap))
        partes += [(c, "VAR_GASTO_FIJO", fr - fp), (c, "VAR_EFICIENCIA_FIJA", tasa * (hr - hp))]
        partes += [("CENTRO:%s|CAUSA:%s" % (c, k), "VAR_CAPACIDAD", v) for k, v in sorted(causas.items())]
        out += [_f(k if "|CAUSA:" in k else "CENTRO:" + k, con, v, mon) for k, con, v in partes]
        total = sum(v for _, _, v in partes)
        if abs(total - (fr - tasa * hp)) > par["tolerancia"]:
            raise ValueError("%s: las partes no suman REAL - aplicado" % c)
        out.append(_f("CENTRO:" + c, "VAR_TOTAL", fr - tasa * hp, mon))
    return out


def _cartas(d, par):
    out = []
    for s in sorted(d.get("SERIE_VARIACION", {})):
        fs = sorted(d["SERIE_VARIACION"][s], key=lambda f: f["fecha"])
        uni = _unidad(d, ("SERIE_VARIACION",), (s,))
        y, n0 = [f["valor"] for f in fs], par["n_base"]
        if len(y) <= n0 or n0 < 3:
            raise ValueError("%s: historia insuficiente para la carta (%d <= n_base %d)" % (s, len(y), n0))
        base = y[:n0]
        mu = sum(base) / n0
        sig = sum(abs(base[i] - base[i - 1]) for i in range(1, n0)) / (n0 - 1) / 1.128
        lcs, lci = mu + par["L_shewhart"] * sig, mu - par["L_shewhart"] * sig
        # Los limites NO son un intervalo del valor: filas propias con p05 = p95 = valor y conf = None.
        out += [_f(s + "|" + k, "LIMITE_SHEWHART", v, uni) for k, v in (("LCI", lci), ("LC", mu), ("LCS", lcs))]
        lam, z = par["lambda_ewma"], mu
        for t, f in enumerate(fs, 1):
            z = lam * f["valor"] + (1 - lam) * z
            w = par["L_ewma"] * sig * math.sqrt(lam / (2 - lam) * (1 - (1 - lam) ** (2 * t)))   # varianza variable
            out += [_f("%s|%s|%s" % (s, f["fecha"], k), "LIMITE_EWMA", v, uni) for k, v in (("LCI", mu - w), ("LC", mu), ("LCS", mu + w))]
            if f["valor"] > lcs or f["valor"] < lci:
                out.append(_f("%s|%s|SHEWHART" % (s, f["fecha"]), "FUERA_DE_CONTROL", f["valor"], uni))
            if abs(z - mu) > w:
                out.append(_f("%s|%s|EWMA" % (s, f["fecha"]), "FUERA_DE_CONTROL", z, uni))
    return out


def ejecutar(extracto, parametros):
    par = dict(PARAMETROS)
    par.update(parametros or {})
    d = _agrupar(extracto)
    if not any(c in d for c in ("CANT_REAL", "CIF_FIJO_REAL", "SERIE_VARIACION")):
        raise ValueError("extracto sin datos de variaciones")
    return _materiales(d, par) + _centros(d, par) + _cartas(d, par)
