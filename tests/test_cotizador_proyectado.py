# -*- coding: utf-8 -*-
"""Bloques B y G (decisión 25-nov): costo proyectado de la OT por intervalos y familias con lógica de bloques. Casos a mano."""
import json
from pathlib import Path
import pytest
from reyna_local import familias as F
from reyna_local.cotizador import costo_por_intervalos, cotizar_proyectado
from reyna_local.intervalos_proyectados import sugerir_intervalo, variaciones

ROOT = Path(__file__).resolve().parents[1]


def test_b1_seis_meses_trimestral_pareja():
    tasas = {2: {"MAT": 10, "MOD": 20}, 5: {"MAT": 11, "MOD": 21}}
    r = costo_por_intervalos({"MAT": 1000, "MOD": 600}, lambda c, m: tasas[m][c], 6, 3)
    assert [f["mes_medio"] for f in r["intervalos"]] == [2, 5]
    assert [f["costo"] for f in r["intervalos"]] == [11000, 11800] and r["total"] == 22800


def test_b2_intervalo_sugerido_bimestral():
    assert sugerir_intervalo([10, 10.1, 10.15, 10.5, 10.6, 10.62], 0.02) == 2


def test_b3_variaciones_tasa_y_cantidad():
    v = variaciones(10, 60, 12, 65)
    assert (float(v["tasa"]), float(v["cantidad"]), float(v["total"])) == (60, 120, 180)


def test_g1_pertenencia_por_intervalo_de_prediccion():
    r = F.receta([10, 11, 9, 10, 10])
    assert round(r["minimo"], 2) == 7.85 and round(r["maximo"], 2) == 12.15
    assert F.pertenece({"h": 11.5}, {"h": r})["pertenece"] and not F.pertenece({"h": 14}, {"h": r})["pertenece"]


def test_g2_anova_mismo_efecto():
    a = F.anova([10, 11, 9, 10, 10], [10.2, 9.8, 10.5, 9.9, 10.1])
    assert round(a["F"], 3) == 0.087 and round(a["p"], 3) == 0.776 and a["mismo_efecto"]


def test_curvas_reparten_distinto_pero_suman_lo_mismo_con_tasa_fija():
    for c in ("pareja", "inicio", "final"):
        assert costo_por_intervalos({"X": 900}, lambda c_, m: 2, 6, 2, c)["total"] == 1800


def test_cotizacion_proyectada_con_familia_en_servitec():
    libro = ROOT / "casos/libros/segundo.xlsx"
    r = json.loads((ROOT / "datos/resultados/segundo_2025-08_REAL.json").read_text(encoding="utf-8"))
    import puerto_lectura as P
    med = P.leer(libro, ["MEDIDA"])["MEDIDA"]
    fam = {"BOB": F.receta([48, 50, 52, 49, 51]), "PRU": F.receta([10, 11, 9, 10, 10])}
    q = cotizar_proyectado(libro, "SRV", r, med, {}, {}, 5000, 0.3, meses=6, intervalo=3, familia=fam, unidades=2)
    assert len(q["intervalos"]) == 2 and q["total"] > 0 and q["rango_95"][0] < q["total"] < q["rango_95"][1]
    assert q["brecha"] == round(q["total"] - 3500, 2)
