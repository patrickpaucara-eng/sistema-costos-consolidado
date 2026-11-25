from decimal import Decimal
import pytest
from reyna_local.intervalos_proyectados import sugerir_intervalo, importe_intervalos, variaciones


def test_tres_casos_independientes_del_dueno():
    filas=[[{'cantidad':500,'tasa':10},{'cantidad':300,'tasa':20}],
           [{'cantidad':500,'tasa':11},{'cantidad':300,'tasa':21}]]
    assert importe_intervalos(filas)==([Decimal('11000.00'),Decimal('11800.00')],Decimal('22800.00'))
    assert sugerir_intervalo([10,10.1,10.15,10.5,10.6,10.62],Decimal('.02'))==2
    assert variaciones(10,60,12,65)=={'tasa':Decimal(60),'cantidad':Decimal(120),'total':Decimal(180)}


def test_rechaza_datos_invalidos():
    with pytest.raises(ValueError): sugerir_intervalo([10,0],.02)
    with pytest.raises(ValueError): importe_intervalos([[{'cantidad':-1,'tasa':2}]])
    with pytest.raises(ValueError): variaciones(1,1,float('nan'),1)
