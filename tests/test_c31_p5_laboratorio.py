"""Prueba de laboratorio con libros temporales, transacción real y huella."""
import hashlib
import json
import threading
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import pytest
from reyna_local.__main__ import ReynaServer

ROOT=Path(__file__).resolve().parents[1]


def post(base,path,data):
    req=Request(base+path,data=json.dumps(data).encode(),headers={'Content-Type':'application/json'})
    with urlopen(req,timeout=120) as r:return json.load(r)


def test_crear_editar_y_comparar_sin_alterar_original(tmp_path):
    server=ReynaServer(tmp_path,0);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    base=f'http://127.0.0.1:{server.server_port}'
    try:
        original=post(base,'/api/workspaces',{'name':'Original','workbook_path':str(ROOT/'casos/libros/frenosa.xlsx')})
        source=Path(original['workbook_path']);before=hashlib.sha256(source.read_bytes()).hexdigest()
        lab=post(base,'/api/laboratorio/crear',{'original':original['id']})
        assert lab['id']!=original['id'] and lab['huella_original']==before
        command={'transaction':'T15','user':'SUPERV1','request_id':'lab-consumo',
                 'header':{'FECHA':20101228,'PER':'2010-12','EMP':'FRE','OBJ':'OT-FRENOSA-SW50-2010-12','CEN':'PLANTA_FRE','ALM':'ALM_FRE'},
                 'lines':[{'REC':'MAT_SW50','CANT':1}]}
        response=post(base,f"/api/workspaces/{lab['id']}/execute",command)
        assert response['result']=='OK'
        resultado=post(base,'/api/laboratorio/comparar',{'laboratorio':lab['id'],'periodo':'2010-12','sintesis':'REAL'})
        assert resultado['filas'] and any(x['diferencia'] != 0 for x in resultado['filas'])
        assert hashlib.sha256(source.read_bytes()).hexdigest()==before
        with pytest.raises(HTTPError) as exc:
            post(base,'/api/laboratorio/comparar',{'laboratorio':original['id'],'periodo':'2010-12','sintesis':'REAL'})
        assert exc.value.code==404
        from openpyxl import load_workbook
        wb=load_workbook(source);wb['EMPRESA']['B2']='Cambio posterior';wb.save(source);wb.close()
        with pytest.raises(HTTPError) as exc:
            post(base,'/api/laboratorio/comparar',{'laboratorio':lab['id'],'periodo':'2010-12','sintesis':'REAL'})
        assert exc.value.code==409
    finally: server.shutdown();thread.join();server.server_close()


def test_pantalla_crea_lab_y_edita_copia(tmp_path):
    sync=pytest.importorskip('playwright.sync_api')
    server=ReynaServer(tmp_path,0);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();base=f'http://127.0.0.1:{server.server_port}'
    try:
        original=post(base,'/api/workspaces',{'name':'Original web','workbook_path':str(ROOT/'casos/libros/frenosa.xlsx')})
        source=Path(original['workbook_path']);antes=hashlib.sha256(source.read_bytes()).hexdigest()
        with sync.sync_playwright() as p:
            try: browser=p.chromium.launch(args=['--no-sandbox'])
            except Exception: browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
            page=browser.new_page();page.goto(base)
            page.locator('nav a[href="#espacios"]').click()
            page.locator(f'button[data-workspace-id="{original["id"]}"]').click()
            sync.expect(page.locator('#detail-name')).to_have_text('Original web',timeout=30000)
            page.locator('nav a[href="#laboratorio"]').click()
            page.locator('#lab-crear').click()
            sync.expect(page.locator('#lab-estado')).to_contain_text('Copia creada',timeout=30000)
            page.locator('#lab-editar').click()
            sync.expect(page.locator('#detail-name')).to_contain_text('Laboratorio',timeout=15000)
            page.locator('#transaction').select_option('T15')
            page.locator('#guided-form [data-variable="FECHA"]').wait_for()
            page.locator('#operator').fill('SUPERV1')
            campos={'FECHA':'20101228','PER':'2010-12','EMP':'FRE','OBJ':'OT-FRENOSA-SW50-2010-12','CEN':'PLANTA_FRE','ALM':'ALM_FRE','REC':'MAT_SW50','CANT':'1'}
            for clave,valor in campos.items():
                item=page.locator(f'#guided-form [data-variable="{clave}"]').first
                if item.evaluate('(e)=>e.tagName')=='SELECT': item.select_option(valor)
                else: item.fill(valor)
            page.locator('#execute-form button[type="submit"]').click()
            sync.expect(page.locator('#execute-status')).to_contain_text('confirmada',timeout=30000)
            page.locator('nav a[href="#laboratorio"]').click()
            page.locator('#result-periodo').fill('2010-12');page.locator('#result-sintesis').select_option('REAL')
            page.locator('#lab-comparar').click()
            sync.expect(page.locator('#lab-estado')).to_contain_text('Comparación terminada',timeout=120000)
            assert page.locator('#lab-tabla tbody tr').count()>0
            assert hashlib.sha256(source.read_bytes()).hexdigest()==antes
            import os
            if os.environ.get('C31_CAPTURAS'):
                destino=Path(os.environ['C31_CAPTURAS']);destino.mkdir(parents=True,exist_ok=True)
                page.screenshot(path=str(destino/'punto5_laboratorio.png'))
            browser.close()
    finally:server.shutdown();thread.join();server.server_close()
