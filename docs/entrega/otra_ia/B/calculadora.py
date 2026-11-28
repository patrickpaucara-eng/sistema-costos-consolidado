"""
calculadora.py — Módulo B4 (Calculadora del plan) de la especificación MN 02.

Una sola dependencia: PuLP (con su CBC incluido). Python 3.11.

    from calculadora import plan
    resultado = plan(datos)

Restricciones (ids de spec.py):
  R1 Tiempo          horas usadas en cada recurso y periodo <= capacidad (+ la que agrega una inversión)
  R2 Materiales      inventario final = inicial + llegadas + compras - consumo, y nunca negativo
  R3 Asignación      cada OT en un recurso y un periodo (comprometida: obligatoria; propuesta: opcional)
  R4 Fecha entrega   tardanza = máx(0, periodo fin - fecha comprometida); multa por periodo de tardanza
  R5 Secuencia       si (a, b) es incompatible, b no puede ir en el mismo periodo que a ni en el
                     periodo siguiente, en el mismo recurso (supuesto conservador, ver docstring de plan)
  R6 Ventanas        el proveedor solo entrega en ciertos periodos; las paradas de planta se
                     expresan como capacidad 0 en R1
  R7 Caja            pagos del periodo <= caja disponible + financiamiento  (saldo >= 0)
  R8 Caja mínima     saldo >= caja mínima; si no alcanza, se toma préstamo
  R9 Capacidad fut.  si se compra un activo, su capacidad existe desde su periodo de instalación

Además trae cuatro ayudas que reproducen la lógica de otros módulos de la especificación,
para poder probar los 12 casos: desviacion() (B7), parametro_vigente() (B0),
evaluar_inversion() (B6/B8) y estados_proyectados() (B8). No cambian la arquitectura:
solo calculan lo que esos módulos ya declaran como salida.
"""
from __future__ import annotations

import math
import time
from datetime import date

import pulp

EPS = 1e-6          # desempate: a igual valor, preferir lo más temprano / el menor préstamo
TOL = 1e-6

NOMBRES = {
    "R1": "Tiempo (horas <= capacidad)",
    "R2": "Materiales (consumo <= stock + llegadas)",
    "R3": "Asignación (una OT, un recurso)",
    "R4": "Fecha de entrega (tardanza y multa)",
    "R5": "Secuencia (OT incompatibles)",
    "R6": "Ventanas del proveedor",
    "R7": "Caja (pagos <= caja + financiamiento)",
    "R8": "Caja mínima",
    "R9": "Capacidad futura (inversiones)",
}


ESTADOS_OT = ("propuesto", "comprometido", "en ejecución", "terminado", "cancelado")   # spec.TICKETS


class DatoInvalido(Exception):
    pass


# ----------------------------------------------------------------------------- utilidades
def _por_periodo(valor, T, nombre, defecto=None):
    """Convierte un escalar, lista (periodos 1..T) o dict {periodo: valor} en dict 1..T."""
    if valor is None:
        valor = defecto
    if valor is None:
        raise DatoInvalido(f"falta el dato «{nombre}»")
    if isinstance(valor, (int, float)):
        return {t: float(valor) for t in range(1, T + 1)}
    if isinstance(valor, (list, tuple)):
        if len(valor) != T:
            raise DatoInvalido(f"«{nombre}» debe tener {T} valores (uno por periodo); tiene {len(valor)}")
        return {t: float(valor[t - 1]) for t in range(1, T + 1)}
    if isinstance(valor, dict):
        base = float(defecto) if isinstance(defecto, (int, float)) else 0.0
        out = {t: base for t in range(1, T + 1)}
        for k, v in valor.items():
            out[int(k)] = float(v)
        return out
    raise DatoInvalido(f"formato no reconocido para «{nombre}»")


