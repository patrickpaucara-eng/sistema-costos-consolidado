"""Asignación de una capacidad escasa desde el panel Decidir; caso a mano C32-4."""
import copy
import json
import threading
from pathlib import Path
from urllib.request import Request, urlopen

import pytest

from reyna_local import decidir as D
from reyna_local.__main__ import ReynaServer


ROOT = Path(__file__).resolve().parents[1]


def _caso():
    return {
        'sintesis': 'REAL',
        'objetos': [
            {'codigo': 'OT-A', 'producto': 'A', 'cantidad': 40},
            {'codigo': 'OT-B', 'producto': 'B', 'cantidad': 70},
        ],
        'decidir': {'er_gerencial': {'productos': [
            {'producto': 'A', 'cantidad': 40, 'margen_contribucion': 1200},
            {'producto': 'B', 'cantidad': 70, 'margen_contribucion': 1400},
        ]}},
        'datos_libro': {
            'ventas': [{'producto': 'A', 'cantidad': 40}, {'producto': 'B', 'cantidad': 70}],
            'medidas': [
                {'inductor': 'HM', 'nivel': 'CAP', 'destino': 'MAQUINA', 'destino_nombre': 'Máquina', 'cantidad': 100},
                {'inductor': 'HM', 'nivel': 'OBJ', 'destino': 'OT-A', 'cantidad': 80},
                {'inductor': 'HM', 'nivel': 'OBJ', 'destino': 'OT-B', 'cantidad': 70},
            ],
        },
        'trazas': [{'criterio': 'HM', 'origen': 'MAQUINA', 'destino': 'FO-1'}],
    }


def test_caso_manual_asigna_por_mc_por_hora():
    r = D.asignar_recurso(_caso(), 'HM', 'MAQUINA', {'A': 40, 'B': 70})
    b, a = r['productos']
    assert (b['producto'], b['mc_por_unidad_recurso'], b['unidades_sugeridas'], b['capacidad_usada']) == ('B', 20, 70, 70)
    assert (a['producto'], a['mc_por_unidad_recurso'], a['unidades_sugeridas'], a['capacidad_usada']) == ('A', 15, 15, 30)
    assert (r['capacidad_utilizada'], r['capacidad_restante'], r['margen_contribucion_total']) == (100, 0, 1850)


@pytest.fixture
def server(tmp_path):
    resultados = tmp_path / 'resultados'
    resultados.mkdir()
    (resultados / 'frenosa_2010-07_REAL.json').write_text(json.dumps(_caso()), encoding='utf-8')
    s = ReynaServer(tmp_path, 0)
    t = threading.Thread(target=s.serve_forever, daemon=True)
    t.start()
    yield f'http://127.0.0.1:{s.server_port}', tmp_path
    s.shutdown(); t.join(); s.server_close()


def _post(base, body):
    req = Request(base + '/api/decidir', data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
    with urlopen(req, timeout=30) as response:
        return json.load(response)


def test_api_asigna_la_capacidad_escasa(server):
    base, _ = server
    out = _post(base, {'empresa': 'frenosa', 'periodo': '2010-07', 'caso': 'recurso_escaso',
                         'criterio': 'HM', 'destino': 'MAQUINA', 'demanda_maxima': {'A': 40, 'B': 70}})
    assert out['margen_contribucion_total'] == 1850
    assert [(f['producto'], f['unidades_sugeridas']) for f in out['productos']] == [('B', 70), ('A', 15)]


def test_panel_real_permite_elegir_recurso_y_demanda(server):
    sync = pytest.importorskip('playwright.sync_api')
    base_url, root = server
    resultado = json.loads((ROOT / 'datos/resultados/frenosa_2010-07_REAL.json').read_text(encoding='utf-8'))
    base = _caso()
    resultado['periodo_actual'] = '2010-12'
    resultado['objetos'] = [dict(resultado['objetos'][0], codigo='OT-A', producto='A', cantidad=40),
                            dict(resultado['objetos'][1], codigo='OT-B', producto='B', cantidad=70)]
    resultado['decidir']['er_gerencial']['productos'] = base['decidir']['er_gerencial']['productos']
    resultado['decidir']['er_gerencial']['total'] = {}
    resultado['datos_libro']['ventas'] = base['datos_libro']['ventas']
    resultado['datos_libro']['medidas'] = base['datos_libro']['medidas']
    t1 = copy.deepcopy(resultado['trazas'][0]); t2 = copy.deepcopy(resultado['trazas'][0])
    for t, objeto in ((t1, 'OT-A'), (t2, 'OT-B')):
        t.update(objeto=objeto, elemento='PD', origen='MAQUINA', destino='FO-1', criterio='HM', raiz=True)
    resultado['trazas'] = [t1, t2]
    (root / 'resultados' / 'frenosa_2010-12_REAL.json').write_text(json.dumps(resultado), encoding='utf-8')
    with sync.sync_playwright() as p:
        try:
            browser = p.chromium.launch(args=['--no-sandbox'])
        except Exception:
            browser = p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        page = browser.new_page()
        page.goto(base_url)
        sync.expect(page.locator('#dc-recurso option')).to_have_count(1, timeout=30000)
        page.locator('nav a[href="#decidir"]').click()
        page.locator('#dc-recurso').select_option(value=json.dumps(['HM', 'MAQUINA'], separators=(',', ':')))
        page.locator('#dc-demanda-maxima input[data-producto="A"]').fill('40')
        page.locator('#dc-demanda-maxima input[data-producto="B"]').fill('70')
        page.locator('#dc-asignar').click()
        sync.expect(page.locator('#dc-escasez-resultado tbody tr')).to_have_count(2, timeout=30000)
        filas = page.locator('#dc-escasez-resultado tbody tr').all_text_contents()
        assert 'B' in filas[0] and '70' in filas[0]
        assert 'A' in filas[1] and '15' in filas[1]
        sync.expect(page.locator('#dc-escasez-estado')).to_contain_text('1,850')
        browser.close()
