from decimal import Decimal
import pytest
from reyna_local.cotizador import cotizar_intervalos_parejos


def test_orden_seis_meses_caso_manual():
    r=cotizar_intervalos_parejos({'MAT':1000,'MOD':600}, [{'MAT':10,'MOD':20},{'MAT':11,'MOD':21}],6,3)
    assert r['intervalos']==[Decimal('11000.00'),Decimal('11800.00')]
    assert r['total']==Decimal('22800.00')


def test_rechaza_tasas_incompletas():
    with pytest.raises(ValueError): cotizar_intervalos_parejos({'MAT':1000},[{}],3,3)
