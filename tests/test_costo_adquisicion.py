"""Punto 5: costo de adquisición completo — flete del documento, ajuste tardío T14.2 y centro de compras (D-11)."""
import json, shutil
from pathlib import Path

from openpyxl import load_workbook

from reyna_local import flujo, resultados

RAIZ = Path(__file__).resolve().parents[1]
LIBRO = RAIZ / 'casos/libros/frenosa.xlsx'


def _armar(tmp_path, nombre, filas):
    p = tmp_path / nombre; shutil.copy(LIBRO, p); wb = load_workbook(p)
    for h, d in filas:
        cab = [c.value for c in wb[h][1]]; wb[h].append([d.get(c) for c in cab])
    wb.save(p); return p


def _r(p, s='REAL'):
    q = flujo.preparar(p, s); c = resultados.calcular_periodos(q, 'FRE'); return resultados.construir(q, periodo='2010-12', sintesis=s, _cache=c)


def _md(r): return sum(o['md'] for o in r['objetos'])
def _saldo(r, m): return [k for k in r['kardex'] if k['material'] == m][-1]['saldo_importe']


BASE_FLETE = [('TIPO_RECURSO', dict(TRE_COD='FLETE_COMPRA', TRE_ELE='CAP', TRE_CAP=0, TRE_INV='N')),
              ('RECURSO', dict(REC_COD='FLETE', REC_DES='Flete de compra', REC_TRE='FLETE_COMPRA', REC_UNI='S/', REC_ACTIVO='S', REC_EMP='FRE')),
              ('EVENTO', dict(EVE_NUM=9200, EVE_TRX='T14', EVE_FEC=20101203, EVE_EMP='FRE', EVE_PER='2010-12', EVE_MON='PEN', EVE_TC=1, EVE_CPB='F/ 9-1', EVE_ALM='ALM_FRE')),
              ('LINEA', dict(LIN_EVE=9200, LIN_NUM=1, LIN_REC='MAT_SW50', LIN_CAN=1000, LIN_CU_DOC=3, LIN_CU=3, LIN_MTO=3000))]


def test_flete_del_documento_se_capitaliza_y_se_conserva(tmp_path):
    sin = _r(_armar(tmp_path, 'a.xlsx', BASE_FLETE))
    con = _r(_armar(tmp_path, 'b.xlsx', BASE_FLETE + [('LINEA', dict(LIN_EVE=9200, LIN_NUM=2, LIN_REC='FLETE', LIN_CAN=1, LIN_CU_DOC=300, LIN_CU=300, LIN_MTO=300))]))
    assert any(k['movimiento'] == 'AJUSTE DE VALOR' and abs(k['importe'] - 300) < 0.01 for k in con['kardex'])
    assert abs((_md(con) - _md(sin)) + (_saldo(con, 'MAT_SW50') - _saldo(sin, 'MAT_SW50')) - 300) < 0.05   # ni se pierde ni se crea


def test_t14_2_ajuste_tardio_parte_a_inventario_y_parte_a_gasto(tmp_path):
    wb = load_workbook(LIBRO, read_only=True); cab = [c.value for c in next(wb['KARDEX'].iter_rows(max_row=1))]
    lote = next(dict(zip(cab, f)) for f in wb['KARDEX'].iter_rows(min_row=2, values_only=True)
                if f[cab.index('KDX_PER')] == '2010-11' and f[cab.index('KDX_REC')] == 'MAT_SW50' and f[cab.index('KDX_TRX')] == 'T14' and f[cab.index('KDX_CPB')] != 'SALDO')
    p = _armar(tmp_path, 'c.xlsx', BASE_FLETE[:2] + [
        ('EVENTO', dict(EVE_NUM=9210, EVE_TRX='T14.2', EVE_FEC=20101230, EVE_EMP='FRE', EVE_PER='2010-12', EVE_MON='PEN', EVE_TC=1, EVE_CPB='F/ flete tardío')),
        ('LINEA', dict(LIN_EVE=9210, LIN_NUM=1, LIN_REC='FLETE', LIN_CAN=1, LIN_CU_DOC=200, LIN_MTO=200, LIN_ORI=lote['KDX_EVE']))])
    base = json.loads((RAIZ / 'datos/resultados/frenosa_2010-12_REAL.json').read_text(encoding='utf-8'))
    r = _r(p)
    queda = 5154 / lote['KDX_CAN']                      # existencia al 30-dic (publicada) / cantidad del lote de noviembre
    gasto = sum(x['importe'] for x in r['ajustes_compra'])
    assert abs(gasto - 200 * (1 - queda)) < 0.05
    assert abs(_saldo(r, 'MAT_SW50') - _saldo(base, 'MAT_SW50') - 200 * queda) < 0.05
    assert _md(r) == _md(base)                           # no reabre lo ya consumido
    assert any('T14.2' in x['concepto'] for x in r['estado_resultados'])


def test_centro_de_compras_en_inventario_real_y_gasto_contable(tmp_path):
    p = _armar(tmp_path, 'd.xlsx', BASE_FLETE[:2] + BASE_FLETE[2:] + [
        ('CENTRO', dict(CEN_COD='COMPRAS_FRE', CEN_EMP='FRE', CEN_FUN='COM', CEN_TIPO='COM', CEN_ACTIVO='S')),
        ('RECURSO', dict(REC_COD='SUELDO_COMP', REC_DES='Sueldos de compras', REC_TRE='INDIRECTO', REC_UNI='S/', REC_ACTIVO='S', REC_EMP='FRE')),
        ('REGLA_REPARTO', dict(RRE_ETAPA='P5', RRE_ORIGEN='COMPRAS_FRE', RRE_CRIT='KG_PRODUCIDOS', RRE_DESDE=19000101, RRE_FUENTE='Compras como gasto (CONTABLE)')),
        ('EVENTO', dict(EVE_NUM=9300, EVE_TRX='T17', EVE_FEC=20101231, EVE_EMP='FRE', EVE_PER='2010-12', EVE_CEN='COMPRAS_FRE', EVE_MON='PEN', EVE_TC=1)),
        ('LINEA', dict(LIN_EVE=9300, LIN_NUM=1, LIN_REC='SUELDO_COMP', LIN_CAN=1, LIN_CU_DOC=6000, LIN_MTO=6000))])
    ref = _armar(tmp_path, 'e.xlsx', BASE_FLETE)
    real, real0 = _r(p), _r(ref)
    assert abs((_md(real) - _md(real0)) + sum(_saldo(real, m) - _saldo(real0, m) for m in ('MAT_SW50', 'MAT_FRE9000', 'MAT_FRE9002')) - 6000) < 0.1
    assert abs(sum(o['admin'] for o in real['objetos']) - sum(o['admin'] for o in real0['objetos'])) < 0.01
    cont, cont0 = _r(p, 'CONTABLE'), _r(ref, 'CONTABLE')
    gad = lambda r: -next(x['importe'] for x in r['estado_resultados'] if 'administración' in x['concepto'])
    assert abs(gad(cont) - gad(cont0) - 6000) < 0.03 and _md(cont) == _md(cont0)          # redondeo por orden (ALG-09)
