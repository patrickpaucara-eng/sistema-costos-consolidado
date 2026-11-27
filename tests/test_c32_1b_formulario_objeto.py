"""OT-C32-1b: el formulario guiado muestra y conserva el próximo correlativo de OBJETO."""
import json
import threading
from pathlib import Path
from urllib.request import Request, urlopen

import pytest
from openpyxl import load_workbook

from reyna_local.__main__ import ReynaServer
from reyna_local.correlativo_objeto import especificacion_creacion
from reyna_local.store import load_data


ROOT = Path(__file__).resolve().parents[1]


def _post(base, path, body):
    request = Request(base + path, data=json.dumps(body).encode(),
                      headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=60) as response:
        return response.status, json.load(response)


def _libro_con_estimaciones(path):
    source = ROOT / "casos" / "libros" / "frenosa.xlsx"
    workbook = load_workbook(source)
    sheet = workbook["ESTIMACION"]
    headers = [str(value) for value in next(sheet.iter_rows(min_row=1, max_row=1, values_only=True))]
    for number in (1, 2):
        values = {
            "EST_NUM": f"C32-1B-{number:03d}", "EST_EMP": "FRE", "EST_PER": "2010-12",
            "EST_CLI": "MERCADO", "EST_PRO": "SW50", "EST_CAN": 100,
            "EST_CST": 1234.5, "EST_ESTADO": "PENDIENTE", "EST_OBJ": None,
            "EST_VER": 1, "EST_ORIGEN": "C32-1B", "EST_PRECIO": 1000, "EST_RENT": 0.3,
        }
        sheet.append([values.get(header) for header in headers])
    workbook.save(path)
    workbook.close()


def test_descubre_por_el_dbd_que_t13_crea_objeto_y_t15_no():
    tables, _ = load_data((ROOT / "casos" / "libros" / "frenosa.xlsx").read_bytes())
    spec = especificacion_creacion(tables, "T13")
    assert spec["variable"] == "OBJ"
    assert spec["producto"]["tabla"] == "ESTIMACION"
    assert spec["producto"]["contexto"] == ["EST"]
    assert especificacion_creacion(tables, "T15") is None


def test_formulario_chromium_bloquea_codigo_y_asigna_dos_correlativos(tmp_path):
    sync = pytest.importorskip("playwright.sync_api")
    workbook_path = tmp_path / "frenosa_guiada.xlsx"
    _libro_con_estimaciones(workbook_path)
    server = ReynaServer(tmp_path / "espacios", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    browser = None
    playwright = None
    try:
        status, space = _post(base, "/api/workspaces", {"name": "C32-1b", "workbook_path": str(workbook_path)})
        assert status == 201
        playwright = sync.sync_playwright().start()
        try:
            try:
                browser = playwright.chromium.launch(args=["--no-sandbox"])
            except Exception:
                browser = playwright.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
            page = browser.new_page()
            page.goto(base + "#operar")
            page.locator(f'[data-workspace-id="{space["id"]}"]').click()
            t13_option = page.locator('#transaction option[value="T13"]')
            sync.expect(t13_option).to_be_enabled(timeout=10000)
            page.locator("#transaction").select_option("T13")
            page.locator('[data-variable="FECHA"]').fill("20101228")
            page.locator('[data-variable="PER"]').select_option("2010-12")
            page.locator('[data-variable="EMP"]').select_option("FRE")
            page.locator('[data-variable="MONTO"]').fill("0")
            page.locator('[data-variable="REF"]').fill("PRUEBA-C32-1B")
            page.locator('[data-variable="ALG"]').fill("COSTO_PROYECTADO")
            page.locator('[data-variable="VER"]').fill("1")
            page.locator('[data-variable="HUELLA"]').fill("C32-1B")
            page.locator("#operator").fill("JCOSTOS")

            object_code = page.locator('[data-variable="OBJ"]')
            assert object_code.evaluate("element => element.readOnly") is True
            for index, (estimate, expected) in enumerate((
                ("C32-1B-001", "OT-FRE-SW50-0001"),
                ("C32-1B-002", "OT-FRE-SW50-0002"),
            )):
                if index:
                    page.locator("#new-request").click()
                page.locator('[data-variable="EST"]').select_option(estimate)
                sync.expect(object_code).to_have_value(expected, timeout=10000)
                await_edit_attempt = object_code
                await_edit_attempt.click()
                page.keyboard.press("Control+A")
                page.keyboard.type("OT-EDITADA")
                assert await_edit_attempt.input_value() == expected
                page.locator('#execute-form button[type="submit"]').click()
                sync.expect(page.locator("#execute-status")).to_contain_text("confirmada", timeout=30000)
                sync.expect(object_code).to_have_value(
                    "OT-FRE-SW50-0002" if index == 0 else "OT-FRE-SW50-0003", timeout=10000
                )

            workbook = load_workbook(tmp_path / "espacios" / space["id"] / "libro.xlsx", read_only=True)
            rows = list(workbook["OBJETO"].values)
            workbook.close()
            columns = rows[0]
            codes = {row[columns.index("OBJ_NUM")] for row in rows[1:]}
            assert {"OT-FRE-SW50-0001", "OT-FRE-SW50-0002"} <= codes
        finally:
            if browser:
                browser.close()
            playwright.stop()
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
