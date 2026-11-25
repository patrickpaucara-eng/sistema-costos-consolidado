"""Caso MINI independiente del diseño de proyección y pruebas de invariantes."""
import hashlib
from pathlib import Path
from reyna_local.proyeccion import proyectar_hechos, proyectar_granular

ROOT = Path(__file__).resolve().parents[1]


def mini():
    rules=[('P1','M','CONSUMO'),('P2','MOD','HORAS'),('P4A','IND','A_ACT'),('P4C','ACT','UNIDADES')]
    h={'(sin MCD) REGLA_REPARTO':[{'ETAPA':e,'ORIGEN':o,'CRITERIO':c,'DESDE':19000101} for e,o,c in rules],
       '(sin MCD) MEDIDA':[], '(sin MCD) LINEA':[], 'EVENTO':[], 'RECURSO':[{'CODIGO':'M','TIPO_RECURSO':'MAT'},{'CODIGO':'MOD','TIPO_RECURSO':'PD'},{'CODIGO':'IND','TIPO_RECURSO':'IND'}],
       '(sin MCD) TIPO_RECURSO':[{'CODIGO':'MAT','ELEMENTO_COSTO':'MAT'},{'CODIGO':'PD','ELEMENTO_COSTO':'PD'},{'CODIGO':'IND','ELEMENTO_COSTO':'IND'}],
       'CENTRO':[], '(sin MCD) OBJETO':[{'NUMERO':x,'EMPRESA':'E','TIPO':'OT'} for x in ('A','B')], 'ACTIVIDAD':[{'CODIGO':'ACT','NIVEL':'O'}], 'PERIODO':[{'CODIGO':'2025-01','EMPRESA':'E','INICIO':20250101}]}
    def measure(crit,level,dest,qty):h['(sin MCD) MEDIDA'].append({'PERIODO':'2025-01','EMPRESA':'E','CRITERIO':crit,'NIVEL':level,'DESTINO':dest,'CANTIDAD':qty})
    for crit, pairs in [('HORAS',[('A',30),('B',20)]),('UNIDADES',[('A',60),('B',40)])]:
        for dest,qty in pairs:measure(crit,'OBJ',dest,qty)
    measure('A_ACT','ACT','ACT',1)
    for eid,obj,rec,qty,price in [(1,'A','M',60,None),(2,'B','M',40,None),(3,None,'MOD',1,1000),(4,None,'IND',1,500)]:
        h['EVENTO'].append({'NUMERO':eid,'PERIODO':'2025-01','EMPRESA':'E','OBJETO':obj,'CENTRO':None})
        h['(sin MCD) LINEA'].append({'EVENTO':eid,'NUMERO':1,'RECURSO':rec,'CANTIDAD':qty,'COSTO_UNITARIO_DOCUMENTO':price})
    previous={'VALUACION_PROMEDIO':[('SALIDA','1-1-ALM','MONTO',600),('SALIDA','2-1-ALM','MONTO',400)],'EXCESO':{}}
    objs=[{'OBJ_NUM':x,'OBJ_PRO':x,'OBJ_CAN':1,'OBJ_EMP':'E'} for x in ('A','B')]
    resources=[{'REC_COD':'M','REC_COMPORT':'V'},{'REC_COD':'MOD','REC_COMPORT':'F'},{'REC_COD':'IND','REC_COMPORT':'F'}]
    criteria=[{'CRI_COD':'HORAS','CRI_UNI':'h'},{'CRI_COD':'UNIDADES','CRI_UNI':'u'},{'CRI_COD':'A_ACT','CRI_UNI':'%'}]
    return h,previous,objs,resources,criteria


