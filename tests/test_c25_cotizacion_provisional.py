"""OT-C25: último REAL disponible cuando no hay periodos cerrados."""
import json
import threading
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import pytest
from reyna_local.__main__ import ReynaServer

ROOT = Path(__file__).resolve().parents[1]


def post(base, empresa, actividades):
    data = json.dumps({'empresa': empresa, 'actividades': actividades, 'materiales': {},
                       'precio_mercado': 5000, 'margen_objetivo': .3}).encode()
    with urlopen(Request(base+'/api/cotizar', data=data, headers={'Content-Type': 'application/json'}), timeout=60) as response:
        return json.load(response)


@pytest.mark.parametrize(('empresa','periodo'), [('frenosa','2010-12'),('segundo','2025-08')])
def test_ultimo_real_publicado_sin_cierre(tmp_path, empresa, periodo):
    result = json.loads((ROOT/f'datos/resultados/{empresa}_{periodo}_REAL.json').read_text())
    candidatos = [a['codigo'] for a in result['actividades'] if sum(1 for regla in result['modelo']['reglas'] if regla['etapa'] == 'P4C' and regla['origen'] == a['codigo'] and regla.get('inductor')) == 1]
    act = candidatos[0]
    server = ReynaServer(tmp_path, 0); thread = threading.Thread(target=server.serve_forever,daemon=True); thread.start()
    try:
        quote = post(f'http://127.0.0.1:{server.server_port}', empresa, {act:1})
        assert quote['periodo_base'] == periodo
        assert quote['aviso'] == 'tasas provisionales: mes no cerrado'
        assert quote['aviso'] in quote['avisos']
        assert quote['costo_pedido'] >= 0
    finally: server.shutdown(); thread.join(); server.server_close()


def test_no_inventa_periodo_si_no_hay_resultados(tmp_path):
    import shutil
    books = tmp_path/'libros'; books.mkdir()
    shutil.copyfile(ROOT/'casos/libros/frenosa.xlsx', books/'sin_resultados.xlsx')
    server = ReynaServer(tmp_path, 0); thread = threading.Thread(target=server.serve_forever,daemon=True); thread.start()
    try:
        with pytest.raises(HTTPError) as exc:
            post(f'http://127.0.0.1:{server.server_port}', 'sin_resultados', {})
        assert exc.value.code == 404
    finally: server.shutdown(); thread.join(); server.server_close()


def test_actividad_de_apoyo_sin_inductor_operativo_se_rechaza(tmp_path):
    server = ReynaServer(tmp_path, 0); thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        with pytest.raises(HTTPError) as exc:
            post(f'http://127.0.0.1:{server.server_port}', 'frenosa', {'A-CC': 1})
        assert exc.value.code == 422
        assert 'inductor único' in json.load(exc.value)['error']
    finally: server.shutdown(); thread.join(); server.server_close()
