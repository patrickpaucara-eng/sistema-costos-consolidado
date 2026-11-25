"""Recorrido de pantallas y preservación del borrador guiado en Chromium."""
import json
import threading
from pathlib import Path
from urllib.request import Request,urlopen
import pytest
from reyna_local.__main__ import ReynaServer

ROOT=Path(__file__).resolve().parents[1]


def test_recorrido_y_borrador(tmp_path):
    sync=pytest.importorskip('playwright.sync_api')
    server=ReynaServer(tmp_path,0);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    base=f'http://127.0.0.1:{server.server_port}'
    try:
        body=json.dumps({'name':'Espacio prueba','workbook_path':str(ROOT/'casos/libros/frenosa.xlsx')}).encode()
        with urlopen(Request(base+'/api/workspaces',data=body,headers={'Content-Type':'application/json'}),timeout=30) as response:wid=json.load(response)['id']
        other=json.dumps({'name':'Otro espacio','workbook_path':str(ROOT/'casos/libros/frenosa.xlsx')}).encode()
        with urlopen(Request(base+'/api/workspaces',data=other,headers={'Content-Type':'application/json'}),timeout=30) as response:wid2=json.load(response)['id']
        with sync.sync_playwright() as p:
            try:browser=p.chromium.launch(args=['--no-sandbox'])
            except Exception:browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
            page=browser.new_page();errors=[]
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.on('console',lambda message:errors.append(message.text) if message.type=='error' else None)
            page.goto(base);page.get_by_text('Resultados actualizados.').wait_for(timeout=30000)
            assert page.get_by_role('heading',name='¿Qué necesitas?').is_visible()
            # DECISIONES_DUENO.md, fila 25-nov «APROBADO en OT-C27: E2»: fechas solo en Periodos.
            assert page.locator('#global-desde').count()==0 and page.locator('#sello-global').is_visible()
            links=page.locator('nav a').evaluate_all('(els) => els.map(e => e.getAttribute("href"))')
            for href in links:
                page.locator(f'nav a[href="{href}"]').click()
                page.locator(href).wait_for(state='visible', timeout=5000)
                assert page.locator('#global-desde').count()==0
            page.locator('nav a[href="#espacios"]').click()
            page.locator(f'button[data-workspace-id="{wid}"]').click()
            page.locator('nav a[href="#operar"]').click()
            page.locator('#transaction').select_option('T14')
            page.locator('#guided-form [data-variable=FECHA]').wait_for()
            page.locator('#guided-form [data-variable=FECHA]').fill('20101228')
            page.locator('#support-document').set_input_files({'name':'soporte.txt','mimeType':'text/plain','buffer':b'abc'})
            page.get_by_text('ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad',exact=False).wait_for()
            page.locator('#transaction').select_option('T15')
            page.locator('#guided-form [data-variable=OBJ]').wait_for()
            page.locator('#transaction').select_option('T14')
            page.locator('#guided-form [data-variable=FECHA]').wait_for()
            assert page.locator('#guided-form [data-variable=FECHA]').input_value()=='20101228'
            page.locator('nav a[href="#espacios"]').click();page.locator(f'button[data-workspace-id="{wid2}"]').click()
            page.locator(f'button[data-workspace-id="{wid}"]').click();page.locator('nav a[href="#operar"]').click()
            sync.expect(page.locator('#guided-form [data-variable=FECHA]')).to_have_value('20101228')   # sin eval: la CSP del servidor lo prohíbe
            assert 'huella conservada' in page.locator('#support-hash').inner_text()
            page.locator('nav a[href="#periodos"]').click()
            sync.expect(page.locator('#periodos-desde')).to_be_visible(timeout=5000)
            page.locator('#periodos-desde').fill('2010-03-01')
            assert page.locator('#periodos-desde').input_value()=='2010-03-01'
            assert not errors,errors
            browser.close()
    finally:server.shutdown();thread.join();server.server_close()
