"""Punto 6 y 7: cierre (verificar + conciliar + sellar, reapertura por versión) y aprobación con separación de funciones."""
import json, threading
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from reyna_local.__main__ import ReynaServer


def _post(url, body):
    return json.load(urlopen(Request(url, data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'}, method='POST'), timeout=300))


def _err(url, body):
    try:
        _post(url, body); raise AssertionError('debía rechazar')
    except HTTPError as e:
        return json.load(e)['error']


def test_cierre_conciliado_sellado_aprobado_y_reabierto(tmp_path):
    srv = ReynaServer(tmp_path / 'd', 0); th = threading.Thread(target=srv.serve_forever, daemon=True); th.start()
    b = f'http://127.0.0.1:{srv.server_port}'
    try:
        esp = _post(b + '/api/libros/operar?id=frenosa', {'name': 'Cierre'}); eid = 'esp_' + esp['id'][:12]
        _post(b + f"/api/workspaces/{esp['id']}/execute", {'transaction': 'T15', 'user': 'SUPERV1', 'request_id': 'c1',
              'header': {'FECHA': 20101228, 'PER': '2010-12', 'EMP': 'FRE', 'OBJ': 'OT-FRENOSA-SW50-2010-12', 'CEN': 'PLANTA_FRE', 'ALM': 'ALM_FRE'},
              'lines': [{'REC': 'MAT_SW50', 'CANT': 1000}]})
        assert 'perfil' in _err(b + f'/api/cierres/emitir?empresa={eid}&periodo=2010-12', {'usuario': 'GERENTE'})
        c = _post(b + f'/api/cierres/emitir?empresa={eid}&periodo=2010-12', {'usuario': 'JCOSTOS'})
        assert c['estado'] == 'EMITIDO' and c['version'] == 1
        conc = {x['cuenta']: x for x in c['conciliacion']}
        assert conc['EXISTENCIA MAT_SW50 / ALM_FRE']['ok'] and conc['CTA_OBJ_PER.COP_PERD (merma en exceso)']['ok']   # motor = costeo
        pid = c['id']
        assert 'REVISADO' in _err(b + f'/api/cierres/accion?id={pid}', {'accion': 'APROBAR', 'usuario': 'GERENTE'})       # no salta pasos
        assert _post(b + f'/api/cierres/accion?id={pid}', {'accion': 'REVISAR', 'usuario': 'CONTAB1', 'comentario': 'Conciliado'})['estado'] == 'REVISADO'
        assert _post(b + f'/api/cierres/accion?id={pid}', {'accion': 'APROBAR', 'usuario': 'GERENTE'})['estado'] == 'APROBADO'
        assert json.load(urlopen(b + f'/api/cierres/verificar?id={pid}'))['estado'] == 'INTEGRO'
        assert 'motivo' in _err(b + f'/api/cierres/emitir?empresa={eid}&periodo=2010-12', {'usuario': 'JCOSTOS'})
        v2 = _post(b + f'/api/cierres/emitir?empresa={eid}&periodo=2010-12', {'usuario': 'JCOSTOS', 'motivo': 'Reapertura de prueba'})
        lista = json.load(urlopen(b + f'/api/cierres?empresa={eid}'))['cierres']
        assert v2['version'] == 2 and len(lista) == 2 and lista[1]['previo'] == lista[0]['huella']                       # la v1 no se borra
        f = tmp_path / 'd/resultados/cierres' / f'{pid}.json'; p = json.loads(f.read_text()); p['resultados']['REAL']['kpi']['ventas'] = 1
        f.write_text(json.dumps(p)); assert json.load(urlopen(b + f'/api/cierres/verificar?id={pid}'))['estado'] == 'ALTERADO'
    finally:
        srv.shutdown(); th.join(); srv.server_close()
