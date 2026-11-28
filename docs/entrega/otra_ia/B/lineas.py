"""Líneas de ticket desde el plan (B4) y desde el estado (B3), para que B8 sea solo `sintesis.sintetizar`.

Decisión del dueño (28-nov): el plan es la base y todo presupuesto es una síntesis de líneas con
ticket, recurso, monto, fecha_devengo, fecha_caja, clase y estado (ver sintesis.py). Este módulo no
calcula nada nuevo: traduce a líneas lo que ya decidió la calculadora o lo que ya registró eventos.py.
No modifica calculadora.py ni eventos.py.

    from lineas import lineas_desde_plan, lineas_desde_estado, mensual
    res = calculadora.plan(datos)
    L = lineas_desde_plan(res, mensual("2027-01"), datos)
    sintesis.sintetizar(L, "Presupuesto de efectivo")

Reglas de lineas_desde_plan (siguen los momentos de pago de la calculadora, BITACORA_B supuesto 5):
  OT              INGRESO por el precio: devengo = periodo en que se termina (la calculadora entrega al
                  terminar), caja = ese periodo + plazo_cobro. Multa por tardanza = EGRESO aparte con
                  las mismas fechas (la calculadora la descuenta del cobro).
  Conversión      EGRESO horas × costo_hora: devengo = caja = periodo de producción (la calculadora no
                  tiene plazo de pago).
  Material        EGRESO por lotes PEPS: cada lote (stock inicial, llegada comprometida, compra del plan)
                  se paga al llegar (caja) y se devenga cuando se consume (devengo). Lo no consumido al
                  final se devenga en T+1 (inventario final). El stock inicial se pagó antes del plan:
                  fecha_caja = periodo hoy−1, estado «ejecutado».
  Préstamo        FINANCIAMIENTO entrada en t; devolución e interés = FINANCIAMIENTO salida en t+1
                  (devengo = caja = t+1, igual que estados_proyectados). deuda_inicial: salida en «hoy».
  Inversión       INVERSION por su costo: devengo = periodo de instalación, caja = periodo_pago.
  Externos        cobros/pagos ya comprometidos (flujos_externos): INGRESO si > 0, EGRESO si < 0, caja en
                  su periodo y devengo en hoy−1 (la calculadora dice que no mueven la utilidad).
  Estado          «programado» lo que decide el plan; «comprometido» lo que ya venía comprometido en los
                  datos (llegadas, externos, deuda inicial, inversión aprobada); «ejecutado» el stock
                  inicial y la inversión instalada o en uso.
  Montos 0        no generan línea (p. ej. OT de reproceso con precio 0).
"""
from __future__ import annotations

import os
import re
import sys
from collections import defaultdict, deque
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sintesis as S  # noqa: E402
from sintesis import LineaInvalida  # noqa: E402

TOL = 1e-6


# ----------------------------------------------------------------------------- calendario
def mensual(inicio):
    """Periodo 1 = el mes «AAAA-MM»; cada periodo es un mes. Devuelve t -> 'AAAA-MM-01' (vale para t ≤ 0 y t > T)."""
    if not (isinstance(inicio, str) and re.match(r"^\d{4}-(0[1-9]|1[0-2])$", inicio)):
        raise LineaInvalida(f"El inicio del calendario debe ser AAAA-MM; llegó «{inicio}».")
    a, m = map(int, inicio.split("-"))

    def fecha(t):
        k = a * 12 + (m - 1) + (int(t) - 1)
        return f"{k // 12:04d}-{k % 12 + 1:02d}-01"
    return fecha


def _calendario(cal):
    if callable(cal):
        return cal
    if isinstance(cal, str):
        return mensual(cal)
    if isinstance(cal, dict):
        def fecha(t):
            if t not in cal:
                raise LineaInvalida(f"El calendario no tiene fecha para el periodo {t}; hacen falta también "
                                    "hoy−1 (lo previo al plan) y T+1 (lo que cae después del horizonte).")
            return str(cal[t])
        return fecha
    raise LineaInvalida("El calendario debe ser «AAAA-MM» (mensual), un dict {periodo: 'AAAA-MM-DD'} o una función.")


def _nueva(lineas, ticket, recurso, monto, devengo, caja, clase, estado, **extra):
    monto = round(float(monto), 6)
    if monto <= TOL:
        return
    linea = dict(ticket=ticket, recurso=recurso, monto=monto, fecha_devengo=devengo, fecha_caja=caja,
                 clase=clase, estado=estado, **{k: v for k, v in extra.items() if v is not None})
    lineas.append(S.validar(linea))


