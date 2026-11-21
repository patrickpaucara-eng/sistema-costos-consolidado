# -*- coding: utf-8 -*-
"""MÉTODO · VALUACIÓN DE INVENTARIOS (plug-in, E-101 + OT-022). Primer componente sacado de la base a tu poder.
CONTRATO
  Consume (por CONCEPTOS, OT-022): movimientos de UN recurso en UN almacén, en orden:
           [{"tipo": "E"|"S", "cantidad": q, "monto": m (solo E)}]
           (en la base: KARDEX / LINEA de T14, T15, T16, T19, T20, T29 — cantidades y montos documentados)
  Entrega: por cada salida {"cantidad", "cu", "monto"} y el saldo final {"cantidad", "valor"}
           (en la base: LINEA.LIN_CU / LIN_MTO de la salida y EXISTENCIA.EXI_CAN / EXI_VAL)
Métodos: promedio_movil (NIC 2 §25, el oficial hoy: ALG-PROM) · peps (NIC 2 §25, alternativa).
Redondeo: 2 decimales, mitad hacia arriba (igual que el motor)."""
from decimal import Decimal as D, ROUND_HALF_UP

from metodos import caso_excel


def _r(x, n=2):
    return float(D(str(x)).quantize(D(1).scaleb(-n), rounding=ROUND_HALF_UP))


def promedio_movil(movs):
    """ALG-01 (§7.3) en Decimal. Entrega floats para los llamadores históricos (publicar, probar_metodos)."""
    can = val = D(0)
    salidas = []
    for m in movs:
        q = D(str(m["cantidad"]))
        if m["tipo"] == "E":
            can += q
            val += D(str(m["monto"]))
        else:
            if q > can + TOL:
                raise ValueError(f"R-50: salida de {q} mayor que la existencia {can}")
            q = min(q, can)
            cu = val / can if can else D(0)
            monto = q * cu
            salidas.append(dict(cantidad=float(q), cu=float(cu), monto=_r(monto)))
            can -= q
            val -= monto
            if can == 0:
                val = D(0)
    return dict(salidas=salidas, saldo=dict(cantidad=float(can), valor=_r(val)))


def peps(movs):
    capas, salidas = [], []                               # capas [cantidad, costo unitario]
    for m in movs:
        if m["tipo"] == "E":
            capas.append([m["cantidad"], m["monto"] / m["cantidad"] if m["cantidad"] else 0.0])
        else:
            falta, monto = m["cantidad"], 0.0
            while falta > 1e-12 and capas:
                usa = min(falta, capas[0][0])
                monto += usa * capas[0][1]
                capas[0][0] -= usa
                falta -= usa
                if capas[0][0] <= 1e-12:
                    capas.pop(0)
            if falta > 1e-12:
                raise ValueError("Salida mayor que la existencia (PEPS no admite saldo negativo)")
            salidas.append(dict(cantidad=m["cantidad"], cu=monto / m["cantidad"], monto=_r(monto)))
    return dict(salidas=salidas, saldo=dict(cantidad=sum(c for c, _ in capas),
                                            valor=_r(sum(c * u for c, u in capas))))


METODOS = {"PROMEDIO_MOVIL": promedio_movil, "PEPS": peps}

# ---------------- FORMATO COMPATIBLE (§7.11, ALG-01): interfaz estándar con calcular() y trazar() ----------------
REDONDEO = "ALG-09"
TOL = D("1e-9")   # ruido de representación binaria de las cantidades cargadas (no es saldo negativo)
FICHA = dict(nombre="VALUACION_PROMEDIO", version="2.0", vigente_desde="2026-01-01", eje="VALUACION", objetivo="REAL",
    que_hace="Valoriza cada salida al costo promedio ponderado de la existencia (recurso, almacén) en ese momento.",
    formula="entrada: SVAL += valor, SCAN += cantidad, CPU = SVAL/SCAN; salida de q: monto = q × CPU, SCAN −= q, "
            "SVAL −= monto; si SCAN = 0 entonces SVAL = 0. Orden (FECHA, EVENTO).",
    fuente="NIC 2 §25; ARQUITECTURA_V4_1 §7.3 ALG-01", supuestos="Movimientos de un recurso en un almacén; Decimal de 28 dígitos",
    limites="R-50: una salida mayor que la existencia se rechaza (no admite saldo negativo)",
    caso="Caso_PROMEDIO_MOVIL_7.xlsx")
