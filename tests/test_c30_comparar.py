import pytest
from decimal import Decimal
from reyna_local.comparar_laboratorio import comparar


def test_compara_por_orden_y_elemento():
    a={'empresa':{'codigo':'A'},'periodo_actual':'2025-01','sintesis':'REAL','objetos':[{'codigo':'OT1','md':10}]}
    b={**a,'objetos':[{'codigo':'OT1','md':12}]}
    assert comparar(a,b)[0]['diferencia']==Decimal('2')
    with pytest.raises(ValueError): comparar(a,{**b,'empresa':{'codigo':'B'}})
