# -*- coding: utf-8 -*-
"""A1 (decisión 25-nov): el costo proyectado sale por recurso, centro, actividad y OT, del mismo motor.
Identidad: con factores 1 el mes proyectado reproduce el desglose del mes base."""
import json
from pathlib import Path

from metodos import reparto_etapas as R
from reyna_local import resultados as RS
from reyna_local.proyeccion import desglose, proyectar_granular

ROOT = Path(__file__).resolve().parents[1]


def test_desglose_proyectado_igual_al_base_con_factores_uno():
    libro = ROOT / "casos/libros/segundo.xlsx"
    base = json.loads((ROOT / "datos/resultados/segundo_2025-08_REAL.json").read_text(encoding="utf-8"))
    f = {"vol": {o["producto"]: 1 for o in base["objetos"]}, "pre": {r["codigo"]: 1 for r in base["modelo"]["recursos"]},
         "pv": {o["producto"]: 1 for o in base["objetos"]}}
    p = proyectar_granular(libro, "SRV", meses=1, factores=f)["meses"][0]["desglose"]
    _, h = RS.calcular_periodos(str(libro), "SRV")
    fin, ar, est = R.correr(h, dict(PER="2025-08", EMP="SRV"), RS.previos(str(libro)))
    b = desglose(fin, ar, est)
    assert p["recursos"] == b["recursos"] and p["actividades"] == b["actividades"] and p["centros"] == b["centros"]
    assert [o["costo_total"] for o in p["ordenes"]] == [o["costo_total"] for o in b["ordenes"]]
    assert all(o["orden"].endswith("2025-08") for o in p["ordenes"])           # nombre de la OT original, no el clon
    assert abs(sum(r["monto"] for r in p["recursos"]) - sum(o["costo_total"] for o in p["ordenes"])) <= 0.05   # conservación


def test_precision_de_la_proyeccion_compara_lo_proyectado_del_pasado_con_lo_real():
    from reyna_local.proyeccion import precision
    r = precision(ROOT / "casos/libros/segundo.xlsx", "SRV", minimo=4)
    assert [m["periodo"] for m in r["por_mes"]] == ["2025-05", "2025-06", "2025-07", "2025-08"]
    real = json.loads((ROOT / "datos/resultados/segundo_2025-07_REAL.json").read_text(encoding="utf-8"))
    assert r["por_mes"][2]["real"] == round(sum(o["costo_total"] for o in real["objetos"]), 2)    # el real es el publicado
    assert r["error_medio_abs_pct"] is not None and r["error_medio_abs_pct"] < 10