CONSUME = {"(sin MCD) KARDEX": ["KDX_EVE", "KDX_LIN", "RECURSO", "ALMACEN", "KDX_CAN", "KDX_VAL"]}
DEPENDE_DE = {}
PARAMETROS = []
ENTREGA = {"SALIDA": ["CU", "MONTO"], "EXISTENCIA": ["CANTIDAD", "VALOR"]}


def _campo(r, *nombres):
    for n in nombres:
        if n in r and r[n] not in (None, ""):
            return r[n]
    return None


def _normalizar(r):
    cant = _campo(r, "CANTIDAD", "KDX_CAN")
    if cant is None:
        raise ValueError(f"movimiento sin cantidad: {r}")
    val = _campo(r, "VALOR", "KDX_VAL")
    return dict(eve=_campo(r, "EVENTO", "KDX_EVE"), lin=_campo(r, "LINEA", "KDX_LIN"),
                fec=_campo(r, "FECHA", "KDX_FEC") or 0, rec=r["RECURSO"], alm=r["ALMACEN"],
                cant=D(str(cant)), val=D(str(val if val is not None else 0)))


def _clave_orden(m):
    return (str(m["fec"]), int(m["eve"]) if str(m["eve"]).lstrip("-").isdigit() else 0, str(m["eve"]),
            int(m["lin"]) if str(m["lin"]).lstrip("-").isdigit() else 0)


def _simular(hechos):
    """Devuelve {(rec, alm): dict(movs=[...], saldo_can, saldo_val, capas)} con Decimal. Orden (FECHA, EVENTO)."""
    grupos = {}
    for r in hechos["(sin MCD) KARDEX"]:
        m = _normalizar(r)
        grupos.setdefault((m["rec"], m["alm"]), []).append(m)
    out = {}
    for (rec, alm) in sorted(grupos, key=lambda k: (str(k[0]), str(k[1]))):
        can = val = D(0)
        capas = {}                                   # código de entrada -> valor aún no consumido
        salidas = []
        for m in sorted(grupos[(rec, alm)], key=_clave_orden):
            cod = f"{m['eve']}-{m['lin']}-{alm}"
            if m["cant"] > 0:
                can += m["cant"]
                val += m["val"]
                capas[cod] = capas.get(cod, D(0)) + m["val"]
            else:
                q = -m["cant"]
                if q > can + TOL:
                    raise ValueError(f"R-50: la salida {cod} de {q} es mayor que la existencia {can} de {rec} en {alm}")
                q = min(q, can)
                cpu = val / can if can else D(0)
                monto = q * cpu
                consumo = {}
                if val != 0:
                    for k in capas:
                        consumo[k] = monto * capas[k] / val
                    for k, v in consumo.items():
                        capas[k] -= v
                can -= q
                val -= monto
                if can == 0:
                    val = D(0)
                    capas = {}
                salidas.append(dict(cod=cod, cantidad=q, cpu=cpu, monto=monto, consumo=consumo))
        out[(rec, alm)] = dict(salidas=salidas, can=can, val=val, capas=capas)
    return out


def calcular(hechos, parametros, previos):
    res, expl = [], []
    for (rec, alm), g in _simular(hechos).items():
        for s in g["salidas"]:
            # V4.1 §4.3: valores internos entre métodos; el redondeo (2 decimales, CU 6) se aplica al publicar (REDONDEO = "ALG-09")
            res += [("SALIDA", s["cod"], "CU", float(s["cpu"])), ("SALIDA", s["cod"], "MONTO", float(s["monto"]))]
        res += [("EXISTENCIA", f"{rec}-{alm}", "CANTIDAD", float(g["can"])),
                ("EXISTENCIA", f"{rec}-{alm}", "VALOR", float(g["val"]))]
        expl.append(f"{rec} en {alm}: {len(g['salidas'])} salidas; saldo {g['can']} por {_r(g['val'])}")
    return res, expl


