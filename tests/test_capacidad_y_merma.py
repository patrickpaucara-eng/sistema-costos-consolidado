"""Punto 2: capacidad ociosa (NIC 2 §13) y merma normal frente a anormal (NIC 2 §16 a). Esperados calculados aparte."""
import json, shutil
from pathlib import Path

from openpyxl import load_workbook

from reyna_local import resultados, flujo
from reyna_local.store import Store

RAIZ = Path(__file__).resolve().parents[1]
LIBRO = RAIZ / 'casos/libros/frenosa.xlsx'
PUB = lambda per: json.loads((RAIZ / f'datos/resultados/frenosa_{per}_REAL.json').read_text(encoding='utf-8'))


def test_capacidad_ociosa_no_se_carga_al_producto(tmp_path):
    """MOD de diciembre con capacidad práctica = 125 % de los minutos usados: 20 % del costo de MOD es ocio del periodo."""
    p = tmp_path / 'f.xlsx'; shutil.copy(LIBRO, p); wb = load_workbook(p); ws = wb['MEDIDA']; cab = [c.value for c in ws[1]]
    usados = sum(float(r[cab.index('MED_CAN')]) for r in ws.iter_rows(min_row=2, values_only=True)
                 if r[cab.index('MED_PER')] == '2010-12' and r[cab.index('MED_CRIT')] == 'MIN_STD')
    fila = dict(MED_PER='2010-12', MED_EMP='FRE', MED_CRIT='MIN_STD', MED_NIVEL='CAP', MED_DEST='MOD', MED_CAN=usados * 1.25)
    ws.append([fila.get(c) for c in cab]); wb.save(p)
    c = resultados.calcular_periodos(str(p), 'FRE'); r = resultados.construir(str(p), periodo='2010-12', sintesis='REAL', _cache=c)
    mod_total = sum(o['mod'] for o in PUB('2010-12')['objetos'])            # todo el costo de MOD del mes (publicado)
    ocio = sum(x['importe'] for x in r['capacidad_ociosa'])
    assert abs(ocio - 0.2 * mod_total) < 0.5
    assert abs(sum(o['mod'] for o in r['objetos']) - 0.8 * mod_total) < 0.5
    assert any('capacidad ociosa' in x['concepto'] for x in r['estado_resultados'])
    assert all(x['ok'] for x in r['control'] if 'Conservación' in x['control'])


def test_merma_normal_va_al_producto_y_la_anormal_a_gasto(tmp_path):
    """Con merma normal de 5 % en la lista de materiales, 1,000 kg adicionales (< 5 % de 34,357) son costo de la orden."""
    p = tmp_path / 'f.xlsx'; shutil.copy(LIBRO, p); wb = load_workbook(p); ws = wb['COMPONENTE']; cab = [c.value for c in ws[1]]
    for fila in ws.iter_rows(min_row=2):
        if fila[cab.index('CMP_PRO')].value == 'SW50': fila[cab.index('CMP_MERMA')].value = 5
    wb.save(p)
    st = Store(tmp_path / 'datos'); w = st.create({'name': 'merma', 'workbook_path': str(p)})
    status, resp = st.execute(w['id'], {'transaction': 'T15', 'user': 'SUPERV1', 'request_id': 'm1',
        'header': {'FECHA': 20101228, 'PER': '2010-12', 'EMP': 'FRE', 'OBJ': 'OT-FRENOSA-SW50-2010-12', 'CEN': 'PLANTA_FRE', 'ALM': 'ALM_FRE'},
        'lines': [{'REC': 'MAT_SW50', 'CANT': 1000}]})
    assert status == 200, resp
    q = flujo.preparar(st.path(w['id'])); c = resultados.calcular_periodos(q, 'FRE'); r = resultados.construir(q, periodo='2010-12', sintesis='REAL', _cache=c)
    sw = next(o for o in r['objetos'] if o['producto'] == 'SW50'); base = next(o for o in PUB('2010-12')['objetos'] if o['producto'] == 'SW50')
    assert r['perdidas'] == [] and abs(sw['md'] - base['md'] - 3605.85) < 0.05
