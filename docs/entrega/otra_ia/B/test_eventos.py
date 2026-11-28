"""
test_eventos.py — pruebas de B1 (Receptor de hechos) y B3 (Estado del plan).

Correr:   python -m unittest -v test_eventos.py
No usa la calculadora ni PuLP. Todos los números se pueden verificar a mano.

La prueba de nombres busca spec.py en: variable SPEC_B, ./spec.py o ../tools/mapa_b/spec.py.
"""
import copy
import importlib.util
import os
import unittest
from datetime import date

from eventos import (COBRO_PAGO, DATO_MAESTRO, LLEGA_MATERIAL, MAQUINAS, NO_CONFORMIDAD, PEDIDO, PLANTA,
                     TICKET_DE_EVENTO, TIPOS_EVENTO, EstadoPlan, Rechazo, validar_forma)

D = date.fromisoformat


def base():
    """Estado de partida, todo inventado y chico (hoy = 10-ene-2026)."""
    return EstadoPlan(
        hoy="2026-01-10", inicio="2026-01-01",
        recursos={"M1": 8, "M2": 8},
        materiales={"PVC": 4},
        recetas={"P1": {"horas": {"M1": 0.5}, "material": {"PVC": 1}},
                 "P2": {"horas": {"M2": 1.0}, "material": {}}},
        cuentas={"CTA-1": 100},
        parametros={"caja_minima": 50, "tasa": 0.015},
        tickets=[
            {"tipo": "COMPRA", "estado": "comprometido", "material": "PVC", "cantidad": 6, "proveedor": "PROV-A",
             "fecha_pedido": "2026-01-03", "fecha_llegada": "2026-01-12"},
            {"tipo": "FINANCIAMIENTO", "estado": "propuesto", "monto": 200, "tasa": 0.015},
        ],
    )


def pedido(**kw):
    h = {"tipo": PEDIDO, "accion": "entra", "cliente": "CLI-1", "producto": "P1", "cantidad": 10,
         "fecha": "2026-01-20", "precio": 500}
    h.update(kw)
    return h


def llegada(**kw):
    h = {"tipo": LLEGA_MATERIAL, "proveedor": "PROV-A", "material": "PVC", "cantidad": 6, "fecha": "2026-01-10"}
    h.update(kw)
    return h


def foto(e):
    return copy.deepcopy((e.tickets, e.stock, e.caja, e._estado["paradas"], e._estado["maestros"]))


def cargar_spec():
    for p in (os.environ.get("SPEC_B"), "spec.py", os.path.join("..", "tools", "mapa_b", "spec.py")):
        if p and os.path.exists(p):
            s = importlib.util.spec_from_file_location("spec_b", p)
            m = importlib.util.module_from_spec(s)
            s.loader.exec_module(m)
            return m
    return None


class NombresDeSpec(unittest.TestCase):
    def test_eventos_y_tickets_coinciden_con_spec(self):
        spec = cargar_spec()
        if spec is None:
            self.skipTest("spec.py no encontrado (defina SPEC_B)")
        self.assertEqual([e[0] for e in spec.EVENTOS], list(TIPOS_EVENTO))
        self.assertEqual({e[0]: e[2] for e in spec.EVENTOS}, TICKET_DE_EVENTO)
        for nombre, _campos, estados in spec.TICKETS:
            cod = nombre.split()[0]
            self.assertIn(cod, MAQUINAS)
            esperados = {s.strip() for paso in estados.split("→") for s in paso.split("/")}
            self.assertEqual(esperados, set(MAQUINAS[cod]), cod)


