# -*- coding: utf-8 -*-
"""Panel Decidir (sección H, notas de clase del dueño 25-nov). Caso a mano sintético:
A: 100 u × 80 = 8,000; MAT 2,000 (V), MOD 2,000 (F, controlable, evitable), LUZ 1,000 (mixto 40 %, no controlable).
B:  50 u × 60 = 3,000; MAT 1,000, MOD 1,000, LUZ 500."""
import pytest
from reyna_local import decidir as D

REC = [dict(REC_COD="MAT", REC_COMPORT="V"), dict(REC_COD="MOD", REC_COMPORT="F", REC_EVIT="S"),
       dict(REC_COD="LUZ", REC_COMPORT="M", REC_PCT_VAR=40, REC_CTRL="N")]


def _r():
    t = lambda o, rec, m: dict(objeto=o, elemento="MD" if rec == "MAT" else "PD" if rec == "MOD" else "CIF", origen=rec, monto=m, raiz=True)
    return dict(objetos=[dict(codigo="OT-A", producto="A", cantidad=100, ingreso=8000, md=2000, mod=2000, cif=1000),
                         dict(codigo="OT-B", producto="B", cantidad=50, ingreso=3000, md=1000, mod=1000, cif=500)],
                trazas=[t("OT-A", "MAT", 2000), t("OT-A", "MOD", 2000), t("OT-A", "LUZ", 1000),
                        t("OT-B", "MAT", 1000), t("OT-B", "MOD", 1000), t("OT-B", "LUZ", 500)])


def test_er_gerencial_y_punto_de_equilibrio():
    p = D.panel(_r(), REC); a, b = p["er_gerencial"]["productos"]
    assert (a["cv"], a["margen_contribucion"], a["cf_controlable"], a["cf_no_controlable"], a["utilidad_operativa"]) == (2400, 5600, 2000, 600, 3000)
    assert (b["cv"], b["margen_contribucion"], b["cf_total"], b["utilidad_operativa"]) == (1200, 1800, 1300, 500)
    assert p["er_gerencial"]["total"]["utilidad_operativa"] == 3500
    pe = p["punto_equilibrio"]
    assert pe["preciso"][0]["unidades"] == 46.43 and pe["preciso"][0]["soles"] == 3714.29
    assert pe["preciso"][1]["unidades"] == 36.11 and pe["preciso"][1]["soles"] == 2166.67
    assert pe["ponderado_soles"] == 5797.30
    assert [x["relevante"] for x in p["relevancia"][:3]] == [True, True, True] and p["recursos_supuestos"] == []


def test_casos_de_decision():
    a, b = D.estructura(_r(), REC)[0]
    x = D.producir_o_tercerizar(b, 50, 30, costo_mantener=2, costo_transicion=100)
    assert (x["costo_producir"], x["costo_comprar"], x["ahorro_tercerizar"], x["decision"]) == (2200, 1700, 500, "TERCERIZAR")
    y = D.eliminar_linea(b)
    assert (y["impacto_utilidad"], y["decision"], y["cf_que_se_queda"]) == (-800, "MANTENER", 300)
    z = D.pedido_especial(a, 20, 40)
    assert (z["utilidad_incremental"], z["precio_minimo"], z["decision"]) == (320, 24, "ACEPTAR")
    w = D.pedido_especial(a, 20, 40, capacidad_ociosa=False, unidades_desplazadas=20)
    assert (w["costo_oportunidad"], w["utilidad_incremental"], w["precio_minimo"], w["decision"]) == (1120, -800, 80, "RECHAZAR")


def test_sin_clasificacion_declarada_se_marca_supuesto():
    p = D.panel(_r(), [dict(REC_COD="MAT", elemento="MD"), dict(REC_COD="MOD", elemento="PD"), dict(REC_COD="LUZ", elemento="IND")])
    assert set(p["recursos_supuestos"]) == {"MAT", "MOD", "LUZ"}
