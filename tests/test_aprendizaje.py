from reyna_local.aprendizaje import calibrar_mediana, probabilidad, umbral, vigente


def test_casos_mediana_guardas_y_vigencia():
    values = [10,10.2,9.9,10.1,15,10]
    auto = calibrar_mediana(values,12,'2010-06','consumo','A')
    pending = calibrar_mediana(values,20,'2010-06','consumo','A')
    assert auto['valor_aprendido'] == 10.05
    assert [x['valor'] for x in auto['atipicos']] == [15]
    assert abs(auto['cambio_pct'] - (-.1625)) < 1e-10
    assert auto['mae_aprendido'] < auto['mae_libro'] and auto['estado'] == 'APLICADO'
    assert pending['estado'] == 'PENDIENTE' and abs(pending['cambio_pct'] - (-.4975)) < 1e-10
    assert not vigente(auto, '2010-06') and vigente(auto, '2010-07')
    assert not vigente({**auto, 'estado':'RECHAZADO'}, '2010-07')


def test_probabilidad_y_umbral():
    p = probabilidad([.9,.8,.1])
    assert p == .6 and p*1000 == 600
    assert abs(umbral([-.04,.04])-.08) < 1e-12
    assert umbral([-.01,.01]) == .05


def test_rechazo_persiste_y_no_reaparece(tmp_path):
    from reyna_local.aprendizaje import registrar, decidir
    c = calibrar_mediana([10,10.2,9.9,10.1,15,10],20,'2010-06','consumo','A')
    ruta = tmp_path / 'aprendizaje.json'
    registrar(ruta,[c],hoy='2010-06-30')
    decision = decidir(ruta,c['id'],'RECHAZAR',hoy='2010-07-01',actor='usuario local')
    assert decision['estado'] == 'RECHAZADO'
    same = calibrar_mediana([10,10.2,9.9,10.1,15,10],20,'2010-07','consumo','A')
    assert same['id'] == c['id']
    again = registrar(ruta,[same],hoy='2010-07-02')
    assert len(again)==1 and again[0]['estado']=='RECHAZADO'
    assert not vigente(again[0],'2010-07')


def test_observaciones_mensuales_del_libro_temporal(tmp_path):
    from openpyxl import Workbook
    from reyna_local.aprendizaje import calibrar_componentes
    book = Workbook(); book.remove(book.active)
    for name, header in [('PARAMETRO',['PAR_COD','PAR_VAL']),('OBJETO',['OBJ_NUM','OBJ_PRO','OBJ_CAN','OBJ_EMP']),
                         ('COMPONENTE',['CMP_PRO','CMP_REC','CMP_CAN_EST','CMP_MERMA','CMP_EMP']),
                         ('DIFERENCIA',['DIF_OBJ','DIF_REC','DIF_PER','DIF_QREAL','DIF_QMER','DIF_EMP'])]:
        book.create_sheet(name).append(header)
    book['COMPONENTE'].append(['P','M',12,5,'E'])
    for i, value in enumerate([10,10.2,9.9,10.1,15,10],1):
        oid=f'O{i}'; per=f'2010-{i:02d}'
        book['OBJETO'].append([oid,'P',10,'E'])
        book['DIFERENCIA'].append([oid,'M',per,value*10,value*.5,'E'])
    path=tmp_path/'libro.xlsx';book.save(path);book.close()
    values = calibrar_componentes(path,'E')
    consumption = next(x for x in values if x['calibrador']=='consumo')
    loss = next(x for x in values if x['calibrador']=='merma')
    assert consumption['valor_aprendido'] == 10.05 and consumption['estado'] == 'APLICADO'
    assert abs(loss['valor_aprendido'] - 5) < 1e-9
    assert consumption['vigente_desde'] == '2010-07'
    from reyna_local.aprendizaje import calibrar
    published=[]
    for i, value in enumerate([10,10.2,9.9,10.1,15,10],1):
        entry={'empresa':{'codigo':'E'},'sintesis':'REAL','periodo_actual':f'2010-{i:02d}',
               'objetos':[{'producto':'P','cantidad':10,'costo_total':value*10}], 'actividades':[], 'modelo':{'reglas':[]}}
        if i<=3:entry['seguimiento']=[{'propuesta':f'P{i}','elemento':'MD','cumplimiento':[.9,.8,.1][i-1]}]
        if i==6:entry['proyeccion_info']={'modelo_margen':'SES','mase_margen':.9}
        published.append(entry)
    all_candidates=calibrar(path,'E',published)
    assert next(x for x in all_candidates if x['calibrador']=='umbral')['estado']=='APLICADO'
    assert next(x for x in all_candidates if x['calibrador']=='probabilidad')['valor_aprendido']==.6
    assert next(x for x in all_candidates if x['calibrador']=='modelo_pronostico')['estado']=='INFORMATIVO'


def test_estandar_y_cotizador_respetan_vigencia_y_cantidad_explicita(tmp_path):
    from reyna_local.aprendizaje import registrar, estandar_vigente, factor_estandar
    from reyna_local.cotizador import cotizar
    c=calibrar_mediana([10,10.2,9.9,10.1,15,10],12,'2010-06','consumo',{'empresa':'E','producto':'P','recurso':'M'})
    registrar(tmp_path/'aprendizaje'/'E.json',[c],hoy='2010-06-30')
    assert estandar_vigente('E','P','M','2010-06',tmp_path) is None
    assert estandar_vigente('E','P','M','2010-07',tmp_path)==(10.05,None)
    assert abs(factor_estandar('E','P','M','2010-07',12,5,tmp_path)-10.05/12)<1e-12
    assert factor_estandar('E','P','M','2010-06',12,5,tmp_path) is None
    r={'empresa':{'codigo':'E'},'periodo_actual':'2010-06','sintesis':'REAL','actividades':[], 'modelo':{'reglas':[]},
       'kardex':[{'material':'M','costo_unitario':2,'fecha':'2010-06-30'}]}
    quote=cotizar(r,[],{}, {'M':3},100,.2,producto='P',carpeta_aprendizaje=tmp_path)
    assert quote['costo_pedido']==6 and quote['lineas'][0]['estandar_aprendido']['consumo']==10.05


