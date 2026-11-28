import json
import threading
import pytest
from reyna_local.__main__ import ReynaServer
from nav_helpers import ir_a_pestana


def test_aprobar_y_rechazar_en_navegador(tmp_path):
    sync=pytest.importorskip('playwright.sync_api')
    carpeta=tmp_path/'aprendizaje'; carpeta.mkdir()
    ruta=carpeta/'frenosa.json'
    ruta.write_text(json.dumps([{'id':c*64,'calibrador':'consumo','objeto':c,'valor_aprendido':1,'estado':'PENDIENTE','vigente_desde':'2030-01'} for c in 'ab']))
    server=ReynaServer(tmp_path,0); thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with sync.sync_playwright() as p:
            try: browser=p.chromium.launch(args=['--no-sandbox'])
            except Exception: browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
            page=browser.new_page();page.goto(f'http://127.0.0.1:{server.server_port}/')
            ir_a_pestana(page, '#aprendido')
            page.locator('#ap-actualizar').click()
            sync.expect(page.locator('#ap-calibraciones article')).to_have_count(2)
            page.locator('#ap-calibraciones article').nth(0).get_by_role('button',name='Aprobar').click()
            sync.expect(page.locator('#ap-calibraciones article').nth(0)).to_contain_text('APLICADO')
            page.locator('#ap-calibraciones article').nth(1).get_by_role('button',name='Rechazar').click()
            sync.expect(page.locator('#ap-calibraciones article').nth(1)).to_contain_text('RECHAZADO')
            assert [r['estado'] for r in json.loads(ruta.read_text())]==['APLICADO','RECHAZADO']
            browser.close()
    finally: server.shutdown();thread.join();server.server_close()
