"""Flujo único: el mismo libro DBD se opera (transacciones del motor) y se costea. Un consumo registrado en la operación
aparece en el kardex, en la orden (si está dentro del estándar) o como pérdida anormal (si excede el estándar, NIC 2 §16 a)."""
import json
from pathlib import Path
import threading
from urllib.request import Request, urlopen

from reyna_local.__main__ import ReynaServer

RAIZ = Path(__file__).resolve().parents[1]


def _post(url, body):
    return json.load(urlopen(Request(url, data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'}, method='POST'), timeout=180))


def test_operar_y_costear_el_mismo_libro(tmp_path):
    server = ReynaServer(tmp_path / 'datos', 0); th = threading.Thread(target=server.serve_forever, daemon=True); th.start()
    base = f'http://127.0.0.1:{server.server_port}'
    try:
        esp = _post(base + '/api/libros/operar?id=frenosa', {'name': 'Planta Frenosa'})
        assert esp['company_code'] == 'FRE'
        eid = 'esp_' + esp['id'][:12]
        assert eid in {l['id'] for l in json.load(urlopen(base + '/api/libros'))['libros']}
        antes = _post(base + f'/api/calcular?empresa={eid}&sintesis=REAL&periodo=2010-12', {})
        publicado = json.loads((RAIZ / 'datos/resultados/frenosa_2010-12_REAL.json').read_text(encoding='utf-8'))
        assert antes['kpi'] == publicado['kpi']                         # el libro operable costea idéntico al publicado
        # consumo de 1,000 kg de SW50 a una orden que ya consumió su estándar → todo es exceso (pérdida del periodo)
        r = _post(base + f"/api/workspaces/{esp['id']}/execute", {
            'transaction': 'T15', 'user': 'SUPERV1', 'request_id': 'flujo-1',
            'header': {'FECHA': 20101228, 'PER': '2010-12', 'EMP': 'FRE', 'OBJ': 'OT-FRENOSA-SW50-2010-12', 'CEN': 'PLANTA_FRE', 'ALM': 'ALM_FRE'},
            'lines': [{'REC': 'MAT_SW50', 'CANT': 1000}]})
        assert r.get('result') != 'ERROR', r
        despues = _post(base + f'/api/calcular?empresa={eid}&sintesis=REAL&periodo=2010-12', {})
        sw = lambda x: next(o for o in x['objetos'] if o['producto'] == 'SW50')
        assert sw(despues)['md'] == sw(antes)['md']                     # el exceso no entra a la orden
        perdida = despues['perdidas'][0]
        assert perdida['cantidad_exceso'] == 1000 and abs(perdida['importe'] - 3605.84) < 0.02
        assert abs((antes['kpi']['margen_operativo'] - despues['kpi']['margen_operativo']) - perdida['importe']) < 0.02
        mov = [k for k in despues['kardex'] if k['material'] == 'MAT_SW50'][-1]
        assert mov['cantidad'] == -1000 and mov['fecha'] == '2010-12-28'  # kardex derivado de la transacción
        assert all(c['ok'] for c in despues['control'] if 'kardex' in c['control'].lower() or 'Conservación' in c['control'])
    finally:
        server.shutdown(); th.join(); server.server_close()