def _leer(datos: dict) -> dict:
    """Valida y normaliza la entrada. Lanza DatoInvalido con un mensaje en castellano."""
    if not isinstance(datos, dict):
        raise DatoInvalido("la entrada debe ser un diccionario")
    T = int(datos.get("periodos", 0))
    if T < 1:
        raise DatoInvalido("«periodos» debe ser un entero >= 1")
    hoy = int(datos.get("hoy", 1))
    if not 1 <= hoy <= T:
        raise DatoInvalido("«hoy» debe estar entre 1 y «periodos»")
    P = list(range(hoy, T + 1))

    recursos = {}
    for r, d in (datos.get("recursos") or {}).items():
        recursos[r] = {
            "cap": _por_periodo(d.get("capacidad"), T, f"capacidad de {r}"),
            "costo_hora": float(d.get("costo_hora", 0.0)),
        }
    materiales = {}
    for m, d in (datos.get("materiales") or {}).items():
        compra = d.get("compra") or {}
        vent = compra.get("ventanas")
        materiales[m] = {
            "stock": float(d.get("stock", 0.0)),
            "costo": float(d.get("costo", 0.0)),
            "llegadas": {int(k): float(v) for k, v in (d.get("llegadas") or {}).items()},
            "compra": bool(compra.get("permitida", False)),
            "ventanas": None if vent is None else {int(x) for x in vent},
            "plazo": int(compra.get("plazo", 0)),
            "costo_compra": float(compra.get("costo", d.get("costo", 0.0))),
        }
    ots, ids = [], set()
    pc_def = int(datos.get("plazo_cobro", 0))
    for o in datos.get("ot") or []:
        oid = str(o["id"])
        if oid in ids:
            raise DatoInvalido(f"la OT {oid} está repetida")
        ids.add(oid)
        estado = o.get("estado", "comprometido")
        if estado not in ESTADOS_OT:
            sug = " ¿Quiso decir «en ejecución»?" if estado == "en curso" else ""
            raise DatoInvalido(f"la OT {oid} tiene estado «{estado}», que no existe; válidos: {ESTADOS_OT}.{sug}")
        if estado in ("terminado", "cancelado"):
            continue                       # ya no consume nada del futuro
        q = float(o.get("cantidad", 1))
        hu = {r: float(h) for r, h in (o.get("horas_unidad") or {}).items()}
        if not hu:
            raise DatoInvalido(f"la OT {oid} no dice en qué recurso se hace")
        for r in hu:
            if r not in recursos:
                raise DatoInvalido(f"la OT {oid} usa el recurso {r}, que no está en «recursos»")
        mu = {m: float(v) for m, v in (o.get("material_unidad") or {}).items()}
        for m in mu:
            if m not in materiales:
                raise DatoInvalido(f"la OT {oid} usa el material {m}, que no está en «materiales»")
        precio = float(o.get("precio", 0.0))
        multa = o.get("multa")
        ots.append({
            "id": oid, "q": q, "hu": hu, "mu": mu, "precio": precio,
            "entrega": int(o.get("entrega", T)),
            "multa": float(multa) if multa is not None else 0.01 * precio,   # S: 1 % del precio por periodo
            "obligatoria": estado in ("comprometido", "en ejecución"),
            "pc": int(o.get("plazo_cobro", pc_def)),
        })
    invs = []
    for k in datos.get("inversiones") or []:
        if k["recurso"] not in recursos:
            raise DatoInvalido(f"la inversión {k['id']} agrega capacidad a {k['recurso']}, que no existe")
        vida = k.get("vida_util")
        invs.append({
            "id": str(k["id"]), "costo": float(k["costo"]), "recurso": k["recurso"],
            "cap": float(k["capacidad"]), "periodo": int(k["periodo"]),
            "pago": int(k.get("periodo_pago", k["periodo"])),
            "fin": T if vida is None else int(k["periodo"]) + int(vida) - 1,
            "vida": None if vida is None else int(vida),
            "residual": float(k.get("valor_residual", 0.0)),
            "estado": k.get("estado", "propuesto"),
        })
    inc = [(str(a), str(b)) for a, b in (datos.get("incompatibles") or [])]

    r_desc = _por_periodo(datos.get("tasa_descuento"), T, "tasa_descuento", 0.0)
    tasa = _por_periodo(datos.get("tasa_prestamo"), T, "tasa_prestamo", 0.0)
    cmin = _por_periodo(datos.get("caja_minima"), T, "caja_minima", 0.0)
    ext = _por_periodo(datos.get("flujos_externos") or {}, T, "flujos_externos", 0.0)
    lim = datos.get("limite_prestamo")
    lim = None if lim is None else _por_periodo(lim, T, "limite_prestamo")
    # factores de descuento contados desde el inicio de «hoy»
    d = {hoy - 1: 1.0}
    for t in range(hoy, T + 2):
        d[t] = d[t - 1] / (1.0 + r_desc.get(t, r_desc[T]))
    return dict(r_ult=r_desc[T], T=T, hoy=hoy, P=P, recursos=recursos, materiales=materiales, ots=ots, invs=invs,
                inc=inc, d=d, tasa=tasa, cmin=cmin, ext=ext, lim=lim,
                caja0=float(datos.get("caja_inicial", 0.0)),
                deuda0=float(datos.get("deuda_inicial", 0.0)),
                tiempo_max=float(datos.get("tiempo_max", 120)))


def _desc(D, s):
    """Factor de descuento del periodo s; más allá de T+1 se extiende con la última tasa."""
    d, T = D["d"], D["T"]
    if s in d:
        return d[s]
    return d[T + 1] / (1.0 + D["r_ult"]) ** (s - T - 1)


