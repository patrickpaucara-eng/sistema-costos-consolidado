"""C37-6: tres accesos iniciales, escenarios en Futuro y Word en Configuración."""
import threading
import re

import pytest
from nav_helpers import ir_a_pestana
from reyna_local.__main__ import ReynaServer


def test_inicio_escenarios_y_word_codigo_en_chromium(tmp_path):
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
            try:
                page = browser.new_page()
                page.goto(f'http://127.0.0.1:{server.server_port}/')
                sync.expect(page.locator('#result-status')).to_contain_text('actualizados', timeout=30000)
                cards = page.locator('#portada .inicio-tarjetas a')
                assert cards.count() == 3
                assert cards.evaluate_all("els => els.map(e => e.getAttribute('href'))") == ['#cotizador', '#operar', '#dashboard']
                for href in ('#cotizador', '#operar', '#dashboard'):
                    ir_a_pestana(page, '#portada')
                    page.locator(f'#portada .inicio-tarjetas a[href="{href}"]').click()
                    sync.expect(page.locator(href)).to_be_visible()

                ir_a_pestana(page, '#proyeccion')
                sync.expect(page.locator('#simulacion')).to_be_visible()
                assert page.locator('#result-escenarios tbody tr').count() > 0
                assert page.locator('nav a[href="#simulacion"]').count() == 0
                page.evaluate("location.hash = '#simulacion'")
                sync.expect(page).to_have_url(re.compile(r'#proyeccion$'))
                sync.expect(page.locator('#proyeccion')).to_be_visible()

                ir_a_pestana(page, '#modelo')
                button = page.locator('#modelo button[data-exportar="codigo"]')
                assert button.is_visible()
                assert page.locator('#reportes button[data-exportar="codigo"]').count() == 0
                with page.expect_download(timeout=60000) as download_info:
                    button.click()
                assert download_info.value.suggested_filename.endswith('.docx')
                sync.expect(page.locator('#codigo-export-status')).to_contain_text('Documento de código listo')
            finally:
                browser.close()
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
