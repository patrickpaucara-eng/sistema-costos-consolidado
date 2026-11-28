"""OT-C37-1: registrar una transacción desde campos tipados, sin editor JSON."""
import json
import threading
from pathlib import Path
from urllib.request import Request, urlopen

import pytest
from openpyxl import load_workbook

from reyna_local.__main__ import ReynaServer


ROOT = Path(__file__).resolve().parents[1]


def _request(url, body=None):
    data = None if body is None else json.dumps(body).encode()
    request = Request(url, data=data, headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=60) as response:
        return response.status, json.load(response)


def _event_count(path):
    workbook = load_workbook(path, read_only=True, data_only=True)
    count = sum(1 for _ in workbook["EVENTO"].iter_rows(min_row=2, values_only=True))
    workbook.close()
    return count


def test_t15_tipado_busqueda_y_rechazo_local_de_texto_numerico(tmp_path):
    sync = pytest.importorskip("playwright.sync_api")
    source = ROOT / "casos" / "libros" / "frenosa.xlsx"
    server = ReynaServer(tmp_path / "espacios", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    browser = None
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        status, space = _request(base + "/api/workspaces", {"name": "C37-1", "workbook_path": str(source)})
        assert status == 201
        _, config = _request(base + f"/api/trx-campos?id={space['id']}&trx=T15")
        fields = {(field["nivel"], field["variable"]): field for field in config["campos"]}
        assert fields[("L", "CANT")]["tipo"] == "numero"
        assert fields[("C", "FECHA")]["tipo"] == "fecha"
        assert fields[("C", "OBJ")]["tipo"] == "lista"
        assert fields[("L", "REC")]["tipo"] == "lista"

        with sync.sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch(args=["--no-sandbox"])
            except Exception:
                browser = playwright.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
            page = browser.new_page()
            page.goto(base + "#operar")
            page.locator(f'[data-workspace-id="{space["id"]}"]').click()
            sync.expect(page.locator("#detail-version")).to_have_text("0", timeout=10000)
            page.locator('#transaction option[value="T15"]').wait_for(state="attached")
            page.locator("#transaction").select_option("T15")
            cantidad = page.locator('[data-variable="CANT"]')
            sync.expect(cantidad).to_have_attribute("type", "number")
            filtros = {"OBJ": "OT-FRENOSA", "CEN": "PLANTA_FRE", "REC": "MAT_SW50"}
            for variable, termino in filtros.items():
                control = page.locator(f'[data-variable="{variable}"]')
                assert control.evaluate("el => el.tagName") == "SELECT"
                buscar = control.locator("xpath=preceding-sibling::input[@type='search']")
                assert buscar.count() == 1
                buscar.fill(termino)
                assert control.locator("option").count() > 0
                valores = control.locator("option").evaluate_all("els => els.map(el => el.value).filter(Boolean)")
                assert valores and all(termino.lower() in value.lower() for value in valores)

            page.locator('[data-variable="FECHA"]').fill("20101228")
            page.locator('[data-variable="PER"]').select_option("2010-12")
            page.locator('[data-variable="EMP"]').select_option("FRE")
            page.locator('[data-variable="OBJ"]').select_option("OT-FRENOSA-SW50-2010-12")
            page.locator('[data-variable="CEN"]').select_option("PLANTA_FRE")
            page.locator('[data-variable="ALM"]').select_option("ALM_FRE")
            page.locator('[data-variable="REC"]').select_option("MAT_SW50")
            page.locator("#operator").fill("SUPERV1")
            antes = _event_count(tmp_path / "espacios" / space["id"] / "libro.xlsx")

            cantidad.press_sequentially("texto")
            page.locator('#execute-form button[type="submit"]').click()
            sync.expect(page.locator("#execute-status")).to_contain_text("número válido", timeout=5000)
            sync.expect(page.locator("#execute-status")).to_contain_text("No se envió la transacción")
            sync.expect(page.locator("#detail-version")).to_have_text("0")
            assert _event_count(tmp_path / "espacios" / space["id"] / "libro.xlsx") == antes

            cantidad.fill("1")
            page.locator('#execute-form button[type="submit"]').click()
            sync.expect(page.locator("#execute-status")).to_contain_text("Transacción T15 confirmada", timeout=30000)
            sync.expect(page.locator("#detail-version")).to_have_text("1")
            assert _event_count(tmp_path / "espacios" / space["id"] / "libro.xlsx") == antes + 1

            assert page.locator("#import-form").count() == 0
            assert page.locator("#espacios form").count() == 0
            assert page.locator("#cargar-libro #libro-archivo").count() == 1
            assert page.locator("#advanced-json").count() == 0
            page.goto(base + "#importar")
            sync.expect(page.locator("#cargar-libro")).to_be_visible()
            assert page.evaluate("location.hash") == "#cargar-libro"
            browser.close()
            browser = None
    finally:
        if browser:
            try:
                browser.close()
            except Exception:
                pass
        server.shutdown()
        thread.join()
        server.server_close()
