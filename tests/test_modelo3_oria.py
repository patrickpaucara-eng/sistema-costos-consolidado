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
    # decisión del dueño 22/23-nov: entre pares del mismo nivel se permite el recíproco; repartirse a sí mismo sigue prohibido
    with pytest.raises(R.Rechazo, match="niveles inferiores|a sí mismo"):
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


def test_frenosa_corre_como_modelo3():
    """El caso Frenosa: el soporte (mantenimiento, calidad, ingeniería) lo reparte el sistema por CA → ACA → ACO."""
    from reyna_local.resultados import construir
    raiz = os.path.join(os.path.dirname(__file__), "..")
    r = construir(os.path.join(raiz, "casos", "libros", "frenosa.xlsx"), "FRE", "Frenosa")
    etapas = {t["etapa"] for t in r["trazas"] if t["elemento"] == "CIF"}
    assert {"P4A", "P4D", "P4E", "P4C"} <= etapas
    niveles = {a["codigo"]: a["nivel"] for a in r["modelo"]["actividades"]}
    assert niveles["A-MANT"] == "Apoyo" and niveles["FO-1"] == "Operativa"


def _reciproco_caso(nivel_centros=True):
    """S1 propio 1000, S2 propio 500. S1 → S2 20 %, P1 50 %, P2 30 %. S2 → S1 10 %, P1 60 %, P2 30 %.
    X1 = 1000 + 0.1·X2; X2 = 500 + 0.2·X1 → X1 = 7500/7, X2 = 5000/7. P1 = 0.5·X1 + 0.6·X2 = 6750/7; P2 = 0.3·(X1 + X2) = 3750/7."""
    reglas = [("P4A", "R1", "K1"), ("P4A", "R2", "K2"), ("P4B", "S1", "D1"), ("P4B", "S2", "D2"), ("P4C", "P1", "U1"), ("P4C", "P2", "U2")]
    med = (_med("K1", "CEN", (("S1", 1),)) + _med("K2", "CEN", (("S2", 1),)) + _med("D1", "CEN", (("S2", 20), ("P1", 50), ("P2", 30)))
           + _med("D2", "CEN", (("S1", 10), ("P1", 60), ("P2", 30))) + _med("U1", "OBJ", (("OT1", 1),)) + _med("U2", "OBJ", (("OT2", 1),)))
    return {"(sin MCD) REGLA_REPARTO": [dict(ETAPA=e, ORIGEN=o, CRITERIO=c, DESDE=19000101) for e, o, c in reglas], "(sin MCD) MEDIDA": med,
            "(sin MCD) LINEA": [dict(EVENTO=1, NUMERO=1, RECURSO="R1", CANTIDAD=1, COSTO_UNITARIO_DOCUMENTO=1000),
                                dict(EVENTO=1, NUMERO=2, RECURSO="R2", CANTIDAD=1, COSTO_UNITARIO_DOCUMENTO=500)],
            "EVENTO": [dict(NUMERO=1, PERIODO="X", EMPRESA="E", OBJETO=None, CENTRO=None)],
            "RECURSO": [dict(CODIGO="R1", TIPO_RECURSO="IND_T"), dict(CODIGO="R2", TIPO_RECURSO="IND_T")],
            "(sin MCD) TIPO_RECURSO": [dict(CODIGO="IND_T", ELEMENTO_COSTO="IND")],
            "CENTRO": [dict(CODIGO="S1", EMPRESA="E", TIPO="APR"), dict(CODIGO="S2", EMPRESA="E", TIPO="APR"),
                       dict(CODIGO="P1", EMPRESA="E", TIPO="PRO"), dict(CODIGO="P2", EMPRESA="E", TIPO="PRO")],
            "(sin MCD) OBJETO": [dict(NUMERO="OT1", EMPRESA="E", TIPO="OT"), dict(NUMERO="OT2", EMPRESA="E", TIPO="OT")],
            "ACTIVIDAD": [], "PERIODO": [dict(CODIGO="X", EMPRESA="E", INICIO=20260101)]}


def test_reciproco_entre_centros_de_apoyo_a_mano():
    h = _reciproco_caso()
    f = R.interno(h, PAR, PREV)
    assert abs(f["OT1"]["CIF"] - D(6750) / 7) < D("1e-20") and abs(f["OT2"]["CIF"] - D(3750) / 7) < D("1e-20")
    traza = R.trazar(h, PAR, PREV, "OBJETO", "OT1", "CIF")
    assert abs(sum(l["monto_atribuido"] for l in traza if l["raiz"]) - D(6750) / 7) < D("1e-20")


def test_reciproco_sin_servicio_de_vuelta_es_el_escalonado():
    """Si S2 no sirve a S1: X1 = 1000; S2 = 500 + 200 = 700 y se reparte 2:1 → P1 = 500 + 466.67; P2 = 300 + 233.33."""
    h = _reciproco_caso()
    h["(sin MCD) MEDIDA"] = [m for m in h["(sin MCD) MEDIDA"] if not (m["CRITERIO"] == "D2" and m["DESTINO"] == "S1")]
    f = R.interno(h, PAR, PREV)
    assert abs(f["OT1"]["CIF"] - (D(500) + D(1400) / 3)) < D("1e-20") and abs(f["OT2"]["CIF"] - (D(300) + D(700) / 3)) < D("1e-20")


def test_reciproco_entre_actividades_de_apoyo():
    """Mismo caso con actividades de apoyo (P4E, nivel A) que se prestan servicio y bajan a operativas."""
    h = _reciproco_caso()
    h["CENTRO"] = []; h["ACTIVIDAD"] = [dict(CODIGO=c, NIVEL=n) for c, n in (("S1", "A"), ("S2", "A"), ("P1", "O"), ("P2", "O"))]
    h["(sin MCD) REGLA_REPARTO"] = [dict(r, ETAPA={"P4B": "P4E"}.get(r["ETAPA"], r["ETAPA"])) for r in h["(sin MCD) REGLA_REPARTO"]]
    h["(sin MCD) MEDIDA"] = [dict(m, NIVEL="ACT" if m["NIVEL"] == "CEN" else m["NIVEL"]) for m in h["(sin MCD) MEDIDA"]]
    f = R.interno(h, PAR, PREV)
    assert abs(f["OT1"]["CIF"] - D(6750) / 7) < D("1e-20") and abs(f["OT2"]["CIF"] - D(3750) / 7) < D("1e-20")