# ----------------------------------------------------------------------------- modelo
def _construir(D: dict, relajar: frozenset = frozenset(), elastico: bool = False):
    """Arma el modelo. relajar: familias de restricciones a quitar (análisis de costo).
    elastico: agrega holguras artificiales para diagnosticar infactibilidad."""
    T, P, d = D["T"], D["P"], D["d"]
    hoy = D["hoy"]
    prob = pulp.LpProblem("B4_plan", pulp.LpMaximize)
    V = {}

    # variables de decisión ---------------------------------------------------------------
    z = {}
    for o in D["ots"]:
        for r in o["hu"]:
            for t in P:
                z[o["id"], r, t] = pulp.LpVariable(f"z_{o['id']}_{r}_{t}", cat="Binary")
    y = {k["id"]: pulp.LpVariable(f"inv_{k['id']}", cat="Binary") for k in D["invs"]}
    for k in D["invs"]:
        if k["estado"] in ("aprobado", "instalado", "en uso"):
            prob += y[k["id"]] == 1, f"inv_fija_{k['id']}"
    comp, inv = {}, {}
    for m, md in D["materiales"].items():
        for t in P:
            ok = md["compra"] and t >= hoy + md["plazo"]
            if "R6" not in relajar and md["ventanas"] is not None:
                ok = ok and t in md["ventanas"]
            if ok:
                comp[m, t] = pulp.LpVariable(f"compra_{m}_{t}", lowBound=0)
            inv[m, t] = pulp.LpVariable(f"inv_{m}_{t}", lowBound=None if "R2" in relajar else 0)
    L = {}
    for t in P:
        ub = None if D["lim"] is None else D["lim"][t]
        L[t] = pulp.LpVariable(f"prestamo_{t}", lowBound=0, upBound=ub)
    caja = {t: pulp.LpVariable(f"caja_{t}") for t in P}

    # holguras artificiales (solo en modo diagnóstico)
    S = {}
    def holg(nombre):
        v = pulp.LpVariable(nombre, lowBound=0)
        S[nombre] = v
        return v

    ot_by = {o["id"]: o for o in D["ots"]}

    # R3 Asignación -----------------------------------------------------------------------
    for o in D["ots"]:
        suma = pulp.lpSum(z[o["id"], r, t] for r in o["hu"] for t in P)
        if o["obligatoria"]:
            if elastico:
                prob += suma + holg(f"s_R3_{o['id']}") == 1, f"R3_{o['id']}"
            else:
                prob += suma == 1, f"R3_{o['id']}"
        else:
            prob += suma <= 1, f"R3_{o['id']}"

    # R1 Tiempo + R9 Capacidad futura -----------------------------------------------------
    for r, rd in D["recursos"].items():
        for t in P:
            usado = pulp.lpSum(o["hu"][r] * o["q"] * z[o["id"], r, t] for o in D["ots"] if r in o["hu"])
            extra = pulp.lpSum(k["cap"] * y[k["id"]] for k in D["invs"]
                               if k["recurso"] == r and k["periodo"] <= t <= k["fin"])
            if "R1" in relajar:
                continue
            rhs = rd["cap"][t] + extra
            if elastico:
                rhs = rhs + holg(f"s_R1_{r}_{t}")
            prob += usado <= rhs, f"R1_{r}_{t}"

    # R2 Materiales (y R6 ventanas a través de qué compras existen) -----------------------
    for m, md in D["materiales"].items():
        for t in P:
            previo = md["stock"] if t == hoy else inv[m, t - 1]
            consumo = pulp.lpSum(o["mu"][m] * o["q"] * z[o["id"], r, t]
                                 for o in D["ots"] if m in o["mu"] for r in o["hu"])
            entra = md["llegadas"].get(t, 0.0) + (comp[m, t] if (m, t) in comp else 0)
            if elastico:
                entra = entra + holg(f"s_R2_{m}_{t}")
            prob += inv[m, t] == previo + entra - consumo, f"R2_{m}_{t}"

    # R5 Secuencia ------------------------------------------------------------------------
    if "R5" not in relajar:
        for a, b in D["inc"]:
            if a not in ot_by or b not in ot_by:
                continue
            comunes = set(ot_by[a]["hu"]) & set(ot_by[b]["hu"])
            for r in comunes:
                for t in P:
                    lhs = z[a, r, t] + z[b, r, t] + (z[b, r, t + 1] if t + 1 <= T else 0)
                    if elastico:
                        prob += lhs <= 1 + holg(f"s_R5_{a}_{b}_{r}_{t}"), f"R5_{a}_{b}_{r}_{t}"
                    else:
                        prob += lhs <= 1, f"R5_{a}_{b}_{r}_{t}"

    # flujos de dinero por periodo --------------------------------------------------------
    def cobro_en(o, s):      # ingreso neto de multa que entra en s, por terminar en t = s - pc
        t = s - o["pc"]
        if t not in P:
            return 0
        tard = max(0, t - o["entrega"])
        return (o["precio"] - o["multa"] * tard) * pulp.lpSum(z[o["id"], r, t] for r in o["hu"])

    def conversion_en(t):
        return pulp.lpSum(o["hu"][r] * o["q"] * D["recursos"][r]["costo_hora"] * z[o["id"], r, t]
                          for o in D["ots"] for r in o["hu"])

    def compras_en(t):
        e = 0
        for m, md in D["materiales"].items():
            e += md["llegadas"].get(t, 0.0) * md["costo"]
            if (m, t) in comp:
                e += md["costo_compra"] * comp[m, t]
        return e

    def inversion_en(t):
        return pulp.lpSum(k["costo"] * y[k["id"]] for k in D["invs"] if k["pago"] == t)

    def interes_en(t):       # interés que se paga en t por el préstamo de t-1
        if t == hoy:
            return D["deuda0"] * D["tasa"][t]
        return D["tasa"][t - 1] * L[t - 1]

    def amort_en(t):
        return D["deuda0"] if t == hoy else L[t - 1]

    # R7 / R8 Caja ------------------------------------------------------------------------
    for t in P:
        previo = D["caja0"] if t == hoy else caja[t - 1]
        prob += (caja[t] == previo + pulp.lpSum(cobro_en(o, t) for o in D["ots"]) - conversion_en(t)
                 - compras_en(t) - inversion_en(t) + L[t] - amort_en(t) - interes_en(t) + D["ext"][t]), f"saldo_{t}"
        if "R78" in relajar:
            continue
        lado = D["cmin"][t] if "R8" not in relajar else 0.0
        if elastico:
            prob += caja[t] + holg(f"s_R8_{t}") >= lado, f"R8_{t}"
        else:
            prob += caja[t] >= lado, f"R8_{t}"

    # objetivo: ingresos - costos - multas - intereses, descontado -------------------------
    obj = 0
    for o in D["ots"]:
        for r in o["hu"]:
            for t in P:
                tard = max(0, t - o["entrega"])
                neto = (o["precio"] - o["multa"] * tard) * _desc(D, t + o["pc"])
                obj += (neto - o["hu"][r] * o["q"] * D["recursos"][r]["costo_hora"] * d[t]) * z[o["id"], r, t]
                obj += -EPS * t * z[o["id"], r, t]
    for t in P:
        obj += -compras_en(t) * d[t] - interes_en(t) * d[t] - EPS * L[t]
    obj += -D["tasa"][T] * L[T] * d[T + 1]                        # interés del último préstamo
    for k in D["invs"]:
        obj += (-k["costo"] * d[k["pago"]] + k["residual"] * d[T]) * y[k["id"]]
    if elastico:                                                   # solo minimizar lo que falta
        pesos = {"R1": 1.0, "R2": 1.0, "R3": 1000.0, "R5": 100.0, "R8": 0.01}
        obj = -pulp.lpSum(pesos[n.split("_")[1]] * v for n, v in S.items())
    prob += obj

    V.update(z=z, y=y, comp=comp, inv=inv, L=L, caja=caja, S=S,
             f=dict(cobro=cobro_en, conv=conversion_en, compras=compras_en,
                    inversion=inversion_en, interes=interes_en, amort=amort_en))
    return prob, V


