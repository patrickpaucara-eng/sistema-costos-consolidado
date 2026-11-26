"""El servicio conserva las cifras del cálculo al exportar las tres síntesis."""
import json
from pathlib import Path
import tempfile
import threading
from urllib.request import Request, urlopen
from openpyxl import load_workbook
from reyna_local.__main__ import ReynaServer


def test_calcular_consultar_exportar():
    with tempfile.TemporaryDirectory() as directory:
        server = ReynaServer(directory, 0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f'http://127.0.0.1:{server.server_port}'
        try:
            for sintesis in ('REAL', 'CONTABLE'):  # ESTIMADO retirado como síntesis (DECISIONES_DUENO 25-nov)
                query = f'?sintesis={sintesis}&periodo=2010-07'
                request = Request(base + '/api/calcular' + query, data=b'{}', headers={'Content-Type':'application/json'}, method='POST')
                with urlopen(request, timeout=120) as response:
                    calculated = json.load(response)
                with urlopen(base + '/api/resultados' + query) as response:
                    result = json.load(response)
                assert result == calculated
                publicado = json.loads((Path(__file__).resolve().parents[1] / 'datos/resultados' / f'frenosa_2010-07_{sintesis}.json').read_text())
                for key in ('ventas', 'costo_total', 'margen_operativo'):
                    assert result['kpi'][key] == publicado['kpi'][key]
                payload = json.dumps({'resultados': result}).encode()
                request = Request(base + '/api/exportar?tipo=resultados', data=payload, headers={'Content-Type':'application/json'}, method='POST')
                with urlopen(request) as response:
                    name = Path(json.load(response)['ruta']).name
                with urlopen(base + '/api/descargar?archivo=' + name) as response:
                    data = response.read()
                file = Path(directory) / 'exportado.xlsx'
                file.write_bytes(data)
                book = load_workbook(file, data_only=True)
                values = list(book['Objetos'].values)
                headers = list(values[0])
                for key in ('md', 'mod', 'costo_total'):
                    assert values[1][headers.index(key)] == result['objetos'][0][key]
                book.close()
        finally:
            server.shutdown()
            thread.join()
            server.server_close()
