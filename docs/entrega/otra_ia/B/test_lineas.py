"""Pruebas de lineas.py: el plan y el estado, convertidos en líneas, se sintetizan con sintesis.py.

Caso principal: «k_estados» de casos_B.xlsx (caja + financiamiento + material + plazo de cobro).
Calendario mensual: periodo 1 = 2027-01, periodo 0 (antes del plan) = 2026-12, periodo 4 = 2027-04.

Datos: caja inicial 60, caja mínima 20, tasa 2 %, M1 a S/ 5 la hora, PVC a S/ 3 (stock 10, llegan 10 en p2),
OT1 y OT2: 10 h, 10 PVC, precio 200, plazo de cobro 1. La calculadora pone OT1 en p1 y OT2 en p2.

Líneas (monto · devengo · caja · clase):
  OT1 venta 200 · p1 · p2 · INGRESO          OT2 venta 200 · p2 · p3 · INGRESO
  OT1 conversión 10 h × 5 = 50 · p1 · p1     OT2 conversión 50 · p2 · p2            (EGRESO)
  STOCK PVC 10 × 3 = 30 · p1 (consumo OT1) · p0 (ya pagado, ejecutado)               (EGRESO)
  LLEGADA PVC p2 10 × 3 = 30 · p2 (consumo OT2) · p2 (se paga al llegar, comprometido) (EGRESO)
  Préstamo p1 10 entrada · p1;  devolución 10 salida · p2;  interés 10 × 2 % = 0.2 salida · p2  (FINANCIAMIENTO)

Efectivo (reloj caja) en el horizonte:
  p1 = −50 + 10 = −40          → saldo 60 − 40 = 20      (calculadora: 20)
  p2 = 200 − 50 − 30 − 10 − 0.2 = 109.8 → saldo 129.8   (calculadora: 129.8)
  p3 = +200                    → saldo 329.8             (calculadora: 329.8)
  (p0 = −30 es el stock inicial, pagado antes del plan: no entra al saldo, ya está en la caja inicial.)
Operativo (reloj devengo):
  p1: INGRESO 200, EGRESO −(50 + 30) = −80;  p2: INGRESO 200, EGRESO −80
  = ventas − conversión − material consumido de la hoja k (120 y 120) y de estados_proyectados.
Financiero (caja): p1 +10, p2 −10.2.

Las demás pruebas repiten la conciliación con los casos e, f, g, h, j y el caso aleatorio de 50 OT.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pytest

pytest.importorskip("pulp")
import calculadora as C  # noqa: E402
import lineas as LN  # noqa: E402
import sintesis as S  # noqa: E402
import test_calculadora as TC  # noqa: E402
from eventos import COBRO_PAGO, LLEGA_MATERIAL, PEDIDO, EstadoPlan  # noqa: E402

CAL = LN.mensual("2027-01")


def mes(t):
    return CAL(t)[:7]


def correr(datos):
    res = C.plan(dict(datos, analisis=False))
    assert res["factible"], res.get("mensaje")
    return res, LN.lineas_desde_plan(res, CAL, datos)


def saldos(lineas, datos):
    D = C._leer(datos)
    ef = S.sintetizar(lineas, "Presupuesto de efectivo")
    out, s = {}, D["caja0"]
    for t in D["P"]:
        s += ef.get((mes(t),), 0.0)
        out[t] = round(s, 2)
    return out


def operativo(lineas, t, sin_material=None):
    L = [l for l in lineas if sin_material is None or l["recurso"] not in sin_material]
    op = S.sintetizar(L, "Presupuesto operativo")
    return round(op.get((mes(t), "INGRESO"), 0.0) + op.get((mes(t), "EGRESO"), 0.0), 2)


# --------------------------------------------------------------------------- caso k a mano
def test_k_a_mano():
    res, L = correr(TC.CASO_K)
    assert S.sintetizar(L, "Presupuesto de efectivo") == {
        ("2026-12",): -30.0, ("2027-01",): -40.0, ("2027-02",): 109.8, ("2027-03",): 200.0}
    assert saldos(L, TC.CASO_K) == {1: 20.0, 2: 129.8, 3: 329.8} == res["caja"]
    assert S.sintetizar(L, "Presupuesto operativo") == {
        ("2027-01", "EGRESO"): -80.0, ("2027-01", "INGRESO"): 200.0,
        ("2027-02", "EGRESO"): -80.0, ("2027-02", "INGRESO"): 200.0}
    assert S.sintetizar(L, "Presupuesto financiero") == {("2027-01", "FINANCIAMIENTO"): 10.0,
                                                         ("2027-02", "FINANCIAMIENTO"): -10.2}
    e = C.estados_proyectados(TC.CASO_K, res)
    for t in (1, 2, 3):
        r = e[t]["resultados"]
        assert operativo(L, t) == round(r["ventas"] - r["multas"] - r["conversion"] - r["material"], 2)
    estados = {(l["ticket"], l["estado"]) for l in L if l["recurso"] == "PVC"}
    assert estados == {("STOCK PVC", "ejecutado"), ("LLEGADA PVC p2", "comprometido")}
    assert all(l["estado"] == "programado" for l in L if l["recurso"] != "PVC")


def test_e_a_mano():
    """Caso e: caja 50, mínimo 40, OT1 cuesta 30 en p1 y cobra 60 en p2 → préstamo 20 en p1.
    p1: −30 + 20 → 40;  p2: +60 − 20 − 0.3 → 79.7;  p3: 79.7."""
    res, L = correr(TC.CASO_E)
    assert saldos(L, TC.CASO_E) == {1: 40.0, 2: 79.7, 3: 79.7} == res["caja"]
    assert operativo(L, 1) == 30.0 and operativo(L, 2) == 0.0      # 60 − 30 devengado en p1


# --------------------------------------------------------------------------- conciliación general
CASOS = {"e": TC.CASO_E, "f_1.5%": TC.caso_f(0.015), "f_20%": TC.caso_f(0.20), "g": TC.CASO_G,
         "h1": TC.CASO_H1, "j": TC.caso_j([0.015, 0.015, 0.02, 0.02], 2), "k": TC.CASO_K}


@pytest.mark.parametrize("nombre", list(CASOS))
def test_efectivo_y_operativo_reproducen_la_calculadora(nombre):
    datos = CASOS[nombre]
    res, L = correr(datos)
    assert saldos(L, datos) == {t: round(v, 2) for t, v in res["caja"].items()}
    e = C.estados_proyectados(datos, res)
    for t in C._leer(datos)["P"]:
        r = e[t]["resultados"]
        assert operativo(L, t) == round(r["ventas"] - r["multas"] - r["conversion"] - r["material"], 2), t


def test_caso_aleatorio_50_ot():
    """Compras con ventanas, llegadas, inversión, préstamos, multas y plazos 0–2. Aquí el material
    comprado (S/ 5) cuesta más que el del stock (S/ 4): el devengo PEPS de lineas.py difiere de
    estados_proyectados (que valora todo el consumo a S/ 4); por eso el material se concilia aparte."""
    datos = TC.caso_aleatorio()
    res, L = correr(datos)
    assert saldos(L, datos) == {t: round(v, 2) for t, v in res["caja"].items()}
    mats = set(datos["materiales"])
    e = C.estados_proyectados(datos, res)
    for t in range(1, 13):
        r = e[t]["resultados"]
        assert operativo(L, t, sin_material=mats) == round(r["ventas"] - r["multas"] - r["conversion"], 2)
    M = [l for l in L if l["recurso"] in mats]
    caja_plan = sum(l["monto"] for l in M if "2027-01" <= l["fecha_caja"][:7] <= "2027-12")
    assert round(caja_plan, 2) == round(res["componentes"]["costo_materiales"], 2)
    stock0 = sum(m["stock"] * m["costo"] for m in datos["materiales"].values())
    assert round(sum(l["monto"] for l in M), 2) == round(stock0 + caja_plan, 2)     # nada se pierde ni se duplica
    assert round(sum(l["monto"] for l in L if l["clase"] == "INGRESO"), 2) == res["componentes"]["ingresos"]


# --------------------------------------------------------------------------- rechazos y sentido
def test_plan_infactible_y_calendario_incompleto_se_rechazan():
    with pytest.raises(S.LineaInvalida, match="no es factible"):
        LN.lineas_desde_plan(C.plan(TC.CASO_L1), CAL, TC.CASO_L1)
    res = C.plan(dict(TC.CASO_E, analisis=False))
    with pytest.raises(S.LineaInvalida, match="periodo 2"):
        LN.lineas_desde_plan(res, {1: "2027-01-01"}, TC.CASO_E)
    with pytest.raises(S.LineaInvalida, match="AAAA-MM"):
        LN.mensual("2027-13")


def test_sentido_solo_en_financiamiento_y_aporte():
    base = dict(ticket="X", recurso="r", monto=10, fecha_devengo="2027-01-01", fecha_caja="2027-01-01",
                estado="programado")
    L = [dict(base, clase="FINANCIAMIENTO", sentido="salida"), dict(base, clase="APORTE", sentido="salida"),
         dict(base, clase="EGRESO", sentido="salida")]
    assert S.sintetizar(L, "Presupuesto de efectivo") == {("2027-01",): -30.0}
    with pytest.raises(S.LineaInvalida, match="no puede ir en sentido"):
        S.sintetizar([dict(base, clase="INGRESO", sentido="salida")], "Presupuesto de efectivo")
    with pytest.raises(S.LineaInvalida, match="sentido «sale»"):
        S.sintetizar([dict(base, clase="FINANCIAMIENTO", sentido="sale")], "Presupuesto de efectivo")


# --------------------------------------------------------------------------- (b) desde el estado
def estado_ejemplo():
    """hoy 10-ene-2026. COMPRA de 6 PVC (S/ 2) para el 12-ene; llegan 4 el 10-ene (parcial).
    Préstamo FI-0001 de 200 al 1.5 %, se toma el 10-ene y se paga el 10-feb.
    Pedido OT-0001 por 500, entrega 20-ene. Inversión IN-0001 «Horno 2» de 120 el 1-mar, aprobada."""
    e = EstadoPlan(hoy="2026-01-10", inicio="2026-01-01", recursos={"M1": 8}, materiales={"PVC": 0},
                   recetas={"P1": {"horas": {"M1": 0.5}, "material": {"PVC": 1}}}, cuentas={"CTA-1": 100},
                   parametros={"plazo_cobro_dias": 30, "plazo_pago_dias": 15},
                   tickets=[{"tipo": "COMPRA", "estado": "comprometido", "material": "PVC", "cantidad": 6,
                             "proveedor": "PROV-A", "fecha_pedido": "2026-01-03", "fecha_llegada": "2026-01-12"},
                            {"tipo": "FINANCIAMIENTO", "estado": "propuesto", "monto": 200, "tasa": 0.015,
                             "fecha_pago": "2026-02-10"}])
    assert e.registrar({"tipo": PEDIDO, "accion": "entra", "cliente": "C1", "producto": "P1", "cantidad": 10,
                        "fecha": "2026-01-20", "precio": 500})["aceptado"]
    assert e.registrar({"tipo": LLEGA_MATERIAL, "proveedor": "PROV-A", "material": "PVC", "cantidad": 4,
                        "fecha": "2026-01-10"})["aceptado"]
    assert e.registrar({"tipo": COBRO_PAGO, "movimiento": "cobro", "monto": 200, "fecha": "2026-01-10",
                        "cuenta": "CTA-1", "ticket": "FI-0001"})["aceptado"]
    e.crear_ticket("INVERSIÓN", {"activo": "Horno 2", "costo": 120, "fecha": "2026-03-01"})
    assert e.mover("IN-0001", "aprobado", "gerente")["aceptado"]
    return e


def test_lineas_desde_estado_a_mano():
    """Caja: ene +200 (préstamo) − 12 (6 PVC × 2, pago 12-ene + 15 d = 27-ene) = 188;
    feb +500 (cobro 20-ene + 30 d = 19-feb) − 200 − 3 (devolución e interés 200 × 1.5 %) = 297; mar −120."""
    L = LN.lineas_desde_estado(estado_ejemplo(), costo_material={"PVC": 2})
    assert S.sintetizar(L, "Presupuesto de efectivo") == {("2026-01",): 188.0, ("2026-02",): 297.0,
                                                          ("2026-03",): -120.0}
    assert S.sintetizar(L, "Presupuesto operativo") == {("2026-01", "EGRESO"): -12.0, ("2026-01", "INGRESO"): 500.0}
    est = {(l["ticket"], l["recurso"], l["estado"]): l["monto"] for l in L}
    assert est == {("CO-0001", "PVC", "ejecutado"): 8.0, ("CO-0001", "PVC", "comprometido"): 4.0,
                   ("FI-0001", "Préstamo", "ejecutado"): 200.0,
                   ("FI-0001", "Devolución de préstamo", "comprometido"): 200.0,
                   ("FI-0001", "Interés", "comprometido"): 3.0,
                   ("IN-0001", "Horno 2", "comprometido"): 120.0, ("OT-0001", "Venta", "comprometido"): 500.0}
    ctl = {f["recurso"]: f for f in S.control_ejecucion(L, {"PVC": 12})}
    assert (ctl["PVC"]["comprometido"], ctl["PVC"]["ejecutado"], ctl["PVC"]["disponible"]) == (4.0, 8.0, 0.0)


def test_estado_avanza_y_cancela():
    e = estado_ejemplo()
    e.mover("OT-0001", "en ejecución", "costos")
    e.mover("OT-0001", "terminado", "costos")
    assert e.registrar({"tipo": PEDIDO, "accion": "entra", "cliente": "C2", "producto": "P1", "cantidad": 1,
                        "fecha": "2026-01-25", "precio": 90})["aceptado"]
    assert e.registrar({"tipo": PEDIDO, "accion": "cancela", "ot": "OT-0002"})["aceptado"]
    L = LN.lineas_desde_estado(e, costo_material={"PVC": 2})
    ots = {(l["ticket"], l["estado"]) for l in L if l["clase"] == "INGRESO"}
    assert ots == {("OT-0001", "ejecutado")}                       # la cancelada no deja línea


def test_estado_sin_datos_se_rechaza_sin_asumir_cero():
    e = estado_ejemplo()
    with pytest.raises(S.LineaInvalida, match="costo por unidad de «PVC»"):
        LN.lineas_desde_estado(e)
    e2 = EstadoPlan(hoy="2026-01-10", recursos={"M1": 8}, recetas={"P1": {"horas": {"M1": 1}}})
    e2.registrar({"tipo": PEDIDO, "accion": "entra", "cliente": "C1", "producto": "P1", "cantidad": 1,
                  "fecha": "2026-01-20", "precio": 50})
    with pytest.raises(S.LineaInvalida, match="plazo_cobro_dias"):
        LN.lineas_desde_estado(e2)
    assert LN.lineas_desde_estado(e2, plazo_cobro_dias=0)[0]["fecha_caja"] == "2026-01-20"
    e3 = EstadoPlan(hoy="2026-01-10", tickets=[{"tipo": "FINANCIAMIENTO", "estado": "propuesto", "monto": 200,
                                                "tasa": 0.015}])
    assert LN.lineas_desde_estado(e3) == []                        # propuesto: lo trae el plan
    with pytest.raises(S.LineaInvalida, match="fecha de toma"):
        LN.lineas_desde_estado(e3, incluir_propuestos=True)
