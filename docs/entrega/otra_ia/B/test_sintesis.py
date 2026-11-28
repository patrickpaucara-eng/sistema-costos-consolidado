"""Casos a mano de sintesis.py. Una venta a crédito y una compra a crédito separan devengo de caja."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pytest
import sintesis as S

L = [
    dict(ticket="OT-1", recurso="Venta OT-1", monto=1000, fecha_devengo="2027-01-20", fecha_caja="2027-03-20", clase="INGRESO", estado="comprometido"),
    dict(ticket="CO-1", recurso="Material", monto=400, fecha_devengo="2027-01-10", fecha_caja="2027-02-10", clase="EGRESO", estado="ejecutado"),
    dict(ticket="FI-1", recurso="Préstamo", monto=500, fecha_devengo="2027-01-05", fecha_caja="2027-01-05", clase="FINANCIAMIENTO", estado="ejecutado"),
    dict(ticket="IN-1", recurso="Horno", monto=300, fecha_devengo="2027-02-15", fecha_caja="2027-02-15", clase="INVERSION", estado="programado"),
    dict(ticket="OT-1", recurso="Impuesto", monto=50, fecha_devengo="2027-01-31", fecha_caja="2027-03-15", clase="IMPUESTO", estado="programado"),
]


def test_operativo_por_devengo():
    # Enero: ingreso 1000 y egreso 400 (aunque se cobre en marzo y se pague en febrero)
    assert S.sintetizar(L, "Presupuesto operativo") == {("2027-01", "EGRESO"): -400.0, ("2027-01", "INGRESO"): 1000.0}


def test_efectivo_por_caja():
    # Ene +500 préstamo; Feb −400 material −300 horno; Mar +1000 cobro −50 impuesto
    assert S.sintetizar(L, "Presupuesto de efectivo") == {("2027-01",): 500.0, ("2027-02",): -700.0, ("2027-03",): 950.0}


def test_inversiones_y_financiero():
    assert S.sintetizar(L, "Presupuesto de inversiones") == {("2027-02", "Horno"): -300.0}
    assert S.sintetizar(L, "Presupuesto financiero") == {("2027-01", "FINANCIAMIENTO"): 500.0, ("2027-03", "IMPUESTO"): -50.0}


def test_presupuesto_nuevo_es_una_fila_del_catalogo():
    cat = dict(S.CATALOGO, **{"Ventas por ticket (caja)": ("caja", ("INGRESO",), ("ticket", "periodo"))})
    assert S.sintetizar(L, "Ventas por ticket (caja)", catalogo=cat) == {("OT-1", "2027-03"): 1000.0}


def test_control_de_ejecucion():
    f = {x["recurso"]: x for x in S.control_ejecucion(L, {"Material": 350, "Horno": 300})}
    assert f["Material"]["disponible"] == -50.0 and f["Material"]["exceso"]           # ejecutó 400 de 350
    assert f["Horno"]["disponible"] == 300.0 and not f["Horno"]["exceso"]           # solo programado: no consume


@pytest.mark.parametrize("cambio,texto", [({"clase": "VENTA"}, "clase"), ({"estado": "listo"}, "estado"),
                                          ({"monto": -5}, "monto"), ({"fecha_caja": ""}, "falta fecha_caja")])
def test_lineas_malas_se_rechazan(cambio, texto):
    with pytest.raises(S.LineaInvalida, match=texto):
        S.sintetizar([dict(L[0], **cambio)], "Presupuesto de efectivo")
