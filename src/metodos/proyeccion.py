# -*- coding: utf-8 -*-
"""MÉTODO · PROYECCION_OT (OT-082, ARQUITECTURA_V4_1 §7.8 ALG-07). Cotización proyectada.
Propone la tarifa (LES_TAR, 6 decimales) de cada línea desde el último periodo real, agrega la línea CIF con
LES_CAN = EST_CAN y devuelve EST_CST, costo unitario proyectado, costo máximo admisible y estado DENTRO/EXCEDIDO.
Función pura, Decimal de 28 dígitos. PRECISION=INTERNA (parámetro) entrega valores internos; sin ella, publicados."""
from decimal import Decimal as D, ROUND_HALF_UP

FICHA = dict(nombre="PROYECCION_OT", version="1.0", vigente_desde="2026-01-01", eje="PROYECCION", objetivo="ESTIMADO",
    que_hace="Propone las tarifas de una cotización, calcula su costo proyectado y lo compara con el costo máximo admisible.",
    formula="LES_TAR: MD = CPU de cierre; PD = Σ costo PD / Σ medida P2; SD = precio última compra; CIF = Σ C_CIF / Σ OBJ_CAN "
            "de las OT terminadas de la familia. EST_CST = Σ LES_CAN × LES_TAR; máximo = EST_PRECIO × (1 − EST_RENT)",
    fuente="ARQUITECTURA_V4_1 §7.8 ALG-07, §13.4", supuestos="Cantidades por recurso las entrega el presupuestador",
    limites="R-40: sin OT terminada de la familia se rechaza; no calcula precios")
CONSUME = {"(sin MCD) ESTIMACION": ["NUMERO", "EMPRESA", "PERIODO", "COMPONENTE", "CANTIDAD", "ESTADO", "OBJETO", "EST_PRECIO", "EST_RENT"],
           "(sin MCD) LIN_ESTIM": ["ESTIMACION", "RECURSO", "CANTIDAD", "TARIFA", "LES_TAR_ORIGEN"],
           "(sin MCD) OBJETO": ["NUMERO", "EMPRESA", "COMPONENTE", "CANTIDAD", "ESTADO", "TIPO"]}
DEPENDE_DE = {"REPARTO_ETAPAS": [("ORIGEN", "ELEMENTO"), ("ORIGEN", "MONTO"), ("ORIGEN", "MEDIDA_TOTAL"),
                                 ("ORIGEN", "CPU_CIERRE"), ("ORIGEN", "CRITERIO"), ("ORIGEN", "PRECIO_ULTIMA_COMPRA")],
              "LIQUIDACION_OT": [("OBJETO", "C_CIF")]}
PARAMETROS = [dict(id="PER", etq="Periodo", tipo="texto"), dict(id="EMP", etq="Empresa", tipo="texto"),
              dict(id="PRECISION", etq="Precisión", tipo="texto", opciones=["PUBLICADA", "INTERNA"], defecto="PUBLICADA")]
ENTREGA = {"LIN_ESTIM": ["LES_TAR"], "ESTIMACION": ["EST_CST", "CU_PROYECTADO", "COSTO_MAXIMO", "ESTADO", "DIFERENCIA_EXCESO"]}


def _q(x, n):
    return D(str(x)).quantize(D(1).scaleb(-n), rounding=ROUND_HALF_UP)


def _previos(previos, nombre):
    return previos.get(nombre) or []


def _tarifas_origen(previos):
    """De REPARTO_ETAPAS: {recurso: dict(elemento, cpu, monto, medida, criterio, precio)}."""
    o = {}
    for t, clave, con, val in (tuple(f[:4]) for f in _previos(previos, "REPARTO_ETAPAS")):
        if t == "ORIGEN":
            o.setdefault(str(clave), {})[con] = val
    return o


def _tasa_familia(hechos, previos, comp, cod_cot):
    cif = {str(f[1]): D(str(f[3])) for f in _previos(previos, "LIQUIDACION_OT") if f[0] == "OBJETO" and f[2] == "C_CIF"}
    tot_c = tot_q = D(0)
    for o in hechos.get("(sin MCD) OBJETO", []):
        if o.get("ESTADO") == "T" and o.get("COMPONENTE") == comp and str(o["NUMERO"]) in cif:
            tot_c += cif[str(o["NUMERO"])]
            tot_q += D(str(o["CANTIDAD"]))
    if tot_q <= 0:
        raise ValueError(f"R-40: No hay base histórica para el producto {comp}. Ingrese la tasa de CIF en la línea CIF "
                         "(queda marcada MANUAL) o espere el cierre de una OT de esa familia.")
    return tot_c / tot_q


def _tarifa_linea(rec, org, linea):
    if rec not in org:
        raise ValueError(f"{linea['ESTIMACION']}|{rec}: el recurso no tiene base en el último periodo real")
    d = org[rec]
    el = d.get("ELEMENTO")
    if el == "MD":
        return D(str(d["CPU_CIERRE"]))
    if el == "SD":
        return D(str(d["PRECIO_ULTIMA_COMPRA"]))
    raise ValueError(f"{rec}: elemento {el!r} no admitido como línea de cotización")


