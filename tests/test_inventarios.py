"""Inventario de producto terminado, en proceso y D14 (venta antes de liquidar), con esperados calculados aparte
desde los costos por orden publicados (no desde el módulo que se prueba)."""
import json, shutil
from pathlib import Path

from openpyxl import load_workbook

from reyna_local import resultados

RAIZ = Path(__file__).resolve().parents[1]
LIBRO = RAIZ / 'casos/libros/frenosa.xlsx'


def _pub(per, s='CONTABLE'):
    return json.loads((RAIZ / f'datos/resultados/frenosa_{per}_{s}.json').read_text(encoding='utf-8'))


def _orden(per, prod):
    return next(o for o in _pub(per)['objetos'] if o['producto'] == prod)


def _editar(tmp_path, cambios):
    p = tmp_path / 'f.xlsx'; shutil.copy(LIBRO, p); wb = load_workbook(p)
    for hoja, filtro, col, valor in cambios:
        ws = wb[hoja]; cab = [c.value for c in ws[1]]
        for fila in ws.iter_rows(min_row=2):
            d = {cab[i]: c.value for i, c in enumerate(fila)}
            if filtro(d): fila[cab.index(col)].value = valor
    wb.save(p); return str(p)


def _r(libro, per):
    c = resultados.calcular_periodos(libro, 'FRE'); return resultados.construir(libro, periodo=per, sintesis='CONTABLE', _cache=c)


def test_producto_terminado_queda_en_inventario(tmp_path):
    sw = _orden('2010-12', 'SW50')
    mitad = sw['cantidad'] / 2
    libro = _editar(tmp_path, [('VENTA', lambda d: d['VTA_PER'] == '2010-12' and d['VTA_REC'] == 'SW50', 'VTA_CAN', mitad)])
    r = _r(libro, '2010-12'); inv = r['inventarios']
    assert abs(inv['total_pt'] - sw['costo_total'] / 2) < 0.05                      # medio lote al costo de producción
    assert abs(inv['costo_ventas'] - (_pub('2010-12')['inventarios']['costo_ventas'] - sw['costo_total'] / 2)) < 0.05
    assert abs(r['kpi']['margen_operativo'] - (_pub('2010-12')['kpi']['margen_operativo'] + sw['costo_total'] / 2)) < 0.05


def test_orden_abierta_es_inventario_en_proceso_y_su_venta_es_provisional(tmp_path):
    f2 = _orden('2010-12', 'FRE9002'); cu_nov = _orden('2010-11', 'FRE9002')['costo_unitario']
    libro = _editar(tmp_path, [('OBJETO', lambda d: d['OBJ_NUM'] == f2['codigo'], 'OBJ_EST', 'A')])
    inv = _r(libro, '2010-12')['inventarios']
    assert [x['orden'] for x in inv['en_proceso']] == [f2['codigo']] and abs(inv['total_proceso'] - f2['costo_total']) < 0.05
    vendidas = f2['cantidad']                                                       # en el caso se vende lo producido
    esperado = _pub('2010-12')['inventarios']['costo_ventas'] - f2['costo_total'] + cu_nov * vendidas
    assert abs(inv['costo_ventas'] - esperado) < 1.0                               # costo provisional = último costo unitario
    assert inv['ventas_pendientes_d14'] == [dict(producto='FRE9002', cantidad=vendidas)]


def test_d14_ajusta_el_costo_de_ventas_cuando_la_orden_se_liquida(tmp_path):
    """La orden de noviembre termina en diciembre: en noviembre su venta sale a costo provisional (octubre); en diciembre
    entra con su costo real y la diferencia se reconoce como ajuste, sin reescribir la venta de noviembre."""
    nov = _orden('2010-11', 'FRE9002'); cu_oct = _orden('2010-10', 'FRE9002')['costo_unitario']
    libro = _editar(tmp_path, [('OBJETO', lambda d: d['OBJ_NUM'] == nov['codigo'], 'OBJ_FEC_TER', 20101215)])
    inv_nov = _r(libro, '2010-11')['inventarios']; inv_dic = _r(libro, '2010-12')['inventarios']
    assert inv_nov['ventas_pendientes_d14'][0]['producto'] == 'FRE9002'
    aj = inv_dic['ajustes_d14'][0]
    assert aj['venta_de'] == '2010-11' and abs(aj['cu_provisional'] - cu_oct) < 1e-3
    assert abs(aj['ajuste'] - (nov['costo_unitario'] - cu_oct) * nov['cantidad']) < 2.0
