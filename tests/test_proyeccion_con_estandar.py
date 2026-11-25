# -*- coding: utf-8 -*-
"""C21 + C22: la proyección usa el consumo estándar aprendido (APLICADO y vigente) por unidad buena; sin capa, el del libro."""
import json, os, sys
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from reyna_local.proyeccion import proyectar_granular  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def test_consumo_aprendido_reemplaza_al_del_mes_base(tmp_path):
    libro = ROOT / "casos/libros/frenosa.xlsx"
    base = json.loads((ROOT / "datos/resultados/frenosa_2010-12_REAL.json").read_text())
    f = {"vol": {o["producto"]: 1 for o in base["objetos"]}, "pre": {r["codigo"]: 1 for r in base["modelo"]["recursos"]},
         "pv": {o["producto"]: 1 for o in base["objetos"]}}
    sin = proyectar_granular(libro, "FRE", meses=1, factores=f, carpeta_aprendizaje=tmp_path)
    o = next(x for x in base["objetos"] if x["producto"] == "SW50")
    (tmp_path / "aprendizaje").mkdir()
    from reyna_local.resultados import P
    can = {r["OBJ_NUM"]: float(r["OBJ_CAN"]) for r in P.leer(libro, ["OBJETO"])["OBJETO"]}
    lin = [l for l in P.leer(libro, ["LINEA", "EVENTO"])["LINEA"]]
    eve = {e["EVE_NUM"]: e for e in P.leer(libro, ["EVENTO"])["EVENTO"]}
    q0 = sum(float(l["LIN_CAN"] or 0) for l in lin if l["LIN_REC"] == "MAT_SW50" and eve.get(l["LIN_EVE"], {}).get("EVE_OBJ") == o["codigo"])
    capa = [dict(id="x", calibrador="consumo", objeto=dict(producto="SW50", recurso="MAT_SW50"), valor_aprendido=0.5 * q0 / can[o["codigo"]],   # mitad del consumo por unidad del mes base
                 estado="APLICADO", vigente_desde="2011-01")]
    (tmp_path / "aprendizaje" / "FRE.json").write_text(json.dumps(capa))
    con = proyectar_granular(libro, "FRE", meses=1, factores=f, carpeta_aprendizaje=tmp_path)
    md = lambda r: next(p for p in r["meses"][0]["productos"] if p["producto"] == "SW50")["elementos"]["MD"]
    assert abs(md(sin) - o["md"]) <= 0.01
    assert abs(md(con) - o["md"] * 0.5) <= 0.01
