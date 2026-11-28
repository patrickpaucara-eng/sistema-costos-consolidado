"""C37-3: la pantalla usa ventas y capacidad publicadas y no inventa faltantes."""
import json
import threading
from pathlib import Path

import pytest
from nav_helpers import ir_a_pestana
from reyna_local.__main__ import ReynaServer


ROOT = Path(__file__).resolve().parents[1]


def test_decidir_usa_datos_propios_y_detiene_faltantes(tmp_path):
    sync = pytest.importorskip('playwright.sync_api')
    original = json.loads((ROOT / 'datos/resultados/segundo_2025-04_REAL.json').read_text(encoding='utf-8'))
    results = tmp_path / 'resultados'
    results.mkdir()
    sin_venta = json.loads(json.dumps(original))
    sin_venta['periodo_actual'] = '2025-05'
    sin_venta['datos_libro']['ventas'] = [v for v in sin_venta['datos_libro']['ventas'] if v['producto'] != 'MPR']
    (results / 'segundo_2025-05_REAL.json').write_text(json.dumps(sin_venta), encoding='utf-8')
    sin_cap = json.loads(json.dumps(original))
    sin_cap['periodo_actual'] = '2025-06'
    sin_cap['datos_libro']['medidas'] = [m for m in sin_cap['datos_libro']['medidas'] if m['nivel'] != 'CAP']
    sin_cap['capacidad_ociosa'] = []
    (results / 'segundo_2025-06_REAL.json').write_text(json.dumps(sin_cap), encoding='utf-8')

    server = ReynaServer(tmp_path, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync.sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch(args=['--no-sandbox'])
            except Exception:
                browser = playwright.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
            try:
                page = browser.new_page()
                page.goto(f'http://127.0.0.1:{server.server_port}/')
                page.locator('#result-empresa').select_option('segundo')

                def cargar(periodo):
                    ir_a_pestana(page, '#portada')
                    page.locator('#result-periodo').fill(periodo)
                    with page.expect_response(lambda response: '/api/resultados?' in response.url and 'empresa=segundo' in response.url and periodo in response.url):
                        page.locator('#result-cargar').click()
                    sync.expect(page.locator('#result-status')).to_contain_text('actualizados', timeout=30000)
                    ir_a_pestana(page, '#decidir')

                cargar('2025-04')
                sync.expect(page.locator('#dc-capacidad')).to_contain_text('Capacidad no usada calculada: 40')
                sync.expect(page.locator('#dc-demanda-maxima input[data-producto="MPR"]')).to_have_value('10')
                sync.expect(page.locator('#dc-demanda-maxima input[data-producto="REB"]')).to_have_value('10')
                assert page.locator('#dc-ociosa, #dc-desplazadas').count() == 0
                assert page.locator('#dc-caso option[value="pedido"]').count() == 0
                assert page.locator('#decidir a[href="#cotizador"]').count() == 1
                assert page.locator('#dc-asignar').is_enabled()

                cargar('2025-05')
                entrada = page.locator('#dc-demanda-maxima input[data-producto="MPR"]')
                sync.expect(entrada).to_have_value('')
                sync.expect(page.locator('#dc-demanda-maxima')).to_contain_text('falta dato en VENTA')
                page.locator('#dc-asignar').click()
                sync.expect(page.locator('#dc-escasez-estado')).to_contain_text('Falta dato: demanda máxima de MPR')
                assert page.locator('#dc-escasez-resultado tbody tr').count() == 0

                cargar('2025-06')
                sync.expect(page.locator('#dc-escasez-estado')).to_contain_text('Falta capacidad')
                assert page.locator('#dc-asignar').is_disabled()
            finally:
                browser.close()
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
