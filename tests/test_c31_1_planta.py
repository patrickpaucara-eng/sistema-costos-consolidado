import threading
import pytest
from reyna_local.__main__ import ReynaServer
from nav_helpers import ir_a_pestana


def test_aristas_y_nodos_en_chromium(tmp_path):
    sync=pytest.importorskip('playwright.sync_api')
    s=ReynaServer(tmp_path,0); t=threading.Thread(target=s.serve_forever,daemon=True);t.start()
    try:
        with sync.sync_playwright() as p:
            try: b=p.chromium.launch(args=['--no-sandbox'])
            except Exception: b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
            page=b.new_page();page.goto(f'http://127.0.0.1:{s.server_port}/')
            sync.expect(page.locator('#result-status')).to_contain_text('actualizados',timeout=30000)
            ir_a_pestana(page, '#dashboard')
            line=page.locator('#planta-grafo .planta-arista').first
            sync.expect(line).to_contain_text(' → ')
            line.locator('button').first.click()
            assert page.locator('#planta-enlaces p').count()>0
            b.close()
    finally:s.shutdown();t.join();s.server_close()
