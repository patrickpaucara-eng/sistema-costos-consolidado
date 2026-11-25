import pytest
from reyna_local.cotizador import cotizar


def test_caso_manual_tdabc_y_objetivo():
    activities = [('TORNO',6000,100,12),('SOLD',4000,100,30),('PINT',2500,100,40),('INSP',1000,10,3)]
    r = {'empresa':{'codigo':'X'},'periodo_actual':'2025-07','sintesis':'REAL',
         'actividades':[{'codigo':c,'costo':cost} for c,cost,cap,q in activities],
         'modelo':{'reglas':[{'etapa':'P4C','origen':c,'inductor':'I_'+c} for c,cost,cap,q in activities]},
         'kardex':[{'material':'M','fecha':'2025-07-01','costo_unitario':50}]}
    measures = [{'MED_PER':'2025-07','MED_EMP':'X','MED_CRIT':'I_'+c,'MED_NIVEL':'CAP','MED_DEST':c,'MED_CAN':cap} for c,cost,cap,q in activities]
    order = {c:q for c,cost,cap,q in activities}
    result = cotizar(r,measures,order,{'M':10},5000,.3)
    assert [x['importe'] for x in result['lineas']] == [720,1200,1000,300,500]
    assert result['costo_pedido']==3720 and result['costo_objetivo']==3500 and result['brecha']==220
    no_cap = [m for m in measures if m['MED_DEST']!='TORNO'] + [{'MED_PER':'2025-07','MED_EMP':'X','MED_CRIT':'I_TORNO','MED_NIVEL':'OBJ','MED_CAN':100}]
    assert 'sin capacidad práctica: tasa sobre uso' in cotizar(r,no_cap,order,{'M':10},5000,.3)['avisos'][0]
    with pytest.raises(ValueError, match='Actividad inexistente'): cotizar(r,measures,{'NO_EXISTE':1},{},5000,.3)


def test_api_solo_lee_ultimo_periodo_cerrado(tmp_path):
    import hashlib, json, shutil, threading
    from pathlib import Path
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError
    from openpyxl import load_workbook
    from reyna_local.__main__ import ReynaServer
    root = Path(__file__).resolve().parents[1]
    folder = tmp_path / 'data'; (folder/'libros').mkdir(parents=True); (folder/'resultados').mkdir()
    book = folder/'libros/frenosa_cot.xlsx'; shutil.copyfile(root/'casos/libros/frenosa.xlsx', book)
    wb = load_workbook(book)
    for row in wb['PERIODO'].iter_rows(min_row=2):
        if row[0].value == '2010-07': row[4].value = 'C'
    wb.save(book); wb.close()
    result = json.loads((root/'datos/resultados/frenosa_2010-07_REAL.json').read_text())
    (folder/'resultados/frenosa_cot_2010-07_REAL.json').write_text(json.dumps(result),encoding='utf-8')
    before = hashlib.sha256(book.read_bytes()).digest()
    server = ReynaServer(folder,0); thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        body = {'empresa':'frenosa_cot','actividades':{'FO-1':1},'materiales':{'MAT_SW50':1},'precio_mercado':100,'margen_objetivo':.3}
        req = Request(f'http://127.0.0.1:{server.server_port}/api/cotizar',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
        with urlopen(req,timeout=60) as response: quote=json.load(response)
        assert quote['periodo_base']=='2010-07' and quote['costo_objetivo']==70
        assert quote['costo_pedido'] > 0 and quote['avisos']
        assert hashlib.sha256(book.read_bytes()).digest() == before
        result['empresa']['codigo'] = 'OTRA'
        (folder/'resultados/frenosa_cot_2010-07_REAL.json').write_text(json.dumps(result),encoding='utf-8')
        with pytest.raises(HTTPError) as error: urlopen(req, timeout=60)
        assert error.value.code == 422
    finally:
        server.shutdown(); thread.join(); server.server_close()


def test_acepta_material_con_costo_cero():
    result = {'empresa':{'codigo':'X'},'periodo_actual':'2025-07','sintesis':'REAL','actividades':[],
              'modelo':{'reglas':[]},'kardex':[{'material':'M','costo_unitario':0,'fecha':'2025-07-01'}]}
    assert cotizar(result,[],{}, {'M':1},100,.2)['costo_pedido'] == 0
