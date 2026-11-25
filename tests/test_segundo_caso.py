"""SERVITEC: esperados independientes de docs/diseno/SEGUNDO_CASO.md."""
import hashlib
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
from reyna_local import libro_dbd, resultados

ROOT = Path(__file__).resolve().parents[1]
spec = spec_from_file_location('generar_segundo', ROOT / 'casos/segundo/generar.py')
mod = module_from_spec(spec)
spec.loader.exec_module(mod)
generar = mod.generar


def test_servitec_cifras_manual_y_conservacion(tmp_path):
    original = ROOT / 'casos/libros/frenosa.xlsx'
    before = hashlib.sha256(original.read_bytes()).digest()
    libro = generar(ROOT / 'casos/plantilla_dbd.xlsx', tmp_path / 'segundo.xlsx')
    assert not libro_dbd.validar(libro)
    expected = {'REAL': {'REB': {'md':6174, 'mod':9600, 'cif':5600, 'perdida':126, 'ocio':475, 'admin':1000, 'costo_total':22975},
                         'MPR': {'md':840, 'mod':1920, 'cif':1120, 'perdida':0, 'ocio':285, 'admin':1000, 'costo_total':5165}},
                'CONTABLE': {'REB': {'md':6174, 'mod':9600, 'cif':5600, 'costo_total':21374},
                             'MPR': {'md':840, 'mod':1920, 'cif':1120, 'costo_total':3880}}}
    for synthesis, products in expected.items():
        result = resultados.construir(libro, periodo='2025-07', sintesis=synthesis)
        by_product = {item['producto']: item for item in result['objetos']}
        for prod, fields in products.items():
            for field, value in fields.items():
                assert abs(by_product[prod][field] - value) <= .01, (synthesis, prod, field, by_product[prod][field], value)
    for month in range(1, 9):
        result = resultados.construir(libro, periodo=f'2025-{month:02d}', sintesis='REAL')
        check = next(x for x in result['control'] if x['control'].startswith('Conservación del reparto'))
        assert check['ok'], (month, check)
    assert result['periodo_actual'] == '2025-08'
    projections = [x for x in result['serie'] if x['tipo'] == 'PROYECTADO_EST']
    assert projections and all(x.get('p05') is not None and x.get('p95') is not None for x in projections)
    assert hashlib.sha256(original.read_bytes()).digest() == before