def _resolver(prob, D):
    solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=D["tiempo_max"])
    prob.solve(solver)
    return pulp.LpStatus[prob.status]


def _val(x):
    v = pulp.value(x) if not isinstance(x, (int, float)) else x
    return 0.0 if v is None else float(v)


def _r(x, n=4):
    v = round(x, n)
    return 0.0 if v == 0 else v


# ----------------------------------------------------------------------------- diagnóstico
def _diagnosticar(D):
    prob, V = _construir(D, elastico=True)
    estado = _resolver(prob, D)
    if estado != "Optimal":
        return [{"id": "—", "texto": "Ni siquiera relajando las restricciones se encuentra un plan; revise los datos."}]
    causas = []
    for n, v in V["S"].items():
        x = _val(v)
        if x <= 1e-5:
            continue
        p = n.split("_")
        fam = p[1]
        if fam == "R1":
            r, t = "_".join(p[2:-1]), p[-1]
            causas.append({"id": "R1", "recurso": r, "periodo": int(t), "falta": _r(x, 3),
                           "texto": f"R1 {NOMBRES['R1']}: en {r}, periodo {t}, faltan {x:.2f} h de capacidad."})
        elif fam == "R2":
            m, t = "_".join(p[2:-1]), p[-1]
            md = D["materiales"][m]
            extra = ""
            if md["ventanas"] is not None:
                extra = f" El proveedor solo entrega en los periodos {sorted(md['ventanas'])} (R6)."
            elif not md["compra"]:
                extra = " No hay compra posible de este material en el horizonte."
            causas.append({"id": "R2", "material": m, "periodo": int(t), "falta": _r(x, 3),
                           "texto": f"R2 {NOMBRES['R2']}: faltan {x:.2f} unidades de {m} en el periodo {t}.{extra}"})
        elif fam == "R3":
            oid = "_".join(p[2:])
            causas.append({"id": "R3", "ot": oid,
                           "texto": f"R3/R4: la OT comprometida {oid} no se puede programar dentro del horizonte."})
        elif fam == "R5":
            causas.append({"id": "R5", "texto": f"R5 {NOMBRES['R5']}: la secuencia {p[2]} → {p[3]} no se puede respetar."})
        elif fam == "R8":
            t = p[2]
            causas.append({"id": "R8", "periodo": int(t), "falta": _r(x, 2),
                           "texto": f"R8 {NOMBRES['R8']}: en el periodo {t} faltan S/ {x:,.2f} y el financiamiento está limitado."})
    if not causas:
        causas.append({"id": "—", "texto": "El modelo no encontró plan, pero no se identificó una restricción única."})
    return causas


