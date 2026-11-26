"""E7: tres técnicos sintéticos en una copia de SERVITEC, nunca el libro original."""
import hashlib
import os
import shutil
import threading
from pathlib import Path
from openpyxl import load_workbook
import pytest
from reyna_local.calculo_local import calcular
from reyna_local.__main__ import ReynaServer

ROOT=Path(__file__).resolve().parents[1]


def tres_tecnicos(source, destino):
    shutil.copyfile(source,destino); w=load_workbook(destino)
    for sheet,col in [('RECURSO','REC_COD'),('REGLA_REPARTO','RRE_ORIGEN')]:
        ws=w[sheet]; heads=[x.value for x in ws[1]]; idx=heads.index(col)
        for row in list(ws.iter_rows(min_row=2)):
            if row[idx].value=='MOD':
                values=[c.value for c in row]
                for i in (1,2,3):
                    v=values.copy();v[idx]=f'TEC{i}'
                    if sheet=='RECURSO':v[heads.index('REC_DES')]=f'Técnico {i}'
                    ws.append(v)
                ws.delete_rows(row[0].row);break
    ws=w['LINEA'];h=[x.value for x in ws[1]];rec=h.index('LIN_REC');num=h.index('LIN_NUM');cu=h.index('LIN_CU_DOC');mto=h.index('LIN_MTO')
    for row in list(ws.iter_rows(min_row=2)):
        if row[rec].value=='MOD':
            values=[c.value for c in row];row[rec].value='TEC1';row[cu].value=4000;row[mto].value=4000
            for i in (2,3):
                v=values.copy();v[rec]=f'TEC{i}';v[num]=i;v[cu]=4000;v[mto]=4000;ws.append(v)
    w.save(destino);w.close()


def test_tres_tecnicos_ruta_y_conservacion_en_navegador(tmp_path):
    sync=pytest.importorskip('playwright.sync_api')
    source=ROOT/'casos/libros/segundo.xlsx'; before=hashlib.sha256(source.read_bytes()).digest()
    folder=tmp_path/'datos';(folder/'libros').mkdir(parents=True)
    tres_tecnicos(source,folder/'libros/segundo_personas.xlsx')
    result=calcular(folder,'2025-07','REAL','segundo_personas')
    by={x['producto']:x for x in result['objetos']};assert by['REB']['mod']==9600 and by['MPR']['mod']==1920
    origins={t['origen'] for t in result['trazas'] if t['raiz'] and t['elemento']=='PD'}
    assert origins=={'TEC1','TEC2','TEC3'}
    server=ReynaServer(folder,0);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with sync.sync_playwright() as p:
            try:browser=p.chromium.launch(args=['--no-sandbox'])
            except Exception:browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
            page=browser.new_page();page.goto(f'http://127.0.0.1:{server.server_port}/')
            page.locator('#result-empresa').select_option('segundo_personas');page.locator('#result-periodo').fill('2025-07');page.locator('#result-cargar').click()
            sync.expect(page.locator('#result-status')).to_contain_text('actualizados',timeout=30000)
            page.locator('nav a[href="#ruta"]').click();page.locator('#ruta-objeto').select_option(by['REB']['codigo'])
            for i in (1,2,3):sync.expect(page.locator('#ruta-personas')).to_contain_text(f'Técnico {i}')
            assert page.locator('#ruta-personas tbody tr').count()>=3
            if os.environ.get('C31_CAPTURA'):
                page.screenshot(path=os.environ['C31_CAPTURA'], full_page=True)
            browser.close()
    finally:server.shutdown();thread.join();server.server_close()
    assert hashlib.sha256(source.read_bytes()).digest()==before
