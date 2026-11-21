"""Regresión del ABC por etapas contra las soluciones de Oria (O-2 SEM07 P10 y O-3 P05). Protege el método al
agregar etapas (P7 financieros) o síntesis. Oráculo P10 (Oria): CIF unitario tradicional TV19 135.5140 · TV20 54.2056 ·
TV25 216.8224; ABC TV19 89.7222 · TV20 83.6364 · TV25 234.5000."""
import copy, json, pathlib
from decimal import Decimal as D
import pytest
import puerto_lectura as P
from metodos import reparto_etapas as R
from integra_env import valuacion_alg01
C = pathlib.Path(__file__).resolve().parents[1] / "casos/oria"


def _cif(libro, emp, h=None):
    h = h or P.leer_conceptos(str(libro), R.CONSUME)
    fin = R.interno(h, dict(PER="2026-01", EMP=emp), {"VALUACION_PROMEDIO": valuacion_alg01(str(libro))})
    can = {r["OBJ_NUM"]: R._d(r["OBJ_CAN"]) for r in P.leer(str(libro), ["OBJETO"])["OBJETO"]}
    return {o: v.get("CIF", D(0)) / can[o] for o, v in fin.items()}, h


def _paquete(h, paq):
    h = copy.deepcopy(h); rr = h["(sin MCD) REGLA_REPARTO"]
    for f in paq["filas"]:
        if f["col"] == "(NUEVA)":
            et, org, crit, desde, _ = f["nuevo"].split("|"); rr.append(dict(ETAPA=et, ORIGEN=org, CRITERIO=crit, DESDE=int(desde)))
        else:
            et, org = f["clave"].split("|")
            for r in rr:
                if r["ETAPA"] == et and r["ORIGEN"] == org: r["CRITERIO"] = f["nuevo"]
    return h


@pytest.mark.parametrize("tv,esperado", [("TV19", "135.5140"), ("TV20", "54.2056"), ("TV25", "216.8224")])
def test_p10_tradicional(tv, esperado):
    assert abs(_cif(C / "P10.xlsx", "P10")[0][tv] - D(esperado)) < D("1e-4")


@pytest.mark.parametrize("tv,esperado", [("TV19", "89.7222"), ("TV20", "83.6364"), ("TV25", "234.5000")])
def test_p10_abc(tv, esperado):
    _, h = _cif(C / "P10.xlsx", "P10")
    abc, _ = _cif(C / "P10.xlsx", "P10", _paquete(h, json.load(open(C / "P10_paquete_abc.json", encoding="utf-8"))))
    assert abs(abc[tv] - D(esperado)) < D("1e-4")


def test_p05_corre_y_conserva():
    cif, _ = _cif(C / "P05.xlsx", "P05")
    assert cif and all(v >= 0 for v in cif.values())