def _pd_tarifa(org):
    monto = med = D(0)
    for d in org.values():
        if d.get("ELEMENTO") == "PD":
            monto += D(str(d["MONTO"]))
            med += D(str(d["MEDIDA_TOTAL"]))
    if med <= 0:
        raise ValueError("no hay medida de PD en el último periodo real")
    return monto / med


def _cotizar(hechos, previos, num):
    cab = next((e for e in hechos["(sin MCD) ESTIMACION"] if str(e["NUMERO"]) == str(num)), None)
    if cab is None:
        raise ValueError(f"no existe la cotización {num}")
    org = _tarifas_origen(previos)
    lineas, filas = [], []
    for l in sorted((x for x in hechos["(sin MCD) LIN_ESTIM"] if str(x["ESTIMACION"]) == str(num)), key=lambda x: str(x["RECURSO"])):
        rec = str(l["RECURSO"])
        if rec == "CIF":
            continue
        if rec == "PD":
            tar = _pd_tarifa(org)
        else:
            tar = _tarifa_linea(rec, org, l)
        lineas.append((rec, D(str(l["CANTIDAD"])), _q(tar, 6)))
    manual = next((l for l in hechos["(sin MCD) LIN_ESTIM"] if str(l["ESTIMACION"]) == str(num) and l["RECURSO"] == "CIF"
                   and l.get("TARIFA") not in (None, "")), None)
    cantidad = D(str(cab["CANTIDAD"]))
    if manual:
        tasa = D(str(manual["TARIFA"]))
    else:
        tasa = _q(_tasa_familia(hechos, previos, cab["COMPONENTE"], num), 6)
    lineas.append(("CIF", cantidad, tasa))
    return cab, cantidad, lineas, bool(manual)


def calcular(hechos, parametros, previos):
    interna = (parametros or {}).get("PRECISION") == "INTERNA"
    res, expl = [], []
    for cab in sorted(hechos["(sin MCD) ESTIMACION"], key=lambda e: str(e["NUMERO"])):
        num = str(cab["NUMERO"])
        _, cantidad, lineas, _m = _cotizar(hechos, previos, num)
        est = sum((q * t for _, q, t in lineas), D(0))
        cu = est / cantidad
        maximo = D(str(cab["EST_PRECIO"])) * (1 - D(str(cab["EST_RENT"])))
        dentro = cu <= maximo
        for rec, q, t in lineas:
            res.append(("LIN_ESTIM", f"{num}|{rec}", "LES_TAR", float(t)))
        res += [("ESTIMACION", num, "EST_CST", float(est) if interna else float(_q(est, 2))),
                ("ESTIMACION", num, "CU_PROYECTADO", float(cu) if interna else float(_q(cu, 6))),
                ("ESTIMACION", num, "COSTO_MAXIMO", float(maximo) if interna else float(_q(maximo, 6))),
                ("ESTIMACION", num, "ESTADO", "DENTRO" if dentro else "EXCEDIDO")]
        if not dentro:
            res.append(("ESTIMACION", num, "DIFERENCIA_EXCESO", float((cu - maximo) * cantidad) if interna
                        else float(_q((cu - maximo) * cantidad, 2))))
        expl.append(f"{num}: EST_CST = Σ LES_CAN × LES_TAR = {_q(est, 6)}; CU = {_q(cu, 6)}; máximo = {_q(maximo, 6)}; "
                    f"{'DENTRO' if dentro else 'EXCEDIDO'}")
    return res, expl


def trazar(hechos, parametros, previos, tipo, clave, concepto):
    """Líneas que componen EST_CST: una por LIN_ESTIM, monto = LES_CAN × LES_TAR. Σ = valor publicado (ALG-09)."""
    if tipo != "ESTIMACION" or concepto != "EST_CST":
        raise ValueError(f"trazar: {tipo}/{concepto} no es trazable en PROYECCION_OT")
    _, cantidad, lineas, _m = _cotizar(hechos, previos, clave)
    partes = {rec: q * t for rec, q, t in lineas}
    total = _q(sum(partes.values(), D(0)), 2)
    red = {k: _q(v, 2) for k, v in partes.items()}
    resid = total - sum(red.values(), D(0))
    if resid != 0:
        for k in sorted(partes, key=lambda k: (-partes[k], k)):
            if red[k] + resid >= 0:
                red[k] += resid
                break
    return [dict(etapa="COTIZACION", origen=rec, destino=str(clave), elemento=rec, criterio="LES_CAN",
                 cantidad_destino=float(q), total_criterio=float(cantidad), tasa=float(t),
                 monto_atribuido=float(red[rec]), hechos_fuente=[f"{clave}|{rec}"]) for rec, q, t in lineas]


CASOS = []
