import json
from pathlib import Path
import tempfile
import threading
from urllib.request import Request, urlopen

from docx import Document
from openpyxl import load_workbook

from reyna_local.exportar import exportar
from reyna_local.__main__ import ReynaServer

ROOT = Path(__file__).resolve().parents[1]
RESULTADOS = json.loads((ROOT / 'tests/fixtures/contrato/resultados_ejemplo.json').read_text())


def test_tres_excel_preservan_cifras_del_contrato():
    with tempfile.TemporaryDirectory() as temp:
        p = exportar(RESULTADOS, 'resultados', temp)
        wb = load_workbook(p, data_only=False)
        def read(sheet):
            rows = list(wb[sheet].values)
            return [dict(zip(rows[0], row)) for row in rows[1:]]
        assert read('Objetos')[0]['md'] == RESULTADOS['objetos'][0]['md']
        assert read('Actividades')[1]['costo'] == RESULTADOS['actividades'][1]['costo']
        assert read('Estado NIIF 18')[0]['importe'] == RESULTADOS['estado_resultados'][0]['importe']
        wb.close()
        p = exportar(RESULTADOS, 'analitica', temp)
        wb = load_workbook(p)
        assert read('Relevancia')[0]['importe'] == RESULTADOS['relevancia'][0]['importe']
        assert read('Relevancia')[1]['acumulado'] == RESULTADOS['relevancia'][1]['acumulado']
        assert read('Hallazgos')[0]['impacto'] == RESULTADOS['hallazgos'][0]['impacto']
        wb.close()
        p = exportar(RESULTADOS, 'proyeccion', temp)
        wb = load_workbook(p)
        assert read('Serie')[8]['p05'] == RESULTADOS['serie'][8]['p05']
        assert read('Escenarios')[1]['prob_perdida'] == RESULTADOS['escenarios'][1]['prob_perdida']
        assert read('Propuestas')[0]['impacto_anual'] == RESULTADOS['propuestas'][0]['impacto_anual']
        wb.close()


def test_html_sin_dependencias_externas_y_word_contiene_fuentes():
    with tempfile.TemporaryDirectory() as temp:
        html = exportar(RESULTADOS, 'html', temp).read_text()
        assert 'http://' not in html and 'https://' not in html
        for value in (688200.0, 12500, 48000):
            assert str(value) in html
        path = exportar(None, 'codigo', temp)
        text = '\n'.join(p.text for p in Document(path).paragraphs)
        assert 'src/reyna_local/contrato.py' in text
        assert 'tools/codigo_a_word.py' in text
        assert 'def validar(r):' in text


def test_endpoint_exporta_en_carpeta_de_datos():
    with tempfile.TemporaryDirectory() as temp:
        server = ReynaServer(temp, 0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            body = json.dumps({'resultados': RESULTADOS}).encode()
            req = Request(f'http://127.0.0.1:{server.server_port}/api/exportar?tipo=analitica', data=body,
                          headers={'Content-Type':'application/json'}, method='POST')
            with urlopen(req) as response:
                assert response.status == 201
                path = Path(json.load(response)['ruta'])
            assert path.parent == Path(temp).resolve() / 'exportaciones'
            book = load_workbook(path)
            assert book['Hallazgos']['D2'].value == 12500
            book.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
