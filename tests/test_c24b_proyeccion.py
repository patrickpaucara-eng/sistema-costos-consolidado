"""Excel 8 transcribe C21 y no altera el libro del que parte."""
import hashlib
import json
import threading
from pathlib import Path
from urllib.request import Request, urlopen
from openpyxl import load_workbook
import pytest
from reyna_local.exportar import exportar, obtener_proyeccion
from reyna_local.proyeccion import proyectar_granular

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / 'casos/libros/frenosa.xlsx'
RESULT = json.loads((ROOT / 'datos/resultados/frenosa_2010-12_REAL.json').read_text())


def test_hojas_y_mes_uno_factores_identidad(tmp_path):
    before = hashlib.sha256(BOOK.read_bytes()).hexdigest()
    factores = {'vol': {o['producto']: 1 for o in RESULT['objetos']},
                'pre': {r['codigo']: 1 for r in RESULT['modelo']['recursos']},
                'pv': {o['producto']: 1 for o in RESULT['objetos']}}
    projection = proyectar_granular(BOOK, 'FRE', meses=1, factores=factores)
    path = exportar(RESULT, 'proyeccion', tmp_path, proyeccion_granular=projection)
    wb = load_workbook(path, data_only=True)
    ws = wb['Proyección por hechos']; assert ws['B1'].value == '2010-12'
    assert ws['D1'].value == 'REAL integral'
    rows = list(ws.values); head = rows[1]; rows = [dict(zip(head, r)) for r in rows[2:]]
    assert {r['producto'] for r in rows} == {o['producto'] for o in RESULT['objetos']}
    for obj in RESULT['objetos']:
        row = next(r for r in rows if r['producto'] == obj['producto'])
        assert row['periodo'] == '2011-01'
        assert abs(row['costo_total'] - obj['costo_total']) <= 0.01
    ws = wb['Sensibilidad']; vals = list(ws.values)
    assert [{k: v for k, v in zip(vals[1], row) if k is not None} for row in vals[2:]] == projection['sensibilidad']
    wb.close(); assert hashlib.sha256(BOOK.read_bytes()).hexdigest() == before


def test_rechaza_libro_distinto(tmp_path):
    result = {**RESULT, 'sello': {**RESULT['sello'], 'huella_libro': '0' * 64}}
    with pytest.raises(ValueError, match='libro cambió'):
        obtener_proyeccion(result, tmp_path, 'frenosa')
    result = {**RESULT, 'empresa': {'codigo': 'OTRA'}}
    with pytest.raises(ValueError, match='empresa'):
        obtener_proyeccion(result, tmp_path, 'frenosa')


def test_api_exporta_seis_meses(tmp_path):
    from reyna_local.__main__ import ReynaServer
    server = ReynaServer(tmp_path, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        data = json.dumps({'resultados': RESULT, 'empresa': 'frenosa'}).encode()
        req = Request(f'http://127.0.0.1:{server.server_port}/api/exportar?tipo=proyeccion',
                      data=data, headers={'Content-Type': 'application/json'})
        with urlopen(req, timeout=60) as response: ruta = Path(json.load(response)['ruta'])
        wb = load_workbook(ruta, data_only=True); rows = list(wb['Proyección por hechos'].values)
        assert {r[0] for r in rows[2:]} == {'2011-01','2011-02','2011-03','2011-04','2011-05','2011-06'}
        assert wb['Sensibilidad'].max_row > 2
        wb.close()
    finally:
        server.shutdown(); thread.join(); server.server_close()


def test_manual_cubre_grupos_y_sin_advertencia_obsoleta(tmp_path):
    import importlib.util
    spec = importlib.util.spec_from_file_location('docs_c24', ROOT/'tools/entrega/documentos_c24.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    groups = {x[0].split(' · ')[0] for x in module.PANTALLAS}
    assert groups == {'Definir', 'Estimar', 'Registrar', 'Entregar', 'Aprender'}
    # Se verifica el documento generado sin convertir una captura fallida en aprobación.
    module.generar(tmp_path)
    from docx import Document
    doc = Document(tmp_path/'10_manual_usuario.docx')
    text = '\n'.join(p.text for p in doc.paragraphs)
    assert 'en habilitación' not in text.lower()
    assert all(group in text for group in groups)