def test_mini_y_bloques():
    h,prev,objs,res,criteria=mini(); factors={'vol':{'A':1.5,'B':1},'pre':{},'pv':{}}
    result=proyectar_hechos(h,prev,'E','2025-01',objs,res,criteria,[],factors)
    costs={x['producto']:x['costo_total'] for x in result['productos']}
    assert costs=={'A':1938.46,'B':861.54}
    block=[{'BLQ_REC':'MOD','BLQ_DESDE':20250101,'BLQ_CAP':25,'BLQ_COSTO':500,'BLQ_UNI':'HORAS'}]
    result=proyectar_hechos(h,prev,'E','2025-01',objs,res,criteria,[],factors,bloques=block)
    assert result['bloques'][0]['monto']==1500
    by={x['producto']:x['elementos']['PD'] for x in result['productos']}
    assert by=={'A':1038.46,'B':461.54}


def test_identidad_frenosa_y_libro_inmutable():
    libro=ROOT/'casos/libros/frenosa.xlsx';before=hashlib.sha256(libro.read_bytes()).digest()
    import json
    base=json.loads((ROOT/'datos/resultados/frenosa_2010-12_REAL.json').read_text())
    factors={'vol':{o['producto']:1 for o in base['objetos']},'pre':{r['codigo']:1 for r in base['modelo']['recursos']},'pv':{o['producto']:1 for o in base['objetos']}}
    result=proyectar_granular(libro,'FRE',meses=1,factores=factors)
    actual={p['producto']:p['costo_total'] for p in result['meses'][0]['productos']}
    for o in base['objetos']:assert abs(actual[o['producto']]-o['costo_total']) <= .01
    assert hashlib.sha256(libro.read_bytes()).digest()==before
    sensitivity=result['sensibilidad']
    assert all(max(abs(sensitivity[i]['mas']),abs(sensitivity[i]['menos'])) >= max(abs(sensitivity[i+1]['mas']),abs(sensitivity[i+1]['menos'])) for i in range(len(sensitivity)-1))
    assert sensitivity[0]['mas']*sensitivity[0]['menos'] < 0


def test_volumen_doble_no_aumenta_recursos_fijos_de_frenosa():
    import json
    libro=ROOT/'casos/libros/frenosa.xlsx'
    base=json.loads((ROOT/'datos/resultados/frenosa_2010-12_REAL.json').read_text())
    factors={'vol':{o['producto']:2 for o in base['objetos']},'pre':{r['codigo']:1 for r in base['modelo']['recursos']},'pv':{o['producto']:1 for o in base['objetos']}}
    result=proyectar_granular(libro,'FRE',meses=1,factores=factors)
    before=sum(o['costo_total']-o['md'] for o in base['objetos'])
    after=sum(p['costo_total']-p['elementos'].get('MD',0) for p in result['meses'][0]['productos'])
    assert abs(before-after)<=.01


def test_api_proyeccion_es_solo_lectura(tmp_path):
    import json, threading
    from urllib.request import urlopen
    from reyna_local.__main__ import ReynaServer
    libro=ROOT/'casos/libros/frenosa.xlsx'; before=hashlib.sha256(libro.read_bytes()).digest()
    server=ReynaServer(tmp_path,0);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with urlopen(f'http://127.0.0.1:{server.server_port}/api/proyeccion?empresa=frenosa&meses=1',timeout=60) as response: result=json.load(response)
        assert result['base']=='2010-12' and result['meses'][0]['periodo']=='2011-01'
        assert hashlib.sha256(libro.read_bytes()).digest()==before
    finally:server.shutdown();thread.join();server.server_close()


def test_bloque_sin_inductor_no_inventa_costo_cero():
    import pytest
    h,prev,objs,res,criteria=mini()
    block=[{'BLQ_REC':'MOD','BLQ_DESDE':20250101,'BLQ_CAP':25,'BLQ_COSTO':500,'BLQ_UNI':'INEXISTENTE'}]
    with pytest.raises(ValueError,match='no tiene medidas'):
        proyectar_hechos(h,prev,'E','2025-01',objs,res,criteria,[],{},bloques=block)
