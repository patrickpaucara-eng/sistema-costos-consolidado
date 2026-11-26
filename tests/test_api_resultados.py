"""El servidor entrega contratos publicados y señala el ejemplo alternativo."""
import json
import tempfile
import threading
from urllib.error import HTTPError
from urllib.request import urlopen

from reyna_local.__main__ import ReynaServer
from reyna_local.contrato import validar


def test_api_resultados_reales_ejemplo_y_parametros_invalidos():
    with tempfile.TemporaryDirectory() as directory:
        server = ReynaServer(directory, 0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f'http://127.0.0.1:{server.server_port}/api/resultados'
        try:
            with urlopen(url + '?sintesis=REAL&periodo=2010-07') as response:
                real = json.load(response)
            assert validar(real) == []
            assert real['empresa']['nombre'] == 'Frenosa'
            assert real['kpi']['ventas'] == 888730
            with urlopen(url + '?sintesis=CONTABLE&periodo=2011-08') as response:
                ejemplo = json.load(response)
            assert validar(ejemplo) == []
            assert 'EJEMPLO' in ejemplo['_nota']  # [ARQ] Etapa 3 ya publica 2010-08; el ejemplo se prueba con un periodo sin datos
            try:
                urlopen(url + '?sintesis=REAL&periodo=../../secreto')
            except HTTPError as error:
                assert error.code == 400
            else:
                raise AssertionError('Se aceptó un periodo inválido')
        finally:
            server.shutdown()
            thread.join()
            server.server_close()