class B1_Forma(unittest.TestCase):
    def test_texto_en_numero_se_rechaza_sin_convertir(self):
        _, err = validar_forma(pedido(cantidad="10"))
        self.assertTrue(any("«cantidad» debe ser un número; llegó texto «10»" in x for x in err), err)

    def test_campo_desconocido_y_faltante(self):
        h = pedido()
        h["cantdad"] = h.pop("cantidad")
        _, err = validar_forma(h)
        self.assertTrue(any("Campos que no existen" in x and "cantdad" in x for x in err))
        self.assertTrue(any("Faltan campos obligatorios" in x and "cantidad" in x for x in err))

    def test_fecha_que_no_existe_y_fecha_al_reves(self):
        _, err = validar_forma(pedido(fecha="2026-02-30"))
        self.assertTrue(any("no es una fecha que exista" in x for x in err))
        _, err = validar_forma({"tipo": PLANTA, "accion": "para", "recurso": "M1",
                                "desde": "2026-01-09", "hasta": "2026-01-05"})
        self.assertTrue(any("Fecha al revés" in x for x in err))

    def test_rangos(self):
        for campo, valor in (("cantidad", 0), ("cantidad", -3), ("precio", -1)):
            _, err = validar_forma(pedido(**{campo: valor}))
            self.assertTrue(any(f"«{campo}» debe ser mayor que 0" in x for x in err), (campo, err))
        _, err = validar_forma({"tipo": DATO_MAESTRO, "campo": "tasa", "objeto": "general", "valor": 1.5,
                                "desde": "2026-03-01"})
        self.assertTrue(any("0.015" in x for x in err), err)

    def test_tipo_desconocido_e_id_enviado(self):
        _, err = validar_forma({"tipo": "Llegó material"})
        self.assertIn("Tipo de hecho desconocido", err[0])
        _, err = validar_forma(pedido(id="E-9999"))
        self.assertTrue(any("el sistema asigna" in x for x in err))


