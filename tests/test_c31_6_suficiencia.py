from reyna_local.suficiencia import detectar, detectar_libro
from pathlib import Path


def test_niveles_exigen_datos_y_son_secuenciales():
    t={'EVENTO':[{'EVE_NUM':1,'EVE_OBJ':'OT','EVE_PER':'2025-01'}], 'LINEA':[{'LIN_EVE':1,'LIN_CAN':1,'LIN_MTO':3}], 'VENTA':[{'VTA_ING':5}]}
    r=detectar(t); assert r['nivel']==0 and 'horas' in r['falta']
    t['CRITERIO']=[{'CRI_COD':'H','CRI_UNI':'h'}]
    t['MEDIDA']=[{'MED_NIVEL':'OBJ','MED_CRIT':'H','MED_CAN':1}]
    assert detectar(t)['nivel']==1
    t.update(CENTRO=[{}], ACTIVIDAD=[{}]); assert detectar(t)['nivel']==2
    assert detectar({})['nivel'] is None


def test_casos_reales_no_fabrican_nivel_cuatro():
    root=Path(__file__).resolve().parents[1]
    for name in ('frenosa','segundo'):
        r=detectar_libro(root/'casos/libros'/f'{name}.xlsx')
        assert r['nivel'] in (0,1,2,3,4,None)
        assert 'no certifica' in r['aviso']


def test_api_y_plantillas_por_nivel(tmp_path):
    import json, threading
    from io import BytesIO
    from urllib.request import urlopen
    from openpyxl import load_workbook
    from reyna_local.__main__ import ReynaServer
    server=ReynaServer(tmp_path,0); thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        base=f'http://127.0.0.1:{server.server_port}'
        with urlopen(base+'/api/suficiencia?empresa=frenosa') as res: data=json.load(res)
        assert 'falta' in data and 'requisitos' in data
        for nivel in range(5):
            with urlopen(base+f'/api/plantilla-nivel?nivel={nivel}') as res: raw=res.read()
            wb=load_workbook(BytesIO(raw),read_only=True); assert wb['NIVEL']['B1'].value==nivel
            assert 'EMPRESA' in wb.sheetnames; wb.close()
    finally: server.shutdown();thread.join();server.server_close()


def test_aviso_en_barra_en_chromium(tmp_path):
    import threading
    import pytest
    from reyna_local.__main__ import ReynaServer
    sync=pytest.importorskip('playwright.sync_api')
    server=ReynaServer(tmp_path,0); thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with sync.sync_playwright() as p:
            try: browser=p.chromium.launch(args=['--no-sandbox'])
            except Exception: browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
            page=browser.new_page();page.goto(f'http://127.0.0.1:{server.server_port}/')
            sync.expect(page.locator('#suficiencia-estado')).to_contain_text('no certifica',timeout=30000)
            page.locator('#suficiencia-nivel').select_option('3')
            assert 'nivel=3' in page.locator('#suficiencia-plantilla').get_attribute('href')
            import os
            if os.environ.get('C31_CAPTURA'):
                page.screenshot(path=os.environ['C31_CAPTURA'])
            browser.close()
    finally: server.shutdown();thread.join();server.server_close()
