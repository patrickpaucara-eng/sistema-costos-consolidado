# -*- coding: utf-8 -*-
"""Modelos ABC de Oria (GE704W, semana 07) como datos sobre un solo motor (REPARTO_ETAPAS):
Modelo 3 escalonado EC→CA→ACE→ACA→ACO→OC con costo directo en la actividad operativa; Modelo 2 EC→CA→AC→OC;
rechazos del escalonado (hacia atrás o entre pares, actividad estratégica sin regla, nivel inválido) y trazabilidad."""
import copy
import os
import sys
from decimal import Decimal as D

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from metodos import reparto_etapas as R  # noqa: E402


def _med(crit, nivel, pares):
    return [dict(PERIODO="X", EMPRESA="E", CRITERIO=crit, NIVEL=nivel, DESTINO=d, CANTIDAD=q) for d, q in pares]


def _caso():
    """EC 1000 → CAE 100, CAA 300, CAO 600 (EC-CA). CAE→ACE, CAA→ACA, CAO→ACO1/ACO2 1:2 (CA-AC).
    ACE 100 → ACA 50 %, ACO1 25 %, ACO2 25 % (ACE-ACA, ACE-ACO). ACA 350 → ACO1/ACO2 1:1 (ACA-ACO).
    ACO1 = 200 + 25 + 175 = 400; ACO2 = 400 + 25 + 175 = 600. Servicio directo 100 entra a ACO1 (P3).
    ACO1 → OT1/OT2 1:1; ACO2 → OT1/OT2 1:3 (ACO-OC). OT1 CIF = 200 + 150 = 350; OT2 CIF = 200 + 450 = 650; SD 50/50."""
    reglas = [("P4A", "LUZ", "EC_CA"), ("P3", "SERV", "SD_ACT"), ("P4D", "CAE", "CAE_ACE"), ("P4D", "CAA", "CAA_ACA"),
              ("P4D", "CAO", "CAO_ACO"), ("P4E", "ACE", "ACE_AC"), ("P4E", "ACA", "ACA_ACO"),
              ("P4C", "ACO1", "ACO1_OC"), ("P4C", "ACO2", "ACO2_OC")]
    return {
        "(sin MCD) REGLA_REPARTO": [dict(ETAPA=e, ORIGEN=o, CRITERIO=c, DESDE=19000101) for e, o, c in reglas],
        "(sin MCD) MEDIDA": _med("EC_CA", "CEN", (("CAE", 100), ("CAA", 300), ("CAO", 600)))
                            + _med("SD_ACT", "ACT", (("ACO1", 1),))
                            + _med("CAE_ACE", "ACT", (("ACE", 1),)) + _med("CAA_ACA", "ACT", (("ACA", 1),))
                            + _med("CAO_ACO", "ACT", (("ACO1", 1), ("ACO2", 2)))
                            + _med("ACE_AC", "ACT", (("ACA", 50), ("ACO1", 25), ("ACO2", 25)))
                            + _med("ACA_ACO", "ACT", (("ACO1", 1), ("ACO2", 1)))
                            + _med("ACO1_OC", "OBJ", (("OT1", 1), ("OT2", 1))) + _med("ACO2_OC", "OBJ", (("OT1", 1), ("OT2", 3))),
        "(sin MCD) LINEA": [dict(EVENTO=1, NUMERO=1, RECURSO="LUZ", CANTIDAD=1, COSTO_UNITARIO_DOCUMENTO=1000),
                            dict(EVENTO=1, NUMERO=2, RECURSO="SERV", CANTIDAD=1, COSTO_UNITARIO_DOCUMENTO=100)],
        "EVENTO": [dict(NUMERO=1, PERIODO="X", EMPRESA="E", OBJETO=None, CENTRO=None)],
        "RECURSO": [dict(CODIGO="LUZ", TIPO_RECURSO="IND_T"), dict(CODIGO="SERV", TIPO_RECURSO="SD_T")],
        "(sin MCD) TIPO_RECURSO": [dict(CODIGO="IND_T", ELEMENTO_COSTO="IND"), dict(CODIGO="SD_T", ELEMENTO_COSTO="SD")],
        "CENTRO": [dict(CODIGO=c, EMPRESA="E", TIPO="PRO") for c in ("CAE", "CAA", "CAO")],
        "(sin MCD) OBJETO": [dict(NUMERO=o, EMPRESA="E", TIPO="OT") for o in ("OT1", "OT2")],
        "ACTIVIDAD": [dict(CODIGO="ACE", NIVEL="E"), dict(CODIGO="ACA", NIVEL="A"), dict(CODIGO="ACO1", NIVEL="O"), dict(CODIGO="ACO2", NIVEL=None)],
        "PERIODO": [dict(CODIGO="X", EMPRESA="E", INICIO=20260101)]}