class B3_Hechos(unittest.TestCase):
    def setUp(self):
        self.e = base()

    def test_pedido_entra_crea_ot_comprometida(self):
        r = self.e.registrar(pedido())
        self.assertTrue(r["aceptado"], r)
        self.assertEqual((r["id"], r["tickets"]), ("E-0001", ["OT-0001"]))
        ot = self.e.ticket("OT-0001")
        self.assertEqual((ot["estado"], ot["cantidad"], ot["fecha_entrega"], ot["precio"]),
                         ("comprometido", 10, D("2026-01-20"), 500))

    def test_rechazo_no_cambia_nada(self):
        antes = foto(self.e)
        for malo in (pedido(producto="P9"), pedido(fecha="2026-01-05"), pedido(cantidad="10"), llegada(cantidad=7)):
            r = self.e.registrar(malo)
            self.assertFalse(r["aceptado"])
            self.assertTrue(r["errores"])
        self.assertEqual(foto(self.e), antes)
        self.assertEqual(len(self.e.eventos), 0)
        self.assertEqual(len(self.e.rechazados), 4)

    def test_llegada_completa_mueve_stock_y_compra(self):
        self.e.registrar(pedido())
        r = self.e.registrar(llegada())
        self.assertTrue(r["aceptado"], r)
        self.assertEqual(self.e.stock["PVC"], 10)                         # 4 + 6
        self.assertEqual(self.e.ticket("CO-0001")["estado"], "recibido")
        self.assertEqual(r["afectados"], ["OT-0001"])                      # OT que usa PVC

    def test_llegada_parcial_y_exceso(self):
        r = self.e.registrar(llegada(cantidad=4))
        self.assertEqual(self.e.ticket("CO-0001")["estado"], "comprometido")
        self.assertIn("faltan 2", r["avisos"][0])
        self.assertTrue(self.e.registrar(llegada(cantidad=2))["aceptado"])
        self.assertEqual((self.e.stock["PVC"], self.e.ticket("CO-0001")["estado"]), (10, "recibido"))
        r = self.e.registrar(llegada(cantidad=1))
        self.assertIn("No hay COMPRA comprometida", r["errores"][0])

    def test_llegada_que_no_cuadra(self):
        r = self.e.registrar(llegada(cantidad=7))
        self.assertIn("le faltan 6", r["errores"][0])
        r = self.e.registrar(llegada(proveedor="PROV-B", compra="CO-0001"))
        self.assertIn("no coincide con CO-0001", r["errores"][0])
        r = self.e.registrar(llegada(fecha="2026-01-11"))
        self.assertIn("posterior a hoy", r["errores"][0])

    def test_parada_y_reinicio(self):
        self.e.registrar(pedido())
        r = self.e.registrar({"tipo": PLANTA, "accion": "para", "recurso": "M1",
                              "desde": "2026-01-09", "hasta": "2026-01-12"})
        self.assertTrue(r["aceptado"], r)
        self.assertEqual(r["afectados"], ["OT-0001"])
        self.assertEqual([self.e.capacidad("M1", D(f"2026-01-{d:02d}")) for d in (8, 9, 12, 13)], [8, 0, 0, 8])
        self.assertEqual(self.e.capacidad("M2", D("2026-01-10")), 8)
        r = self.e.registrar({"tipo": PLANTA, "accion": "reinicia", "recurso": "M1", "fecha": "2026-01-10"})
        self.assertTrue(r["aceptado"], r)
        self.assertEqual([self.e.capacidad("M1", D(f"2026-01-{d:02d}")) for d in (9, 10, 11)], [0, 8, 8])
        self.assertEqual(len(self.e._estado["paradas"]), 1)               # el hecho original sigue ahí

    def test_parada_futura_o_al_reves(self):
        r = self.e.registrar({"tipo": PLANTA, "accion": "para", "recurso": "M1",
                              "desde": "2026-01-15", "hasta": "2026-01-16"})
        self.assertIn("es un ticket", r["errores"][0])
        r = self.e.registrar({"tipo": PLANTA, "accion": "para", "recurso": "M1",
                              "desde": "2026-01-09", "hasta": "2026-01-05"})
        self.assertIn("Fecha al revés", r["errores"][0])
        r = self.e.registrar({"tipo": PLANTA, "accion": "reinicia", "recurso": "M1", "fecha": "2026-01-10"})
        self.assertIn("no está parado", r["errores"][0])

    def test_cobro_pago_y_caja_minima(self):
        r = self.e.registrar({"tipo": COBRO_PAGO, "movimiento": "pago", "monto": 80, "fecha": "2026-01-10",
                              "cuenta": "CTA-1"})
        self.assertTrue(r["aceptado"])
        self.assertEqual(self.e.caja["CTA-1"], 20)                         # 100 − 80
        self.assertIn("por debajo de la caja mínima", r["avisos"][0])      # 20 < 50: el hecho se acepta y avisa
        r = self.e.registrar({"tipo": COBRO_PAGO, "movimiento": "cobro", "monto": 200, "fecha": "2026-01-10",
                              "cuenta": "CTA-1", "ticket": "FI-0001"})
        self.assertEqual((self.e.ticket("FI-0001")["estado"], self.e.caja["CTA-1"]), ("tomado", 220))
        r = self.e.registrar({"tipo": COBRO_PAGO, "movimiento": "pago", "monto": 203, "fecha": "2026-01-10",
                              "cuenta": "CTA-1", "ticket": "FI-0001"})
        self.assertEqual(self.e.ticket("FI-0001")["estado"], "pagado")
        self.assertAlmostEqual(self.e.ticket("FI-0001")["interes_pagado"], 3.0)   # 203 − 200
        r = self.e.registrar({"tipo": COBRO_PAGO, "movimiento": "pago", "monto": 203, "fecha": "2026-01-10",
                              "cuenta": "CTA-1", "ticket": "FI-0001"})
        self.assertIn("«pagado» → «pagado»", r["errores"][0])

    def test_no_conformidad_en_ejecucion_y_terminada(self):
        self.e.registrar(pedido())
        nc = {"tipo": NO_CONFORMIDAD, "ot": "OT-0001", "cantidad_mala": 2, "fecha": "2026-01-10"}
        self.assertIn("no se ha empezado", self.e.registrar(nc)["errores"][0])
        self.assertTrue(self.e.mover("OT-0001", "en ejecución", origen="costos")["aceptado"])
        r = self.e.registrar(nc)
        self.assertTrue(r["aceptado"], r)
        self.assertEqual(self.e.ticket("OT-0001")["reproceso"], 2)
        self.assertTrue(self.e.mover("OT-0001", "terminado", origen="costos")["aceptado"])
        r = self.e.registrar(dict(nc, cantidad_mala=1, documento="NC-2"))
        self.assertTrue(r["aceptado"], r)
        rep = self.e.ticket("OT-0002")
        self.assertEqual((rep["estado"], rep["cantidad"], rep["precio"], rep["reproceso_de"]),
                         ("comprometido", 1, 0, "OT-0001"))
        self.assertEqual(self.e.ticket("OT-0001")["estado"], "terminado")  # no vuelve atrás
        r = self.e.registrar(dict(nc, cantidad_mala=8))                    # 10 − 3 malas = 7 buenas
        self.assertIn("mayor que lo que queda bueno", r["errores"][0])

    def test_cambio_de_maestro_con_vigencia(self):
        r = self.e.registrar({"tipo": DATO_MAESTRO, "campo": "tasa", "objeto": "general", "valor": 0.02,
                              "desde": "2026-03-01"})
        self.assertTrue(r["aceptado"], r)
        self.assertEqual(self.e.valor_vigente("tasa", fecha=D("2026-02-15")), 0.015)
        self.assertEqual(self.e.valor_vigente("tasa", fecha=D("2026-03-10")), 0.02)
        h = self.e.historial_maestro("tasa")
        self.assertEqual((h[0]["hasta"], h[1]["hasta"]), (D("2026-02-28"), None))   # cerrado, no borrado
        r = self.e.registrar({"tipo": DATO_MAESTRO, "campo": "tasa", "objeto": "general", "valor": 0.018,
                              "desde": "2026-02-01"})
        self.assertIn("reescribiría la historia", r["errores"][0])
        r = self.e.registrar({"tipo": DATO_MAESTRO, "campo": "capacidad", "objeto": "M9", "valor": 8,
                              "desde": "2026-02-01"})
        self.assertIn("no es un recurso", r["errores"][0])


