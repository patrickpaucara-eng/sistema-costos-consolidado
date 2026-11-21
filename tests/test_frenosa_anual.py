"""Etapa 1 · Frenosa 2010, 12 meses: conservación del costo, encadenamiento del kardex y contrato de resultados."""
import csv, pathlib, sys
from decimal import Decimal as D
import pytest
RAIZ = pathlib.Path(__file__).resolve().parents[1]; sys.path.insert(0, str(RAIZ / "casos/frenosa"))
import generar as G
from reyna_local import contrato, resultados


@pytest.fixture(scope="module")
def caso(tmp_path_factory):
    L, saldos = G.generar(str(RAIZ / "casos/plantilla_caso.xlsx"), str(tmp_path_factory.mktemp("f") / "fre.xlsx"))
    por_per, _ = resultados.calcular_periodos(L, "FRE")
    return L, saldos, por_per


def _entradas_conversion(p):
    pd = [r for r in G.leer("Personal_directos.csv") if r["periodo"] == p][0]
    mod = G.num(pd["cantidad_operarios"]) * G.num(pd["salario_mensual_operario_soles"])
    otros = sum(G.num(r["importe_soles"]) for r in G.leer("costo_otros_recursos(CI).csv") if r["periodo"] == p)
    mant = sum(G.num(r["costo_equipo_soles"]) for r in G.leer("Soporte_Mantenimiento(CI).csv") if r["periodo"] == p)
    cc = sum(G.num(r["cantidad"]) * G.num(r["costo_unitario_soles"]) for r in G.leer("Soporte_Control_Calidad(CI).csv") if r["periodo"] == p)
    ing = sum(G.num(r["cantidad"]) * G.num(r["costo_unitario_soles"]) for r in G.leer("Soporte_Ingenieria(CI).csv") if r["periodo"] == p)
    return round(mod + otros + mant + cc + ing, 2)


def test_cada_mes_conserva_la_conversion(caso):
    _, _, por_per = caso
    assert len(por_per) == 12
    for p, fin in por_per.items():
        conv = sum(v.get("PD", D(0)) + v.get("CIF", D(0)) for v in fin.values())
        assert abs(float(conv) - _entradas_conversion(p)) < 0.01, p


def test_kardex_encadena_meses(caso):
    """El saldo inicial de cada mes de los datos = saldo final calculado (cantidades exactas; importes a céntimos de redondeo)."""
    _, saldos, _ = caso
    assert len(saldos) == 36


def test_julio_material_cerca_del_cuadro_1(caso):
    """Cuadro 1 usa costos unitarios redondeados (3.2045, 5.481, 5.0792) = 443,993.25; el kardex promedio exacto difiere en céntimos por kg."""
    md = sum(v.get("MD", D(0)) for v in caso[2]["2010-07"].values())
    assert abs(float(md) - 443993.25) < 10


def test_contrato_real_valido(caso):
    r = resultados.construir(caso[0], ventas_csv=str(RAIZ / "datos/frenosa/Ventas.csv"), periodo="2010-07")
    assert contrato.validar(r) == []
    assert len(r["serie"]) == 12 and r["kpi"]["ventas"] == 888730.0      # Cuadro 18: 324,479 + 453,602 + 110,649