# ----------------------------------------------------------------------------- función pública
def plan(datos: dict) -> dict:
    """Calcula el plan que maximiza la ganancia descontada respetando R1–R9.

    Entrada (dict). Claves principales; los periodos se numeran 1..periodos:
      periodos, hoy (primer periodo que se puede programar; por defecto 1)
      recursos:   {id: {capacidad: n | [n por periodo], costo_hora}}
      materiales: {id: {stock, costo, llegadas: {periodo: cant},
                        compra: {permitida, ventanas: [periodos], plazo, costo}}}
      ot: [{id, cantidad, horas_unidad: {recurso: h}, material_unidad: {material: u},
            precio (total de la OT), entrega (periodo), multa (S/ por periodo; por defecto 1 % del precio),
            estado ('comprometido' obligatoria | 'propuesto' opcional | 'terminado' se ignora),
            plazo_cobro (periodos)}]
      caja_inicial, caja_minima, tasa_prestamo, tasa_descuento, limite_prestamo (opcional),
      flujos_externos {periodo: monto} (cobros/pagos ya comprometidos: cambian la caja, no la utilidad),
      inversiones: [{id, costo, recurso, capacidad, periodo, vida_util, valor_residual}],
      incompatibles: [(a, b)]  b no puede ir en el mismo periodo que a ni en el siguiente, mismo recurso
      analisis (bool, por defecto True): mide cuánto cuesta cada restricción re-resolviendo sin ella.

    Supuestos del modelo: una OT se hace completa en un periodo y en un solo recurso; el préstamo
    es de un periodo (se toma en t, se devuelve con interés en t+1); la conversión se paga en el
    periodo de producción, el material al llegar, el cobro entra plazo_cobro periodos después.
    """
    t0 = time.perf_counter()
    try:
        D = _leer(datos)
        prob, V = _construir(D)
        estado = _resolver(prob, D)
    except DatoInvalido as e:
        return {"factible": False, "mensaje": f"Dato inválido: {e}.", "restricciones_que_impiden": []}
    except Exception as e:  # nunca devolver traza técnica
        return {"factible": False, "mensaje": f"No se pudo calcular el plan ({type(e).__name__}). Revise los datos.",
                "restricciones_que_impiden": []}

    if estado == "Infeasible":
        causas = _diagnosticar(D)
        return {"factible": False,
                "mensaje": "No hay un plan que cumpla todas las restricciones. " + " ".join(c["texto"] for c in causas),
                "restricciones_que_impiden": causas,
                "tiempo_s": round(time.perf_counter() - t0, 3)}
    if estado != "Optimal":
        return {"factible": False,
                "mensaje": f"La calculadora no terminó (estado: {estado}). Aumente «tiempo_max» o reduzca el horizonte.",
                "restricciones_que_impiden": [], "tiempo_s": round(time.perf_counter() - t0, 3)}

    res = _armar_salida(D, V)
    if datos.get("analisis", True):
        res["restricciones"] = _costo_restricciones(D, res)
    res["tiempo_s"] = round(time.perf_counter() - t0, 3)
    return res


