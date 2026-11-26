"""Las pantallas representan los datos del contrato y los límites de proyección."""
import json
from pathlib import Path
import threading
import pytest
from reyna_local.__main__ import ReynaServer


def test_pantallas_analitica_y_proyeccion(tmp_path):
    sync = pytest.importorskip('playwright.sync_api')
    server = ReynaServer(tmp_path, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync.sync_playwright() as playwright:
            try:
                try:  # [ARQ] solo entorno: primero el Chromium propio de Playwright, luego el del sistema; las aserciones no cambian
                    browser = playwright.chromium.launch(args=['--no-sandbox'])
                except Exception:
                    browser = playwright.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
            except Exception as exc:
                pytest.skip(f'Chromium no disponible: {exc}')
            page = browser.new_page()
            page.goto(f'http://127.0.0.1:{server.server_port}/')
            page.locator('#result-periodo').fill('2010-12')
            root = Path(__file__).resolve().parents[1]
            for synthesis in ('REAL', 'CONTABLE'):  # ESTIMADO retirado como síntesis (DECISIONES_DUENO 25-nov)
                page.locator('#result-sintesis').select_option(synthesis)
                with page.expect_response(lambda r: '/api/resultados?' in r.url and '2010-12' in r.url and f'sintesis={synthesis}' in r.url):
                    page.locator('#result-cargar').click()
                page.get_by_text('Resultados actualizados.').wait_for()
                data = json.loads((root / 'datos/resultados' / f'frenosa_2010-12_{synthesis}.json').read_text())
                for section, field in [('relevancia','relevancia'),('escenarios','escenarios'),('propuestas','propuestas')]:
                    assert page.locator(f'#result-{section} tbody tr').count() == len(data[field])
                assert page.locator('#result-hallazgos article').count() == len(data['hallazgos'])
                assert page.locator('[data-banda="p05-p95"]').count() == 1
                band = sorted((x for x in data['serie'] if x['tipo'] == 'PROYECTADO_EST'), key=lambda x:x['periodo'])
                assert len(page.locator('[data-banda="p05-p95"]').get_attribute('points').split()) == 2 * len(band)
            page.locator('#result-periodo').fill('2010-03')
            with page.expect_response(lambda r: '/api/resultados?' in r.url and '2010-03' in r.url):
                page.locator('#result-cargar').click()
            page.get_by_text('Se necesitan más de 6 meses para proyectar').wait_for()
            browser.close()
    finally:
        server.shutdown()
        thread.join()
        server.server_close()


def test_html_autonomo_preserva_banda_escenarios_y_estimacion(tmp_path):
    from reyna_local.exportar import exportar
    root = Path(__file__).resolve().parents[1]
    for synthesis in ('REAL', 'CONTABLE'):  # ESTIMADO retirado como síntesis (DECISIONES_DUENO 25-nov)
        data = json.loads((root / 'datos/resultados' / f'frenosa_2010-12_{synthesis}.json').read_text())
        text = exportar(data, 'html', tmp_path).read_text(encoding='utf-8')
        assert 'data-banda="p05-p95"' in text
        assert 'Rango de escenarios' in text
        for item in data['escenarios']:
            assert item['nombre'] in text
        if synthesis == 'ESTIMADO':
            assert 'Estimación estadística fuera de muestra' in text
            assert all(str(row['p95']) in text for row in data['estimacion'].values())
        assert 'http://' not in text and 'https://' not in text