class B3_MaquinaDeEstados(unittest.TestCase):
    def setUp(self):
        self.e = base()
        self.e.registrar(pedido())

    def test_terminado_no_vuelve_a_en_ejecucion(self):
        self.e.mover("OT-0001", "en ejecución", "costos")
        self.e.mover("OT-0001", "terminado", "costos")
        r = self.e.mover("OT-0001", "en ejecución", "costos")
        self.assertFalse(r["aceptado"])
        self.assertIn("«terminado» → «en ejecución»", r["errores"][0])
        self.assertIn("estado final", r["errores"][0])
        r = self.e.registrar({"tipo": PEDIDO, "accion": "cancela", "ot": "OT-0001"})
        self.assertIn("«terminado» → «cancelado»", r["errores"][0])

    def test_nombre_de_estado_incorrecto_no_se_corrige(self):
        r = self.e.mover("OT-0001", "en curso", "costos")
        self.assertIn("¿Quiso decir «en ejecución»?", r["errores"][0])
        self.assertEqual(self.e.ticket("OT-0001")["estado"], "comprometido")

    def test_saltos_y_estados_que_no_existen(self):
        r = self.e.mover("OT-0001", "terminado", "costos")                  # comprometido → terminado salta
        self.assertFalse(r["aceptado"])
        r = self.e.mover("FI-0001", "cancelado", "gerente")
        self.assertIn("no es un estado de FINANCIAMIENTO", r["errores"][0])
        r = self.e.mover("OT-0001", "cancelado", "cliente")
        self.assertIn("Origen", r["errores"][0])

    def test_inversion_y_plan(self):
        r = self.e.crear_ticket("INVERSIÓN", {"activo": "Horno 2", "costo": 120, "capacidad": 10, "vida_util": 4},
                                origen="plan")
        self.assertEqual((r["id"], r["estado"]), ("IN-0001", "propuesto"))
        for paso in ("aprobado", "instalado", "en uso"):
            self.assertTrue(self.e.mover("IN-0001", paso, "gerente")["aceptado"])
        self.assertEqual([h["estado"] for h in self.e.ticket("IN-0001")["historial"]],
                         ["propuesto", "aprobado", "instalado", "en uso"])
        self.assertFalse(self.e.mover("IN-0001", "aprobado", "gerente")["aceptado"])


