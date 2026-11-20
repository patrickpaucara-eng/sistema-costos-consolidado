"""D9 regression cases for event-driven account writes and company isolation."""

from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import shutil
import tempfile
import unittest
from unittest.mock import patch

from openpyxl import load_workbook

from src.reyna_local import store
from src.reyna_local.motor_espejo import Error


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/ola1/Sistema_Costos.xlsx"
CASE_FILE = ROOT / "tests/fixtures/d9/caso_t15_eventos.json"
EVENT_CASE_FILE = ROOT / "tests/fixtures/d9/caso_t17_t19_t20_eventos.json"
ACCOUNT_TABLES = (
    "CTA_ACTOR", "CTA_CENTRO", "CTA_GASTO", "CTA_OBJ_PER",
    "CTA_OBJ_REC", "CTA_FUNCION", "CTA_VTA_PER",
)


class D9EventAccounts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.workbook = self.directory / "origen.xlsx"
        shutil.copyfile(FIXTURE, self.workbook)
        self.case = json.loads(CASE_FILE.read_text(encoding="utf-8"))
        self.event_case = json.loads(EVENT_CASE_FILE.read_text(encoding="utf-8"))
        self.assertEqual(hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
                         self.case["source_fixture"]["sha256"])
        self.assertEqual(hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),
                         self.event_case["source_fixture"]["sha256"])
        self.verify_case_inputs_against_fixture()
        self.verify_source_scenarios(self.event_case)
        self.seed_foreign_company_accounts()
        self.local_store = store.Store(self.directory / "workspaces")
        self.workspace = self.local_store.create({
            "name": "D9 cuentas por evento",
            "workbook_path": str(self.workbook),
        })["id"]

    def seed_foreign_company_accounts(self):
        book = load_workbook(self.workbook)
        try:
            rows = {
                "CTA_OBJ_PER": {
                    "COP_OBJ": "OS-01", "COP_PER": "2026-04", "COP_MAT": 77,
                    "COP_IND": 0, "COP_PERD": 0, "COP_TRF": 0, "COP_MOD": 0,
                    "COP_IND_APL": 0, "COP_EMP": "A",
                },
                "CTA_OBJ_REC": {
                    "COR_OBJ": "OS-01", "COR_REC": "CAJA4KG", "COR_PER": "2026-04",
                    "COR_CAN_PERM": 11, "COR_CAN_REAL": 13, "COR_MTO": 17, "COR_EMP": "A",
                },
                "CTA_GASTO": {
                    "CGA_PER": "2026-04", "CGA_CEN": "LINEA1",
                    "CGA_CON": "PERDIDA_ANORMAL", "CGA_MTO": 66,
                    "CGA_DED": "N", "CGA_EMP": "A",
                },
                "CTA_CENTRO": {
                    "CCE_CEN": "LINEA1", "CCE_PER": "2026-04", "CCE_SUM": 123,
                    "CCE_HORAS": 0, "CCE_TASA": 0, "CCE_ASIG": 0, "CCE_OCIO": 0,
                    "CCE_FUN": "PRD", "CCE_RECIB": 0, "CCE_DIST": 0,
                    "CCE_VARH": 0, "CCE_PROP": 0, "CCE_FIJO": 0, "CCE_EMP": "A",
                },
                "CTA_FUNCION": {
                    "CFU_PER": "2026-04", "CFU_FUN": "PRD", "CFU_MTO": 456, "CFU_EMP": "A",
                },
                "CTA_GASTO_DESMEDRO": {
                    "CGA_PER": "2026-04", "CGA_CEN": "ALM1", "CGA_CON": "DESMEDRO",
                    "CGA_MTO": 66, "CGA_DED": "S", "CGA_EMP": "A",
                },
                "CTA_VTA_PER": {
                    "VPE_PER": "2026-04", "VPE_ING": 700, "VPE_CST": 400, "VPE_EMP": "A",
                },
            }
            for name, values in rows.items():
                sheet = book["CTA_GASTO" if name == "CTA_GASTO_DESMEDRO" else name]
                columns = [cell.value for cell in sheet[1]]
                sheet.append([values.get(column) for column in columns])
        finally:
            book.save(self.workbook)
            book.close()

    def verify_source_scenarios(self, case):
        book = load_workbook(FIXTURE, read_only=True, data_only=True)
        try:
            sheet = book["ESCENARIO"]
            rows = iter(sheet.values)
            columns = next(rows)
            scenarios = {row[0]: dict(zip(columns, row)) for row in rows if row[0] is not None}
            for source in case["source_fixture"]["source_scenarios"]:
                actual = scenarios[source["id"]]
                self.assertEqual(actual["ESC_TRX"], source["transaction"])
                self.assertEqual(actual["ESC_TRAMA"], source["trama"])
                self.assertEqual(actual["ESC_ESPERA"], "OK")
        finally:
            book.close()

    def source_row(self, sheet_name, keys):
        book = load_workbook(FIXTURE, read_only=True, data_only=True)
        try:
            rows = iter(book[sheet_name].values)
            columns = next(rows)
            matches = [dict(zip(columns, row)) for row in rows
                       if all(dict(zip(columns, row)).get(k) == v for k, v in keys.items())]
            self.assertEqual(len(matches), 1, f"Fuente única en {sheet_name}: {keys}")
            return matches[0]
        finally:
            book.close()

    def purchase(self, lot):
        scenario = self.case["scenario"]
        return {
            "transaction": "T14", "user": "ALMACEN1", "request_id": lot["request_id"],
            "header": {
                "FECHA": lot["date"], "PER": lot["period"],
                "EMP": scenario["company"], "REC": scenario["resource"], "ALM": "ALM1",
                "CANT": int(lot["quantity"]), "CU_DOC": float(lot["document_unit_price"]),
                "MON": lot["document_currency"], "IMP": self.case["scenario"]["tax_code"],
            },
            "lines": [],
        }

    def consumption(self, request_id=None):
        scenario = self.case["scenario"]
        movement = scenario["consumption"]
        return {
            "transaction": "T15", "user": "SUPERV1",
            "request_id": request_id or movement["request_id"],
            "header": {
                "FECHA": movement["date"], "PER": movement["period"], "EMP": scenario["company"],
                "OBJ": scenario["object"], "CEN": scenario["center"], "REC": scenario["resource"],
                "ALM": "ALM1", "CANT": int(movement["quantity"]),
            },
            "lines": [],
        }

    def verify_case_inputs_against_fixture(self):
        book = load_workbook(FIXTURE, read_only=True, data_only=True)
        try:
            scenario = self.case["scenario"]

            def row_for(sheet_name, keys):
                sheet = book[sheet_name]
                rows = sheet.values
                columns = next(rows)
                matches = [dict(zip(columns, row)) for row in rows
                           if all(dict(zip(columns, row)).get(k) == v for k, v in keys.items())]
                self.assertEqual(len(matches), 1, f"Fuente única en {sheet_name}: {keys}")
                return matches[0]

            company = row_for("EMPRESA", {"EMP_COD": scenario["company"]})
            self.assertEqual(company["EMP_MON_FUN"], scenario["functional_currency"])
            resource = row_for("RECURSO", {
                "REC_COD": scenario["resource"], "REC_EMP": scenario["company"],
            })
            self.assertEqual(resource["REC_UNI"], "UND")
            product = row_for("OBJETO", {"OBJ_NUM": scenario["object"], "OBJ_EMP": scenario["company"]})
            component = row_for("COMPONENTE", {
                "CMP_PRO": product["OBJ_PRO"], "CMP_REC": scenario["resource"],
                "CMP_EMP": scenario["company"],
            })
            self.assertEqual(Decimal(str(product["OBJ_CAN"])), Decimal(scenario["output_units"]))
            self.assertEqual(Decimal(str(component["CMP_CAN_EST"])),
                             Decimal(scenario["standard_resource_per_output"]))
            self.assertEqual(Decimal(str(component["CMP_MERMA"])), Decimal(scenario["normal_loss_percent"]))
            for lot in scenario["purchase_lots"]:
                rate = row_for("TIPO_CAMBIO", {
                    "TCB_MON": lot["document_currency"],
                    "TCB_FEC": lot["exchange_rate_effective_date"],
                })
                self.assertEqual(Decimal(str(rate["TCB_VAL"])),
                                 Decimal(lot["functional_currency_per_document_currency"]))
            tax = row_for("IMPUESTO", {"IMP_COD": scenario["tax_code"]})
            self.assertEqual(tax["IMP_RECUP"] == "S", scenario["tax_recoverable"])
        finally:
            book.close()

    def independent_expected(self):
        """Calcula el oráculo decimal desde eventos y dimensiones, sin llamar al motor de costos."""
        scenario = self.case["scenario"]
        rounding = self.case["independent_calculation"]["rounding_from_configured_formulas"]
        qty_places = rounding["converted_unit_cost_places"]
        money_places = rounding["line_amount_places"]
        qty_quantum = Decimal(1).scaleb(-qty_places)
        money_quantum = Decimal(1).scaleb(-money_places)
        total_qty = Decimal(0)
        total_value = Decimal(0)
        for lot in scenario["purchase_lots"]:
            quantity = Decimal(lot["quantity"])
            unit_cost = (Decimal(lot["document_unit_price"])
                         * Decimal(lot["functional_currency_per_document_currency"])).quantize(
                             qty_quantum, rounding=ROUND_HALF_UP)
            line_value = (quantity * unit_cost).quantize(money_quantum, rounding=ROUND_HALF_UP)
            total_qty += quantity
            total_value += line_value
        unit_cost = (total_value / total_qty).quantize(qty_quantum, rounding=ROUND_HALF_UP)
        allowed = (Decimal(scenario["output_units"])
                   * Decimal(scenario["standard_resource_per_output"])
                   * (Decimal(1) + Decimal(scenario["normal_loss_percent"]) / Decimal(100)))
        allowed = allowed.quantize(Decimal(1).scaleb(-rounding["allowed_quantity_places"]),
                                   rounding=ROUND_HALF_UP)
        actual = Decimal(scenario["consumption"]["quantity"])
        excess = max(Decimal(0), actual - allowed)
        consumed_value = (actual * unit_cost).quantize(money_quantum, rounding=ROUND_HALF_UP)
        object_value = (allowed * unit_cost).quantize(money_quantum, rounding=ROUND_HALF_UP)
        loss_value = (excess * unit_cost).quantize(
            Decimal(1).scaleb(-rounding["loss_amount_places"]), rounding=ROUND_HALF_UP)
        self.assertEqual(consumed_value, object_value + loss_value)
        ending_qty = total_qty - actual
        ending_value = (ending_qty * unit_cost).quantize(money_quantum, rounding=ROUND_HALF_UP)
        return {
            "receipt_quantity": total_qty,
            "receipt_value": total_value,
            "weighted_average_unit_cost": unit_cost,
            "allowed_quantity": allowed,
            "actual_quantity": actual,
            "abnormal_excess_quantity": excess,
            "actual_consumption_value": consumed_value,
            "allowed_object_material_cost": object_value,
            "abnormal_loss_cost": loss_value,
            "ending_inventory_quantity": ending_qty,
            "ending_inventory_value": ending_value,
        }

    @staticmethod
    def persisted_row(tables, table_name, key):
        columns = tables[table_name]["h"]
        return next(
            dict(zip(columns, row)) for row in tables[table_name]["r"]
            if all(str(dict(zip(columns, row)).get(column)) == str(value)
                   for column, value in key.items())
        )

    def execute(self, body):
        return self.local_store.execute(self.workspace, body)

    def load_tables(self):
        path = self.local_store.path(self.workspace)
        tables, _ = store.load_data(store.content_bytes(path))
        return tables

    def account_snapshot(self):
        tables = self.load_tables()
        return {name: (tables[name]["h"], [list(row) for row in tables[name]["r"]])
                for name in ACCOUNT_TABLES}

    @staticmethod
    def company_rows(tables, name, company_column):
        columns = tables[name]["h"]
        index = columns.index(company_column)
        return {str(row[index]): dict(zip(columns, row)) for row in tables[name]["r"]}

    def prepare_purchases(self):
        for lot in self.case["scenario"]["purchase_lots"]:
            body = self.purchase(lot)
            status, result = self.execute(body)
            self.assertEqual(status, 200, result)

    def test_evento_actualiza_cuenta_de_su_empresa_y_reintento_no_duplica(self):
        independent = self.independent_expected()
        expected_math = self.case["independent_calculation"]["results"]
        for field, value in independent.items():
            self.assertEqual(str(value), expected_math[field], f"Oráculo independiente: {field}")
        expected_accounts = self.case["expected_account_rows"]
        self.prepare_purchases()
        status, result = self.execute(self.consumption())
        self.assertEqual(status, 200, result)

        tables = self.load_tables()
        for name, expected in expected_accounts.items():
            actual = self.persisted_row(tables, name, expected["key"])
            for field, expected_value in expected["values"].items():
                if expected_value is None:
                    self.assertIsNone(actual[field], f"{name}.{field}")
                else:
                    self.assertEqual(Decimal(str(actual[field])), Decimal(expected_value),
                                     f"{name}.{field}")
        self.assertEqual(self.persisted_row(tables, "CTA_OBJ_REC", {"COR_EMP": "A"})[
            "COR_CAN_REAL"], 13)
        self.assertEqual(self.persisted_row(tables, "CTA_GASTO", {"CGA_EMP": "A"})[
            "CGA_MTO"], 66)
        self.assertEqual(self.persisted_row(tables, "CTA_OBJ_PER", {"COP_EMP": "A"})[
            "COP_MAT"], 77)

        self.assertEqual(independent["actual_consumption_value"],
                         independent["allowed_object_material_cost"] + independent["abnormal_loss_cost"])
        self.assertEqual(independent["receipt_value"],
                         independent["actual_consumption_value"] + independent["ending_inventory_value"])

        snapshot = self.account_snapshot()
        replay_status, replay = self.execute(self.consumption())
        self.assertEqual(replay_status, status)
        self.assertEqual(replay, result)
        self.assertEqual(self.account_snapshot(), snapshot)

    def test_fallo_tras_escritura_de_cuenta_revierte_el_evento(self):
        self.prepare_purchases()
        before = self.load_tables()
        accounts_before = self.account_snapshot()
        event_tables_before = {
            name: (before[name]["h"], [list(row) for row in before[name]["r"]])
            for name in ("EVENTO", "LINEA", "KARDEX", "EXISTENCIA")
        }
        original = store.Motor.met

        def fail_after_resource_account(motor, code):
            original(motor, code)
            if code == "M-ACU-COR-V":
                raise Error("Fallo inyectado tras escribir CTA_OBJ_REC.")

        with patch.object(store.Motor, "met", new=fail_after_resource_account):
            status, result = self.execute(self.consumption("d9-falla"))

        self.assertEqual(status, 422, result)
        self.assertIn("Fallo inyectado", result["error"])
        self.assertEqual(self.account_snapshot(), accounts_before)
        after = self.load_tables()
        for name, previous in event_tables_before.items():
            self.assertEqual((after[name]["h"], after[name]["r"]), previous, name)

    def test_t17_acumula_costo_en_centro_y_funcion_con_moneda_funcional(self):
        inputs = self.event_case["t17"]["inputs"]
        expected = self.event_case["t17"]["expected"]
        independent_total = sum(
            (Decimal(item["document_amount"]) * Decimal(item["rate"])).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            for item in inputs
        )
        self.assertEqual(independent_total, Decimal(expected["functional_cost_total"]))
        usd_rate = self.source_row("TIPO_CAMBIO", {"TCB_MON": "USD", "TCB_FEC": 20260405})
        self.assertEqual(Decimal(str(usd_rate["TCB_VAL"])), Decimal("3.72"))

        for item in inputs:
            status, result = self.execute({
                "transaction": "T17", "user": "CONTAB1", "request_id": item["request_id"],
                "header": {
                    "FECHA": item["date"], "PER": item["period"], "EMP": item["company"],
                    "CEN": item["center"], "MON": item["currency"],
                },
                "lines": [{"REC": item["resource"], "MTO_DOC": float(item["document_amount"])}],
            })
            self.assertEqual(status, 200, result)

        tables = self.load_tables()
        for table_name in ("CTA_CENTRO", "CTA_FUNCION"):
            row_case = expected["center_row" if table_name == "CTA_CENTRO" else "function_row"]
            row = self.persisted_row(tables, table_name, row_case["key"])
            for field, value in row_case["values"].items():
                actual = row[field]
                if field == "CCE_FUN":
                    self.assertEqual(actual, value)
                else:
                    self.assertEqual(Decimal(str(actual)), Decimal(value), f"{table_name}.{field}")
        self.assertEqual(self.persisted_row(tables, "CTA_CENTRO", {"CCE_EMP": "A"})["CCE_SUM"], 123)
        self.assertEqual(self.persisted_row(tables, "CTA_FUNCION", {"CFU_EMP": "A"})["CFU_MTO"], 456)

    def test_t19_registra_perdida_con_concepto_deducibilidad_y_valor_independiente(self):
        self.prepare_purchases()
        status, result = self.execute(self.consumption())
        self.assertEqual(status, 200, result)
        case = self.event_case["t19"]
        expected = case["expected"]
        rule = self.source_row("REGLA", {"REG_COD": case["reason"]})
        self.assertEqual(rule["REG_CON"], expected["concept_from_rule"])
        self.assertEqual(rule["REG_DED"], expected["deductibility_from_rule"])
        independent_unit_cost = self.independent_expected()["weighted_average_unit_cost"]
        independent_amount = (Decimal(case["quantity"]) * independent_unit_cost).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        self.assertEqual(independent_amount, Decimal(expected["amount"]))

        status, result = self.execute({
            "transaction": "T19", "user": "ALMACEN1", "request_id": case["request_id"],
            "header": {
                "FECHA": case["date"], "PER": case["period"], "EMP": case["company"],
                "ALM": case["warehouse"], "CEN": case["center"], "MOT": case["reason"],
            },
            "lines": [{"REC": case["resource"], "CANT": int(case["quantity"])}],
        })
        self.assertEqual(status, 200, result)
        tables = self.load_tables()
        expense = expected["expense_row"]
        actual = self.persisted_row(tables, "CTA_GASTO", expense["key"])
        self.assertEqual(Decimal(str(actual["CGA_MTO"])), Decimal(expense["values"]["CGA_MTO"]))
        self.assertEqual(actual["CGA_DED"], expense["values"]["CGA_DED"])
        self.assertEqual(self.persisted_row(tables, "CTA_GASTO", {
            "CGA_PER": "2026-04", "CGA_CEN": "ALM1", "CGA_CON": "DESMEDRO", "CGA_EMP": "A",
        })["CGA_MTO"], 66)
        stock = self.persisted_row(tables, "EXISTENCIA", {"EXI_REC": "CAJA4KG", "EXI_ALM": "ALM1", "EXI_EMP": "B"})
        self.assertEqual(Decimal(str(stock["EXI_CAN"])), Decimal(expected["ending_stock"]["EXI_CAN"]))
        self.assertEqual(Decimal(str(stock["EXI_VAL"])).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                         Decimal(expected["ending_stock"]["EXI_VAL"]))

    def test_t20_acumula_ingreso_costo_y_respeta_saldo_de_otra_empresa(self):
        case = self.event_case["t20"]
        expected = case["expected"]
        book = load_workbook(self.workbook)
        try:
            values = [case["product"], case["warehouse"],
                      float(case["opening_balance_test_setup"]["quantity"]),
                      float(case["opening_balance_test_setup"]["value"]),
                      float(case["opening_balance_test_setup"]["unit_cost"]), case["company"]]
            book["EXISTENCIA"].append(values)
            book.save(self.workbook)
        finally:
            book.close()
        self.workspace = self.local_store.create({
            "name": "D9 T20 saldo inicial de prueba", "workbook_path": str(self.workbook),
        })["id"]

        rate = Decimal(case["exchange_rate"])
        revenue = sum(
            (Decimal(line["quantity"]) * Decimal(line["document_unit_price"]) * rate).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            for line in case["lines"]
        )
        total_quantity = sum(Decimal(line["quantity"]) for line in case["lines"])
        unit_cost = Decimal(case["opening_balance_test_setup"]["unit_cost"])
        cost = (total_quantity * unit_cost).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        self.assertEqual(revenue, Decimal(expected["revenue_total"]))
        self.assertEqual(cost, Decimal(expected["cost_of_sales"]))
        self.assertEqual(revenue - cost, Decimal(expected["margin"]))

        body = {
            "transaction": "T20", "user": "COMERC1", "request_id": case["request_id"],
            "header": {
                "FECHA": case["date"], "PER": case["period"], "EMP": case["company"],
                "ALM": case["warehouse"], "CLI": case["client"], "MON": case["currency"],
            },
            "lines": [{
                "REC": case["product"], "CANT": int(line["quantity"]),
                "PVU": float(line["document_unit_price"]),
            } for line in case["lines"]],
        }
        status, result = self.execute(body)
        self.assertEqual(status, 200, result)
        tables = self.load_tables()
        account = expected["account_row"]
        actual = self.persisted_row(tables, "CTA_VTA_PER", account["key"])
        for field, value in account["values"].items():
            self.assertEqual(Decimal(str(actual[field])), Decimal(value), f"CTA_VTA_PER.{field}")
        sale_lines = [row for row in tables["VENTA"]["r"] if row[tables["VENTA"]["h"].index("VTA_EMP")] == "B"]
        self.assertEqual(len(sale_lines), 2)
        for field, value in (("VTA_ING", expected["revenue_total"]),
                             ("VTA_CST", expected["cost_of_sales"]),
                             ("VTA_MAR", expected["margin"])):
            col = tables["VENTA"]["h"].index(field)
            self.assertEqual(sum(Decimal(str(row[col])) for row in sale_lines), Decimal(value), field)
        stock = self.persisted_row(tables, "EXISTENCIA", {
            "EXI_REC": case["product"], "EXI_ALM": case["warehouse"], "EXI_EMP": case["company"],
        })
        self.assertEqual(Decimal(str(stock["EXI_CAN"])), Decimal(expected["ending_stock"]["EXI_CAN"]))
        self.assertEqual(Decimal(str(stock["EXI_VAL"])), Decimal(expected["ending_stock"]["EXI_VAL"]))
        self.assertEqual(self.persisted_row(tables, "CTA_VTA_PER", {
            "VPE_PER": "2026-04", "VPE_EMP": "A",
        })["VPE_ING"], 700)
        before = self.load_tables()
        replay_status, replay = self.execute(body)
        self.assertEqual(replay_status, status)
        self.assertEqual(replay, result)
        self.assertEqual(self.load_tables(), before)

    def test_actualizar_filtra_por_empresa_aunque_la_clave_dbd_la_omita(self):
        motor = store.Motor.__new__(store.Motor)
        motor.T = {"CTA_PRUEBA": {
            "h": ["CTA_COD", "CTA_EMP", "CTA_MTO"],
            "r": [["MISMA-CLAVE", "A", 10], ["MISMA-CLAVE", "B", 20]],
        }}
        motor.tr = {"EMP": "B", "CLAVE": "MISMA-CLAVE", "VARIACION": 5}
        motor.undo = []
        mca = [
            ("M-ACT-PRUEBA", 1, "CTA_COD", "K", None, "VAR", "CLAVE"),
            ("M-ACT-PRUEBA", 2, "CTA_MTO", "V", "SUMA", "VAR", "VARIACION"),
        ]

        motor.m_ACTUALIZAR("M-ACT-PRUEBA", "CTA_PRUEBA", None, "S", None, mca)

        self.assertEqual(motor.T["CTA_PRUEBA"]["r"], [
            ["MISMA-CLAVE", "A", 10], ["MISMA-CLAVE", "B", 25],
        ])


if __name__ == "__main__":
    unittest.main()