# ----------------------------------------------------------------------------- (a) desde el plan
def lineas_desde_plan(salida_calculadora, calendario, datos):
    """Líneas del plan óptimo. `datos` es el mismo dict que recibió calculadora.plan(): la salida no trae
    precio, plazo de cobro, costo por hora ni costo del material, así que se leen de ahí normalizados
    con calculadora._leer (los mismos valores por defecto que usó la calculadora)."""
    import calculadora as C
    res = salida_calculadora
    if not isinstance(res, dict) or not res.get("factible"):
        msg = res.get("mensaje", "") if isinstance(res, dict) else ""
        raise LineaInvalida(f"El plan no es factible: no hay líneas que sintetizar. {msg}".strip())
    D = C._leer(datos)
    f = _calendario(calendario)
    T, hoy, P = D["T"], D["hoy"], D["P"]
    ots = {o["id"]: o for o in D["ots"]}
    L = []

    consumo = defaultdict(float)
    for p in res["programa"]:
        o = ots.get(p["ot"])
        if o is None:
            raise LineaInvalida(f"La OT {p['ot']} del programa no está en los datos: ¿son los datos de otro plan?")
        t, r = p["periodo"], p["recurso"]
        _nueva(L, o["id"], "Venta", o["precio"], f(t), f(t + o["pc"]), "INGRESO", "programado",
               centro=r, cantidad=o["q"])
        _nueva(L, o["id"], "Multa por tardanza", p["multa"], f(t), f(t + o["pc"]), "EGRESO", "programado", centro=r)
        _nueva(L, o["id"], r, o["hu"][r] * o["q"] * D["recursos"][r]["costo_hora"], f(t), f(t), "EGRESO",
               "programado", centro=r, cantidad=o["hu"][r] * o["q"])
        for m, u in o["mu"].items():
            consumo[m, t] += u * o["q"]

    compras = res.get("compras", {})
    for m, md in D["materiales"].items():
        lotes = deque()
        if md["stock"] > TOL:
            lotes.append([md["stock"], md["costo"], hoy - 1, "ejecutado", f"STOCK {m}"])
        for t in P:
            if md["llegadas"].get(t, 0.0) > TOL:
                lotes.append([md["llegadas"][t], md["costo"], t, "comprometido", f"LLEGADA {m} p{t}"])
            q = compras.get(m, {}).get(t, 0.0)
            if q > TOL:
                lotes.append([q, md["costo_compra"], t, "programado", f"COMPRA {m} p{t}"])
            falta = consumo[m, t]
            while falta > TOL:
                if not lotes:
                    raise LineaInvalida(f"En el periodo {t} se consumen {falta:.4f} de {m} que no tienen lote: "
                                        "el plan no cuadra con R2.")
                lote = lotes[0]
                usa = min(falta, lote[0])
                _nueva(L, lote[4], m, usa * lote[1], f(t), f(lote[2]), "EGRESO", lote[3], cantidad=usa)
                lote[0] -= usa
                falta -= usa
                if lote[0] <= TOL:
                    lotes.popleft()
        for q, costo, tc, est, tk in lotes:                       # inventario final: se devenga después del plan
            _nueva(L, tk, m, q * costo, f(T + 1), f(tc), "EGRESO", est, cantidad=q)

    fin = res.get("financiamiento", {})
    for t in P:
        x = float(fin.get(t, 0.0))
        if x > TOL:
            tk = f"PRESTAMO p{t}"
            _nueva(L, tk, "Préstamo", x, f(t), f(t), "FINANCIAMIENTO", "programado", sentido="entrada")
            _nueva(L, tk, "Devolución de préstamo", x, f(t + 1), f(t + 1), "FINANCIAMIENTO", "programado",
                   sentido="salida")
            _nueva(L, tk, "Interés", D["tasa"][t] * x, f(t + 1), f(t + 1), "FINANCIAMIENTO", "programado",
                   sentido="salida")
    if D["deuda0"] > TOL:
        _nueva(L, "DEUDA INICIAL", "Devolución de préstamo", D["deuda0"], f(hoy), f(hoy), "FINANCIAMIENTO",
               "comprometido", sentido="salida")
        _nueva(L, "DEUDA INICIAL", "Interés", D["deuda0"] * D["tasa"][hoy], f(hoy), f(hoy), "FINANCIAMIENTO",
               "comprometido", sentido="salida")

    elegidas = set(res.get("inversiones_elegidas", []))
    est_inv = {"propuesto": "programado", "aprobado": "comprometido", "instalado": "ejecutado", "en uso": "ejecutado"}
    for k in D["invs"]:
        if k["id"] in elegidas:
            _nueva(L, k["id"], k["id"], k["costo"], f(k["periodo"]), f(k["pago"]), "INVERSION",
                   est_inv.get(k["estado"], "programado"), centro=k["recurso"])

    for t in P:
        x = D["ext"][t]
        if abs(x) > TOL:
            _nueva(L, f"EXTERNO p{t}", "Flujo externo", abs(x), f(hoy - 1), f(t), "INGRESO" if x > 0 else "EGRESO",
                   "comprometido")
    return L


# ----------------------------------------------------------------------------- (b) desde el estado
_EST_OT = {"propuesto": "programado", "comprometido": "comprometido", "en ejecución": "comprometido",
           "terminado": "ejecutado"}
_EST_IN = {"propuesto": "programado", "aprobado": "comprometido", "instalado": "ejecutado", "en uso": "ejecutado"}