class B3_Correcciones(unittest.TestCase):
    def test_correccion_es_otro_hecho_y_se_aplica_en_su_lugar(self):
        e = base()
        e.registrar(pedido())
        r1 = e.registrar(llegada(documento="GUIA-001"))                 # se registró 6; en realidad llegaron 5
        self.assertEqual((e.stock["PVC"], e.ticket("CO-0001")["estado"]), (10, "recibido"))
        e.registrar({"tipo": COBRO_PAGO, "movimiento": "cobro", "monto": 10, "fecha": "2026-01-10", "cuenta": "CTA-1"})
        r2 = e.registrar(llegada(cantidad=5, documento="GUIA-001", corrige=r1["id"]))
        self.assertTrue(r2["aceptado"], r2)
        self.assertEqual(e.stock["PVC"], 9)                               # 4 + 5
        self.assertEqual(e.ticket("CO-0001")["estado"], "comprometido")   # faltan 1: la compra sigue abierta
        self.assertEqual([x["id"] for x in e.eventos], ["E-0001", "E-0002", "E-0003", "E-0004"])  # nada se borró
        self.assertEqual(e.evento("E-0002")["anulado_por"], "E-0004")
        self.assertEqual(e.evento("E-0002")["cantidad"], 6)               # el original queda tal cual
        r3 = e.registrar(llegada(cantidad=4, corrige="E-0002"))
        self.assertIn("ya fue corregido por E-0004", r3["errores"][0])

    def test_documento_repetido(self):
        e = base()
        e.registrar(llegada(cantidad=3, documento="GUIA-9"))
        r = e.registrar(llegada(cantidad=3, documento="GUIA-9"))
        self.assertIn("ya está registrado en E-0001", r["errores"][0])

    def test_correccion_que_rompe_lo_posterior_se_rechaza(self):
        e = base()
        r1 = e.registrar(pedido())
        e.mover("OT-0001", "en ejecución", "costos")
        r = e.registrar(pedido(producto="P9", corrige=r1["id"]))
        self.assertFalse(r["aceptado"])
        self.assertEqual(e.ticket("OT-0001")["producto"], "P1")

    def test_reproducir_da_lo_mismo_que_registrar_uno_por_uno(self):
        a, b = base(), base()
        hechos = [pedido(), llegada(cantidad=4), pedido(producto="P2", cantidad=3, precio=90),
                  {"tipo": PLANTA, "accion": "para", "recurso": "M2", "desde": "2026-01-10", "hasta": "2026-01-11"},
                  {"tipo": COBRO_PAGO, "movimiento": "pago", "monto": 30, "fecha": "2026-01-09", "cuenta": "CTA-1"}]
        for h in hechos:
            self.assertTrue(a.registrar(h)["aceptado"])
        for h in hechos:
            b.registrar(h)
        self.assertEqual(foto(a), foto(b))
        nuevo = a._reproducir(a.operaciones)
        self.assertEqual(nuevo["tickets"], a.tickets)
        self.assertEqual((a.stock["PVC"], a.caja["CTA-1"]), (8, 70))      # 4+4 ; 100−30


class Vencidos(unittest.TestCase):
    def test_camion_que_no_llego_es_ticket_vencido_no_evento(self):
        e = base()
        self.assertEqual(e.vencidos(), [])
        e.avanzar("2026-01-13")                                           # la compra debía llegar el 12
        v = e.vencidos()
        self.assertEqual(v, [{"ticket": "CO-0001", "esperado": D("2026-01-12"), "falta": 6}])
        with self.assertRaises(Rechazo):
            e.avanzar("2026-01-01")


if __name__ == "__main__":
    unittest.main(verbosity=2)
