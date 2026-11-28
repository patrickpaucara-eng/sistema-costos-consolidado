"""C35-2: cabecera de una línea y espacio vertical recuperado en Chromium."""
import threading

import pytest

from reyna_local.__main__ import ReynaServer


BASELINE_HEADER_PX = 332.4375
BASELINE_PANEL_TOP_PX = 396.4375


def test_cabecera_compacta_y_acciones_en_inicio(tmp_path):
    sync = pytest.importorskip("playwright.sync_api")
    server = ReynaServer(tmp_path, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    browser = None
    try:
        with sync.sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch(args=["--no-sandbox"])
            except Exception:
                browser = playwright.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
            page = browser.new_page(viewport={"width": 1366, "height": 768})
            page.goto(f"http://127.0.0.1:{server.server_port}/")
            sync.expect(page.locator("#result-status")).to_contain_text("actualizados", timeout=30000)

            metrics = page.evaluate("""() => {
              const header = document.querySelector('#inicio');
              const panel = document.querySelector('#portada');
              const rect = el => { const r = el.getBoundingClientRect(); return {top:r.top, height:r.height}; };
              return {height:rect(header).height, headerTop:rect(header).top, panelTop:rect(panel).top,
                position:getComputedStyle(header).position,
                controlRows:[...header.querySelectorAll('.compact-field,#suficiencia-estado,#sello-global,.global-mas')]
                  .map(el => { const r=el.getBoundingClientRect(); return Math.round(r.top+r.height/2); })};
            }""")
            assert metrics["height"] <= 48
            assert metrics["headerTop"] == 0
            assert metrics["position"] == "sticky"
            assert max(metrics["controlRows"]) - min(metrics["controlRows"]) <= 2
            area_anterior = 768 - BASELINE_PANEL_TOP_PX
            area_actual = 768 - metrics["panelTop"]
            assert area_actual - area_anterior >= 140
            assert BASELINE_HEADER_PX - metrics["height"] >= 140

            for control in ("#suficiencia-nivel", "#suficiencia-plantilla", "#result-cargar", "#result-calcular"):
                assert page.locator(f"#inicio {control}").count() == 0
                assert page.locator(f"#portada {control}").is_visible()
            assert page.locator("#suficiencia-estado").is_visible()
            assert page.locator("#sello-global").is_visible()

            page.locator("#inicio .global-mas summary").click()
            assert page.locator("#inicio .global-mas a[href='#portada']").is_visible()
            page.locator("#inicio .global-mas a[href='#portada']").click()
            page.locator("#result-cargar").click()
            sync.expect(page.locator("#result-status")).to_contain_text("actualizados", timeout=30000)
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