def _armar_salida(D, V):
    T, P, d = D["T"], D["P"], D["d"]
    z, f = V["z"], V["f"]
    programa, tard, no_prog = [], {}, []
    multas = ingresos = conversion = 0.0
    for o in D["ots"]:
        hecho = [(r, t) for r in o["hu"] for t in P if _val(z[o["id"], r, t]) > 0.5]
        if not hecho:
            no_prog.append(o["id"])
            continue
        r, t = hecho[0]
        tt = max(0, t - o["entrega"])
        tard[o["id"]] = tt
        multas += o["multa"] * tt
        ingresos += o["precio"]
        conversion += o["hu"][r] * o["q"] * D["recursos"][r]["costo_hora"]
        programa.append({"ot": o["id"], "recurso": r, "periodo": t, "cantidad": o["q"],
                         "horas": o["hu"][r] * o["q"], "entrega": o["entrega"], "tardanza": tt,
                         "multa": _r(o["multa"] * tt)})
    programa.sort(key=lambda x: (x["periodo"], x["recurso"], x["ot"]))
    fin = {t: _r(_val(V["L"][t])) for t in P}
    compras = {}
    for (m, t), v in V["comp"].items():
        if _val(v) > TOL:
            compras.setdefault(m, {})[t] = _r(_val(v))
    elegidas = [k for k, v in V["y"].items() if _val(v) > 0.5]
    caja = {t: _r(_val(V["caja"][t])) for t in P}
    intereses = sum(_val(f["interes"](t)) for t in P) + D["tasa"][T] * fin[T]
    compras_total = sum(_val(f["compras"](t)) for t in P)
    invers = sum(k["costo"] for k in D["invs"] if k["id"] in elegidas)
    resid = sum(k["residual"] for k in D["invs"] if k["id"] in elegidas)

    # utilidad descontada recalculada sin el desempate EPS
    util = 0.0
    for p in programa:
        o = next(x for x in D["ots"] if x["id"] == p["ot"])
        s = p["periodo"] + o["pc"]
        util += (o["precio"] - p["multa"]) * _desc(D, s)
        util -= p["horas"] * D["recursos"][p["recurso"]]["costo_hora"] * d[p["periodo"]]
    for t in P:
        util -= _val(f["compras"](t)) * d[t] + _val(f["interes"](t)) * d[t]
    util -= D["tasa"][T] * fin[T] * d[T + 1]
    for k in D["invs"]:
        if k["id"] in elegidas:
            util += -k["costo"] * d[k["pago"]] + k["residual"] * d[T]

    flujo = {}
    for t in P:
        flujo[t] = {
            "cobros": _r(sum(_val(f["cobro"](o, t)) for o in D["ots"])),
            "pago_conversion": _r(_val(f["conv"](t))),
            "pago_materiales": _r(_val(f["compras"](t))),
            "pago_inversiones": _r(_val(f["inversion"](t))),
            "prestamo_tomado": fin[t],
            "amortizacion": _r(_val(f["amort"](t))),
            "intereses": _r(_val(f["interes"](t))),
            "externos": _r(D["ext"][t]),
        }

    # holguras por restricción ------------------------------------------------------------
    R = {k: {"nombre": v, "activa": False, "detalle": []} for k, v in NOMBRES.items()}
    for r, rd in D["recursos"].items():
        for t in P:
            usado = sum(p["horas"] for p in programa if p["recurso"] == r and p["periodo"] == t)
            cap = rd["cap"][t] + sum(k["cap"] for k in D["invs"]
                                     if k["id"] in elegidas and k["recurso"] == r and k["periodo"] <= t <= k["fin"])
            h = cap - usado
            act = abs(h) <= TOL and usado > 0
            R["R1"]["detalle"].append({"recurso": r, "periodo": t, "usado": _r(usado), "capacidad": _r(cap),
                                       "holgura": _r(h), "activa": act})
            R["R1"]["activa"] |= act
    for m, md in D["materiales"].items():
        for t in P:
            consumo = sum(o["mu"][m] * o["q"] for o in D["ots"] if m in o["mu"]
                          for p in programa if p["ot"] == o["id"] and p["periodo"] == t)
            h = _val(V["inv"][m, t])
            act = abs(h) <= TOL and consumo > 0
            R["R2"]["detalle"].append({"material": m, "periodo": t, "consumo": _r(consumo),
                                       "stock_final": _r(h), "holgura": _r(h), "activa": act})
            R["R2"]["activa"] |= act
    for o in D["ots"]:
        p = next((x for x in programa if x["ot"] == o["id"]), None)
        R["R3"]["detalle"].append({"ot": o["id"], "recurso": p and p["recurso"], "periodo": p and p["periodo"],
                                   "obligatoria": o["obligatoria"]})
    R["R3"]["activa"] = any(o["obligatoria"] for o in D["ots"])
    for o in D["ots"]:
        if o["id"] in tard:
            R["R4"]["detalle"].append({"ot": o["id"], "entrega": o["entrega"], "tardanza": tard[o["id"]],
                                       "holgura": max(0, o["entrega"] - next(x["periodo"] for x in programa if x["ot"] == o["id"])),
                                       "activa": tard[o["id"]] > 0})
    R["R4"]["activa"] = any(v > 0 for v in tard.values())
    pos = {p["ot"]: p for p in programa}
    for a, b in D["inc"]:
        if a in pos and b in pos:
            pa, pb = pos[a], pos[b]
            act = pa["recurso"] == pb["recurso"] and abs(pa["periodo"] - pb["periodo"]) <= 1
            R["R5"]["detalle"].append({"antes": a, "despues": b, "periodo_antes": pa["periodo"],
                                       "periodo_despues": pb["periodo"], "activa": act})
            R["R5"]["activa"] |= act
    for m, md in D["materiales"].items():
        if md["ventanas"] is not None:
            R["R6"]["detalle"].append({"material": m, "ventanas": sorted(md["ventanas"]),
                                       "compras": compras.get(m, {})})
    for t in P:
        h7 = caja[t]
        h8 = caja[t] - D["cmin"][t]
        R["R7"]["detalle"].append({"periodo": t, "saldo": caja[t], "holgura": _r(h7), "activa": abs(h7) <= TOL})
        a8 = abs(h8) <= 1e-4
        R["R8"]["detalle"].append({"periodo": t, "saldo": caja[t], "minimo": D["cmin"][t], "holgura": _r(h8),
                                   "prestamo": fin[t], "activa": a8})
        R["R7"]["activa"] |= abs(h7) <= TOL
        R["R8"]["activa"] |= a8
    for k in D["invs"]:
        R["R9"]["detalle"].append({"inversion": k["id"], "elegida": k["id"] in elegidas, "recurso": k["recurso"],
                                   "capacidad_extra": k["cap"], "desde": k["periodo"], "hasta": k["fin"]})
    R["R9"]["activa"] = bool(elegidas)

    return {
        "factible": True, "estado": "óptimo",
        "programa": programa, "no_programadas": no_prog, "tardanzas": tard,
        "financiamiento": fin, "deuda_final": fin[T], "compras": compras,
        "inversiones_elegidas": elegidas, "caja": caja,
        "utilidad_descontada": _r(util),
        "componentes": {"ingresos": _r(ingresos), "costo_conversion": _r(conversion),
                        "costo_materiales": _r(compras_total), "multas": _r(multas),
                        "intereses": _r(intereses), "inversiones": _r(invers), "valor_residual": _r(resid)},
        "flujo": flujo, "restricciones": R,
    }


