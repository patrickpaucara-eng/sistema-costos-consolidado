"""Recorrido real de las pantallas C26; C26_CAPTURAS permite guardar evidencia."""
import os
from pathlib import Path
import threading
import pytest
from reyna_local.__main__ import ReynaServer
from nav_helpers import ir_a_pestana


def test_pantallas_c26_en_chromium(tmp_path):
    sync = pytest.importorskip('playwright.sync_api')
    output = Path(os.environ.get('C26_CAPTURAS', str(tmp_path/'capturas')))
    output.mkdir(parents=True, exist_ok=True)
    server=ReynaServer(tmp_path/'datos',0); thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with sync.sync_playwright() as p:
            try: browser=p.chromium.launch(args=['--no-sandbox'])
            except Exception: browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
            page=browser.new_page(viewport={'width':1440,'height':900}); page.goto(f'http://127.0.0.1:{server.server_port}/')
            sync.expect(page.locator('#result-status')).to_contain_text('actualizados',timeout=30000)
            assert page.locator('#nav-destinos details').count()==6
            assert page.locator('#nav-destinos details[open]').count()==1
            assert page.locator('nav a[href="#simulacion"]').count()==0
            ir_a_pestana(page, '#dashboard')
            page.locator('#planta-bloques button').first.click()
            assert page.locator('#planta-detalle tbody tr').count()>0
            page.screenshot(path=str(output/'E04_planta.png'))
            ir_a_pestana(page, '#cotizador');page.locator('#cot-precio').fill('5000')
            page.locator('#cotizar-form button').click()
            sync.expect(page.locator('#cot-estado')).to_contain_text('Costo:',timeout=30000)
            page.screenshot(path=str(output/'E15_cotizador.png'))
            ir_a_pestana(page, '#aprendido');page.locator('#ap-actualizar').click()
            sync.expect(page.locator('#ap-estado')).not_to_have_text('Consultando…',timeout=30000)
            page.screenshot(path=str(output/'E16_aprendizaje.png'))
            ir_a_pestana(page, '#proyeccion')
            sync.expect(page.locator('#sensibilidad-estado')).not_to_have_text('Consultando sensibilidad…',timeout=30000)
            assert page.locator('.sens-row').count()>0
            page.screenshot(path=str(output/'E13_sensibilidad.png'))
            for selector, name in [('analisis','E17_variable'),('control','E18_calidad'),('inventarios','E19_rechazos'),('propuestas','E24_propuestas'),('periodos','E11_periodos'),('costos','E07_personas'),('ruta','E21_tramos')]:
                ir_a_pestana(page, f'#{selector}')
                if selector=='ruta': page.locator('#ruta details summary').click()
                if selector=='propuestas':
                    assert page.locator('#propuestas-por-decisor button').count()>0
                    page.locator('#propuestas-por-decisor summary').first.click()
                page.screenshot(path=str(output/(name+'.png')))
            browser.close()
    finally: server.shutdown();thread.join();server.server_close()
