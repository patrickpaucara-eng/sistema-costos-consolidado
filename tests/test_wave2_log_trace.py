"""Aceptación HTTP/XLSX de la traza D2 para una compra T14."""

import json
import unittest

import test_capacidad_inicial


class Wave2LogTraceTest(unittest.TestCase):
    def setUp(self):
        self.http = test_capacidad_inicial.CapacidadInicial("runTest")
        self.addCleanup(self.http.doCleanups)
        self.http.setUp()

    def test_compra_confirmada_y_rechazo_idempotente_tras_reapertura(self):
        workspace, initial_version = self.http.import_workspace("Ola 2 D2 · Traza T14")
        purchase = self.http.compra("d2-compra")
        confirmed = self.http.execute(workspace, purchase)
        version = initial_version + 1
        self.assertEqual(confirmed["result"], "OK")
        self.assertEqual(confirmed["version"], version)

        self.http.stop_server(self.http.server)
        self.http.start_server()
        log_table = self.http.workbook_table(workspace, "LOG_TRX")
        bit_table = self.http.workbook_table(workspace, "BITACORA")
        log_header, *log_rows = log_table
        self.assertEqual(len(log_rows), 1)
        log = dict(zip(log_header, log_rows[0]))
        self.assertEqual((log["LOG_TRX"], log["LOG_USR"], log["LOG_EST"]),
                         ("T14", "ALMACEN1", "A"))
        bit_header, *bit_rows = bit_table
        entries = [dict(zip(bit_header, row)) for row in bit_rows]
        self.assertTrue(entries)
        self.assertEqual({(entry["BIT_LOG"], entry["BIT_TRX"], entry["BIT_USR"]) for entry in entries},
                         {(log["LOG_NUM"], "T14", "ALMACEN1")})
        self.assertEqual(log["LOG_NCAMB"], len(entries))

        self.assertEqual(self.http.execute(workspace, purchase), confirmed)
        self.assertEqual(self.http.workbook_table(workspace, "LOG_TRX"), log_table)
        self.assertEqual(self.http.workbook_table(workspace, "BITACORA"), bit_table)

        rejected = self.http.consumo("d2-rechazo", 2600)
        failure = self.http.execute(workspace, rejected, expected_status=422)
        self.assertEqual((failure["result"], failure["request_id"], failure["version"]),
                         ("ERROR", "d2-rechazo", version))
        self.assertEqual(self.http.workbook_table(workspace, "LOG_TRX"), log_table)
        self.assertEqual(self.http.workbook_table(workspace, "BITACORA"), bit_table)

        self.http.stop_server(self.http.server)
        self.http.start_server()
        self.assertEqual(self.http.execute(workspace, rejected, expected_status=422), failure)
        self.assertEqual(self.http.workbook_table(workspace, "LOG_TRX"), log_table)
        self.assertEqual(self.http.workbook_table(workspace, "BITACORA"), bit_table)
        status, detail = self.http.request("GET", workspace)
        self.assertEqual(status, 200, detail)
        self.assertEqual(detail["version"], version)

        header, *rows = self.http.workbook_table(workspace, "_ReynaRecibos")
        receipts = [dict(zip(header, row)) for row in rows]
        self.assertEqual([(receipt["request_id"], receipt["status"]) for receipt in receipts],
                         [("d2-compra", 200), ("d2-rechazo", 422)])
        self.assertEqual(json.loads(receipts[1]["response"]), failure)