def _costo_restricciones(D, res):
    """Cuánto mejora la utilidad si se quita cada familia (re-resolviendo). 0 = no cuesta nada."""
    R = res["restricciones"]
    base = res["utilidad_descontada"]
    pruebas = {"R1": {"R1"}, "R2": {"R2"}, "R5": {"R5"}, "R6": {"R6"}, "R8": {"R8"}, "R7": {"R78"}}
    for fam, rel in pruebas.items():
        if fam == "R5" and not D["inc"]:
            R[fam]["costo"] = 0.0
            continue
        if fam == "R6" and all(m["ventanas"] is None for m in D["materiales"].values()):
            R[fam]["costo"] = 0.0
            continue
        prob, V = _construir(D, relajar=frozenset(rel))
        if _resolver(prob, D) != "Optimal":
            R[fam]["costo"] = None
            continue
        sin = _armar_salida(D, V)["utilidad_descontada"]
        costo = max(0.0, sin - base)
        if fam == "R7":
            costo = max(0.0, costo - R["R8"].get("costo", 0.0))
        R[fam]["costo"] = _r(costo)
        if costo > 1e-4:          # quitarla mejora la utilidad: la restricción está mandando
            R[fam]["activa"] = True
    R["R4"]["costo"] = _r(res["componentes"]["multas"])
    R["R3"]["costo"] = None
    R["R9"]["costo"] = None
    return R


# ----------------------------------------------------------------------------- ayudas B7, B0, B6/B8
def desviacion(programado: float, ejecutado: float, umbral: float = 0.10) -> dict:
    """B7: desviación relativa sobre lo programado; dispara si es MAYOR que el umbral."""
    if programado == 0:
        return {"desviacion": None, "disparo": ejecutado != 0, "mensaje": "Programado = 0: toda ejecución es desvío."}
    dv = abs(ejecutado - programado) / abs(programado)
    return {"desviacion": round(dv, 6), "disparo": dv > umbral + 1e-12}


def parametro_vigente(historial: list[dict], fecha: date):
    """B0: valor vigente en una fecha. historial = [{valor, desde, hasta(None = abierto)}]."""
    for h in sorted(historial, key=lambda x: x["desde"]):
        if h["desde"] <= fecha and (h.get("hasta") is None or fecha <= h["hasta"]):
            return h["valor"]
    return None


