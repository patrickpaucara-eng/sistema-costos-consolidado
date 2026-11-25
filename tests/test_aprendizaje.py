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
