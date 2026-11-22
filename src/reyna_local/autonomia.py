"""Analítica autónoma (punto 9): aprende de sus propias propuestas con resultados medidos.
1. DECISIÓN: una propuesta cuenta como decidida cuando su paquete de cierre quedó APROBADO (punto 7).
2. SEGUIMIENTO: en cada periodo posterior se mide el costo unitario real del mismo producto y elemento contra la línea base y
   el objetivo guardados en la propuesta: ahorro realizado = (CU base − CU actual) × cantidad del mes; cumplimiento =
   ahorro realizado / ahorro prometido (prometido = (CU base − CU objetivo) × cantidad).
3. APRENDIZAJE: por tipo de propuesta (elemento), el factor de efectividad es el promedio del cumplimiento medido (acotado a
   [0, 1.5]); con él se ajusta el impacto esperado de las propuestas nuevas y se reordenan. Sin historia medida, factor 1
   (sin ajuste) y se dice explícitamente. Todo es determinista y reproducible desde los paquetes sellados."""
import json
from pathlib import Path

ELEM = {"MD": "md", "PD": "mod", "CIF": "cif"}


def _aprobados(base, empresa):
    d = Path(base) / "resultados" / "cierres"
    if not d.is_dir(): return []
    out = []
    for f in sorted(d.glob(f"{empresa}_*.json")):
        p = json.loads(f.read_text(encoding="utf-8"))
        if p.get("estado") == "APROBADO": out.append(p)
    vig = {}
    for p in out:                                           # la versión aprobada más reciente de cada periodo
        if p["periodo"] not in vig or p["version"] > vig[p["periodo"]]["version"]: vig[p["periodo"]] = p
    return [vig[k] for k in sorted(vig)]


def aplicar(resultado, base, empresa):
    per = resultado["periodo_actual"]
    actual = {o["producto"]: o for o in resultado["objetos"]}
    seg = []
    for p in _aprobados(base, empresa):
        if p["periodo"] >= per: continue
        for pr in p["resultados"]["REAL"].get("propuestas") or []:
            o = actual.get(pr.get("producto")); col = ELEM.get(pr.get("elemento"))
            if not o or not col or not o["cantidad"] or pr.get("cu_base") is None or pr.get("cu_objetivo") is None: continue
            cu_now = o[col] / o["cantidad"]
            prometido = (pr["cu_base"] - pr["cu_objetivo"]) * o["cantidad"]
            realizado = (pr["cu_base"] - cu_now) * o["cantidad"]
            seg.append(dict(propuesta=pr["codigo"], decidida_en=p["periodo"], version=p["version"], elemento=pr["elemento"],
                            producto=pr["producto"], cu_base=pr["cu_base"], cu_objetivo=pr["cu_objetivo"], cu_actual=round(cu_now, 6),
                            ahorro_prometido_mes=round(prometido, 2), ahorro_realizado_mes=round(realizado, 2),
                            cumplimiento=round(max(0.0, min(1.5, realizado / prometido)), 4) if prometido > 0 else None))
    apr = {}
    for x in seg:
        if x["cumplimiento"] is not None: apr.setdefault(x["elemento"], []).append(x["cumplimiento"])
    factor = {e: dict(factor=round(sum(v) / len(v), 4), mediciones=len(v)) for e, v in apr.items()}
    for pr in resultado.get("propuestas") or []:
        f = factor.get(pr.get("elemento"), {}).get("factor")
        pr["impacto_esperado"] = round(pr["impacto_anual"] * (f if f is not None else 1.0), 2)
        pr["base_aprendizaje"] = (f"factor {f:.2f} de {factor[pr['elemento']]['mediciones']} mediciones" if f is not None
                                  else "sin historia medida (factor 1)")
    resultado["propuestas"] = sorted(resultado.get("propuestas") or [], key=lambda p: -p.get("impacto_esperado", p["impacto_anual"]))
    resultado["seguimiento"] = seg; resultado["aprendizaje"] = factor
    return resultado