def _d(v, que):
    if isinstance(v, date):
        return v
    if isinstance(v, str):
        try:
            return date.fromisoformat(v)
        except ValueError:
            pass
    raise LineaInvalida(f"{que}: «{v}» no es una fecha AAAA-MM-DD.")


def lineas_desde_estado(estado, costo_material=None, plazo_cobro_dias=None, plazo_pago_dias=None,
                        incluir_propuestos=False):
    """Líneas de los tickets de un eventos.EstadoPlan con su estado (programado, comprometido, ejecutado).

    costo_material   {material: S/ por unidad}: el ticket COMPRA no trae monto.
    plazo_cobro_dias / plazo_pago_dias: si no se pasan, se buscan como parámetro del estado
                     (EstadoPlan(parametros={"plazo_cobro_dias": 30, ...})). Si hacen falta y no están, se
                     rechaza: nunca se asume 0.
    incluir_propuestos: los propuestos son lo que el plan programa; por defecto no se repiten aquí
                     (ya salen de lineas_desde_plan). Cancelados: sin línea, salvo lo ya recibido de una compra.
    """
    def plazo(valor, nombre):
        if valor is None:
            valor = estado.valor_vigente(nombre)
        if valor is None:
            raise LineaInvalida(f"Falta «{nombre}»: páselo a lineas_desde_estado o regístrelo como parámetro "
                                "del estado (no se asume 0).")
        return timedelta(days=int(valor))

    L = []
    for tid in sorted(estado.tickets):
        t = estado.tickets[tid]
        tipo, est = t["tipo"], t["estado"]
        if est == "propuesto" and not incluir_propuestos:
            continue
        if tipo == "OT":
            el = _EST_OT.get(est)
            if el is None:
                continue
            if t.get("precio") is None:
                raise LineaInvalida(f"{tid}: la OT no tiene precio; no se puede armar su ingreso.")
            if not t.get("precio"):
                continue
            fd = t.get("fin") or t.get("fecha_entrega")
            if fd is None:
                raise LineaInvalida(f"{tid}: la OT no tiene fecha de entrega ni de fin.")
            fd = _d(fd, tid)
            _nueva(L, tid, "Venta", t["precio"], fd.isoformat(), (fd + plazo(plazo_cobro_dias, "plazo_cobro_dias")).isoformat(),
                   "INGRESO", el, centro=t.get("recurso"), cantidad=t.get("cantidad"))
        elif tipo == "COMPRA":
            m = t.get("material")
            if est == "cancelado" and not t.get("recibido"):
                continue
            if not costo_material or m not in costo_material:
                raise LineaInvalida(f"{tid}: falta el costo por unidad de «{m}» en costo_material.")
            if t.get("fecha_llegada") is None:
                raise LineaInvalida(f"{tid}: la compra no tiene fecha de llegada.")
            fd = _d(t["fecha_llegada"], tid)
            fc = (fd + plazo(plazo_pago_dias, "plazo_pago_dias")).isoformat()
            rec = t.get("recibido", 0) or 0
            pend = 0 if est in ("recibido", "cancelado") else t["cantidad"] - rec
            _nueva(L, tid, m, rec * costo_material[m], fd.isoformat(), fc, "EGRESO", "ejecutado", cantidad=rec)
            _nueva(L, tid, m, pend * costo_material[m], fd.isoformat(), fc, "EGRESO",
                   "programado" if est == "propuesto" else "comprometido", cantidad=pend)
        elif tipo == "FINANCIAMIENTO":
            if t.get("fecha_toma") is None or t.get("fecha_pago") is None:
                raise LineaInvalida(f"{tid}: el financiamiento «{est}» necesita fecha de toma y fecha de pago.")
            ft, fp = _d(t["fecha_toma"], tid).isoformat(), _d(t["fecha_pago"], tid).isoformat()
            e_toma = "programado" if est == "propuesto" else "ejecutado"
            e_pago = {"propuesto": "programado", "tomado": "comprometido", "pagado": "ejecutado"}[est]
            if est == "pagado":
                interes = t.get("interes_pagado", 0.0)
            else:
                if t.get("tasa") is None:
                    raise LineaInvalida(f"{tid}: sin tasa no se puede programar el interés.")
                interes = t["monto"] * t["tasa"]                     # S: un periodo, como la calculadora
            _nueva(L, tid, "Préstamo", t["monto"], ft, ft, "FINANCIAMIENTO", e_toma, sentido="entrada")
            _nueva(L, tid, "Devolución de préstamo", t["monto"], fp, fp, "FINANCIAMIENTO", e_pago, sentido="salida")
            _nueva(L, tid, "Interés", interes, fp, fp, "FINANCIAMIENTO", e_pago, sentido="salida")
        elif tipo == "INVERSIÓN":
            if t.get("fecha") is None or t.get("costo") is None:
                raise LineaInvalida(f"{tid}: la inversión necesita costo y fecha.")
            fd = _d(t["fecha"], tid).isoformat()
            _nueva(L, tid, t.get("activo") or tid, t["costo"], fd, fd, "INVERSION", _EST_IN[est],
                   centro=t.get("recurso"))
    return L
