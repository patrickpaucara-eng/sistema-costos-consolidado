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


def _coproductos(tmp_path):
    """La orden SW50 de diciembre rinde 30,000 piezas SW50 y 4,357 kg de material recuperado (coproducto RECUP)."""
    p = tmp_path / 'c.xlsx'; shutil.copy(LIBRO, p); wb = load_workbook(p)
    def fila(h, **d):
        cab = [c.value for c in wb[h][1]]; wb[h].append([d.get(c) for c in cab])
    fila('RECURSO', REC_COD='SW50', REC_DES='Forro SW50', REC_TRE='PRODUCTO', REC_UNI='pieza', REC_ACTIVO='S', REC_EMP='FRE')
    fila('RECURSO', REC_COD='RECUP', REC_DES='Material recuperado', REC_TRE='PRODUCTO', REC_UNI='kg', REC_ACTIVO='S', REC_EMP='FRE')
    fila('EVENTO', EVE_NUM=9001, EVE_TRX='T18', EVE_FEC=20101231, EVE_EMP='FRE', EVE_PER='2010-12', EVE_OBJ='OT-FRENOSA-SW50-2010-12', EVE_MON='PEN', EVE_TC=1)
    fila('LINEA', LIN_EVE=9001, LIN_NUM=1, LIN_REC='SW50', LIN_CAN=30000)
    fila('LINEA', LIN_EVE=9001, LIN_NUM=2, LIN_REC='RECUP', LIN_CAN=4357)
    ws = wb['VENTA']; cab = [c.value for c in ws[1]]
    for f in ws.iter_rows(min_row=2):
        d = {cab[i]: c.value for i, c in enumerate(f)}
        if d['VTA_PER'] == '2010-12' and d['VTA_REC'] == 'SW50':
            precio = d['VTA_ING'] / d['VTA_CAN']; f[cab.index('VTA_CAN')].value = 30000; f[cab.index('VTA_ING')].value = round(30000 * precio, 2)
    fila('VENTA', VTA_EVE=9002, VTA_LIN=1, VTA_PER='2010-12', VTA_CLI='MERCADO', VTA_REC='RECUP', VTA_CAN=4357, VTA_ING=4357 * 2.0, VTA_EMP='FRE')
    wb.save(p); return str(p), precio


def test_coproductos_real_por_unidades_y_contable_por_vvr(tmp_path):
    libro, precio = _coproductos(tmp_path)
    c = resultados.calcular_periodos(libro, 'FRE')
    costo = _orden('2010-12', 'SW50')['costo_total']                              # costo conjunto (MD+MOD+CIF), publicado
    real = {x['producto']: x for x in resultados.construir(libro, periodo='2010-12', sintesis='REAL', _cache=c)['inventarios']['coproductos']}
    cont = {x['producto']: x for x in resultados.construir(libro, periodo='2010-12', sintesis='CONTABLE', _cache=c)['inventarios']['coproductos']}
    assert real['SW50']['base'] == 'FISICA' and abs(real['SW50']['costo_asignado'] - costo * 30000 / 34357) < 0.05
    vvr_sw, vvr_rec = 30000 * precio, 4357 * 2.0
    assert cont['SW50']['base'] == 'VVR' and abs(cont['RECUP']['costo_asignado'] - costo * vvr_rec / (vvr_sw + vvr_rec)) < 0.05
    assert abs(sum(x['costo_asignado'] for x in cont.values()) - costo) < 0.02     # el costo conjunto se conserva
