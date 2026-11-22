"""Punto 9: la analítica mide sus propuestas aprobadas en los meses siguientes y aprende un factor de efectividad."""
import json, threading
from pathlib import Path
from urllib.request import Request, urlopen

from reyna_local.__main__ import ReynaServer

RAIZ = Path(__file__).resolve().parents[1]
PUB = lambda per: json.loads((RAIZ / f'datos/resultados/frenosa_{per}_REAL.json').read_text(encoding='utf-8'))


def _post(url, body):
    return json.load(urlopen(Request(url, data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'}, method='POST'), timeout=300))


def test_seguimiento_y_aprendizaje_desde_propuestas_aprobadas(tmp_path):
    srv = ReynaServer(tmp_path / 'd', 0); th = threading.Thread(target=srv.serve_forever, daemon=True); th.start()
    b = f'http://127.0.0.1:{srv.server_port}'
    try:
        sin = _post(b + '/api/calcular?empresa=frenosa&sintesis=REAL&periodo=2010-12', {})
        assert sin['seguimiento'] == [] and all(p['base_aprendizaje'].startswith('sin historia') for p in sin['propuestas'])
        pid = _post(b + '/api/cierres/emitir?empresa=frenosa&periodo=2010-11', {'usuario': 'JCOSTOS'})['id']
        _post(b + f'/api/cierres/accion?id={pid}', {'accion': 'REVISAR', 'usuario': 'CONTAB1'})
        _post(b + f'/api/cierres/accion?id={pid}', {'accion': 'APROBAR', 'usuario': 'GERENTE'})
        r = _post(b + '/api/calcular?empresa=frenosa&sintesis=REAL&periodo=2010-12', {})
        nov, dic = {o['producto']: o for o in PUB('2010-11')['objetos']}, {o['producto']: o for o in PUB('2010-12')['objetos']}
        props = [p for p in PUB('2010-11')['propuestas'] if p['elemento'] == 'MD']
        assert props and len([s for s in r['seguimiento'] if s['elemento'] == 'MD']) == len(props)
        for s in (x for x in r['seguimiento'] if x['elemento'] == 'MD'):
            n, d = nov[s['producto']], dic[s['producto']]
            esperado = (n['md'] / n['cantidad'] - d['md'] / d['cantidad']) * d['cantidad']
            assert abs(s['ahorro_realizado_mes'] - esperado) < 0.05
        f = r['aprendizaje']['MD']
        medidos = [s['cumplimiento'] for s in r['seguimiento'] if s['elemento'] == 'MD' and s['cumplimiento'] is not None]
        assert f['mediciones'] == len(medidos) and abs(f['factor'] - sum(medidos) / len(medidos)) < 1e-4
        for p in (x for x in r['propuestas'] if x['elemento'] == 'MD'):
            assert abs(p['impacto_esperado'] - p['impacto_anual'] * f['factor']) < 0.02
    finally:
        srv.shutdown(); th.join(); srv.server_close()
