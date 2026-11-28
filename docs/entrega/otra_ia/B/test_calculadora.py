"""
test_calculadora.py — reproduce los 12 casos de casos_B.xlsx y mide el tiempo con 50 OT y 4 recursos.

Correr:   python -m unittest -v test_calculadora.py
Solo usa la biblioteca estándar + PuLP (la misma dependencia de calculadora.py).
Los valores esperados son los que salen en la hoja «Resultado esperado» de cada caso del Excel.
"""
import random
import time
import unittest
from datetime import date

from calculadora import (cambiar_parametro, desviacion, estados_proyectados, evaluar_inversion, plan,
                         parametro_vigente)

T6 = 4   # decimales para comparar dinero


def ot(id, horas, recurso="M1", cantidad=1, precio=100, entrega=1, **kw):
    d = {"id": id, "cantidad": cantidad, "horas_unidad": {recurso: horas}, "precio": precio, "entrega": entrega}
    d.update(kw)
    return d


# --------------------------------------------------------------------------- datos de los casos
CASO_A = dict(periodos=2, caja_inicial=1000, recursos={"M1": {"capacidad": 10, "costo_hora": 2}},
              ot=[ot("OT1", 8, precio=100, entrega=1), ot("OT2", 6, precio=300, entrega=1)])

CASO_B = dict(periodos=3, caja_inicial=1000, recursos={"M1": {"capacidad": 20, "costo_hora": 1}},
              ot=[ot("NEGRO", 8, precio=100, entrega=1), ot("BLANCO", 8, precio=100, entrega=1)],
              incompatibles=[("NEGRO", "BLANCO")])

CASO_C = dict(periodos=3, caja_inicial=1000, recursos={"M1": {"capacidad": 10, "costo_hora": 1}},
              materiales={"PVC": {"stock": 0, "costo": 2,
                                  "compra": {"permitida": True, "ventanas": [3], "plazo": 0, "costo": 2}}},
              ot=[ot("OT1", 1, cantidad=5, precio=100, entrega=2, material_unidad={"PVC": 1})])

CASO_D = dict(periodos=3, caja_inicial=1000, recursos={"M1": {"capacidad": 20, "costo_hora": 1}},
              materiales={"PVC": {"stock": 4, "costo": 3, "llegadas": {2: 6}}},
              ot=[ot("OT1", 1, cantidad=10, precio=200, entrega=1, material_unidad={"PVC": 1})])

CASO_E = dict(periodos=3, caja_inicial=50, caja_minima=40, tasa_prestamo=0.015,
              recursos={"M1": {"capacidad": 10, "costo_hora": 3}},
              ot=[ot("OT1", 1, cantidad=10, precio=60, entrega=1, plazo_cobro=1)])


def caso_f(tasa):
    return dict(periodos=3, caja_inicial=0, caja_minima=0, tasa_prestamo=tasa, tasa_descuento=0.012,
                flujos_externos={2: 100}, recursos={"M1": {"capacidad": 10, "costo_hora": 10}},
                ot=[ot("OT1", 10, precio=150, entrega=1, multa=5, plazo_cobro=1)])


CASO_G = dict(periodos=4, caja_inicial=500, tasa_descuento=0.012,
              recursos={"M2": {"capacidad": 0, "costo_hora": 2}, "M3": {"capacidad": 0, "costo_hora": 2}},
              inversiones=[{"id": "A", "costo": 120, "recurso": "M2", "capacidad": 10, "periodo": 1, "vida_util": 4},
                           {"id": "B", "costo": 200, "recurso": "M3", "capacidad": 10, "periodo": 1, "vida_util": 4}],
              ot=[ot(f"A{t}", 10, recurso="M2", precio=60, entrega=t, estado="propuesto") for t in range(1, 5)]
              + [ot(f"B{t}", 10, recurso="M3", precio=60, entrega=t, estado="propuesto") for t in range(1, 5)])

H_OTS = [ot("OT1", 8, precio=100, entrega=1), ot("OT2", 8, precio=200, entrega=2), ot("OT3", 8, precio=100, entrega=3)]
CASO_H0 = dict(periodos=5, caja_inicial=1000, recursos={"M1": {"capacidad": 8, "costo_hora": 1}}, ot=H_OTS)
CASO_H1 = dict(periodos=5, hoy=2, caja_inicial=1000,
               recursos={"M1": {"capacidad": [8, 0, 0, 8, 8], "costo_hora": 1}},
               ot=[dict(H_OTS[0], estado="terminado"), H_OTS[1], H_OTS[2]])

HIST_TASA = [{"valor": 0.015, "desde": date(2026, 1, 1), "hasta": None}]


