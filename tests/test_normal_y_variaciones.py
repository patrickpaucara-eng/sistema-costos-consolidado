"""Punto 4: costeo normal (tasa predeterminada) y variaciones de material. Esperados desde los costos publicados."""
import json, shutil
from pathlib import Path

from openpyxl import load_workbook

from reyna_local import resultados

RAIZ = Path(__file__).resolve().parents[1]
LIBRO = RAIZ / 'casos/libros/frenosa.xlsx'
PUB = json.loads((RAIZ / 'datos/resultados/frenosa_2010-12_REAL.json').read_text(encoding='utf-8'))


def _libro(tmp_path, filas):
    p = tmp_path / 'n.xlsx'; shutil.copy(LIBRO, p); wb = load_workbook(p)
    for h, d in filas:
        cab = [c.value for c in wb[h][1]]; wb[h].append([d.get(c) for c in cab])
    wb.save(p); c = resultados.calcular_periodos(str(p), 'FRE')
    return resultados.construir(str(p), periodo='2010-12', sintesis='REAL', _cache=c)


def test_costeo_normal_con_tasa_presupuestada(tmp_path):
    r = _libro(tmp_path, [('TARIFA_CENTRO', dict(TCE_CEN='PLANTA_FRE', TCE_TIPO='PRED', TCE_PER='2010-01', TCE_EMP='FRE', TCE_VAL=1.25))])
    cn = r['costeo_normal']; assert cn['tasa'] == 1.25 and 'presupuestada' in cn['fuente_tasa']
    for f in cn['ordenes']:
        o = next(x for x in PUB['objetos'] if x['codigo'] == f['orden'])
        assert f['base'] == o['cantidad'] and abs(f['cif_aplicado'] - 1.25 * o['cantidad']) < 0.01 and abs(f['cif_real'] - o['cif']) < 0.01
    assert abs(cn['total_variacion'] - sum(1.25 * o['cantidad'] - o['cif'] for o in PUB['objetos'])) < 0.05


def test_variacion_de_precio_del_material_contra_estandar(tmp_path):
    r = _libro(tmp_path, [('TARIFA', dict(TAR_REC='MAT_SW50', TAR_TIPO='STD', TAR_PER='2010-12', TAR_VAL=3.5, TAR_EMP='FRE'))])
    v = next(x for x in r['variaciones'] if x['material'] == 'MAT_SW50')
    o = next(x for x in PUB['objetos'] if x['producto'] == 'SW50')
    assert v['fuente_precio'].startswith('TARIFA STD') and v['q_real'] == o['cantidad'] and v['var_cantidad'] == 0
    assert abs(v['var_precio'] - (o['md'] - 3.5 * o['cantidad'])) < 0.05


def test_compra_en_dolares_entra_al_kardex_en_moneda_funcional(tmp_path):
    from reyna_local.store import Store
    from reyna_local import flujo
    p = tmp_path / 'u.xlsx'; shutil.copy(LIBRO, p); wb = load_workbook(p); wb['TIPO_CAMBIO'].append(['USD', 20101201, 2.82]); wb.save(p)
    st = Store(tmp_path / 'd'); w = st.create({'name': 'usd', 'workbook_path': str(p)})
    status, resp = st.execute(w['id'], {'transaction': 'T14', 'user': 'ALMACEN1', 'request_id': 'u1',
        'header': {'FECHA': 20101229, 'PER': '2010-12', 'EMP': 'FRE', 'ALM': 'ALM_FRE', 'MON': 'USD', 'IMP': 'IGV', 'CPB': 'F001-999', 'RUC': '20100000001'},
        'lines': [{'REC': 'MAT_SW50', 'CANT': 1000, 'CU_DOC': 1.2}]})
    assert status == 200, resp
    q = flujo.preparar(st.path(w['id'])); c = resultados.calcular_periodos(q, 'FRE')
    k = [x for x in resultados.construir(q, periodo='2010-12', sintesis='REAL', _cache=c)['kardex'] if x['material'] == 'MAT_SW50'][-1]
    assert k['movimiento'] == 'ENTRADA' and abs(k['importe'] - 1000 * 1.2 * 2.82) < 0.01          # sin IGV, al tipo de cambio del día


def test_devolucion_de_cliente_reingresa_al_costo_de_salida(tmp_path):
    sw = next(x for x in PUB['objetos'] if x['producto'] == 'SW50'); cu = sw['costo_total'] / sw['cantidad']
    precio = sw['ingreso'] / sw['cantidad']
    r = _libro(tmp_path, [('VENTA', dict(VTA_EVE=9100, VTA_LIN=1, VTA_PER='2010-12', VTA_CLI='MERCADO', VTA_REC='SW50', VTA_CAN=-500, VTA_ING=-500 * precio, VTA_EMP='FRE'))])
    cont = json.loads((RAIZ / 'datos/resultados/frenosa_2010-12_CONTABLE.json').read_text(encoding='utf-8'))
    inv = r['inventarios']; prod_cu = next(x for x in cont['objetos'] if x['producto'] == 'SW50')['costo_unitario']
    assert abs(inv['costo_ventas'] - (cont['inventarios']['costo_ventas'] - 500 * prod_cu)) < 1.0
    assert abs(next(s for s in inv['saldos_pt'] if s['producto'] == 'SW50')['cantidad'] - 500) < 1e-6
    assert abs(r['kpi']['ventas'] - (PUB['kpi']['ventas'] - 500 * precio)) < 0.05
