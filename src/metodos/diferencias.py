# -*- coding: utf-8 -*-
"""MÉTODO · DIFERENCIAS_OT (OT-082, ARQUITECTURA_V4_1 §7.9 ALG-08). Variaciones por OT terminada con cotización emitida.
Presupuesto flexible: k = OBJ_CAN / EST_CAN; Qe = LES_CAN × k; Pe = LES_TAR. Precio (Pr − Pe) × Qr; cantidad (Qr − Qe) × Pe;
CIF: variación única = C(OT, CIF del periodo) − tasa_fam × OBJ_CAN. Identidad: Σ variaciones = real − estimado flexible.
Real = CTOT. Función pura, Decimal. PRECISION=INTERNA entrega valores internos; sin ella, publicados con residuo ALG-09."""
from decimal import Decimal as D, ROUND_HALF_UP

FICHA = dict(nombre="DIFERENCIAS_OT", version="1.0", vigente_desde="2026-01-01", eje="DIFERENCIAS", objetivo="REAL",
    que_hace="Descompone la diferencia entre el costo real de la OT y su estimado flexible en variaciones de precio y cantidad.",
    formula="precio = (Pr − Pe) × Qr; cantidad = (Qr − Qe) × Pe; CIF = C(OT, CIF periodo) − tasa_fam × OBJ_CAN",
    fuente="ARQUITECTURA_V4_1 §7.9 ALG-08; Horngren caps. 7-8", supuestos="La cotización emitida hace de estándar",
    limites="Solo OT terminadas con cotización emitida (EST_OBJ = OT); IIPP distinta de cero no soportada (ver dudas)")
CONSUME = {"(sin MCD) ESTIMACION": ["NUMERO", "EMPRESA", "PERIODO", "CANTIDAD", "ESTADO", "OBJETO", "EST_CST"],
           "(sin MCD) LIN_ESTIM": ["ESTIMACION", "RECURSO", "CANTIDAD", "TARIFA", "LES_TAR_ORIGEN"],
           "(sin MCD) OBJETO": ["NUMERO", "EMPRESA", "CANTIDAD", "ESTADO", "TIPO"]}
DEPENDE_DE = {"REPARTO_ETAPAS": [("ARISTA", "ELEMENTO"), ("ARISTA", "MEDIDA"), ("ARISTA", "MONTO")],
              "LIQUIDACION_OT": [("OBJETO", "PER_CIF"), ("OBJETO", "CTOT"), ("OBJETO", "INI_MD"), ("OBJETO", "INI_PD"),
                                 ("OBJETO", "INI_SD"), ("OBJETO", "INI_CIF")]}
PARAMETROS = [dict(id="PER", etq="Periodo", tipo="texto"), dict(id="EMP", etq="Empresa", tipo="texto"),
              dict(id="PRECISION", etq="Precisión", tipo="texto", opciones=["PUBLICADA", "INTERNA"], defecto="PUBLICADA")]
ENTREGA = {"OBJETO": ["EST_CST", "REAL", "DIFERENCIA", "VAR_PRECIO_MD", "VAR_CANTIDAD_MD", "VAR_PRECIO_PD", "VAR_CANTIDAD_PD",
                      "VAR_SD", "VAR_CIF", "SUMA_VARIACIONES", "EFECTO_VOLUMEN", "ESTIMADO_FLEXIBLE"]}
VARS = ("VAR_PRECIO_MD", "VAR_CANTIDAD_MD", "VAR_PRECIO_PD", "VAR_CANTIDAD_PD", "VAR_SD", "VAR_CIF")


def _q(x, n=2):
    return D(str(x)).quantize(D(1).scaleb(-n), rounding=ROUND_HALF_UP)


def _liq(previos, obj, con):
    for f in previos.get("LIQUIDACION_OT") or []:
        if f[0] == "OBJETO" and str(f[1]) == obj and f[2] == con:
            return D(str(f[3]))
    return None


