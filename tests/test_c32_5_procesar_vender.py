"""Calculadora de proceso adicional frente a venta en el punto de separación."""
import json
import threading
from urllib.request import Request, urlopen

import pytest

from reyna_local import decidir as D
from reyna_local.__main__ import ReynaServer


def test_caso_manual_procesar_da_un_sol_por_unidad():
    resultado = D.vender_o_procesar(10, 14, 3)
    assert (resultado['ingreso_incremental_unitario'], resultado['costo_incremental_unitario'],
            resultado['beneficio_incremental_unitario'], resultado['decision']) == (4, 3, 1, 'PROCESAR')


@pytest.fixture
def server(tmp_path):
    app = ReynaServer(tmp_path, 0)
    thread = threading.Thread(target=app.serve_forever, daemon=True)
    thread.start()
    yield f'http://127.0.0.1:{app.server_port}'
    app.shutdown(); thread.join(); app.server_close()


def _post(base, body):
    req = Request(base + '/api/decidir', data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
    with urlopen(req, timeout=30) as response:
        return json.load(response)


def test_api_compara_incremento_y_costo(server):
    resultado = _post(server, {'empresa': 'frenosa', 'periodo': '2010-12', 'caso': 'vender_procesar',
                               'precio_venta_actual': 10, 'precio_venta_procesado': 14, 'costo_procesamiento': 3})
    assert resultado['beneficio_incremental_unitario'] == 1
    assert resultado['decision'] == 'PROCESAR'


def test_panel_permite_comparar_en_el_punto_de_separacion(server):
    sync = pytest.importorskip('playwright.sync_api')
    with sync.sync_playwright() as p:
        try:
            browser = p.chromium.launch(args=['--no-sandbox'])
        except Exception:
            browser = p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        page = browser.new_page()
        page.goto(server)
        page.locator('nav a[href="#decidir"]').click()
        page.locator('#dc-proceso-venta-actual').fill('10')
        page.locator('#dc-proceso-venta-final').fill('14')
        page.locator('#dc-proceso-costo').fill('3')
        page.locator('#dc-proceso-form button[type="submit"]').click()
        sync.expect(page.locator('#dc-proceso-resultado')).to_contain_text('PROCESAR', timeout=30000)
        sync.expect(page.locator('#dc-proceso-resultado')).to_contain_text('1')
        browser.close()