def test_costos_sin_cambios_con_capa_activa(tmp_path):
    from pathlib import Path
    from reyna_local.aprendizaje import contexto, registrar, _registro
    from reyna_local.resultados import construir
    root=Path(__file__).resolve().parents[1];libro=root/'casos/libros/frenosa.xlsx'
    layer=[_registro('umbral',{'empresa':'FRE','producto':'SW50'},.08,'2010-06',[.01,.02]),
           _registro('probabilidad',{'empresa':'FRE','tipo':'MD'},.6,'2010-06',[.9,.8,.1])]
    registrar(tmp_path/'aprendizaje'/'frenosa.json',layer,hoy='2010-06-30')
    for synthesis in ('REAL','CONTABLE'):
        before=construir(libro,periodo='2010-07',sintesis=synthesis)
        with contexto(tmp_path,'frenosa'):after=construir(libro,periodo='2010-07',sintesis=synthesis)
        assert after['objetos']==before['objetos'] and after['kpi']==before['kpi']
        assert after['estado_resultados']==before['estado_resultados']
        assert all(p.get('prioridad')==round(p['impacto_anual']*.6,2) for p in after['propuestas'] if p.get('elemento')=='MD')


def test_api_consulta_y_decision_rechazada_no_reaparece(tmp_path):
    import json, threading
    from urllib.request import Request,urlopen
    from reyna_local.__main__ import ReynaServer
    from reyna_local.aprendizaje import registrar
    c=calibrar_mediana([10,10.2,9.9,10.1,15,10],20,'2010-06','consumo',{'empresa':'E','producto':'P','recurso':'M'})
    path=tmp_path/'aprendizaje'/'empresa.json';registrar(path,[c],hoy='2010-06-30')
    server=ReynaServer(tmp_path,0);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        base=f'http://127.0.0.1:{server.server_port}'
        with urlopen(base+'/api/aprendizaje?empresa=empresa',timeout=30) as response: assert len(json.load(response)['calibraciones'])==1
        body=json.dumps({'id':c['id'],'decision':'RECHAZAR'}).encode()
        req=Request(base+'/api/aprendizaje/decidir',data=body,headers={'Content-Type':'application/json'})
        with urlopen(req,timeout=30) as response: assert json.load(response)['estado']=='RECHAZADO'
        assert registrar(path,[c],hoy='2010-07-01')[0]['estado']=='RECHAZADO'
    finally:server.shutdown();thread.join();server.server_close()


def test_mae_de_estandares_empieza_en_tercer_mes():
    c=calibrar_mediana([1,100,100],100,'2010-03','consumo','A')
    assert c['mae_libro']==0 and c['mae_aprendido']==49.5 and c['estado']=='PENDIENTE'


def test_una_propuesta_medida_en_varios_meses_es_un_solo_intento(tmp_path):
    from openpyxl import Workbook
    from reyna_local.aprendizaje import calibrar
    book=Workbook();book.remove(book.active)
    for n,header in [('PARAMETRO',['PAR_COD','PAR_VAL']),('OBJETO',['OBJ_NUM','OBJ_PRO','OBJ_CAN','OBJ_EMP']),('COMPONENTE',['CMP_PRO','CMP_REC','CMP_CAN_EST','CMP_MERMA','CMP_EMP']),('DIFERENCIA',['DIF_OBJ','DIF_REC','DIF_PER','DIF_QREAL','DIF_QMER','DIF_EMP']),('MEDIDA',['MED_PER','MED_EMP','MED_CRIT','MED_NIVEL','MED_DEST','MED_CAN'])]: book.create_sheet(n).append(header)
    path=tmp_path/'book.xlsx';book.save(path);book.close()
    rows=[]
    for month,outcome in [(1,.2),(2,.9)]:
        rows.append({'empresa':{'codigo':'E'},'sintesis':'REAL','periodo_actual':f'2010-{month:02d}','objetos':[],
                     'seguimiento':[{'propuesta':'P','decidida_en':'2009-12','version':1,'elemento':'MD','cumplimiento':outcome}]})
    candidates=calibrar(path,'E',rows)
    p=next(x for x in candidates if x['calibrador']=='probabilidad')
    assert abs(p['valor_aprendido']-2/3)<1e-12


def test_aprobacion_tardia_no_cambia_periodos_anteriores(tmp_path):
    from reyna_local.aprendizaje import registrar, decidir
    c=calibrar_mediana([10,10.2,9.9,10.1,15,10],20,'2010-06','consumo','A')
    path=tmp_path/'capa.json';registrar(path,[c],hoy='2010-06-30')
    result=decidir(path,c['id'],'APROBAR',hoy='2010-08-15')
    assert result['vigente_desde']=='2010-09'
    assert not vigente(result,'2010-08') and vigente(result,'2010-09')


def test_calibracion_no_cuenta_meses_duplicados(tmp_path):
    import pytest
    from reyna_local.aprendizaje import calibrar
    r={'empresa':{'codigo':'E'},'sintesis':'REAL','periodo_actual':'2010-01'}
    with pytest.raises(ValueError,match='duplicados'):
        calibrar(tmp_path/'no-se-lee.xlsx','E',[r,r])
