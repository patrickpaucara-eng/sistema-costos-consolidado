"""Barreras del contrato de resultados (reglas del dueño que bloquean, no aconsejan)."""
import copy, json, pathlib
from reyna_local import contrato
EJ = json.loads((pathlib.Path(__file__).parent / "fixtures/contrato/resultados_ejemplo.json").read_text(encoding="utf-8"))

def test_ejemplo_cumple():
    assert contrato.validar(EJ) == []

def test_contable_no_lleva_financieros_al_costo():   # D-9 / NIC 2
    r = copy.deepcopy(EJ); r["sintesis"] = "CONTABLE"
    assert any("NIC 2" in e for e in contrato.validar(r))

def test_estocastico_exige_percentiles():
    r = copy.deepcopy(EJ); r["serie"].append(dict(periodo="2011-02", tipo="PROYECTADO_EST", ventas=1, costo_total=1, margen=0))
    assert any("P05" in e for e in contrato.validar(r))

def test_elementos_suman_el_costo_total():
    r = copy.deepcopy(EJ); r["objetos"][0]["md"] += 100
    assert any("costo_total" in e for e in contrato.validar(r))
