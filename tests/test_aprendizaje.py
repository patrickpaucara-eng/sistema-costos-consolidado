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
