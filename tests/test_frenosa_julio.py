"""Etapa 1 · Caso Frenosa julio 2010 por el ABC por etapas (mismo método verificado con Oria P10).
Valores esperados calculados A MANO desde los cuadros del caso (Cherres Juárez 2010), no desde el motor."""
import importlib.util, pathlib
from decimal import Decimal as D
import puerto_lectura as P
from metodos import reparto_etapas as R
from integra_env import valuacion_alg01
RAIZ = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("gen", RAIZ / "casos/frenosa/generar_julio.py"); gen = importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)


def _correr(tmp_path):
    L = gen.generar(str(RAIZ / "casos/plantilla_caso.xlsx"), str(tmp_path / "fre.xlsx"))
    return R.interno(P.leer_conceptos(L, R.CONSUME), dict(PER="2010-07", EMP="FRE"), {"VALUACION_PROMEDIO": valuacion_alg01(L)})


def test_conserva_el_costo_total(tmp_path):
    # MD 122,328.58 + 241,377.76 + 80,286.91 = 443,993.25 · MOD 59 × 1,350 = 79,650 · otros 92,138 · soporte 14,538 + 5,827 + 4,737 = 25,102
    fin = _correr(tmp_path)
    assert round(sum(sum(v.values()) for v in fin.values()), 2) == D("640883.25")


def test_ot001_a_mano(tmp_path):
    v = _correr(tmp_path)["OT001"]
    assert round(v["MD"], 2) == D("122328.58")                 # 38,174 × 3.2045
    assert round(v["PD"], 2) == D("35842.50")                  # 79,650 × 0.45
    assert round(v["CIF"], 2) == D("51251.88")                 # 92,138 × 0.45 + 25,102 × 0.39


def test_ot003_a_mano(tmp_path):
    v = _correr(tmp_path)["OT003"]
    assert round(v["PD"], 2) == D("2389.50")                   # 79,650 × 0.03
    assert round(v["CIF"], 2) == D("6780.46")                  # 92,138 × 0.03 + 25,102 × 0.16


def test_material_va_directo_a_la_orden_no_por_reparto(tmp_path):   # D-10
    L = gen.generar(str(RAIZ / "casos/plantilla_caso.xlsx"), str(tmp_path / "fre.xlsx"))
    rr = P.leer(L, ["REGLA_REPARTO"])["REGLA_REPARTO"]
    assert all(r["RRE_CRIT"] == "CONSUMO" for r in rr if str(r["RRE_ORIGEN"]).startswith("MAT_"))