def _real_por_elemento(previos, obj):
    """{recurso: dict(el, q, m)} desde las aristas «origen>OBJ» de REPARTO_ETAPAS."""
    a = {}
    for f in previos.get("REPARTO_ETAPAS") or []:
        if f[0] == "ARISTA" and str(f[1]).endswith(">" + obj):
            a.setdefault(str(f[1]).split(">")[0], {})[f[2]] = f[3]
    return a


def _descomponer(hechos, previos, cab):
    obj = str(cab["OBJETO"])
    ot = next((o for o in hechos["(sin MCD) OBJETO"] if str(o["NUMERO"]) == obj), None)
    if ot is None or ot.get("ESTADO") != "T":
        return None
    k = D(str(ot["CANTIDAD"])) / D(str(cab["CANTIDAD"]))
    lin = {str(l["RECURSO"]): l for l in hechos["(sin MCD) LIN_ESTIM"] if str(l["ESTIMACION"]) == str(cab["NUMERO"])}
    arist = _real_por_elemento(previos, obj)
    v = {n: D(0) for n in VARS}
    real = flex = D(0)
    pd_q = pd_m = D(0)
    detalle = {n: {} for n in VARS}
    for rec in sorted(arist):
        d = arist[rec]
        el = d["ELEMENTO"]
        qr, m = D(str(d["MEDIDA"])), D(str(d["MONTO"]))
        real += m
        if el == "PD":
            pd_q += qr
            pd_m += m
            continue
        if rec not in lin:
            raise ValueError(f"{obj}: el recurso {rec} se consumió pero no está en la cotización {cab['NUMERO']}")
        pe, qe = D(str(lin[rec]["TARIFA"])), D(str(lin[rec]["CANTIDAD"])) * k
        pr = m / qr if qr else D(0)
        flex += qe * pe
        vp, vc = (pr - pe) * qr, (qr - qe) * pe
        if el == "MD":
            v["VAR_PRECIO_MD"] += vp; v["VAR_CANTIDAD_MD"] += vc
            detalle["VAR_PRECIO_MD"][rec] = vp; detalle["VAR_CANTIDAD_MD"][rec] = vc
        elif el == "SD":
            v["VAR_SD"] += vp + vc
            detalle["VAR_SD"][rec] = vp + vc
        else:
            raise ValueError(f"{rec}: elemento {el!r} no admitido en variaciones")
    if pd_q:
        pe, qe = D(str(lin["PD"]["TARIFA"])), D(str(lin["PD"]["CANTIDAD"])) * k
        pr = pd_m / pd_q
        flex += qe * pe
        v["VAR_PRECIO_PD"] = (pr - pe) * pd_q
        v["VAR_CANTIDAD_PD"] = (pd_q - qe) * pe
        detalle["VAR_PRECIO_PD"]["PD"] = v["VAR_PRECIO_PD"]; detalle["VAR_CANTIDAD_PD"]["PD"] = v["VAR_CANTIDAD_PD"]
    cif = _liq(previos, obj, "PER_CIF")
    if cif is None:
        raise ValueError(f"{obj}: falta el CIF del periodo (PER_CIF) en LIQUIDACION_OT")
    tasa, qe = D(str(lin["CIF"]["TARIFA"])), D(str(lin["CIF"]["CANTIDAD"])) * k
    flex += qe * tasa
    real += cif
    v["VAR_CIF"] = cif - tasa * D(str(ot["CANTIDAD"]))
    detalle["VAR_CIF"]["CIF"] = v["VAR_CIF"]
    for c in ("INI_MD", "INI_PD", "INI_SD", "INI_CIF"):
        if (_liq(previos, obj, c) or D(0)) != 0:
            raise ValueError(f"{obj}: la IIPP ({c}) distinta de cero no está definida en ALG-08 (ver informes/V41/OT-082_dudas.md)")
    ctot = _liq(previos, obj, "CTOT")
    if ctot is not None and abs(ctot - real) > D("0.000001"):
        raise ValueError(f"{obj}: CTOT {ctot} no cuadra con la suma de sus aristas y CIF {real}")
    real = ctot if ctot is not None else real
    est_cst = D(str(sum((D(str(x["CANTIDAD"])) * D(str(x["TARIFA"])) for x in lin.values()), D(0))))
    return dict(obj=obj, v=v, real=real, flex=flex, est_cst=est_cst, k=k, detalle=detalle)


