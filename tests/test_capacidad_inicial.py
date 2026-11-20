"""HTTP/Excel acceptance for the real Ola 1 interpreter and workbook.

Run with python -m unittest discover -s tests -v. To use another fixture,
set REYNA_TEST_WORKBOOK to its file path. The workbook is copied per test.
"""

import concurrent.futures
import hashlib
import http.client
import json
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from xml.etree import ElementTree
from zipfile import ZipFile

from openpyxl import load_workbook


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = Path(
    os.environ.get("REYNA_TEST_WORKBOOK", ROOT / "tests/fixtures/ola1/Sistema_Costos.xlsx")
)
STOCK_KEY = {"EXI_REC": "CAJA4KG", "EXI_ALM": "ALM1", "EXI_EMP": "B"}


class CapacidadInicial(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.directory = Path(temp.name)
        self.data_dir = self.directory / "workspaces"
        self.workbook = self.directory / "origen.xlsx"
        shutil.copyfile(FIXTURE, self.workbook)
        self.start_server()

    def start_server(self):
        server = subprocess.Popen(
            [
                sys.executable, "-u", "-m", "reyna_local",
                "--data-dir", str(self.data_dir), "--port", "0",
            ],
            cwd=ROOT,
            env={
                "PATH": os.defpath, "HOME": str(self.directory),
                "PYTHONPATH": str(ROOT / "src"), "PYTHONDONTWRITEBYTECODE": "1",
                "LC_ALL": "C.UTF-8",
            },
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True,
        )
        self.addCleanup(self.stop_server, server)
        output = queue.Queue()

        def read_output():
            for line in server.stdout:
                output.put(line)
            output.put(None)

        threading.Thread(target=read_output, daemon=True).start()
        startup = []
        try:
            while True:
                line = output.get(timeout=10)
                if line is None:
                    self.fail("El servidor terminó al iniciar:\n" + "".join(startup))
                startup.append(line)
                address = re.search(r"http://127\.0\.0\.1:(\d+)", line)
                if address:
                    self.server = server
                    self.port = int(address.group(1))
                    return self.port
        except queue.Empty:
            self.fail("El servidor no anunció su puerto:\n" + "".join(startup))

    @staticmethod
    def stop_server(server):
        if server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=3)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=3)
        server.stdout.close()

    def request(self, method, path, body=None, headers=None, port=None):
        connection = http.client.HTTPConnection("127.0.0.1", port or self.port, timeout=20)
        try:
            payload = None if body is None else json.dumps(body).encode()
            request_headers = {"Content-Type": "application/json", **(headers or {})}
            connection.request(method, path, body=payload, headers=request_headers)
            response = connection.getresponse()
            raw = response.read()
            try:
                result = json.loads(raw)
            except ValueError:
                result = raw.decode(errors="replace")
            return response.status, result
        finally:
            connection.close()

    def import_workspace(self, name="Caso de compra y consumo"):
        status, result = self.request(
            "POST", "/api/workspaces", {"name": name, "workbook_path": str(self.workbook)},
        )
        self.assertEqual(status, 201, result)
        return f"/api/workspaces/{result['id']}", result["version"]

    @staticmethod
    def compra(request_id, second=False):
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
    def consumo(request_id, quantity):
        return {
            "transaction": "T15", "user": "SUPERV1", "request_id": request_id,
            "header": {
                "FECHA": 20260410, "PER": "2026-04", "EMP": "B",
                "OBJ": "OS-01", "CEN": "LINEA1", "REC": "CAJA4KG",
                "ALM": "ALM1", "CANT": quantity,
            },
            "lines": [],
        }

    def execute(self, workspace, body, expected_status=200, port=None):
        status, result = self.request("POST", workspace + "/execute", body, port=port)
        self.assertEqual(status, expected_status, result)
        return result

    def close_month(self, workspace, body, expected_status=200, port=None):
        status, result = self.request("POST", workspace + "/close-month", body, port=port)
        self.assertEqual(status, expected_status, result)
        return result

    def table(self, workspace, table):
        status, result = self.request("GET", f"{workspace}/tables/{table}")
        self.assertEqual(status, 200, result)
        return result

    def stock(self, workspace):
        table = self.table(workspace, "EXISTENCIA")
        rows = [dict(zip(table["columns"], row)) for row in table["rows"]]
        return [
            (row["EXI_CAN"], row["EXI_VAL"], row["EXI_CPU"])
            for row in rows if all(row.get(key) == value for key, value in STOCK_KEY.items())
        ]

    def workbook_path(self, workspace):
        return self.data_dir / workspace.rsplit("/", 1)[-1] / "libro.xlsx"

    def workbook_table(self, workspace, table):
        with self.workbook_path(workspace).open("rb") as file:
            book = load_workbook(file, read_only=True)
            try:
                return list(book[table].values)
            finally:
                book.close()

    def test_compra_consumo_saldo_y_reapertura(self):
        source_digest = hashlib.sha256(self.workbook.read_bytes()).hexdigest()
        workspace, version = self.import_workspace()
        detail_status, detail = self.request("GET", workspace)
        self.assertEqual(detail_status, 200, detail)
        self.assertEqual(detail["company_code"], "B")
        self.assertEqual(self.stock(workspace), [])
        self.execute(workspace, self.compra("compra-uno"))
        self.execute(workspace, self.compra("compra-dos", second=True))
        result = self.execute(workspace, self.consumo("consumo", 2600))
        self.assertEqual(result["result"], "OK")
        self.assertEqual(result["version"], version + 3)
        # (2000 × 0.80 × 3.75 + 1000 × 0.85 × 3.72) ÷ 3000 = 3.054.
        # Recoverable IGV is excluded. The remaining 400 units are worth S/ 1221.60.
        [(quantity, amount, unit_cost)] = self.stock(workspace)
        self.assertEqual(quantity, 400)
        self.assertAlmostEqual(amount, 1221.6, places=2)
        self.assertAlmostEqual(unit_cost, 3.054, places=6)
        expected = self.table(workspace, "EXISTENCIA")
        self.stop_server(self.server)
        self.start_server()
        self.assertEqual(self.table(workspace, "EXISTENCIA"), expected)
        rows = self.workbook_table(workspace, "EXISTENCIA")
        self.assertEqual(rows[0], tuple(expected["columns"]))
        self.assertEqual(rows[1], tuple(expected["rows"][0]))
        self.assertEqual(hashlib.sha256(self.workbook.read_bytes()).hexdigest(), source_digest)

    def test_transaccion_t17_y_limite_de_t16_desde_api(self):
        workspace, _ = self.import_workspace("Costo de centro por API")
        status, detail = self.request("GET", workspace)
        self.assertEqual(status, 200, detail)
        self.assertEqual(detail["transactions"], ["T14", "T15", "T17", "T19", "T20"])
        result = self.execute(workspace, {
            "transaction": "T17", "user": "CONTAB1", "request_id": "api-t17",
            "header": {"FECHA": 20260430, "PER": "2026-04", "EMP": "B", "CEN": "LINEA1", "MON": "PEN"},
            "lines": [{"REC": "DEP_LINEA", "MTO_DOC": 30000}],
        })
        self.assertEqual(result["result"], "OK")
        status, result = self.request("POST", workspace + "/execute", {
            "transaction": "T16", "user": "SUPERV1", "request_id": "api-t16",
            "header": {"FECHA": 20260430, "PER": "2026-04", "EMP": "B"}, "lines": [],
        })
        self.assertEqual(status, 400, result)
        self.assertIn("no está habilitada", result["error"])

    def test_importacion_rechaza_dos_empresas_operativas(self):
        book = load_workbook(self.workbook)
        try:
            users = book["USUARIO"]
            source = next(row for row in users.iter_rows(min_row=2, values_only=True) if row[0] == "ALMACEN1")
            users.append(["ALMACENA", source[1], "ALMACEN", "A"])
            book.save(self.workbook)
        finally:
            book.close()
        status, result = self.request(
            "POST", "/api/workspaces",
            {"name": "Dos empresas", "workbook_path": str(self.workbook)},
        )
        self.assertEqual(status, 422, result)
        self.assertIn("un solo ámbito empresarial", result["error"])
        list_status, workspaces = self.request("GET", "/api/workspaces")
        self.assertEqual(list_status, 200, workspaces)
        self.assertEqual(workspaces["workspaces"], [])

    def test_operador_no_puede_cambiar_empresa_del_espacio(self):
        workspace, _ = self.import_workspace()
        body = self.compra("empresa-distinta")
        body["header"]["EMP"] = "A"
        result = self.execute(workspace, body, expected_status=422)
        self.assertIn("Usuario o empresa no autorizados", result["error"])
        self.assertEqual(self.stock(workspace), [])

    def test_cierre_oficial_guarda_una_vez_y_reintenta(self):
        workspace, version = self.import_workspace()
        self.execute(workspace, self.compra("cierre-compra-uno"))
        self.execute(workspace, self.compra("cierre-compra-dos", second=True))
        self.execute(workspace, self.consumo("cierre-consumo", 2600))
        version += 3
        status, detail = self.request("GET", workspace)
        self.assertEqual(status, 200, detail)
        self.assertTrue(detail["close_month_enabled"])
        body = {"period": "2026-04", "user": "JCOSTOS", "request_id": "cierre-abril"}
        result = self.close_month(workspace, body)
        self.assertEqual(result["result"], "OK")
        self.assertEqual([step["step"] for step in result["steps"]],
                         ["T23.1", "T23.2", "T23.3", "T23.5", "T23.9"])
        self.assertEqual(result["version"], version + 5)
        carga = self.workbook_table(workspace, "CARGA")
        self.assertEqual([row[4] for row in carga[-5:]], ["OK"] * 5)
        cuentas = ("CTA_ACTOR", "CTA_CENTRO", "CTA_GASTO", "CTA_OBJ_PER",
                   "CTA_OBJ_REC", "CTA_FUNCION", "CTA_VTA_PER")
        cuentas_tras_cierre = {name: self.workbook_table(workspace, name) for name in cuentas}
        self.stop_server(self.server)
        self.start_server()
        self.assertEqual(self.close_month(workspace, body), result)
        self.assertEqual(len(self.workbook_table(workspace, "CARGA")[-5:]), 5)
        for name, previous in cuentas_tras_cierre.items():
            self.assertEqual(self.workbook_table(workspace, name), previous,
                             f"El reintento del cierre alteró {name}.")
        period_table = self.table(workspace, "PERIODO")
        period = [dict(zip(period_table["columns"], row)) for row in period_table["rows"]]
        self.assertEqual(next(row["PER_EST"] for row in period
                             if row["PER_COD"] == "2026-04" and row["PER_EMP"] == "B"), "C")
        [(quantity, amount, unit_cost)] = self.stock(workspace)
        self.assertEqual(quantity, 400)
        self.assertAlmostEqual(amount, 1221.6, places=2)
        self.assertAlmostEqual(unit_cost, 3.054, places=6)
        changed = {**body, "period": "2026-05"}
        self.close_month(workspace, changed, expected_status=409)

    def test_cierre_fallido_no_persiste_pasos_parciales(self):
        from src.reyna_local import store

        local_store = store.Store(self.data_dir)
        workspace = local_store.create({"name": "Cierre con fallo", "workbook_path": str(self.workbook)})
        identifier = workspace["id"]
        path = Path(workspace["workbook_path"])
        before, _ = store.load_data(path.read_bytes())
        original = store.Motor.ejecutar

        def fail_at_liquidation(motor, transaction, header, user, lines=None):
            if transaction == "T23.3":
                raise RuntimeError("Fallo de liquidación inyectado.")
            return original(motor, transaction, header, user, lines)

        body = {"period": "2026-04", "user": "JCOSTOS", "request_id": "falla-cierre"}
        with patch.object(store.Motor, "ejecutar", new=fail_at_liquidation):
            status, response = local_store.close_month(identifier, body)
        self.assertEqual(status, 422, response)
        self.assertEqual(response["steps"][0]["error"],
                         "La cadena de cierre no pudo completarse: RuntimeError.")
        retry_status, retry = local_store.close_month(identifier, body)
        self.assertEqual(retry_status, status)
        self.assertEqual(retry, response)
        after, _ = store.load_data(path.read_bytes())
        for name in before:
            if name not in (store.META, store.RECEIPTS):
                self.assertEqual(after[name], before[name], f"El cierre fallido alteró {name}.")
        self.assertEqual(store.metadata(after)["version"], workspace["version"])

    def test_reintento_persiste_y_otro_payload_es_conflicto(self):
        workspace, version = self.import_workspace()
        body = self.compra("misma-solicitud")
        result = self.execute(workspace, body)
        self.assertEqual(result["version"], version + 1)
        expected = self.table(workspace, "EXISTENCIA")
        self.assertEqual(self.stock(workspace), [(2000, 6000, 3)])
        self.stop_server(self.server)
        self.start_server()
        self.assertEqual(self.execute(workspace, body), result)
        self.assertEqual(self.table(workspace, "EXISTENCIA"), expected)
        body["header"]["CANT"] = 1000
        self.execute(workspace, body, expected_status=409)
        self.assertEqual(self.table(workspace, "EXISTENCIA"), expected)

    def test_falla_en_segunda_linea_revierte_la_primera(self):
        workspace, version = self.import_workspace()
        before = {
            table: self.table(workspace, table)
            for table in ("EXISTENCIA", "EVENTO", "LINEA", "KARDEX")
        }
        body = {
            "transaction": "T14", "user": "ALMACEN1", "request_id": "dos-lineas",
            "header": {
                "FECHA": 20260421, "PER": "2026-04", "EMP": "B",
                "ALM": "ALM2", "MON": "PEN", "IMP": "IGV",
            },
            "lines": [
                {"REC": "CAJA4KG", "CANT": 100, "CU_DOC": 3},
                {"REC": "HORA_LINEA", "CANT": 1, "CU_DOC": 1},
            ],
        }
        accepted_control = {**body, "request_id": "control", "lines": body["lines"][:1]}
        control_workspace, _ = self.import_workspace("Control de primera línea")
        self.execute(control_workspace, accepted_control)
        self.assertNotEqual(self.table(control_workspace, "EXISTENCIA")["rows"], before["EXISTENCIA"]["rows"])
        failed = self.execute(workspace, body, expected_status=422)
        self.assertEqual(failed["version"], version)
        self.assertIn("inventariable", json.dumps(failed, ensure_ascii=False).lower())
        self.stop_server(self.server)
        self.start_server()
        for table, previous in before.items():
            self.assertEqual(self.table(workspace, table), previous)
        self.assertEqual(self.execute(workspace, body, expected_status=422), failed)

    def test_dos_espacios_aislados_con_la_misma_solicitud(self):
        workspace_a, _ = self.import_workspace("Espacio A")
        workspace_b, _ = self.import_workspace("Espacio B")
        self.assertNotEqual(workspace_a, workspace_b)
        self.execute(workspace_a, self.compra("id-compartido"))
        self.assertEqual(self.stock(workspace_b), [])
        self.execute(workspace_b, self.compra("id-compartido", second=True))
        self.assertEqual(self.stock(workspace_a), [(2000, 6000, 3)])
        self.assertEqual(self.stock(workspace_b), [(1000, 3162, 3.162)])

    def test_concurrencia_no_duplica_ni_pierde_compras(self):
        workspace, version = self.import_workspace()
        first_port = self.port
        second_port = self.start_server()
        barrier = threading.Barrier(3)

        def concurrent_execute(body, port):
            barrier.wait(timeout=5)
            return self.execute(workspace, body, port=port)

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            jobs = [
                pool.submit(concurrent_execute, self.compra("concurrente-uno"), first_port),
                pool.submit(concurrent_execute, self.compra("concurrente-uno"), second_port),
                pool.submit(
                    concurrent_execute, self.compra("concurrente-dos", second=True), second_port,
                ),
            ]
            first, replay, second = [job.result(timeout=25) for job in jobs]
        self.assertEqual(first, replay)
        self.assertEqual({first["version"], second["version"]}, {version + 1, version + 2})
        self.assertEqual(self.stock(workspace), [(3000, 9162, 3.054)])

    def test_reemplazo_fallido_no_publica_filas_ni_recibo_y_respaldo_reabre(self):
        from src.reyna_local import store

        workspace, version = self.import_workspace()
        workspace_id = workspace.rsplit("/", 1)[-1]
        purchase = self.compra("primera")
        first = self.execute(workspace, purchase)
        working_file = self.workbook_path(workspace)
        before = working_file.read_bytes()
        backup_file = working_file.with_name("respaldo.xlsx")
        self.assertTrue(backup_file.is_file())
        real_replace = store.os.replace
        body = self.compra("segunda", second=True)
        local_store = store.Store(self.data_dir)

        def fail_workbook_replace(source, destination, *args, **kwargs):
            if Path(destination) == working_file:
                raise OSError("Falla de reemplazo inyectada por la prueba")
            return real_replace(source, destination, *args, **kwargs)

        with patch.object(store.os, "replace", side_effect=fail_workbook_replace) as replace:
            try:
                status, _ = local_store.execute(workspace_id, body)
            except OSError as error:
                self.assertIn("inyectada", str(error))
            else:
                self.assertGreaterEqual(status, 500)
            self.assertTrue(
                any(Path(call.args[1]) == working_file for call in replace.call_args_list)
            )
        self.assertEqual(working_file.read_bytes(), before)
        second = self.execute(workspace, body)
        self.assertEqual(second["version"], version + 2)
        self.assertEqual(backup_file.read_bytes(), before)
        self.stop_server(self.server)
        shutil.copyfile(backup_file, working_file)
        self.start_server()
        self.assertEqual(self.execute(workspace, purchase), first)
        self.assertEqual(self.stock(workspace), [(2000, 6000, 3)])
        self.assertEqual(self.execute(workspace, body)["version"], version + 2)
        self.assertEqual(self.stock(workspace), [(3000, 9162, 3.054)])

    def test_preserva_partes_ooxml_y_formula_fuera_del_parque(self):
        book = load_workbook(self.workbook)
        try:
            book["INSTALAR"]["A100"] = "=1+2"
            business_sheet = book["EXISTENCIA"]
            business_sheet["E2"].number_format = "0.0000"
            business_sheet["J2"] = "=1+2"
            book.save(self.workbook)
        finally:
            book.close()
        source = self.workbook.read_bytes()
        workspace, _ = self.import_workspace()
        self.execute(workspace, self.compra("partes-ooxml"))
        package_path = self.workbook_path(workspace)
        ns_main = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
        ns_document_rel = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
        with ZipFile(self.workbook) as original, ZipFile(package_path) as updated:
            workbook = ElementTree.fromstring(original.read("xl/workbook.xml"))
            sheet = workbook.find(f".//{ns_main}sheet[@name='INSTALAR']")
            relationship_id = sheet.attrib[ns_document_rel + "id"]
            relationships = ElementTree.fromstring(original.read("xl/_rels/workbook.xml.rels"))
            target = next(r.attrib["Target"] for r in relationships if r.attrib["Id"] == relationship_id)
            sheet_path = target.lstrip("/") if target.startswith("/") else "xl/" + target
            for member in (sheet_path, "xl/styles.xml", "xl/theme/theme1.xml"):
                with self.subTest(member=member):
                    self.assertEqual(updated.read(member), original.read(member))
        updated_book = load_workbook(package_path)
        try:
            self.assertEqual(updated_book["INSTALAR"]["A100"].value, "=1+2")
            self.assertEqual(updated_book["EXISTENCIA"]["J2"].value, "=1+2")
            self.assertEqual(updated_book["EXISTENCIA"]["E2"].value, 3)
            self.assertEqual(updated_book["EXISTENCIA"]["E2"].number_format, "0.0000")
        finally:
            updated_book.close()
        self.assertEqual(self.workbook.read_bytes(), source)

    def test_api_no_publica_credenciales_del_libro(self):
        workspace, _ = self.import_workspace()
        status, summary = self.request("GET", workspace)
        self.assertEqual(status, 200, summary)
        self.assertNotIn("USU_CLAVE", json.dumps(summary))
        for table in ("USUARIO", "SEM_USUARIO"):
            with self.subTest(table=table):
                status, result = self.request("GET", f"{workspace}/tables/{table}")
                self.assertIn(status, (403, 404), result)
                self.assertNotIn("USU_CLAVE", json.dumps(result))

    def test_http_rechaza_origen_ajeno_y_host_ajeno(self):
        workspace, _ = self.import_workspace()
        body = self.compra("origen-rechazado")
        for headers in (
            {"Origin": "https://ajeno.invalid"},
            {"Origin": "https://ajeno.invalid", "Content-Type": "text/plain"},
            {"Host": f"ajeno.invalid:{self.port}"},
        ):
            with self.subTest(headers=headers):
                status, result = self.request("POST", workspace + "/execute", body, headers)
                self.assertIn(status, (400, 403, 415, 421), result)
        self.assertEqual(self.stock(workspace), [])
        status, result = self.request(
            "POST", workspace + "/execute", body,
            {"Origin": f"http://127.0.0.1:{self.port}"},
        )
        self.assertEqual(status, 200, result)


if __name__ == "__main__":
    unittest.main()
