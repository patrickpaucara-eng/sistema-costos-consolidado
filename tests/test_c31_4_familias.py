"""Pantalla y API de familias: cálculos del diseño y casos inválidos."""
import json
import os
import threading
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from pathlib import Path
import pytest
from nav_helpers import ir_a_pestana
from reyna_local.__main__ import ReynaServer


@pytest.fixture
def server(tmp_path):
    s=ReynaServer(tmp_path,0); t=threading.Thread(target=s.serve_forever,daemon=True);t.start()
    yield f'http://127.0.0.1:{s.server_port}'
    s.shutdown();t.join();s.server_close()


def post(base, body):
    request=Request(base+'/api/familias/analizar',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
    with urlopen(request,timeout=30) as r:return json.load(r)


def test_casos_y_datos_incompletos(server):
    a={'ACT':[10,11,9,10,10]};b={'ACT':[10.2,9.8,10.5,9.9,10.1]}
    r=post(server,{'historia':a,'componente':{'ACT':11.5},'comparar':b})
    assert round(r['receta']['ACT']['minimo'],2)==7.85
    assert round(r['receta']['ACT']['maximo'],2)==12.15
    assert r['pertenencia']['pertenece'] and r['sugerir_fusion']
    assert round(r['comparacion']['ACT']['p'],3)==.776
    assert not post(server,{'historia':a,'componente':{'ACT':14}})['pertenencia']['pertenece']
    with pytest.raises(HTTPError) as exc: post(server,{'historia':a,'componente':{}})
    assert exc.value.code==422


def test_pantalla_real(server):
    sync=pytest.importorskip('playwright.sync_api')
    with sync.sync_playwright() as p:
        try: browser=p.chromium.launch(args=['--no-sandbox'])
        except Exception: browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        page=browser.new_page();page.goto(server);ir_a_pestana(page, '#familias')
        page.locator('#fam-historia').fill('{"ACT": [10,11,9,10,10]}')
        page.locator('#fam-componente').fill('{"ACT": 11.5}')
        page.locator('#fam-analizar').click()
        sync.expect(page.locator('#fam-estado')).to_contain_text('calculada')
        sync.expect(page.locator('#fam-decision')).to_contain_text('compatible')
        assert page.locator('#fam-receta tbody tr').count()==1
        if os.getenv('C31_CAPTURA'): page.screenshot(path=os.environ['C31_CAPTURA'], full_page=False)
        page.locator('#fam-usar').click()
        sync.expect(page.locator('#cotizador')).to_be_visible()
        browser.close()


def test_cotizacion_proyectada_por_familia(server):
    historia={'FO-1':[1,1.1,.9,1,1]}
    familia=post(server,{'historia':historia})['receta']
    body={'empresa':'frenosa','actividades':{},'materiales':{},'precio_mercado':10000,'margen_objetivo':.2,'meses':1,'intervalo':1,'familia':familia,'unidades':2}
    req=Request(server+'/api/cotizar',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
    with urlopen(req,timeout=60) as r: out=json.load(r)
    assert out['total']>0 and out['intervalos']
    body['familia']['FO-1']['media']=-1
    req=Request(server+'/api/cotizar',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
    with pytest.raises(HTTPError) as exc: urlopen(req,timeout=60)
    assert exc.value.code==422
