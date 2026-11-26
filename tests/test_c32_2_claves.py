import pytest
from reyna_local.motor_espejo import Motor, Error


def test_crear_rechaza_primera_columna_duplicada():
    m=Motor.__new__(Motor);m.T={'X':{'h':['COD','VAL'],'r':[['A',1]]}};m.creados=[];m.tr={}
    m.val=lambda tipo, valor:valor
    with pytest.raises(Error,match='ya existe X'):
        m.m_CREAR('M','X',None,None,None,[[None,None,'COD',None,None,'VAL','A']])


def test_clave_compuesta_no_confunde_primera_columna():
    m=Motor.__new__(Motor);m.T={'X':{'h':['COD','EMP'],'r':[['A','E1']]}};m.creados=[];m.tr={}
    m.val=lambda tipo, valor:valor
    m.m_CREAR('M','X',None,None,None,[[None,None,'COD','K',None,'VAL','A'],[None,None,'EMP','K',None,'VAL','E2']])
    assert m.T['X']['r'][-1]==['A','E2']
