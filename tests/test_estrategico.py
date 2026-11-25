from reyna_local.estrategico import calcular


def test_caso_manual_calidad_y_gobierno():
    result = {'kpi':{'ventas':10000}, 'trazas':[{'raiz':True,'origen':'P','elemento':'CIF','monto':300,'criterio':'C1'}, {'raiz':True,'origen':'E','elemento':'CIF','monto':200,'criterio':'C2'}, {'raiz':False,'criterio':'C3'}],
              'rechazos':[{'importe':450}], 'perdidas':[{'importe':50}], 'inventarios':{'kardex_pt':[{'movimiento':'DEVOLUCIÓN DE CLIENTE','importe':250}]}}
    resources = [{'REC_COD':'P','REC_COQ':'PREVENCION'}, {'REC_COD':'E','REC_COQ':'EVALUACION'}]
    criteria = [{'CRI_COD':'C1','CRI_RESP':'R','CRI_EVID':'E'}, {'CRI_COD':'C2','CRI_RESP':'R','CRI_EVID':'E'}, {'CRI_COD':'C3','CRI_RESP':'R'}]
    out = calcular(result, resources, criteria)
    assert out['coq'] == {'prevencion':300,'evaluacion':200,'falla_interna':500,'falla_externa':250,'total':1250,'pct_ventas':12.5}
    assert out['gobierno_dato']['porcentaje'] == 66.67
    assert out['gobierno_dato']['faltantes'][0]['criterio'] == 'C3'


def test_sin_trazas_no_inventa_calidad_ni_gobierno():
    result = {'kpi':{'ventas':100}, 'trazas':[], 'rechazos':[], 'perdidas':[]}
    out = calcular(result, [{'REC_COD':'P','REC_COQ':'PREVENCION'}], [])
    assert out['coq']['total'] is None and out['gobierno_dato']['porcentaje'] is None


def test_frenosa_sin_columnas_mantiene_costos_publicados():
    import json
    from pathlib import Path
    from reyna_local.resultados import construir
    root = Path(__file__).resolve().parents[1]
    for synthesis in ('REAL','CONTABLE','ESTIMADO'):
        expected = json.loads((root / f'datos/resultados/frenosa_2010-07_{synthesis}.json').read_text())
        actual = construir(root / 'casos/libros/frenosa.xlsx', periodo='2010-07', sintesis=synthesis)
        assert actual['kpi']['costo_total'] == expected['kpi']['costo_total']
        assert [o['costo_total'] for o in actual['objetos']] == [o['costo_total'] for o in expected['objetos']]
        assert 'estrategico' in actual
