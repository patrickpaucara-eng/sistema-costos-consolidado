"""La pantalla usa el endpoint de periodos y conserva el alcance de los datos."""
import json
import threading
from pathlib import Path
from urllib.request import urlopen

from reyna_local.__main__ import ReynaServer

ROOT = Path(__file__).resolve().parents[1]


def test_endpoint_bimestral_y_controles(tmp_path):
    server = ReynaServer(tmp_path, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f'http://127.0.0.1:{server.server_port}'
        with urlopen(base + '/api/periodos?empresa=frenosa&sintesis=REAL&desde=2010-07-01&hasta=2010-08-31&grano=bimestre', timeout=60) as response:
            (bucket,) = json.load(response)['cubetas']
        monthly = [json.loads((ROOT / f'datos/resultados/frenosa_2010-{m}_REAL.json').read_text()) for m in ('07', '08')]
        assert bucket['costo']['completo']
        assert abs(bucket['costo']['costo_total'] - sum(x['kpi']['costo_total'] for x in monthly)) < .01
        page = (ROOT / 'src/reyna_local/web/index.html').read_text(encoding='utf-8')
        for control in ('periodos-desde', 'periodos-hasta', 'periodos-grano', 'periodos-sintesis', 'periodos-resultados'):
            assert f'id="{control}"' in page
        assert '/api/periodos?' in page
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
