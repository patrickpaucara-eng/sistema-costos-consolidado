"""Caso manual de la OT-C18 y controlabilidad por fracción."""
from reyna_local.variable import calcular, regresion


def test_caso_manual_y_controlabilidad():
    resources = [{'REC_COD':'MAT','REC_COMPORT':'V','REC_CTRL':'S'}, {'REC_COD':'MOD','REC_COMPORT':'F','REC_CTRL':'N'}, {'REC_COD':'LUZ','REC_COMPORT':'M','REC_PCT_VAR':40,'REC_CTRL':'S'}]
    objects = [{'codigo':'A','producto':'A','cantidad':100,'ingreso':8000,'costo_total':4600}, {'codigo':'B','producto':'B','cantidad':50,'ingreso':3000,'costo_total':2400}]
    montos = {'A':{'MD':2000,'PD':2000,'CIF':600}, 'B':{'MD':1000,'PD':1000,'CIF':400}}
    traces = [{'objeto':o,'elemento':e,'origen':r,'monto':m,'raiz':True} for o,e,r,m in [('A','MD','MAT',2000),('B','MD','MAT',1000),('A','PD','MOD',2000),('B','PD','MOD',1000),('A','CIF','LUZ',600),('B','CIF','LUZ',400)]]
    props = [{'codigo':'p1','producto':'A','elemento':'MD','impacto_anual':100}, {'codigo':'p2','producto':'A','elemento':'PD','impacto_anual':100}]
    result, kept = calcular(objects,montos,traces,resources,props)
    by = {p['producto']:p for p in result['productos']}
    assert by['A']['costo_variable']==2240 and by['B']['costo_variable']==1160
    assert by['A']['margen_contribucion']==5760 and by['B']['margen_contribucion']==1840
    assert sum(p['margen_contribucion'] for p in by.values()) == 7600
    assert result['fijos_periodo']==3600 and result['punto_equilibrio_ventas']==5210.53
    assert sum(p['margen_contribucion'] for p in by.values()) - result['fijos_periodo'] == 4000
    assert by['A']['costo_variable_unitario']==22.4 and by['B']['costo_variable_unitario']==23.2
    assert [p['codigo'] for p in kept]==['p1'] and result['no_controlables'][0]['codigo']=='p2'
    partial_resources = resources + [{'REC_COD':'OTRA','REC_COMPORT':'V','REC_CTRL':'N'}]
    partial_traces = traces + [{'objeto':'A','elemento':'MD','origen':'OTRA','monto':2000,'raiz':True}]
    _, adjusted = calcular(objects,montos,partial_traces,partial_resources,props[:1])
    assert adjusted[0]['impacto_anual']==50 and '50.00 %' in adjusted[0]['nota_controlabilidad']


def test_regresion_usa_historia_suficiente_y_no_inventa_variacion():
    r = regresion([(x, 100+2*x) for x in range(1,7)])
    assert r['n']==6 and r['r2']==1 and abs(r['b']-2)<1e-10
    assert abs(r['fraccion_variable']-7/107)<1e-10
    assert regresion([(1,2)]*6)['fraccion_variable']==0
    assert regresion([(1,2)]*5)['n']==5


def test_frenosa_mismos_costos_en_tres_sintesis():
    import json
    from pathlib import Path
    from reyna_local.resultados import construir
    root = Path(__file__).resolve().parents[1]
    for synthesis in ('REAL','CONTABLE','ESTIMADO'):
        expected = json.loads((root / f'datos/resultados/frenosa_2010-07_{synthesis}.json').read_text())
        actual = construir(root / 'casos/libros/frenosa.xlsx', periodo='2010-07', sintesis=synthesis)
        assert actual['kpi']['costo_total'] == expected['kpi']['costo_total']
        assert [(x['codigo'],x['costo_total']) for x in actual['objetos']] == [(x['codigo'],x['costo_total']) for x in expected['objetos']]
        assert len(actual['costeo_variable']['productos']) == len(actual['objetos'])
        if synthesis == 'REAL':
            pairs = []
            for month in range(1,8):
                published = json.loads((root / f'datos/resultados/frenosa_2010-{month:02d}_REAL.json').read_text())
                rows = [t for t in published['trazas'] if t['raiz'] and t['origen'] == 'MAT_SW50' and t['elemento'] == 'MD']
                pairs.append((sum(t['cantidad_destino'] for t in rows), sum(t['monto'] for t in rows)))
            expected_slope = regresion(pairs)['b']
            observed = next(r for r in actual['costeo_variable']['regresiones'] if r['recurso'] == 'MAT_SW50')
            assert abs(observed['b'] - expected_slope) < .0001  # no sumar compras y consumos dos veces


def test_perdida_y_ocio_fuera_del_inventario_se_mantienen_fijos():
    objs = [{'codigo':'A','producto':'A','cantidad':1,'ingreso':100,'costo_total':50}]
    traces = [{'objeto':'A','elemento':'MD','origen':'MAT','monto':50,'raiz':True}]
    result, _ = calcular(objs, {'A':{'MD':50}}, traces, [{'REC_COD':'MAT','REC_COMPORT':'V'}], [], gastos_fijos={'A':10})
    assert result['fijos_periodo'] == 10
    assert result['gastos_fijos_fuera_costo'] == 10
    assert result['punto_equilibrio_ventas'] == 20


def test_no_infiere_punto_de_equilibrio_si_falta_traza():
    obj = [{'codigo':'A','producto':'A','cantidad':1,'ingreso':100,'costo_total':50}]
    r, _ = calcular(obj, {'A':{'MD':50}}, [], [{'REC_COD':'MAT','REC_COMPORT':'V'}], [])
    assert r['sin_trazas'] == [{'orden':'A','elemento':'MD'}]
    assert r['punto_equilibrio_ventas'] is None


def test_no_atribuye_control_a_recurso_inexistente():
    import pytest
    objs = [{'codigo':'A','producto':'A','cantidad':1,'ingreso':100,'costo_total':50}]
    trace = [{'objeto':'A','elemento':'MD','origen':'SIN_MAESTRO','monto':50,'raiz':True}]
    with pytest.raises(ValueError, match='recurso no definido'):
        calcular(objs, {'A':{'MD':50}}, trace, [], [])
