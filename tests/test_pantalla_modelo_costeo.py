"""La vista del modelo y la hoja de costos representan el contrato de julio."""
import json
import threading
from pathlib import Path
import pytest
from nav_helpers import ir_a_pestana
from reyna_local.__main__ import ReynaServer

ROOT = Path(__file__).resolve().parents[1]


def test_modelo_y_avisos_en_chromium(tmp_path):
    sync = pytest.importorskip('playwright.sync_api')
    server = ReynaServer(tmp_path, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync.sync_playwright() as p:
            try:
                browser = p.chromium.launch(args=['--no-sandbox'])
            except Exception:
                browser = p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
            page = browser.new_page()
            errors = []
            page.on('pageerror', lambda exc: errors.append(str(exc)))
            page.goto(f'http://127.0.0.1:{server.server_port}/')
            ir_a_pestana(page, '#portada')
            page.get_by_text('Resultados actualizados.').wait_for()
            page.locator('#result-periodo').fill('2010-07')
            with page.expect_response(lambda response: '/api/resultados?' in response.url and '2010-07' in response.url and 'REAL' in response.url):
                page.locator('#result-cargar').click()
            page.get_by_text('Resultados actualizados.').wait_for()
            ir_a_pestana(page, '#modelo')
            data = json.loads((ROOT / 'datos/resultados/frenosa_2010-07_REAL.json').read_text())
            assert page.get_by_role('heading', name='Modelo de costeo').is_visible()
            assert page.locator('#modelo-flujos tbody tr').count() == len(data['trazas'])
            assert page.locator('#modelo-actividades tbody tr').count() == len(data['modelo']['actividades'])
            ir_a_pestana(page, '#control')
            assert page.get_by_text('Aviso del dato fuente:', exact=False).count() > 0
            assert not errors
            browser.close()
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
