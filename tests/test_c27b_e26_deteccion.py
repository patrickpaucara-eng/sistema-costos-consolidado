from reyna_local.store import detectar_transacciones_e26


def test_solo_detecta_transacciones_con_tres_definiciones():
    tablas={'TRX':{'r':[['T13'],['T18.3'],['T999']]},
            'TRX_CAMPO':{'r':[['T13'],['T18.3'],['T999']]},
            'TOP':{'r':[['T13'],['T999']]}}
    assert detectar_transacciones_e26(tablas)==['T13']
    assert detectar_transacciones_e26({})==[]
