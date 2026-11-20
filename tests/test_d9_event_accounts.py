"""D9 regression cases for event-driven account writes and company isolation."""

from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from openpyxl import load_workbook

from src.reyna_local import store
from src.reyna_local.motor_espejo import Error


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/ola1/Sistema_Costos.xlsx"
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
            }
            for name, values in rows.items():
                sheet = book[name]
                columns = [cell.value for cell in sheet[1]]
                sheet.append([values.get(column) for column in columns])
        finally:
            book.save(self.workbook)
            book.close()

    @staticmethod
    def purchase(request_id, second=False):
        return {
            "transaction": "T14", "user": "ALMACEN1", "request_id": request_id,
            "header": {
                "FECHA": 20260405 if second else 20260310,
                "PER": "2026-04" if second else "2026-03",
                "EMP": "B", "REC": "CAJA4KG", "ALM": "ALM1",
                "CANT": 1000 if second else 2000,
                "CU_DOC": 0.85 if second else 0.80, "MON": "USD", "IMP": "IGV",
            },
            "lines": [],
        }

    @staticmethod
    def consumption(request_id):
        return {
            "transaction": "T15", "user": "SUPERV1", "request_id": request_id,
            "header": {
                "FECHA": 20260410, "PER": "2026-04", "EMP": "B",
                "OBJ": "OS-01", "CEN": "LINEA1", "REC": "CAJA4KG",
                "ALM": "ALM1", "CANT": 2600,
            },
            "lines": [],
        }

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

    def prepare_consumption(self):
        for body in (self.purchase("d9-compra-1"), self.purchase("d9-compra-2", second=True)):
            status, result = self.execute(body)
            self.assertEqual(status, 200, result)

    def test_evento_actualiza_cuenta_de_su_empresa_y_reintento_no_duplica(self):
        self.prepare_consumption()
        status, result = self.execute(self.consumption("d9-consumo"))
        self.assertEqual(status, 200, result)

        tables = self.load_tables()
        rec = self.company_rows(tables, "CTA_OBJ_REC", "COR_EMP")
        self.assertEqual(rec["A"], {
            "COR_OBJ": "OS-01", "COR_REC": "CAJA4KG", "COR_PER": "2026-04",
            "COR_CAN_PERM": 11, "COR_CAN_REAL": 13, "COR_MTO": 17, "COR_EMP": "A",
        })
        self.assertEqual(rec["B"]["COR_CAN_PERM"], 2550)
        self.assertEqual(rec["B"]["COR_CAN_REAL"], 2600)
        self.assertAlmostEqual(rec["B"]["COR_MTO"], 7940.4, places=2)

        expenses = self.company_rows(tables, "CTA_GASTO", "CGA_EMP")
        self.assertEqual(expenses["A"]["CGA_MTO"], 66)
        self.assertAlmostEqual(expenses["B"]["CGA_MTO"], 152.7, places=2)

        objects = self.company_rows(tables, "CTA_OBJ_PER", "COP_EMP")
        self.assertEqual(objects["A"]["COP_MAT"], 77)
        self.assertAlmostEqual(objects["B"]["COP_MAT"], 7787.7, places=2)
        self.assertAlmostEqual(objects["B"]["COP_PERD"], 152.7, places=2)

        snapshot = self.account_snapshot()
        replay_status, replay = self.execute(self.consumption("d9-consumo"))
        self.assertEqual(replay_status, status)
        self.assertEqual(replay, result)
        self.assertEqual(self.account_snapshot(), snapshot)

    def test_fallo_tras_escritura_de_cuenta_revierte_el_evento(self):
        self.prepare_consumption()
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
