"""Contrato T25.4 → T23.5 con oráculo en moneda funcional y dos empresas."""
import hashlib
import json
from decimal import Decimal
from pathlib import Path
import tempfile
import unittest

from openpyxl import load_workbook

from src.reyna_local import store
from src.reyna_local.motor_espejo import Error as MotorError
from src.reyna_local.receipt_audit import audit_receipts


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tests/fixtures/ola1/Sistema_Costos.xlsx"
CASE = ROOT / "tests/fixtures/d9/caso_t23_3_t23_5_cierre.json"
METHOD = "VNR_PRUEBA"
PERIOD = "2026-04"


class ExternalVNR(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.service = store.Store(self.root / "espacios")
        self.case = json.loads(CASE.read_text())
        self.assertEqual(hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                         self.case["source_fixture"]["sha256"])

    def create(self, external=True, configure=None):
        book = load_workbook(SOURCE)
        try:
            if external:
                book["METODO_REGISTRADO"].append([METHOD, "1.0", "APROBADO", "proveedor ficticio",
                                                   "Oráculo de prueba", 20260401, "COSTO_CONTABLE"])
            book["EXISTENCIA"].append(["CAJA_SINT", "ALM1", 12, 600, 50, "A"])
            book["EXISTENCIA"].append(["CAJA4KG", "ALM1", 5, 505, 101, "A"])
            book["CTA_GASTO"].append([PERIOD, "ALM1", "REBAJA_VNR", 77, "S", "A"])
            if configure:
                configure(book)
            path = self.root / "caso.xlsx"
            book.save(path)
        finally:
            book.close()
        space = self.service.create({"name": "Prueba T25.4", "workbook_path": str(path)})
        self.space = space["id"]
        return space

    def produce(self, company="B", period=PERIOD):
        for body in self.case["test_setup"]["events"]:
            body = json.loads(json.dumps(body))
            body["header"]["EMP"] = company
            body["header"]["PER"] = period
            status, reply = self.service.execute(self.space, body)
            self.assertEqual(status, 200, reply)

    def delivery(self, fingerprint, amount, user="JCOSTOS", company="B", period=PERIOD):
        return {"transaction": "T25.4", "user": user, "request_id": "entrega-" + fingerprint,
                "header": {"EMP": company, "PER": period, "PRS_METODO": METHOD, "PRS_VER": "1.0",
                           "PRS_HUELLA": fingerprint},
                "lines": [{"PRS_TIPO": "EXISTENCIA", "PRS_CONC": "REBAJA",
                           "PRS_CLAVE": "CAJA_SINT|ALM1", "PRS_VALOR": amount}]}

    def close(self, key, fingerprint=None, period=PERIOD):
        body = {"user": "JCOSTOS", "request_id": key, "period": period}
        if fingerprint is not None:
            body["result_hash"] = fingerprint
        return self.service.close_month(self.space, body)

    def tables(self):
        raw = self.service.path(self.space).read_bytes()
        return store.load_data(raw)[0]

    def row(self, tables, name, **keys):
        rows = [dict(zip(tables[name]["h"], r)) for r in tables[name]["r"]]
        found = [r for r in rows if all(r[k] == v for k, v in keys.items())]
        self.assertEqual(len(found), 1, (name, keys, found))
        return found[0]

    def assert_accounts(self, amount):
        tables = self.tables()
        stock = self.row(tables, "EXISTENCIA", EXI_EMP="B", EXI_REC="CAJA_SINT", EXI_ALM="ALM1")
        self.assertEqual(stock["EXI_CAN"], 2500)
        self.assertEqual(stock["EXI_VAL"], 25500 - amount)
        expected_vnr = 7 if amount == 8000 else 8
        self.assertEqual(stock["EXI_CPU"], expected_vnr)
        adj = self.row(tables, "AJUSTE_VNR", AVN_EMP="B", AVN_PER=PERIOD, AVN_REC="CAJA_SINT", AVN_ALM="ALM1")
        self.assertEqual((adj["AVN_CPU"], adj["AVN_VNR"], adj["AVN_REB"]),
                         (10.2, expected_vnr, amount))
        gasto = {"CGA_CON": "REBAJA_VNR", "CGA_PER": PERIOD, "CGA_CEN": "ALM1"}
        self.assertEqual(self.row(tables, "CTA_GASTO", CGA_EMP="B", **gasto)["CGA_MTO"], amount)
        self.assertEqual(self.row(tables, "CTA_GASTO", CGA_EMP="A", **gasto)["CGA_MTO"], 77)
        for resource, expected in (("CAJA_SINT", 600), ("CAJA4KG", 505)):
            self.assertEqual(self.row(tables, "EXISTENCIA", EXI_REC=resource, EXI_EMP="A",
                                      EXI_ALM="ALM1")["EXI_VAL"], expected)
        return tables

    def test_cierre_externo_concilia_una_huella_exacta(self):
        def foreign_run(book):
            for company in ("A", "*"):
                book["CORRIDA_METODO"].append([METHOD, "1.0", PERIOD, company, "001", "OTRO", "RECIBIDO", 1])
                book["RESULTADO_METODO"].append([METHOD, "1.0", PERIOD, company, "001",
                                                  "EXISTENCIA", "CAJA_SINT|ALM1", "REBAJA", 100])
        self.assertTrue(self.create(configure=foreign_run)["result_port_enabled"])
        self.produce()
        amount = (Decimal("25500") / 2500 - (9 - 1)) * 2500
        for invalid in ("", "X" * 21, " abc", 123):
            with self.subTest(huella=invalid):
                invalid_delivery = self.delivery("reemplazar", 1)
                invalid_delivery["header"]["PRS_HUELLA"] = invalid
                with self.assertRaises(store.Problem) as exc:
                    self.service.execute(self.space, invalid_delivery)
                self.assertEqual(exc.exception.status, 400)
                with self.assertRaises(store.Problem) as exc:
                    self.close("invalida", invalid)
                self.assertEqual(exc.exception.status, 400)
        for fingerprint, value in (("1", 500), ("001", int(amount))):
            delivery = self.delivery(fingerprint, value, "MODELO1" if fingerprint == "1" else "JCOSTOS")
            status, reply = self.service.execute(self.space, delivery)
            self.assertEqual(status, 200, reply)
            self.assertEqual(self.service.execute(self.space, delivery), (status, reply))
        with self.assertRaises(store.Problem) as missing_hash:
            self.close("falta", None)
        self.assertEqual(missing_hash.exception.status, 422)
        with self.assertRaises(store.Problem) as unknown:
            self.close("desconocida", "X")
        self.assertEqual(unknown.exception.status, 422)
        self.assertEqual(self.tables()["AJUSTE_VNR"]["r"], [])
        status, reply = self.close("cerrar", "001")
        self.assertEqual(status, 200, reply)
        tables = self.assert_accounts(amount)
        for company in ("A", "*"):
            foreign = self.row(tables, "RESULTADO_METODO", RES_EMP=company, RES_HUELLA="001")
            self.assertEqual(foreign["RES_VALOR"], 100)
        for fingerprint, value in (("1", 500), ("001", amount)):
            self.assertEqual(self.row(tables, "CORRIDA_METODO", COR_EMP="B", COR_HUELLA=fingerprint)["COR_EST"],
                             "RECIBIDO")
            self.assertEqual(self.row(tables, "RESULTADO_METODO", RES_EMP="B",
                                      RES_HUELLA=fingerprint)["RES_VALOR"], value)
        self.assertEqual(self.close("cerrar", "001"), (status, reply))
        with self.assertRaises(store.Problem) as error:
            self.close("cerrar", "1")
        self.assertEqual(error.exception.status, 409)
        self.assertTrue(audit_receipts(self.service.path(self.space))["valid"])

    def test_cierre_base_conserva_ambito(self):
        self.create(external=False)
        self.produce()
        with self.assertRaises(store.Problem) as error:
            self.close("seleccion-sin-externo", "superflua")
        self.assertEqual(error.exception.status, 422)
        status, reply = self.close("base")
        self.assertEqual(status, 200, reply)
        self.assertEqual(self.assert_accounts(8000)["RESULTADO_METODO"]["r"], [])

    def test_duplicado_existencia_y_perfil(self):
        def duplicates(book):
            for _ in range(2):
                book["EXISTENCIA"].append(["CAJA4KG", "ALM1", 3, 9, 3, "B"])
        self.create(configure=duplicates)
        status, reply = self.service.execute(self.space, self.case["test_setup"]["events"][0])
        self.assertEqual(status, 422, reply)
        self.assertIn("duplicada", reply["error"])
        status, reply = self.service.execute(self.space, self.delivery("sin-permiso", 50, "ALMACEN1"))
        self.assertEqual(status, 422, reply)
        tables = self.tables()
        self.assertEqual(tables["RESULTADO_METODO"]["r"], [])
        permisos = {(r[0], r[1]) for r in tables["PERFIL_TRX"]["r"]}
        self.assertEqual({perfil for perfil, trx in permisos if trx == "T25.4"},
                         {"INTEGRACION", "COSTOS", "DESARROLLO"})
        self.assertEqual({perfil for perfil, trx in permisos if trx == "T23.5"}, {"COSTOS", "PILOTO"})

    def test_rollback_por_falta_de_conciliacion(self):
        def omit_expense(book):
            sheet = book["OME"]
            for row in sheet.iter_rows(min_row=2):
                if row[0].value == "OP-VNR-REB" and row[2].value == "M-ACU-CGA-VNR":
                    sheet.delete_rows(row[0].row)
                    return
            self.fail("No se encontró el escritor de gasto que se intenta omitir.")

        self.create(configure=omit_expense)
        self.produce()
        status, reply = self.service.execute(self.space, self.delivery("correcta", 5500))
        self.assertEqual(status, 200, reply)
        before = self.tables()
        status, reply = self.close("sin-gasto", "correcta")
        self.assertEqual(status, 422, reply)
        self.assertTrue(any("no concilia" in step.get("error", "") for step in reply["steps"]), reply)
        after = self.tables()
        for name in before:
            if name != store.RECEIPTS:
                self.assertEqual(before[name], after[name], name)

    def test_libro_antiguo_y_empresa_solo_integradora(self):
        def old_book(book):
            del book["CORRIDA_METODO"]
            for name in ("TOP", "TRX_CAMPO"):
                sheet = book[name]
                for row in range(sheet.max_row, 1, -1):
                    if sheet.cell(row, 1).value == "T25.4":
                        sheet.delete_rows(row)
            book["PERFIL_TRX"].append(["SOLO_T254", "T25.4"])
            book["USUARIO"].append(["AGENTE_A", "sin clave", "SOLO_T254", "A"])
            book["USUARIO_PERFIL"].append(["AGENTE_A", "SOLO_T254"])

        space = self.create(configure=old_book)
        self.assertEqual(space["company_code"], "B")
        self.assertFalse(self.service.get(self.space)["result_port_enabled"])
        with self.assertRaises(store.Problem) as error:
            self.service.execute(self.space, self.delivery("123", 20))
        self.assertEqual(error.exception.status, 422)

    def test_esquema_y_claves_del_puerto(self):
        motor = store.Motor.__new__(store.Motor)
        motor.tr = {"EMP": "B"}
        for name, columns in {
            "EXISTENCIA": ("EXI_EMP", "EXI_REC", "EXI_ALM"),
            "CORRIDA_METODO": ("COR_EMP", "COR_METODO", "COR_VER", "COR_PER", "COR_HUELLA"),
            "RESULTADO_METODO": ("RES_EMP", "RES_METODO", "RES_VER", "RES_PER", "RES_HUELLA",
                                 "RES_TIPO", "RES_CLAVE", "RES_CONC"),
        }.items():
            with self.subTest(table=name):
                row = ["B", *["prueba"] * (len(columns) - 1)]
                motor.T = {name: {"h": list(columns), "r": [row, list(row)]}}
                with self.assertRaisesRegex(MotorError, "duplicada"):
                    motor.coincide(name, [])
                for bad_columns in (list(columns[1:]), [*columns, "OTRA_EMP"]):
                    motor.T = {name: {"h": bad_columns, "r": []}}
                    with self.assertRaisesRegex(MotorError, "ambigua"):
                        motor.coincide(name, [])

    def test_dos_productos_concilian_un_gasto_de_almacen(self):
        def opening(book):
            book["EXISTENCIA"].append(["DESCARTE_SINT", "ALM1", 10, 20, 2, "B"])
        self.create(configure=opening)
        self.produce()
        delivery = self.delivery("dos-productos", 5500)
        delivery["lines"].append({"PRS_TIPO": "EXISTENCIA", "PRS_CLAVE": "DESCARTE_SINT|ALM1",
                                  "PRS_CONC": "REBAJA", "PRS_VALOR": 10})
        status, reply = self.service.execute(self.space, delivery)
        self.assertEqual(status, 200, reply)
        status, reply = self.close("gasto-agrupado", "dos-productos")
        self.assertEqual(status, 200, reply)
        tables = self.tables()
        gasto = self.row(tables, "CTA_GASTO", CGA_EMP="B", CGA_PER=PERIOD,
                         CGA_CEN="ALM1", CGA_CON="REBAJA_VNR")
        esperado = {"CAJA_SINT": Decimal("5500"), "DESCARTE_SINT": 10 * (2 - Decimal("1"))}
        self.assertEqual(gasto["CGA_MTO"], sum(esperado.values()))
        for producto, importe in esperado.items():
            adjust = self.row(tables, "AJUSTE_VNR", AVN_EMP="B", AVN_PER=PERIOD,
                              AVN_REC=producto, AVN_ALM="ALM1")
            detail = self.row(tables, "RESULTADO_METODO", RES_EMP="B", RES_PER=PERIOD,
                              RES_CLAVE=producto + "|ALM1", RES_HUELLA="dos-productos")
            self.assertEqual(adjust["AVN_REB"], importe)
            self.assertEqual(detail["RES_VALOR"], importe)

    def test_cierre_ignora_cargas_anteriores_reintentables(self):
        def mark_error(book):
            book["CARGA"]["E2"] = "ERROR"
            book["CARGA"]["F2"] = "Intento previo conservado"
        self.create(external=False, configure=mark_error)
        original = self.tables()["CARGA"]["r"]
        status, reply = self.close("solo-cadena-nueva")
        self.assertEqual(status, 200, reply)
        tables = self.tables()
        self.assertEqual(tables["CARGA"]["r"][:len(original)], original)
        self.assertEqual(len(tables["CARGA"]["r"]), len(original) + len(reply["steps"]))

    def test_recepcion_exige_aprobacion_y_fecha_efectiva(self):
        def methods(book):
            book["METODO_REGISTRADO"].append(["FUTURO", "1.0", "APROBADO", "sintético",
                                               "prueba", 20260402, "COSTO_CONTABLE"])
            book["METODO_REGISTRADO"].append(["BORRADOR", "1.0", "EN_PRUEBA", "sintético",
                                               "prueba", 20260301, "COSTO_CONTABLE"])
        self.create(configure=methods)
        for method, message in (("FUTURO", "efectivo"), ("BORRADOR", "APROBADO")):
            data = self.delivery(method, 10)
            data["header"]["PRS_METODO"] = method
            with self.assertRaisesRegex(store.Problem, message) as exc:
                self.service.execute(self.space, data)
            self.assertEqual(exc.exception.status, 422)
        tables = self.tables()
        for name in ("CORRIDA_METODO", "RESULTADO_METODO"):
            self.assertEqual(tables[name]["r"], [])

    def test_rebaja_mayor_al_valor_de_existencia_revierte_cierre(self):
        self.create()
        self.produce()
        status, reply = self.service.execute(self.space, self.delivery("excesiva", 30000))
        self.assertEqual(status, 200, reply)
        before = self.tables()
        status, reply = self.close("rechazar-excesiva", "excesiva")
        self.assertEqual(status, 422, reply)
        self.assertTrue(any("excede el valor" in step.get("error", "") for step in reply["steps"]), reply)
        after = self.tables()
        for name in before:
            if name != store.RECEIPTS:
                self.assertEqual(before[name], after[name], name)

    def test_conciliacion_detecta_doble_consumo_en_el_cierre(self):
        def duplicate_consumer(book):
            book["OME"].append(["OP-VNR-EXT", 2, "M-PC-VNR-RES"])

        self.create(configure=duplicate_consumer)
        self.produce()
        self.assertEqual(self.service.execute(self.space, self.delivery("doble", 5500))[0], 200)
        before = self.tables()
        status, reply = self.close("doble-consumo", "doble")
        self.assertEqual(status, 422, reply)
        self.assertTrue(any("más de una vez" in step.get("error", "") for step in reply["steps"]), reply)
        after = self.tables()
        for name in before:
            if name != store.RECEIPTS:
                self.assertEqual(before[name], after[name], name)

    def test_conciliacion_detecta_escritor_de_cpu_ausente(self):
        def omit_unit_cost(book):
            sheet = book["MCA"]
            for row in range(sheet.max_row, 1, -1):
                if sheet.cell(row, 1).value == "M-ACT-EXI-VNR" and sheet.cell(row, 3).value == "EXI_CPU":
                    sheet.delete_rows(row)
                    return
            self.fail("No se encontró el escritor de EXI_CPU que se intenta omitir.")

        self.create(configure=omit_unit_cost)
        self.produce()
        self.assertEqual(self.service.execute(self.space, self.delivery("sin-cpu", 5500))[0], 200)
        before = self.tables()
        status, reply = self.close("cierre-sin-cpu", "sin-cpu")
        self.assertEqual(status, 422, reply)
        self.assertTrue(any("costo unitario" in step.get("error", "") for step in reply["steps"]), reply)
        after = self.tables()
        for name in before:
            if name != store.RECEIPTS:
                self.assertEqual(before[name], after[name], name)

    def test_acepta_resultado_cero_con_existencia_agotada(self):
        def exhausted_stock(book):
            book["EXISTENCIA"].append(["CAJA_SINT", "ALM2", 0, 0, 0, "B"])
        self.create(configure=exhausted_stock)
        self.produce()
        delivery = self.delivery("cero", 5500)
        delivery["lines"].append({"PRS_TIPO": "EXISTENCIA", "PRS_CLAVE": "CAJA_SINT|ALM2",
                                  "PRS_CONC": "REBAJA", "PRS_VALOR": 0})
        self.assertEqual(self.service.execute(self.space, delivery)[0], 200)
        status, reply = self.close("cierre-cero", "cero")
        self.assertEqual(status, 200, reply)
        stock = self.row(self.tables(), "EXISTENCIA", EXI_EMP="B", EXI_REC="CAJA_SINT", EXI_ALM="ALM2")
        self.assertEqual((stock["EXI_CAN"], stock["EXI_VAL"], stock["EXI_CPU"]), (0, 0, 0))

    def test_cierre_conserva_codigos_textuales_numericos(self):
        def textual_codes(book):
            for sheet in book.worksheets:
                headers = [sheet.cell(1, col).value for col in range(1, sheet.max_column + 1)]
                for col, header in enumerate(headers, 1):
                    if header in ("EMP_COD", "EMP") or (isinstance(header, str) and header.endswith("_EMP")):
                        for row in range(2, sheet.max_row + 1):
                            if sheet.cell(row, col).value == "B":
                                sheet.cell(row, col).value = "001"
                    if header == "PER_COD" or header == "PER" or (isinstance(header, str) and header.endswith("_PER")):
                        for row in range(2, sheet.max_row + 1):
                            if sheet.cell(row, col).value == PERIOD:
                                sheet.cell(row, col).value = "001"
            period = book["PERIODO"]
            period.insert_rows(2)
            for col, value in enumerate(("1", "001", 20260401, 20260430, "A"), 1):
                period.cell(2, col).value = value
            book["CTA_GASTO"].append(["001", "ALM1", "REBAJA_VNR", 0, "S", "1"])

        space = self.create(configure=textual_codes)
        self.assertEqual(space["company_code"], "001")
        self.produce(company="001", period="001")
        status, reply = self.service.execute(self.space,
                                             self.delivery("codigos-001", 5500, company="001", period="001"))
        self.assertEqual(status, 200, reply)
        status, reply = self.close("cierre-001", "codigos-001", period="001")
        self.assertEqual(status, 200, reply)
        tables = self.tables()
        self.row(tables, "RESULTADO_METODO", RES_EMP="001", RES_PER="001",
                 RES_HUELLA="codigos-001", RES_CLAVE="CAJA_SINT|ALM1")
        period_001 = self.row(tables, "PERIODO", PER_COD="001", PER_EMP="001")
        period_1 = self.row(tables, "PERIODO", PER_COD="1", PER_EMP="001")
        self.assertEqual((period_001["PER_EST"], period_1["PER_EST"]), ("C", "A"))
        foreign_expense = self.row(tables, "CTA_GASTO", CGA_PER="001", CGA_CEN="ALM1",
                                   CGA_CON="REBAJA_VNR", CGA_EMP="1")
        self.assertEqual((foreign_expense["CGA_MTO"], foreign_expense["CGA_DED"]), (0, "S"))

    def test_rechaza_si_falta_el_escritor_de_lineas_t25_4(self):
        def remove_line_operation(book):
            sheet = book["TOP"]
            for row in range(sheet.max_row, 1, -1):
                if sheet.cell(row, 1).value == "T25.4" and sheet.cell(row, 3).value == "OP-PRS-LIN":
                    sheet.delete_rows(row)
                    return
            self.fail("No se encontró la operación de líneas T25.4.")

        space = self.create(configure=remove_line_operation)
        self.assertFalse(space["result_port_enabled"])
        before = self.service.get(self.space)["version"]
        with self.assertRaises(store.Problem) as error:
            self.service.execute(self.space, self.delivery("sin-lineas", 5500))
        self.assertEqual(error.exception.status, 422)
        self.assertEqual(self.service.get(self.space)["version"], before)
        tables = self.tables()
        self.assertEqual(tables["CORRIDA_METODO"]["r"], [])
        self.assertEqual(tables["RESULTADO_METODO"]["r"], [])

    def test_rechaza_si_t235_ya_ejecuto_una_rebaja_base(self):
        def prior_base_rebaja(book):
            book["TOP"].append(["T23.5", 3.5, "OP-VNR", "L"])

        self.create(configure=prior_base_rebaja)
        self.produce()
        self.assertEqual(self.service.execute(self.space, self.delivery("doble-ruta", 5500))[0], 200)
        before = self.tables()
        status, reply = self.close("base-y-externa", "doble-ruta")
        self.assertEqual(status, 422, reply)
        self.assertTrue(any("no concilia" in step.get("error", "") for step in reply["steps"]), reply)
        after = self.tables()
        for name in before:
            if name != store.RECEIPTS:
                self.assertEqual(before[name], after[name], name)

    def test_aplica_el_importe_externo_y_recalcula_cpu(self):
        self.create()
        self.produce()
        amount = 1234.56
        self.assertEqual(self.service.execute(self.space, self.delivery("importe-externo", amount))[0], 200)
        status, reply = self.close("aplicar-importe-externo", "importe-externo")
        self.assertEqual(status, 200, reply)
        tables = self.tables()
        stock = self.row(tables, "EXISTENCIA", EXI_EMP="B", EXI_REC="CAJA_SINT", EXI_ALM="ALM1")
        self.assertEqual(stock["EXI_VAL"], 25500 - amount)
        self.assertAlmostEqual(stock["EXI_CPU"], 9.706176, places=6)
        adjustment = self.row(tables, "AJUSTE_VNR", AVN_EMP="B", AVN_PER=PERIOD,
                              AVN_REC="CAJA_SINT", AVN_ALM="ALM1")
        self.assertEqual(adjustment["AVN_REB"], amount)
        expense = self.row(tables, "CTA_GASTO", CGA_EMP="B", CGA_PER=PERIOD,
                           CGA_CEN="ALM1", CGA_CON="REBAJA_VNR")
        self.assertEqual((expense["CGA_MTO"], expense["CGA_DED"]), (amount, "N"))

    def test_conciliacion_rechaza_deducibilidad_distinta_del_dbd(self):
        def set_deductible(book):
            sheet = book["MCA"]
            for row in range(2, sheet.max_row + 1):
                if sheet.cell(row, 1).value == "M-ACU-CGA-VNR" and sheet.cell(row, 3).value == "CGA_DED":
                    sheet.cell(row, 7).value = "S"
                    return
            self.fail("No se encontró el valor de deducibilidad que se intenta cambiar.")

        self.create(configure=set_deductible)
        self.produce()
        self.assertEqual(self.service.execute(self.space, self.delivery("deducible", 5500))[0], 200)
        before = self.tables()
        status, reply = self.close("rechaza-deducible", "deducible")
        self.assertEqual(status, 422, reply)
        self.assertTrue(any("deducibilidad" in step.get("error", "") for step in reply["steps"]), reply)
        after = self.tables()
        for name in before:
            if name != store.RECEIPTS:
                self.assertEqual(before[name], after[name], name)

    def test_recepcion_rechaza_un_valor_distinto_al_comando(self):
        def literal_amount(book):
            sheet = book["MCA"]
            for row in range(2, sheet.max_row + 1):
                if sheet.cell(row, 1).value == "M-PRS-ACU-RES" and sheet.cell(row, 3).value == "RES_VALOR":
                    sheet.cell(row, 6).value = "LIT"
                    sheet.cell(row, 7).value = 1
                    return
            self.fail("No se encontró el escritor del importe de RESULTADO_METODO.")

        space = self.create(configure=literal_amount)
        before = space["version"]
        status, reply = self.service.execute(self.space, self.delivery("valor-alterado", 5500))
        self.assertEqual(status, 422, reply)
        self.assertIn("valores persistidos", reply["error"])
        self.assertEqual(self.service.get(self.space)["version"], before)
        tables = self.tables()
        self.assertEqual(tables["CORRIDA_METODO"]["r"], [])
        self.assertEqual(tables["RESULTADO_METODO"]["r"], [])

    def test_cpu_se_contrasta_con_formula_dbd_independiente(self):
        def wrong_divisor(book):
            sheet = book["FRM"]
            for row in range(2, sheet.max_row + 1):
                if sheet.cell(row, 1).value == "M-F-VNR-EXT" and sheet.cell(row, 3).value == "DIVIDE":
                    sheet.cell(row, 4).value = None
                    sheet.cell(row, 5).value = 1
                    return
            self.fail("No se encontró el divisor de M-F-VNR-EXT.")

        self.create(configure=wrong_divisor)
        self.produce()
        self.assertEqual(self.service.execute(self.space, self.delivery("cpu-alterado", 5500))[0], 200)
        before = self.tables()
        status, reply = self.close("rechaza-cpu-alterado", "cpu-alterado")
        self.assertEqual(status, 422, reply)
        self.assertTrue(any("costo unitario" in step.get("error", "") for step in reply["steps"]), reply)
        after = self.tables()
        for name in before:
            if name != store.RECEIPTS:
                self.assertEqual(before[name], after[name], name)

    def test_compara_el_periodo_completo_con_otros_productos_y_almacenes(self):
        def other_stock(book):
            book["EXISTENCIA"].append(["SEC", "ALM2", 10, 20, 2, "B"])
            book["TOP"].append(["T23.5", 3.5, "OP-VNR", "L"])

        self.create(configure=other_stock)
        self.produce()
        delivery = self.delivery("otro-almacen", 10)
        delivery["lines"][0]["PRS_CLAVE"] = "SEC|ALM2"
        self.assertEqual(self.service.execute(self.space, delivery)[0], 200)
        before = self.tables()
        status, reply = self.close("rechaza-fuera-alcance", "otro-almacen")
        self.assertEqual(status, 422, reply)
        self.assertTrue(any("no concilia" in step.get("error", "")
                            or "fuera" in step.get("error", "") for step in reply["steps"]), reply)
        after = self.tables()
        for name in before:
            if name != store.RECEIPTS:
                self.assertEqual(before[name], after[name], name)

    def test_entrega_incremental_acumula_y_reemplaza_detalles_por_clave(self):
        def other_stock(book):
            book["EXISTENCIA"].append(["SEC", "ALM2", 10, 20, 2, "B"])

        self.create(configure=other_stock)
        self.produce()
        first = self.delivery("incremental", 5500)
        self.assertEqual(self.service.execute(self.space, first)[0], 200)
        second = self.delivery("incremental", 10)
        second["request_id"] = "entrega-incremental-2"
        second["lines"][0]["PRS_CLAVE"] = "SEC|ALM2"
        self.assertEqual(self.service.execute(self.space, second)[0], 200)
        third = self.delivery("incremental", 5400)
        third["request_id"] = "entrega-incremental-3"
        self.assertEqual(self.service.execute(self.space, third)[0], 200)
        tables = self.tables()
        header = self.row(tables, "CORRIDA_METODO", COR_EMP="B", COR_PER=PERIOD,
                          COR_HUELLA="incremental")
        self.assertEqual(header["COR_N"], 3)
        results = [dict(zip(tables["RESULTADO_METODO"]["h"], row))
                   for row in tables["RESULTADO_METODO"]["r"] if row[3] == "B" and row[4] == "incremental"]
        self.assertEqual(len(results), 2)
        by_key = {row["RES_CLAVE"]: row["RES_VALOR"] for row in results}
        self.assertEqual(by_key, {"CAJA_SINT|ALM1": 5400, "SEC|ALM2": 10})
        status, reply = self.close("cierre-incremental", "incremental")
        self.assertEqual(status, 200, reply)
        tables = self.tables()
        caja = self.row(tables, "EXISTENCIA", EXI_EMP="B", EXI_REC="CAJA_SINT", EXI_ALM="ALM1")
        sec = self.row(tables, "EXISTENCIA", EXI_EMP="B", EXI_REC="SEC", EXI_ALM="ALM2")
        self.assertEqual((caja["EXI_VAL"], sec["EXI_VAL"]), (20100, 10))

    def test_acepta_y_aplica_rebaja_positiva_menor_a_un_millonimo(self):
        def other_stock(book):
            book["EXISTENCIA"].append(["SEC", "ALM2", 10, 20, 2, "B"])

        self.create(configure=other_stock)
        self.produce()
        amount = 0.0000001
        delivery = self.delivery("rebaja-pequena", amount)
        delivery["lines"][0]["PRS_CLAVE"] = "SEC|ALM2"
        self.assertEqual(self.service.execute(self.space, delivery)[0], 200)
        status, reply = self.close("cierre-rebaja-pequena", "rebaja-pequena")
        self.assertEqual(status, 200, reply)
        tables = self.tables()
        stock = self.row(tables, "EXISTENCIA", EXI_EMP="B", EXI_REC="SEC", EXI_ALM="ALM2")
        self.assertAlmostEqual(stock["EXI_VAL"], 20 - amount, places=10)
        self.assertEqual(stock["EXI_CPU"], 2)
        adjustment = self.row(tables, "AJUSTE_VNR", AVN_EMP="B", AVN_PER=PERIOD,
                              AVN_REC="SEC", AVN_ALM="ALM2")
        self.assertEqual(adjustment["AVN_REB"], amount)

    def test_rebaja_pequena_con_saldo_inicial_grande_no_falla_por_cancelacion(self):
        def large_stock(book):
            book["EXISTENCIA"].append(["SEC", "ALM2", 1_000_000, 100_000_000, 100, "B"])

        self.create(configure=large_stock)
        self.produce()
        delivery = self.delivery("precision-monetaria", 0.01)
        delivery["lines"][0]["PRS_CLAVE"] = "SEC|ALM2"
        self.assertEqual(self.service.execute(self.space, delivery)[0], 200)
        status, reply = self.close("cierre-precision-monetaria", "precision-monetaria")
        self.assertEqual(status, 200, reply)
        stock = self.row(self.tables(), "EXISTENCIA", EXI_EMP="B", EXI_REC="SEC", EXI_ALM="ALM2")
        self.assertEqual(stock["EXI_VAL"], 100_000_000 - 0.01)

    def test_metodo_externo_exige_corrida_aunque_falte_el_consumidor(self):
        def remove_external_selection(book):
            sheet = book["TOP"]
            for row in range(sheet.max_row, 1, -1):
                if sheet.cell(row, 1).value == "T23.5" and sheet.cell(row, 3).value == "OP-VNR-SEL":
                    sheet.delete_rows(row)
                    return
            self.fail("No se encontró OP-VNR-SEL en T23.5.")

        self.create(configure=remove_external_selection)
        self.produce()
        before = self.service.get(self.space)["version"]
        with self.assertRaises(store.Problem) as error:
            self.close("sin-consumidor", None)
        self.assertEqual(error.exception.status, 422)
        self.assertIn("huella", str(error.exception))
        self.assertEqual(self.service.get(self.space)["version"], before)

    def test_cierre_aplica_metodo_vigente_aunque_otra_corrida_comparta_huella(self):
        def competing_method(book):
            for row in book["METODO_REGISTRADO"].iter_rows(min_row=2):
                if row[0].value == METHOD and row[1].value == "1.0":
                    row[5].value = 20260331
            book["METODO_REGISTRADO"].append(["OTRO", "1.0", "APROBADO ", "sintético",
                                                "más reciente", 20260401, "COSTO_CONTABLE"])
            book["CORRIDA_METODO"].append(["OTRO", "1.0", PERIOD, "B", "VNR-5500",
                                            "JCOSTOS", "RECIBIDO", 1])
            book["RESULTADO_METODO"].append(["OTRO", "1.0", PERIOD, "B", "VNR-5500",
                                              "EXISTENCIA", "CAJA_SINT|ALM1", "REBAJA", 900])
            book["CORRIDA_METODO"].append(["OTRO", "0.9", PERIOD, "B", "VNR-5500",
                                            "JCOSTOS", "RECIBIDO", 1])
            book["RESULTADO_METODO"].append(["OTRO", "0.9", PERIOD, "B", "VNR-5500",
                                              "EXISTENCIA", "CAJA_SINT|ALM1", "REBAJA", 123])

        self.create(configure=competing_method)
        self.assertEqual(
            store.effective_cost_accounting_method(self.tables(), "B", PERIOD),
            ("OTRO", "1.0", "BASE_AJUSTES_NIC2"),
        )
        self.produce()
        status, reply = self.service.execute(self.space, self.delivery("VNR-5500", 5500))
        self.assertEqual(status, 200, reply)
        status, reply = self.close("cierre-metodo-vigente", "VNR-5500")
        self.assertEqual(status, 200, reply)

        tables = self.tables()
        stock = self.row(tables, "EXISTENCIA", EXI_EMP="B", EXI_REC="CAJA_SINT", EXI_ALM="ALM1")
        adjustment = self.row(tables, "AJUSTE_VNR", AVN_EMP="B", AVN_PER=PERIOD,
                              AVN_REC="CAJA_SINT", AVN_ALM="ALM1")
        gasto = self.row(tables, "CTA_GASTO", CGA_EMP="B", CGA_PER=PERIOD,
                         CGA_CEN="ALM1", CGA_CON="REBAJA_VNR")
        received = self.row(tables, "RESULTADO_METODO", RES_EMP="B", RES_METODO=METHOD,
                            RES_HUELLA="VNR-5500")
        vigente = self.row(tables, "RESULTADO_METODO", RES_EMP="B", RES_METODO="OTRO",
                           RES_VER="1.0", RES_HUELLA="VNR-5500")
        anterior = self.row(tables, "RESULTADO_METODO", RES_EMP="B", RES_METODO="OTRO",
                            RES_VER="0.9", RES_HUELLA="VNR-5500")
        self.assertEqual((stock["EXI_VAL"], stock["EXI_CPU"]), (24600, 9.84))
        self.assertEqual((adjustment["AVN_REB"], gasto["CGA_MTO"]), (900, 900))
        self.assertEqual((received["RES_VALOR"], vigente["RES_VALOR"], anterior["RES_VALOR"]),
                         (5500, 900, 123))
