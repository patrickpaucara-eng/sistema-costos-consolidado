"""Ruta del costo, kardex, modelo y panel de calidad: lo que hace visible el método (no solo el resultado)."""
import json
from pathlib import Path

RES = Path(__file__).resolve().parents[1] / 'datos/resultados'


def _r(per, s):
    return json.loads((RES / f'frenosa_{per}_{s}.json').read_text(encoding='utf-8'))


def test_ruta_del_costo_explica_cada_elemento_de_cada_orden():
    """ALG-11: los tramos origen (desde un recurso) suman el elemento del objeto; vale en REAL y en CONTABLE."""
    campos = dict(MD='md', CIF='cif', GAD='admin', GVT='gasto_venta', GFI='financiero')
    for s in ('REAL', 'CONTABLE'):
        r = _r('2010-07', s)
        for o in r['objetos']:
            for e, campo in campos.items():
                raiz = sum(t['monto'] for t in r['trazas'] if t['objeto'] == o['codigo'] and t['elemento'] == e and t['raiz'])
                assert abs(raiz - o[campo]) < 0.05, (s, o['producto'], e)
            mod = sum(t['monto'] for t in r['trazas'] if t['objeto'] == o['codigo'] and t['elemento'] in ('PD', 'SD') and t['raiz'])
            assert abs(mod - o['mod']) < 0.05


def test_contable_no_traza_gastos_del_periodo():
    r = _r('2010-07', 'CONTABLE')
    assert {t['elemento'] for t in r['trazas']} <= {'MD', 'PD', 'SD', 'CIF'}


def test_kardex_continuo_y_md_igual_a_salidas():
    """El MD de julio es lo que salió del kardex (salidas − devoluciones no van a la orden)."""
    r = _r('2010-07', 'REAL')
    salidas = -sum(k['importe'] for k in r['kardex'] if k['movimiento'] == 'SALIDA')
    assert abs(salidas - sum(o['md'] for o in r['objetos'])) < 0.05
    assert all(k['saldo_cantidad'] >= 0 for k in r['kardex'])


def test_panel_de_calidad_detecta_inductores_que_no_suman_100():
    """El caso publicado tiene inductores que suman 99 % y 101 %: el sistema los detecta y aun así conserva el costo."""
    r = _r('2010-07', 'REAL')
    observados = [c for c in r['control'] if not c['ok']]
    assert len(observados) == 4 and all('suma' in c['control'] for c in observados)
    assert all(c['ok'] for c in r['control'] if 'Conservación' in c['control'] or 'Kardex' in c['control'])


def test_modelo_abc_es_dato_del_libro():
    m = _r('2010-07', 'REAL')['modelo']
    assert {x['etapa'] for x in m['reglas']} >= {'P1', 'P2', 'P4A', 'P4C', 'P5', 'P6', 'P7'}
    assert len(m['actividades']) == 14 and all(x['nombre'] for x in m['recursos'])