def caso_j(tasas, pago_periodo):
    return dict(periodos=4, caja_inicial=0, tasa_prestamo=tasas,
                flujos_externos={pago_periodo: -100, 4: 200}, recursos={}, ot=[])


CASO_K = dict(periodos=3, caja_inicial=60, caja_minima=20, tasa_prestamo=0.02,
              recursos={"M1": {"capacidad": 10, "costo_hora": 5}},
              materiales={"PVC": {"stock": 10, "costo": 3, "llegadas": {2: 10}}},
              ot=[ot("OT1", 1, cantidad=10, precio=200, entrega=1, plazo_cobro=1, material_unidad={"PVC": 1}),
                  ot("OT2", 1, cantidad=10, precio=200, entrega=2, plazo_cobro=1, material_unidad={"PVC": 1})])

CASO_L1 = dict(periodos=2, caja_inicial=1000, recursos={"M1": {"capacidad": 10, "costo_hora": 1}},
               ot=[ot("OT1", 12, precio=100, entrega=1)])
CASO_L2 = dict(periodos=2, caja_inicial=0, caja_minima=10, limite_prestamo=0, recursos={}, ot=[])


def periodo_de(res, id_ot):
    return next(p["periodo"] for p in res["programa"] if p["ot"] == id_ot)


# --------------------------------------------------------------------------- pruebas
class Casos(unittest.TestCase):

    def test_a_dos_ot_un_recurso_multa(self):
        r = plan(CASO_A)
        self.assertEqual(periodo_de(r, "OT2"), 1)
        self.assertEqual(periodo_de(r, "OT1"), 2)
        self.assertEqual(r["tardanzas"], {"OT1": 1, "OT2": 0})
        self.assertAlmostEqual(r["componentes"]["multas"], 1.0, T6)
        self.assertAlmostEqual(r["utilidad_descontada"], 371.0, T6)
        self.assertTrue(r["restricciones"]["R1"]["activa"])
        self.assertAlmostEqual(r["restricciones"]["R1"]["costo"], 1.0, T6)

    def test_b_secuencia_prohibida(self):
        r = plan(CASO_B)
        self.assertEqual(periodo_de(r, "BLANCO"), 1)
        self.assertEqual(periodo_de(r, "NEGRO"), 2)
        self.assertAlmostEqual(r["utilidad_descontada"], 183.0, T6)
        self.assertTrue(r["restricciones"]["R5"]["activa"])
        self.assertAlmostEqual(r["restricciones"]["R5"]["costo"], 1.0, T6)

    def test_c_ventana_proveedor(self):
        r = plan(CASO_C)
        self.assertEqual(r["compras"], {"PVC": {3: 5.0}})
        self.assertEqual(periodo_de(r, "OT1"), 3)
        self.assertEqual(r["tardanzas"]["OT1"], 1)
        self.assertAlmostEqual(r["utilidad_descontada"], 84.0, T6)
        self.assertAlmostEqual(r["restricciones"]["R6"]["costo"], 1.0, T6)
        self.assertTrue(r["restricciones"]["R6"]["activa"])

    def test_d_falta_material(self):
        r = plan(CASO_D)
        self.assertEqual(periodo_de(r, "OT1"), 2)
        self.assertEqual(r["tardanzas"]["OT1"], 1)
        self.assertAlmostEqual(r["utilidad_descontada"], 170.0, T6)
        r2 = [x for x in r["restricciones"]["R2"]["detalle"] if x["periodo"] == 2][0]
        self.assertTrue(r2["activa"])
        self.assertAlmostEqual(r2["stock_final"], 0.0, T6)

    def test_e_caja_minima_obliga_a_financiar(self):
        r = plan(CASO_E)
        self.assertAlmostEqual(r["financiamiento"][1], 20.0, T6)
        self.assertAlmostEqual(r["caja"][1], 40.0, T6)
        self.assertAlmostEqual(r["caja"][2], 79.7, T6)
        self.assertAlmostEqual(r["componentes"]["intereses"], 0.3, T6)
        self.assertAlmostEqual(r["utilidad_descontada"], 29.7, T6)
        self.assertTrue(r["restricciones"]["R8"]["activa"])

    def test_f_tasa_que_sube_conviene_atrasar(self):
        r1 = plan(caso_f(0.015))
        self.assertEqual(periodo_de(r1, "OT1"), 1)
        self.assertAlmostEqual(r1["financiamiento"][1], 100.0, T6)
        self.assertAlmostEqual(r1["utilidad_descontada"], 46.18491, 4)
        r2 = plan(caso_f(0.20))
        self.assertEqual(periodo_de(r2, "OT1"), 2)
        self.assertEqual(r2["tardanzas"]["OT1"], 1)
        self.assertAlmostEqual(sum(r2["financiamiento"].values()), 0.0, T6)
        self.assertAlmostEqual(r2["utilidad_descontada"], 42.26030, 4)

    def test_g_inversion_que_conviene_y_que_no(self):
        r = plan(CASO_G)
        self.assertEqual(r["inversiones_elegidas"], ["A"])
        self.assertEqual(sorted(p["ot"] for p in r["programa"]), ["A1", "A2", "A3", "A4"])
        self.assertAlmostEqual(r["utilidad_descontada"], 36.73575, 3)
        a = evaluar_inversion([-80, 40, 40, 40], 0.012)
        b = evaluar_inversion([-160, 40, 40, 40], 0.012)
        self.assertAlmostEqual(a["van"], 36.73575, 3)
        self.assertAlmostEqual(a["tir"], 0.233752, 5)
        self.assertEqual(a["recuperacion"], 3)
        self.assertAlmostEqual(b["van"], -42.31563, 3)
        self.assertAlmostEqual(b["tir"], -0.131123, 5)
        self.assertIsNone(b["recuperacion"])
        self.assertTrue(a["conviene"] and not b["conviene"])

    def test_h_planta_parada_y_reprogramacion_desde_hoy(self):
        r0 = plan(CASO_H0)
        self.assertEqual([periodo_de(r0, x) for x in ("OT1", "OT2", "OT3")], [1, 2, 3])
        self.assertAlmostEqual(r0["utilidad_descontada"], 376.0, T6)
        r1 = plan(CASO_H1)
        self.assertEqual(periodo_de(r1, "OT2"), 4)
        self.assertEqual(periodo_de(r1, "OT3"), 5)
        self.assertEqual(r1["tardanzas"], {"OT2": 2, "OT3": 2})
        self.assertAlmostEqual(r1["componentes"]["multas"], 6.0, T6)
        self.assertAlmostEqual(r1["utilidad_descontada"], 278.0, T6)

    def test_i_desviacion_bajo_y_sobre_umbral(self):
        self.assertEqual(desviacion(100, 92, 0.10), {"desviacion": 0.08, "disparo": False})
        self.assertEqual(desviacion(100, 90, 0.10), {"desviacion": 0.10, "disparo": False})
        self.assertEqual(desviacion(100, 115, 0.10), {"desviacion": 0.15, "disparo": True})

    def test_j_cambio_de_parametro_con_vigencia(self):
        h = cambiar_parametro(HIST_TASA, 0.02, date(2026, 3, 1))
        self.assertEqual(h[0]["hasta"], date(2026, 2, 28))
        self.assertEqual(parametro_vigente(h, date(2026, 2, 15)), 0.015)
        self.assertEqual(parametro_vigente(h, date(2026, 3, 10)), 0.02)
        meses = [date(2026, m, 1) for m in (1, 2, 3, 4)]
        tasas = [parametro_vigente(h, f) for f in meses]
        self.assertEqual(tasas, [0.015, 0.015, 0.02, 0.02])
        r = plan(caso_j(tasas, 3))
        self.assertAlmostEqual(r["financiamiento"][3], 100.0, T6)
        self.assertAlmostEqual(r["componentes"]["intereses"], 2.0, T6)
        self.assertAlmostEqual(r["caja"][4], 98.0, T6)
        r_feb = plan(caso_j(tasas, 2))
        # si el pago fuera en febrero: 100 × 1.5 % (feb) + 101.5 × 2 % (mar, tasa nueva) = 3.53
        self.assertAlmostEqual(r_feb["financiamiento"][2], 100.0, T6)
        self.assertAlmostEqual(r_feb["financiamiento"][3], 101.5, T6)
        self.assertAlmostEqual(r_feb["componentes"]["intereses"], 3.53, T6)

    def test_k_estados_proyectados_cuadran(self):
        r = plan(CASO_K)
        self.assertAlmostEqual(r["financiamiento"][1], 10.0, T6)
        e = estados_proyectados(CASO_K, r, 0.295)
        esperado_caja = {1: 20.0, 2: 129.8, 3: 329.8}
        esperado_un = {1: 84.6, 2: 84.459, 3: 0.0}
        for t in (1, 2, 3):
            self.assertAlmostEqual(e[t]["caja"]["final"], esperado_caja[t], T6)
            self.assertAlmostEqual(e[t]["caja"]["inicial"] + e[t]["caja"]["flujo_neto"], e[t]["caja"]["final"], T6)
            self.assertAlmostEqual(e[t]["resultados"]["utilidad_neta"], esperado_un[t], 3)
            self.assertTrue(e[t]["balance"]["cuadra"])
            self.assertAlmostEqual(r["caja"][t], e[t]["caja"]["final"], T6)
        self.assertAlmostEqual(e[3]["balance"]["activo"], 329.8, T6)
        self.assertAlmostEqual(e[3]["balance"]["ir_por_pagar"], 70.741, 3)

    def test_l_sin_solucion_factible(self):
        r = plan(CASO_L1)
        self.assertFalse(r["factible"])
        ids = [c["id"] for c in r["restricciones_que_impiden"]]
        self.assertEqual(ids, ["R1"])
        self.assertAlmostEqual(r["restricciones_que_impiden"][0]["falta"], 2.0, 3)
        self.assertIn("faltan 2.00 h", r["mensaje"])
        self.assertNotIn("Traceback", r["mensaje"])
        r2 = plan(CASO_L2)
        self.assertFalse(r2["factible"])
        self.assertEqual({c["id"] for c in r2["restricciones_que_impiden"]}, {"R8"})
        self.assertAlmostEqual(r2["restricciones_que_impiden"][0]["falta"], 10.0, 3)
        r3 = plan({"periodos": 0})
        self.assertFalse(r3["factible"])
        self.assertTrue(r3["mensaje"].startswith("Dato inválido"))