PAR = dict(PER="X", EMP="E"); PREV = {"VALUACION_PROMEDIO": []}


def _final(h):
    return {o: {e: round(float(v), 6) for e, v in el.items() if v} for o, el in R.interno(h, PAR, PREV).items()}


def test_modelo3_escalonado_con_directo_en_actividad():
    f = _final(_caso())
    assert f["OT1"] == {"CIF": 350.0, "SD": 50.0}
    assert f["OT2"] == {"CIF": 650.0, "SD": 50.0}
    _, aristas, _ = R.correr(_caso(), PAR, PREV)
    etapas = [a["etapa"] for a in aristas]
    assert etapas.index("P4D") < etapas.index("P4E") < etapas.index("P4C")
    llegada = {}
    for a in aristas:
        if a["nivel"] == "ACT": llegada[a["destino"]] = llegada.get(a["destino"], 0) + float(a["monto"])
    assert round(llegada["ACA"], 6) == 350.0 and round(llegada["ACO1"], 6) == 500.0 and round(llegada["ACO2"], 6) == 600.0


def test_modelo2_es_el_mismo_motor_sin_niveles():
    h = _caso()
    h["ACTIVIDAD"] = [dict(CODIGO=c, NIVEL=None) for c in ("ACE", "ACA", "ACO1", "ACO2")]
    h["(sin MCD) REGLA_REPARTO"] = [r for r in h["(sin MCD) REGLA_REPARTO"] if r["ETAPA"] != "P4E"] + [
        dict(ETAPA="P4C", ORIGEN="ACE", CRITERIO="ACO1_OC", DESDE=19000101), dict(ETAPA="P4C", ORIGEN="ACA", CRITERIO="ACO2_OC", DESDE=19000101)]
    f = _final(h)
    # CAE 100 → ACE → OT 50/50; CAA 300 → ACA → OT 75/225; CAO 600 → ACO1 200 (100/100), ACO2 400 (100/300)
    assert f["OT1"]["CIF"] == 325.0 and f["OT2"]["CIF"] == 675.0
    assert round(sum(sum(x.values()) for x in f.values()), 6) == 1100.0


def test_escalonado_no_va_hacia_atras_ni_entre_pares():
    h = _caso()
    h["(sin MCD) MEDIDA"] += _med("ACA_ACO", "ACT", (("ACE", 1),))
    with pytest.raises(R.Rechazo, match="niveles inferiores"):
        R.correr(h, PAR, PREV)
    h = _caso()
    h["(sin MCD) MEDIDA"] += _med("ACE_AC", "ACT", (("ACE", 1),))
    with pytest.raises(R.Rechazo, match="niveles inferiores"):
        R.correr(h, PAR, PREV)


def test_actividad_estrategica_sin_regla_detiene_el_calculo():
    h = _caso()
    h["(sin MCD) REGLA_REPARTO"] = [r for r in h["(sin MCD) REGLA_REPARTO"] if r["ORIGEN"] != "ACE"]
    with pytest.raises(R.Rechazo, match="R-52: P4E ACE"):
        R.correr(h, PAR, PREV)


def test_nivel_invalido_se_rechaza():
    h = _caso()
    h["ACTIVIDAD"][0]["NIVEL"] = "X"
    with pytest.raises(R.Rechazo, match="nivel"):
        R.correr(h, PAR, PREV)


def test_traza_del_modelo3_cuadra_con_el_objeto():
    h = _caso()
    lineas = R.trazar(h, PAR, PREV, "OBJETO", "OT2", "CIF")
    assert abs(sum(l["monto_atribuido"] for l in lineas if l["raiz"]) - D("650")) < D("1e-9")
    assert {"P4A", "P4D", "P4E", "P4C"} <= {l["etapa"] for l in lineas}


def test_caso_anterior_del_motor_sigue_igual():
    c = copy.deepcopy(R.CASOS[0])
    f = R.interno(c["hechos"], c["parametros"], c["previos"])
    for _, o, e, v in c["espera"]:
        assert round(float(f[o][e]), 6) == v
