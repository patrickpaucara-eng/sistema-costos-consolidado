"""OT-C33-3: los límites del modelo aparecen en Chromium junto a sus vistas."""
import threading

import pytest

from reyna_local.__main__ import ReynaServer


AVISOS = (
    ("proyeccion", "c33-limite-futuro",
     "El costo variable se proyecta lineal dentro del rango observado de cantidades."),
    ("cotizador", "c33-limite-cotizador",
     "El costo variable se proyecta lineal dentro del rango observado de cantidades."),
    ("familias", "c33-limite-familias",
     "Supone que el proceso no cambió; si cambió máquina, proveedor o método, reinicie la historia de la familia."),
    ("decidir", "c33-limite-decision",
     "Una sola restricción. Con varias, use Exportar a Excel para Solver."),
    ("operar", "c33-limite-sistema", "Uso de un solo usuario a la vez."),
)


@pytest.fixture
def local_server(tmp_path):
    server = ReynaServer(tmp_path / "espacios", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    thread.join()
    server.server_close()


def test_chromium_muestra_cada_aviso_fijo_en_su_seccion(local_server):
    sync = pytest.importorskip("playwright.sync_api")
    with sync.sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(args=["--no-sandbox"])
        except Exception:
            browser = playwright.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        try:
            page = browser.new_page()
            page.goto(local_server)
            for section, notice_id, expected in AVISOS:
                page.locator(f'nav a[href="#{section}"]').click()
                notice = page.locator(f"#{notice_id}")
                sync.expect(notice).to_be_visible(timeout=10000)
                sync.expect(notice).to_have_text(expected)
        finally:
            browser.close()
