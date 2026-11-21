"""Pruebas de la auditoría de recibos sobre copias temporales del piloto."""

from hashlib import sha256
from http.client import HTTPConnection
from io import BytesIO
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
from threading import Thread
import unittest
from zipfile import ZipFile

from src.reyna_local.__main__ import ReynaServer
from src.reyna_local.receipt_audit import _command_identity, audit_receipts
from src.reyna_local.store import META, RECEIPTS, Store, load_data, patch_cells, sheet_parts, write_archive


FIXTURE = Path(__file__).parent / "fixtures" / "ola1" / "Sistema_Costos.xlsx"


def purchase(request_id, april=False):
    return {
        "transaction": "T14", "user": "ALMACEN1", "request_id": request_id,
        "header": {
            "FECHA": 20260405 if april else 20260310, "PER": "2026-04" if april else "2026-03",
            "EMP": "B", "REC": "CAJA4KG", "ALM": "ALM1", "CANT": 1000 if april else 2000,
            "CU_DOC": 0.85 if april else 0.80, "MON": "USD", "IMP": "IGV",
        },
        "lines": [],
    }


def serialized(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


class ReceiptAuditTest(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        source = self.directory / "origen.xlsx"
        shutil.copyfile(FIXTURE, source)
        self.store = Store(self.directory / "espacios")
        workspace = self.store.create({"name": "Auditoría de laboratorio", "workbook_path": str(source)})
        self.identifier = workspace["id"]
        self.workbook = self.store.path(self.identifier)
        self.backup = self.workbook.with_name("respaldo.xlsx")

    def assert_valid_snapshot(self, path, version, receipts):
        before = path.read_bytes()
        self.assertEqual(audit_receipts(path), {
            "valid": True, "workbook_version": version, "expected_version": version,
            "receipt_count": receipts, "issue_count": 0, "issues": [],
        })
        self.assertEqual(path.read_bytes(), before)

    def snapshot_with_edits(self, name, edits):
        snapshot = self.directory / f"{name}.xlsx"
        source = self.workbook.read_bytes()
        with ZipFile(BytesIO(source)) as archive:
            parts = sheet_parts(archive)
            patches = {parts[sheet]: patch_cells(archive.read(parts[sheet]), cells) for sheet, cells in edits.items()}
        write_archive(snapshot, source, patches)
        return snapshot

    def assert_snapshot_issue(self, name, edits, code, sheet, row):
        path = self.snapshot_with_edits(name, edits)
        before = path.read_bytes()
        report = audit_receipts(path)
        self.assertFalse(report["valid"])
        self.assertIn((code, sheet, row), {(item["code"], item["sheet"], item["row"]) for item in report["issues"]})
        self.assertEqual(path.read_bytes(), before)
        return report

    def test_close_command_identity_accepts_optional_textual_result_fingerprint(self):
        base = {"operation": "close_month", "user": "JCOSTOS", "period": "2026-04"}
        external = {**base, "result_hash": "001"}
        self.assertEqual(_command_identity(serialized(base)),
                         {"operation": "close_month", "period": "2026-04"})
        self.assertEqual(_command_identity(serialized(external)),
                         {"operation": "close_month", "period": "2026-04"})
        self.assertIsNone(_command_identity(serialized({**base, "result_hash": " "})))
        self.assertIsNone(_command_identity(serialized({**base, "result_hash": "x" * 21})))
        self.assertIsNone(_command_identity(serialized({**base, "other": "unexpected"})))

    def test_import_version_zero_and_first_success(self):
        self.assert_valid_snapshot(self.workbook, 0, 0)
        self.assertFalse(self.backup.exists())
        command = purchase("compra-única")
        status, response = self.store.execute(self.identifier, command)
        self.assertEqual((status, response["version"]), (200, 1))
        tables, _ = load_data(self.workbook.read_bytes(), {RECEIPTS})
        key, digest, saved_status, saved_response, payload, _ = tables[RECEIPTS]["r"][0]
        self.assertEqual((key, saved_status, json.loads(saved_response)), (command["request_id"], status, response))
        self.assertEqual(payload, serialized({field: value for field, value in command.items() if field != "request_id"}))
        self.assertEqual(digest, sha256(payload.encode("utf-8")).hexdigest())
        self.assert_valid_snapshot(self.workbook, 1, 1)
        self.assert_valid_snapshot(self.backup, 0, 0)

    def test_rejections_preserve_version_and_idempotent_retries(self):
        rejected = purchase("rechazo")
        rejected["header"]["EMP"] = "A"
        status, response = self.store.execute(self.identifier, rejected)
        self.assertEqual((status, response["version"]), (422, 0))
        failed_close = {"period": "2026-04", "user": "desconocido", "request_id": "rechazo-cierre"}
        close_status, close_response = self.store.close_month(self.identifier, failed_close)
        self.assertEqual((close_status, close_response["version"]), (422, 0))
        self.assertEqual(close_response["steps"][0]["result"], "ERROR")
        current, backup = self.workbook.read_bytes(), self.backup.read_bytes()
        self.assertEqual(self.store.execute(self.identifier, rejected), (status, response))
        self.assertEqual(self.store.close_month(self.identifier, failed_close), (close_status, close_response))
        self.assertEqual((self.workbook.read_bytes(), self.backup.read_bytes()), (current, backup))
        self.assert_valid_snapshot(self.workbook, 0, 2)
        self.assert_valid_snapshot(self.backup, 0, 1)

    def test_successful_multistep_close_and_prior_backup(self):
        self.assertEqual(self.store.execute(self.identifier, purchase("marzo"))[0], 200)
        self.assertEqual(self.store.execute(self.identifier, purchase("abril", april=True))[0], 200)
        consume = {"transaction": "T15", "user": "SUPERV1", "request_id": "consumo",
                   "header": {"FECHA": 20260410, "PER": "2026-04", "EMP": "B", "OBJ": "OS-01",
                              "CEN": "LINEA1", "REC": "CAJA4KG", "ALM": "ALM1", "CANT": 2600}, "lines": []}
        self.assertEqual(self.store.execute(self.identifier, consume)[0], 200)
        pre_close = self.workbook.read_bytes()
        status, response = self.store.close_month(
            self.identifier, {"period": "2026-04", "user": "JCOSTOS", "request_id": "cierre-abril"},
        )
        self.assertEqual((status, response["version"]), (200, 8))
        self.assertEqual([item["step"] for item in response["steps"]],
                         ["T23.1", "T23.2", "T23.3", "T23.5", "T23.9"])
        self.assertEqual(self.backup.read_bytes(), pre_close)
        self.assert_valid_snapshot(self.workbook, 8, 4)
        self.assert_valid_snapshot(self.backup, 3, 3)

        trimmed = {**response, "steps": response["steps"][:-1]}
        report = self.assert_snapshot_issue("cierre-pasos", {RECEIPTS: [(5, 4, serialized(trimmed))]},
                                            "receipt_version_mismatch", RECEIPTS, 5)
        self.assertEqual(report["expected_version"], 7)
        self.assertIn("workbook_version_mismatch", {item["code"] for item in report["issues"]})

    def test_tampered_receipts_and_version_report_coordinates(self):
        self.assertEqual(self.store.execute(self.identifier, purchase("identificador-privado"))[0], 200)
        status, response = self.store.execute(self.identifier, purchase("otra-compra", april=True))
        self.assertEqual(status, 200)
        tables, positions = load_data(self.workbook.read_bytes(), {META, RECEIPTS})
        version_row = next(row for row, (key, _) in zip(positions[META], tables[META]["r"]) if key == "version")
        command = tables[RECEIPTS]["r"][1][4]
        current, backup = self.workbook.read_bytes(), self.backup.read_bytes()
        changes = [
            ("digest", RECEIPTS, 3, 2, "0" * 64, "digest_mismatch"),
            ("comando", RECEIPTS, 3, 5, command.replace("ALMACEN1", "usuario-privado"), "digest_mismatch"),
            ("respuesta", RECEIPTS, 3, 4, serialized({**response, "transaction": "T15"}), "invalid_response"),
            ("html-privado", RECEIPTS, 3, 4, "<html>respuesta privada</html>", "invalid_response"),
            ("id-repetido", RECEIPTS, 3, 1, "identificador-privado", "duplicate_request_id"),
            ("id-en-respuesta", RECEIPTS, 3, 4, serialized({**response, "request_id": "valor alterado"}),
             "response_request_id_mismatch"),
            ("id-ausente", RECEIPTS, 3, 1, None, "invalid_request_id"),
            ("estado", RECEIPTS, 3, 3, 422, "response_status_mismatch"),
            ("version-respuesta", RECEIPTS, 3, 4, serialized({**response, "version": 900}), "receipt_version_mismatch"),
            ("version-tipo", RECEIPTS, 3, 4, serialized({**response, "version": True}), "receipt_version_mismatch"),
            ("version-libro", META, version_row, 2, 3, "workbook_version_mismatch"),
        ]
        for name, sheet, row, column, value, code in changes:
            with self.subTest(name=name):
                report = self.assert_snapshot_issue(name, {sheet: [(row, column, value)]}, code, sheet, row)
                result = serialized(report)
                for secret in ("identificador-privado", "usuario-privado", "otra-compra", "respuesta privada", command):
                    self.assertNotIn(secret, result)
        self.assertEqual((self.workbook.read_bytes(), self.backup.read_bytes()), (current, backup))

    def test_api_reports_current_workbook_without_writing_or_leaking_payload(self):
        status, response = self.store.execute(self.identifier, purchase("identificador-privado"))
        self.assertEqual(status, 200)
        path = self.snapshot_with_edits("api", {RECEIPTS: [(2, 4, serialized({**response, "request_id": "privado"}))]})
        shutil.copyfile(path, self.workbook)
        current, backup = self.workbook.read_bytes(), self.backup.read_bytes()
        files = sorted(self.workbook.parent.iterdir())
        server = ReynaServer(self.store.root, 0)
        self.addCleanup(server.server_close)
        thread = Thread(target=server.serve_forever)
        thread.start()
        self.addCleanup(thread.join)
        self.addCleanup(server.shutdown)
        connection = HTTPConnection("127.0.0.1", server.server_port, timeout=10)
        self.addCleanup(connection.close)
        connection.request("GET", f"/api/workspaces/{self.identifier}/audit")
        result = connection.getresponse()
        self.assertEqual(result.status, 200)
        body = result.read()
        self.assertFalse(json.loads(body)["valid"])
        self.assertIn(b"response_request_id_mismatch", body)
        self.assertNotIn(b"privado", body)
        connection.request("GET", "/api/workspaces/espacio-inexistente/audit")
        missing = connection.getresponse()
        self.assertEqual(missing.status, 404)
        self.assertEqual((self.workbook.read_bytes(), self.backup.read_bytes()), (current, backup))
        self.assertEqual(sorted(self.workbook.parent.iterdir()), files)
