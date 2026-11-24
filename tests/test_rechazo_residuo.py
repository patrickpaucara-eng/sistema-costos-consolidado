# -*- coding: utf-8 -*-
"""Tarea 2.9b (decisión del dueño 24-nov).
- Rechazo interno sin reproceso = costo de no calidad: la fracción rechazada del costo normal de producción de la orden pasa a
  PERDIDA; la orden conserva su total en REAL, CONTABLE lo saca del inventario y el estado de resultados lo muestra aparte.
- Con reproceso, o con causa tipificada como normal (CIN_DESTINO = CIF), no se reclasifica.
- Coproductos: lo que nunca tuvo valor de venta es residuo y no se costea."""
import os, shutil, sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from reyna_local import inventarios as INV  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
PROD = ("MD", "PD", "SD", "CIF")


def _libro(tmp_path, reprocesa="N", destino=None):
    from openpyxl import load_workbook
    p = tmp_path / "f.xlsx"; shutil.copy(RAIZ / "casos/libros/frenosa.xlsx", p); wb = load_workbook(p)
    cab = [c.value for c in wb["OBJETO"][1]]
    o = next(r for r in wb["OBJETO"].iter_rows(min_row=2, values_only=True) if str(r[cab.index("OBJ_NUM")]).endswith("2010-07"))
    orden, buenas = o[cab.index("OBJ_NUM")], float(o[cab.index("OBJ_CAN")])
    wb["CAUSA_INEF"].append(["C1", "Fuera de medida", "RECHAZO", "S", destino or "PERDIDA"])
    wb["RECHAZO"].append(["R1", "FRE", "2010-07", orden, buenas / 3, "C1", reprocesa])   # 1/3 de las buenas → 25 % del total
    wb.save(p)
    return str(p), orden


def _prod(v):
    return sum(float(x) for k, x in v.items() if k.split("|")[0] in PROD)


def test_rechazo_sin_reproceso_pasa_un_cuarto_a_perdida(tmp_path):
    from reyna_local import resultados
    base, _ = resultados.calcular_periodos(str(RAIZ / "casos/libros/frenosa.xlsx"), "FRE")
    p, orden = _libro(tmp_path)
    c = resultados.calcular_periodos(p, "FRE"); nuevo = c[0]["2010-07"]
    for o, v in base["2010-07"].items():
        assert _prod(nuevo[o]) == pytest.approx(_prod(v), abs=1e-6)              # no se crea ni se pierde dinero
        if o != orden: assert nuevo[o] == v
    perd = sum(float(x) for k, x in nuevo[orden].items() if k.endswith("|PERDIDA"))
    norm0 = sum(float(x) for k, x in base["2010-07"][orden].items() if k in PROD)
    assert perd == pytest.approx(norm0 * 0.25, abs=1e-6)
    real = resultados.construir(p, periodo="2010-07", sintesis="REAL", _cache=c)
    cont = resultados.construir(p, periodo="2010-07", sintesis="CONTABLE", _cache=c)
    o_r = next(x for x in real["objetos"] if x["codigo"] == orden); o_c = next(x for x in cont["objetos"] if x["codigo"] == orden)
    assert o_r["perdida"] == pytest.approx(round(norm0 * 0.25, 2), abs=0.02) and o_c["perdida"] == 0
    assert real["rechazos"] == cont["rechazos"] and real["rechazos"][0]["importe"] == pytest.approx(norm0 * 0.25, abs=0.01)
    assert any("rechazos sin reproceso" in x["concepto"] for x in cont["estado_resultados"])
    tr = [t for t in real["trazas"] if t["objeto"] == orden and t["raiz"] and t["elemento"].endswith("|PERDIDA")]
    assert sum(t["monto"] for t in tr) == pytest.approx(o_r["perdida"], abs=0.05 * max(1, len(tr) / 10))


@pytest.mark.parametrize("reprocesa,destino", [("S", None), ("N", "CIF")])
def test_reproceso_o_causa_normal_no_reclasifica(tmp_path, reprocesa, destino):
    from reyna_local import resultados
    base, _ = resultados.calcular_periodos(str(RAIZ / "casos/libros/frenosa.xlsx"), "FRE")
    p, _ = _libro(tmp_path, reprocesa, destino)
    assert resultados.calcular_periodos(p, "FRE")[0]["2010-07"] == base["2010-07"]


def test_coproducto_nunca_vendido_es_residuo():
    pr = {("2010-07", "A"): 20.0, ("2010-05", "B"): 5.0}
    partes, base = INV.reparto_conjunto(1000.0, [("A", 10), ("R", 50)], pr, "2010-07", "VVR")
    assert base == "VVR+RESIDUO" and partes[0][2] == 1000.0 and partes[1][2] == 0.0
    partes, base = INV.reparto_conjunto(1000.0, [("A", 10), ("R", 50)], pr, "2010-07", "FISICA")
    assert base == "FISICA+RESIDUO" and partes[1][2] == 0.0
    partes, base = INV.reparto_conjunto(1000.0, [("A", 10), ("B", 20)], pr, "2010-07", "VVR")   # B: último precio conocido
    assert base == "VVR" and partes[0][2] == pytest.approx(1000 * 200 / 300)
    partes, base = INV.reparto_conjunto(900.0, [("X", 10), ("Y", 20)], {}, "2010-07", "VVR")    # sin precios: físico, como antes
    assert base == "FISICA" and partes[0][2] == pytest.approx(300.0)
