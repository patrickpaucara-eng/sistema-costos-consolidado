"""C35-1/E34: seis destinos, recorrido de las 26 vistas y pestaña persistente."""
from __future__ import annotations

import threading

import pytest

from reyna_local.__main__ import ReynaServer


DESTINOS = {
    "Pedido": ("#cotizador", "#costos", "#ruta"),
    "Operación": ("#operar", "#importar", "#cierre"),
    "Costos": ("#portada", "#dashboard", "#periodos", "#reportes", "#inventarios", "#normal"),
    "Futuro": ("#proyeccion", "#laboratorio", "#familias", "#comparar", "#decidir", "#propuestas"),
    "Aprendizaje": ("#aprendido", "#analisis"),
    "Configuración": ("#modelo", "#datos", "#cargar-libro", "#espacios", "#consultar", "#control"),
}


def test_recorrido_26_pantallas_y_pestana_activa_tras_actualizar(tmp_path):
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
            page.locator("#result-status").wait_for()
            assert page.locator("#nav-destinos details").count() == 6
            assert page.locator("#nav-destinos details[open]").count() == 1
            assert page.locator("#nav-destinos summary").all_text_contents() == list(DESTINOS)

            visitadas = []
            for destino, hrefs in DESTINOS.items():
                menu = page.locator("#nav-destinos details").filter(has=page.get_by_text(destino, exact=True))
                if not menu.evaluate("e => e.open"):
                    menu.locator("summary").click()
                assert page.locator("#nav-destinos details[open]").count() == 1
                assert menu.locator("a[href^='#']").evaluate_all("els => els.map(a => a.getAttribute('href'))") == list(hrefs)
                for href in hrefs:
                    page.locator(f"#module-tabs [role='tab'][href='{href}']").click()
                    page.locator(href).wait_for(state="visible", timeout=5000)
                    assert page.locator("#nav-destinos details[open]").count() == 1
                    assert page.locator(f"#module-tabs [role='tab'][href='{href}'][aria-current='page']").count() == 1
                    visitadas.append(href)

            assert len(visitadas) == len(set(visitadas)) == 26
            costos = page.locator("#nav-destinos details[data-destino='costos']")
            if not costos.evaluate("e => e.open"):
                costos.locator("summary").click()
            page.locator("#module-tabs [role='tab'][href='#dashboard']").click()
            assert page.locator("#module-tabs").evaluate("e => getComputedStyle(e).position") == "sticky"
            page.reload()
            page.locator("#result-status").wait_for()
            assert page.locator("#module-tabs [role='tab'][href='#dashboard'][aria-current='page']").count() == 1
            assert page.locator("#nav-destinos details[open]").count() == 1
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