def _con_residuo(valores, total, n=2):
    red = {c: _q(x, n) for c, x in valores.items()}
    resid = _q(total, n) - sum(red.values(), D(0))
    if resid != 0:
        for c in sorted(valores, key=lambda c: (-abs(valores[c]), c)):
            if red[c] + resid >= 0 or valores[c] < 0:
                red[c] += resid
                break
    return red


def calcular(hechos, parametros, previos):
    interna = (parametros or {}).get("PRECISION") == "INTERNA"
    res, expl = [], []
    for cab in sorted(hechos["(sin MCD) ESTIMACION"], key=lambda e: str(e["NUMERO"])):
        if cab.get("ESTADO") != "E" or not cab.get("OBJETO"):
            continue
        d = _descomponer(hechos, previos, cab)
        if d is None:
            continue
        obj, v = d["obj"], d["v"]
        suma = sum(v.values(), D(0))
        if abs(suma - (d["real"] - d["flex"])) > D("0.000001"):
            raise ValueError(f"{obj}: no se cumple Σ variaciones = real − estimado flexible ({suma} ≠ {d['real'] - d['flex']})")
        efecto = d["flex"] - d["est_cst"]
        f = (lambda x: float(x)) if interna else (lambda x: float(_q(x)))
        if interna:
            pub = {n: float(v[n]) for n in VARS}
            suma_pub = float(suma)
        else:
            r = _con_residuo(v, suma)
            pub = {n: float(r[n]) for n in VARS}
            suma_pub = float(_q(suma))
        res += [("OBJETO", obj, "EST_CST", f(d["est_cst"])), ("OBJETO", obj, "REAL", f(d["real"])),
                ("OBJETO", obj, "DIFERENCIA", f(d["real"] - d["est_cst"]))]
        res += [("OBJETO", obj, n, pub[n]) for n in VARS]
        res += [("OBJETO", obj, "SUMA_VARIACIONES", suma_pub), ("OBJETO", obj, "EFECTO_VOLUMEN", f(efecto)),
                ("OBJETO", obj, "ESTIMADO_FLEXIBLE", f(d["flex"]))]
        expl.append(f"{obj}: k = {d['k']}; Σ variaciones {_q(suma, 6)} = real {_q(d['real'], 6)} − flexible {_q(d['flex'], 6)}")
    return res, expl


def trazar(hechos, parametros, previos, tipo, clave, concepto):
    """Líneas por recurso de una variación (Σ = valor publicado, ALG-09)."""
    if tipo != "OBJETO" or concepto not in VARS:
        raise ValueError(f"trazar: {tipo}/{concepto} no es trazable en DIFERENCIAS_OT")
    for cab in hechos["(sin MCD) ESTIMACION"]:
        if str(cab.get("OBJETO")) == str(clave) and cab.get("ESTADO") == "E":
            d = _descomponer(hechos, previos, cab)
            if d:
                det = d["detalle"][concepto]
                r = _con_residuo(det, d["v"][concepto]) if det else {}
                return [dict(etapa="VARIACION", origen=rec, destino=str(clave), elemento=rec, criterio=concepto,
                             cantidad_destino=1.0, total_criterio=1.0, tasa=float(det[rec]),
                             monto_atribuido=float(r[rec]), hechos_fuente=[f"{rec}>{clave}"]) for rec in sorted(det)]
    raise ValueError(f"trazar: {clave} no tiene cotización emitida y OT terminada")


CASOS = []