def _con_residuo(partes, n=2):
    """ALG-09: redondea cada parte y suma el residuo a la de mayor monto bruto (empate: menor código)."""
    cod_ord = sorted(partes, key=lambda k: (-partes[k], str(k)))
    red_ = {k: D(str(_r(v, n))) for k, v in partes.items()}
    resid = D(str(_r(sum(partes.values(), D(0)), n))) - sum(red_.values(), D(0))
    if resid != 0 and cod_ord:
        paso = D(1).scaleb(-n)
        for k in cod_ord:
            if red_[k] + resid >= 0:
                red_[k] += resid
                break
    return red_


def trazar(hechos, parametros, previos, tipo, clave, concepto):
    """Líneas que explican un valor publicado: cada entrada aporta su parte. Σ monto_atribuido = valor publicado (I9)."""
    sim = _simular(hechos)
    n = 6 if concepto == "CU" else 2
    clave = str(clave)
    if tipo == "SALIDA":
        for (rec, alm), g in sim.items():
            for s in g["salidas"]:
                if s["cod"] == clave and concepto in ("MONTO", "CU"):
                    total = s["monto"] if concepto == "MONTO" else s["cpu"]
                    base = s["consumo"] or {s["cod"]: s["monto"]}
                    frac = {k: (v / s["monto"] if s["monto"] else D(1) / len(base)) for k, v in base.items()}
                    partes = {k: total * f for k, f in frac.items()}
                    return _lineas(partes, n, "VALUACION", s["cod"], f"{rec}-{alm}", rec, s["cantidad"],
                                   s["cpu"], concepto)
        raise ValueError(f"trazar: no existe la salida {clave}")
    if tipo == "EXISTENCIA" and concepto in ("VALOR", "CANTIDAD"):
        for (rec, alm), g in sim.items():
            if f"{rec}-{alm}" == clave:
                if concepto == "VALOR":
                    partes = dict(g["capas"]) or {clave: g["val"]}
                    return _lineas(partes, n, "VALUACION", clave, clave, rec, g["can"], D(0), concepto)
                return [dict(etapa="VALUACION", origen=clave, destino=clave, elemento=rec, criterio="CANTIDAD",
                             cantidad_destino=float(g["can"]), total_criterio=float(g["can"]), tasa=1.0,
                             monto_atribuido=float(g["can"]), hechos_fuente=[clave])]
        raise ValueError(f"trazar: no existe la existencia {clave}")
    raise ValueError(f"trazar: {tipo}/{concepto} no es trazable en VALUACION_PROMEDIO")


def _lineas(partes, n, etapa, destino, origen_txt, rec, cantidad, cpu, concepto):
    red_ = _con_residuo(partes, n)
    out = []
    for k in sorted(partes, key=str):
        out.append(dict(etapa=etapa, origen=k, destino=destino, elemento=rec, criterio="COSTO_PROMEDIO",
                        cantidad_destino=float(cantidad), total_criterio=float(cantidad),
                        tasa=float(_r(cpu, 6)), monto_atribuido=float(red_[k]), hechos_fuente=[k]))
    return out


CASOS = caso_excel.cargar(FICHA["caso"]) + [dict(nombre="10 a 2.00 + 10 a 4.00, sale 15",
    hechos={"(sin MCD) KARDEX": [
        dict(KDX_EVE=1, KDX_LIN=1, RECURSO="R", ALMACEN="A", KDX_CAN=10, KDX_VAL=20),
        dict(KDX_EVE=2, KDX_LIN=1, RECURSO="R", ALMACEN="A", KDX_CAN=10, KDX_VAL=40),
        dict(KDX_EVE=3, KDX_LIN=1, RECURSO="R", ALMACEN="A", KDX_CAN=-15, KDX_VAL=0)]},
    parametros={}, previos={}, espera=[("SALIDA", "3-1-A", "MONTO", 45.0), ("EXISTENCIA", "R-A", "VALOR", 15.0)])]
