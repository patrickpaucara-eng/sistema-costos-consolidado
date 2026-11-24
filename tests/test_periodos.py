"""Tarea 2.6: periodos por fecha libre sobre el libro y los resultados publicados de Frenosa."""
import json, pathlib
import pytest
from reyna_local import periodos as PE

RAIZ = pathlib.Path(__file__).resolve().parents[1]
LIBRO = RAIZ / "casos/libros/frenosa.xlsx"; PUB = [RAIZ / "datos/resultados"]
R = lambda p: json.loads((RAIZ / f"datos/resultados/frenosa_{p}_REAL.json").read_text(encoding="utf-8"))


def test_bimestre_es_la_suma_de_sus_dos_meses():
    out = PE.desde_archivos(LIBRO, PUB, "frenosa", "REAL", "2010-07-01", "2010-08-31", "bimestre")
    (c,) = out["cubetas"]
    assert c["etiqueta"] == "2010-B4" and c["costo"]["completo"] and c["costo"]["meses"] == ["2010-07", "2010-08"]
    assert abs(c["costo"]["costo_total"] - R("2010-07")["kpi"]["costo_total"] - R("2010-08")["kpi"]["costo_total"]) < 0.01
    p = {x["producto"]: x for x in c["costo"]["productos"]}["SW50"]
    assert p["costo_unitario"] == round(p["costo"] / p["cantidad"], 4)


def test_anio_suma_los_12_meses_y_trimestre_parcial_se_marca():
    (a,) = PE.desde_archivos(LIBRO, PUB, "frenosa", "REAL", "2010-01-01", "2010-12-31", "anio")["cubetas"]
    assert a["costo"]["completo"] and abs(a["costo"]["costo_total"] - sum(R(f"2010-{m:02d}")["kpi"]["costo_total"] for m in range(1, 13))) < 0.05
    t = PE.desde_archivos(LIBRO, PUB, "frenosa", "REAL", "2010-02-01", "2010-03-31", "trimestre")["cubetas"]
    assert len(t) == 1 and not t[0]["costo"]["completo"] and "excede" in t[0]["nota"]


def test_quincena_y_dia_solo_hechos_que_cuadran_con_el_mes():
    q = PE.desde_archivos(LIBRO, PUB, "frenosa", "REAL", "2010-07-01", "2010-07-31", "quincena")["cubetas"]
    m = PE.desde_archivos(LIBRO, PUB, "frenosa", "REAL", "2010-07-01", "2010-07-31", "mes")["cubetas"][0]
    assert [c["etiqueta"] for c in q] == ["2010-07-Q1", "2010-07-Q2"] and all(c["costo"] is None for c in q)
    for trx, h in m["hechos"].items():
        assert abs(sum(c["hechos"].get(trx, {}).get("importe", 0) for c in q) - h["importe"]) < 0.02


def test_grano_y_fechas_invalidos_se_rechazan():
    with pytest.raises(ValueError): PE.agrupar([], [], {}, "2010-01-01", "2010-01-31", "semana")
    with pytest.raises(ValueError): PE.agrupar([], [], {}, "2010-02-01", "2010-01-31", "mes")


def test_propuesta_de_material_segun_causa():
    """Tarea 2.7: variación de precio → Compras; de cantidad → Producción."""
    from reyna_local.resultados import _propuesta_por_causa
    props = [dict(elemento="MD", producto="A"), dict(elemento="MD", producto="B"), dict(elemento="CIF", producto="A")]
    var = [dict(orden="o1", var_precio=500.0, var_cantidad=100.0), dict(orden="o2", var_precio=-50.0, var_cantidad=300.0)]
    _propuesta_por_causa(props, var, {"o1": "A", "o2": "B"})
    assert props[0]["causa"] == "PRECIO" and props[0]["responsable"] == "Compras"
    assert props[1]["causa"] == "CANTIDAD" and props[1]["responsable"] == "Producción"
    assert "causa" not in props[2]