# --------------------------------------------------------------------------- tiempo
def caso_aleatorio(n_ot=50, n_rec=4, T=12, semilla=2026):
    rnd = random.Random(semilla)
    recursos = {f"R{i+1}": {"capacidad": 40, "costo_hora": rnd.choice([8, 10, 12, 15])} for i in range(n_rec)}
    materiales = {"MP1": {"stock": 200, "costo": 4, "llegadas": {4: 150, 8: 150},
                          "compra": {"permitida": True, "ventanas": [3, 6, 9, 12], "plazo": 1, "costo": 5}},
                  "MP2": {"stock": 100, "costo": 6,
                          "compra": {"permitida": True, "ventanas": None, "plazo": 2, "costo": 6}}}
    ots = []
    for k in range(n_ot):
        rec = rnd.sample(list(recursos), rnd.choice([1, 2]))
        q = rnd.randint(5, 20)
        hu = {r: round(rnd.uniform(0.3, 1.2), 2) for r in rec}
        mu = {"MP1": rnd.choice([1, 2])} if rnd.random() < 0.7 else {"MP2": 1}
        costo_aprox = q * (max(hu.values()) * 12 + 2 * 5)
        ots.append({"id": f"OT{k+1:02d}", "cantidad": q, "horas_unidad": hu, "material_unidad": mu,
                    "precio": round(costo_aprox * rnd.uniform(1.2, 1.8), 0), "entrega": rnd.randint(2, T),
                    "estado": "comprometido" if rnd.random() < 0.6 else "propuesto",
                    "plazo_cobro": rnd.choice([0, 1, 2])})
    inc = [(f"OT{a:02d}", f"OT{b:02d}") for a, b in rnd.sample([(a, b) for a in range(1, n_ot + 1)
                                                                 for b in range(1, n_ot + 1) if a != b], 15)]
    return dict(periodos=T, caja_inicial=3000, caja_minima=1000, tasa_prestamo=0.015, tasa_descuento=0.012,
                recursos=recursos, materiales=materiales, ot=ots, incompatibles=inc,
                inversiones=[{"id": "Extrusora2", "costo": 2500, "recurso": "R1", "capacidad": 30, "periodo": 4,
                              "vida_util": 60, "valor_residual": 2000}],
                tiempo_max=120)


class Tiempo(unittest.TestCase):
    def test_50_ot_4_recursos(self):
        datos = caso_aleatorio()
        t0 = time.perf_counter()
        r = plan(dict(datos, analisis=False))
        t1 = time.perf_counter() - t0
        t0 = time.perf_counter()
        r2 = plan(dict(datos, analisis=True))
        t2 = time.perf_counter() - t0
        print(f"\n  50 OT × 4 recursos × 12 periodos (semilla 2026): plan {t1:.2f} s | "
              f"plan + costo de cada restricción {t2:.2f} s | factible={r['factible']} | "
              f"OT programadas={len(r.get('programa', []))} | utilidad={r.get('utilidad_descontada')}")
        self.assertTrue(r["factible"], r.get("mensaje"))
        self.assertAlmostEqual(r["utilidad_descontada"], r2["utilidad_descontada"], 2)
        self.assertLess(t1, 120)


if __name__ == "__main__":
    unittest.main(verbosity=2)
