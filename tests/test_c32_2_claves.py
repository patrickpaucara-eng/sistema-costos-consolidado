import pytest
from reyna_local.motor_espejo import Motor, Error


def test_crear_rechaza_clave_mca_repetida():
    m=Motor.__new__(Motor);m.T={'X':{'h':['COD','VAL'],'r':[['A',1]]}};m.creados=[];m.tr={}
    m.val=lambda tipo, valor:valor
    with pytest.raises(Error,match='ya existe X'):
        m.m_CREAR('M','X',None,None,None,[[None,None,'COD','K',None,'VAL','A']])


def test_tabla_sin_clave_declarada_no_usa_heuristica_de_primera_columna():
    m=Motor.__new__(Motor);m.T={'X':{'h':['COD','VAL'],'r':[['A',1]]}};m.creados=[];m.tr={}
    m.val=lambda tipo, valor:valor
    m.m_CREAR('M','X',None,None,None,[[None,None,'COD','V',None,'VAL','A']])
    assert m.T['X']['r']==[['A',1],['A',None]]


def test_clave_compuesta_no_confunde_primera_columna():
    m=Motor.__new__(Motor);m.T={'X':{'h':['COD','EMP'],'r':[['A','E1']]}};m.creados=[];m.tr={}
    m.val=lambda tipo, valor:valor
    m.m_CREAR('M','X',None,None,None,[[None,None,'COD','K',None,'VAL','A'],[None,None,'EMP','K',None,'VAL','E2']])
    assert m.T['X']['r'][-1]==['A','E2']


def test_lineas_del_mismo_evento_se_distinguen_por_numero_y_repetir_linea_revierte():
    m=Motor.__new__(Motor)
    m.T={'LINEA':{'h':['LIN_EVE','LIN_NUM','LIN_REC'],'r':[[1,1,'M1']]}}
    m.creados=[];m.tr={};m.val=lambda tipo, valor:valor
    m.m_CREAR('M','LINEA',None,None,None,[
        [None,None,'LIN_EVE','V',None,'VAL',1],
        [None,None,'LIN_NUM','V',None,'VAL',2],
        [None,None,'LIN_REC','V',None,'VAL','M2'],
    ])
    assert m.T['LINEA']['r']==[[1,1,'M1'],[1,2,'M2']]
    with pytest.raises(Error,match=r'ya existe LINEA \(1, 2\)'):
        m.m_CREAR('M','LINEA',None,None,None,[
            [None,None,'LIN_EVE','V',None,'VAL',1],
            [None,None,'LIN_NUM','V',None,'VAL',2],
            [None,None,'LIN_REC','V',None,'VAL','M3'],
        ])
    assert m.T['LINEA']['r']==[[1,1,'M1'],[1,2,'M2']]


def test_t13_directo_rechaza_objeto_existente_sin_alterar_libro():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    m=Motor(str(root/'casos/libros/frenosa.xlsx'))
    existente=m.T['OBJETO']['r'][0][m.col('OBJETO','OBJ_NUM')]
    estimacion=['C32-DIRECTA','FRE','2010-12','MERCADO','SW50',100,1234.5,'PENDIENTE',None,
                None,'PRUEBA_C32',1000,0.3]
    m.T['ESTIMACION']['r'].append(estimacion)
    objetos_antes=[list(r) for r in m.T['OBJETO']['r']]
    tarifa_antes=[list(r) for r in m.T['TARIFA']['r']]
    resultado=m.ejecutar('T13',{
        'FECHA':20101228,'PER':'2010-12','EMP':'FRE','EST':'C32-DIRECTA','OBJ':existente,
        'MONTO':0,'REF':'','ALG':'','VER':'','HUELLA':'',
    },'JCOSTOS')
    assert resultado.startswith(f'ERROR: ya existe OBJETO (\'{existente}\',)')
    assert m.T['OBJETO']['r']==objetos_antes
    assert m.T['TARIFA']['r']==tarifa_antes
    assert m.T['ESTIMACION']['r'][-1][m.col('ESTIMACION','EST_ESTADO')]=='PENDIENTE'


def test_ventas_del_mismo_evento_se_distinguen_por_numero_de_linea():
    m=Motor.__new__(Motor)
    m.T={'VENTA':{'h':['VTA_EVE','VTA_LIN','VTA_REC'],'r':[[7,1,'P1']]}}
    m.creados=[];m.tr={};m.val=lambda tipo, valor:valor
    m.m_CREAR('M','VENTA',None,None,None,[
        [None,None,'VTA_EVE','V',None,'VAL',7],
        [None,None,'VTA_LIN','V',None,'VAL',2],
        [None,None,'VTA_REC','V',None,'VAL','P2'],
    ])
    assert m.T['VENTA']['r']==[[7,1,'P1'],[7,2,'P2']]
    with pytest.raises(Error,match=r'ya existe VENTA \(7, 2\)'):
        m.m_CREAR('M','VENTA',None,None,None,[
            [None,None,'VTA_EVE','V',None,'VAL',7],
            [None,None,'VTA_LIN','V',None,'VAL',2],
            [None,None,'VTA_REC','V',None,'VAL','P3'],
        ])
    assert m.T['VENTA']['r']==[[7,1,'P1'],[7,2,'P2']]


def test_ajuste_vnr_usa_la_clave_primaria_declarada_en_dbd():
    m=Motor.__new__(Motor)
    m.T={'AJUSTE_VNR':{'h':['AVN_REC','AVN_ALM','AVN_PER','AVN_EMP','AVN_REB'],
                       'r':[['CAJA_SINT','ALM1','2026-04','B',10]]}}
    m.creados=[];m.tr={};m.val=lambda tipo, valor:valor
    crear=lambda almacen: [[None,None,'AVN_REC','V',None,'VAL','CAJA_SINT'],
                           [None,None,'AVN_ALM','V',None,'VAL',almacen],
                           [None,None,'AVN_PER','V',None,'VAL','2026-04'],
                           [None,None,'AVN_EMP','V',None,'VAL','B'],
                           [None,None,'AVN_REB','V',None,'VAL',5]]
    with pytest.raises(Error,match=r'ya existe AJUSTE_VNR') as exc:
        m.m_CREAR('M','AJUSTE_VNR',None,None,None,crear('ALM2'))
    assert 'no concilia' in str(exc.value)
    assert len(m.T['AJUSTE_VNR']['r'])==1