def cambiar_parametro(historial: list[dict], valor, desde: date) -> list[dict]:
    """B0: cierra el valor abierto el día anterior a «desde» y abre el nuevo (no borra la historia)."""
    from datetime import timedelta
    nuevo = [dict(h) for h in historial]
    for h in nuevo:
        if h.get("hasta") is None and h["desde"] < desde:
            h["hasta"] = desde - timedelta(days=1)
    nuevo.append({"valor": valor, "desde": desde, "hasta": None})
    return nuevo


def evaluar_inversion(flujos: list[float], tasa: float) -> dict:
    """B6/B8: VAN, TIR y recuperación de flujos por periodo 1..n (convención de VNA de Excel)."""
    van = sum(f / (1 + tasa) ** (i + 1) for i, f in enumerate(flujos))

    def vpn(x):
        return sum(f / (1 + x) ** i for i, f in enumerate(flujos))
    tir = None
    lo, hi = -0.99, 10.0
    if vpn(lo) * vpn(hi) < 0:
        for _ in range(200):
            mid = (lo + hi) / 2
            if vpn(lo) * vpn(mid) <= 0:
                hi = mid
            else:
                lo = mid
        tir = (lo + hi) / 2
    acum, rec = 0.0, None
    for i, f in enumerate(flujos, start=1):
        acum += f
        if acum >= -1e-9 and rec is None:
            rec = i
    return {"van": round(van, 4), "tir": None if tir is None else round(tir, 6), "recuperacion": rec,
            "conviene": van > 0}


def estados_proyectados(datos: dict, res: dict, tasa_ir: float = 0.295) -> dict:
    """B8: estado de resultados, flujo de caja y balance por periodo a partir del plan.
    Supuestos: venta reconocida al terminar la OT; multa rebaja la cuenta por cobrar; material
    al costo; IR del periodo se devenga (por pagar) y se paga fuera del horizonte."""
    D = _leer(datos)
    P = D["P"]
    stock0 = sum(m["stock"] * m["costo"] for m in D["materiales"].values())
    capital = D["caja0"] + stock0 - D["deuda0"]
    inv_val = stock0
    cxc = af = 0.0
    deuda = D["deuda0"]
    ir_pp = util_ac = 0.0
    caja = D["caja0"]
    out = {}
    for t in P:
        fl = res["flujo"][t]
        hechas = [p for p in res["programa"] if p["periodo"] == t]
        ventas = sum(next(o["precio"] for o in D["ots"] if o["id"] == p["ot"]) for p in hechas)
        multas = sum(p["multa"] for p in hechas)
        conv = fl["pago_conversion"]
        mat = sum(next(o for o in D["ots"] if o["id"] == p["ot"])["mu"].get(m, 0) * p["cantidad"] * md["costo"]
                  for p in hechas for m, md in D["materiales"].items())
        dep = sum(k["costo"] / k["vida"] for k in D["invs"] if k["id"] in res["inversiones_elegidas"]
                  and k["vida"] and k["periodo"] <= t <= k["fin"])
        inter = fl["intereses"]
        uai = ventas - multas - conv - mat - dep - inter
        ir = tasa_ir * uai if uai > 0 else 0.0
        un = uai - ir
        flujo_neto = (fl["cobros"] - fl["pago_conversion"] - fl["pago_materiales"] - fl["pago_inversiones"]
                      + fl["prestamo_tomado"] - fl["amortizacion"] - fl["intereses"] + fl["externos"])
        caja_ini = caja
        caja = caja + flujo_neto
        cxc += ventas - multas - fl["cobros"]
        inv_val += fl["pago_materiales"] - mat
        af += fl["pago_inversiones"] - dep
        deuda += fl["prestamo_tomado"] - fl["amortizacion"]
        ir_pp += ir
        util_ac += un
        # los flujos externos se tratan como cobro de cuentas previas (dentro del capital inicial)
        capital_t = capital
        activo = caja + cxc + inv_val + af
        pasivo = deuda + ir_pp
        patrimonio = capital_t + util_ac + sum(D["ext"][s] for s in P if s <= t)
        out[t] = {
            "resultados": {"ventas": _r(ventas), "multas": _r(multas), "conversion": _r(conv),
                           "material": _r(mat), "depreciacion": _r(dep), "intereses": _r(inter),
                           "utilidad_antes_ir": _r(uai), "ir": _r(ir), "utilidad_neta": _r(un)},
            "caja": {"inicial": _r(caja_ini), "flujo_neto": _r(flujo_neto), "final": _r(caja)},
            "balance": {"caja": _r(caja), "cxc": _r(cxc), "inventario": _r(inv_val), "activo_fijo": _r(af),
                        "activo": _r(activo), "deuda": _r(deuda), "ir_por_pagar": _r(ir_pp),
                        "capital": _r(capital_t), "utilidades": _r(util_ac),
                        "pasivo_patrimonio": _r(pasivo + patrimonio),
                        "cuadra": abs(activo - pasivo - patrimonio) < 1e-6},
        }
    return out
