"""OT-C08: un comando arma los entregables de la monografía; los Excel repiten las cifras del contrato publicado."""
import json
from pathlib import Path
import sys

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/entrega'))


def test_armar_entregables(tmp_path, monkeypatch):
    import armar
    monkeypatch.setattr(armar.subprocess, 'run', lambda *a, **k: None)          # no reescribir el registro del repo en la prueba
    monkeypatch.setattr(armar.shutil, 'copy', lambda o, d: Path(d).write_bytes(Path(o).read_bytes()) and d)
    junit = tmp_path / 'j.xml'
    junit.write_text('<testsuites><testsuite><testcase classname="tests.test_contrato" name="test_valido"/></testsuite></testsuites>')
    salida = tmp_path / 'entrega'
    armar.armar('2010-12', salida, junit)
    nombres = {p.name for p in salida.iterdir()}
    for n, _, arch in armar.INDICE:
        if n == '11':
            continue                                                            # EXE: se compila en Windows
        for s in armar.SINTESIS if '{s}' in arch else ('',):
            for a in arch.format(s=s).split(', '):
                assert a in nombres, a
    for s in armar.SINTESIS:
        r = json.loads((ROOT / f'datos/resultados/frenosa_2010-12_{s}.json').read_text(encoding='utf-8'))
        ws = load_workbook(salida / f'06_resultados_{s}.xlsx', read_only=True)['Objetos']
        filas = list(ws.iter_rows(values_only=True)); col = filas[0].index('costo_total')
        assert abs(sum(f[col] for f in filas[1:]) - r['kpi']['costo_total']) < 0.05
        html = (salida / f'12b_informe_{s}.html').read_text(encoding='utf-8')
        assert 'http://' not in html and 'https://' not in html                 # sin conexión de verdad
    sistema = (salida / '12_sistema_sin_conexion.html').read_text(encoding='utf-8')
    assert 'window.__DATOS=' in sistema and 'frenosa_2010-12_ESTIMADO' in sistema
    assert 'src="http' not in sistema and 'href="http' not in sistema          # ningún recurso externo
    entrada = load_workbook(salida / '05_datos_entrada.xlsx', read_only=True)          # el libro DBD con que se calcula
    assert entrada.sheetnames[0] == 'LEEME' and {'EMPRESA', 'KARDEX', 'REGLA_REPARTO', 'VENTA'} <= set(entrada.sheetnames)
    fuentes = load_workbook(salida / '05b_fuentes_erp_adaptador.xlsx', read_only=True)  # lo que el adaptador convierte
    assert 'FUENTES' in fuentes.sheetnames and 'Gastos_Operativos_SUPUESTOS' in fuentes.sheetnames
    assert '11. Ejecutable' in (salida / 'LEEME.txt').read_text(encoding='utf-8')
