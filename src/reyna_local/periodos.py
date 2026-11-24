"""Periodos por fecha libre (tarea 2.6; decisión del dueño 23-nov): cualquier rango y grano sin código nuevo por periodo.
- HECHOS (compras, consumos, gastos, ventas registradas): por cualquier grano, desde la fecha de cada evento (EVE_FEC).
- COSTO COMPLETO ABC: se calcula por mes (el indirecto se reparte al cierre). Un grano de mes o mayor suma meses completos;
  si un mes del grano cae fuera del rango o no tiene resultado, la cubeta se marca incompleta. Día y quincena: solo hechos.
Solo lee resultados publicados y el libro: no recalcula costos."""
from datetime import date, timedelta

GRANOS = ("dia", "quincena", "mes", "bimestre", "trimestre", "semestre", "anio")
_MESES = {"mes": 1, "bimestre": 2, "trimestre": 3, "semestre": 6, "anio": 12}


def _fecha(v):
    s = str(v).replace("-", "")[:8]
    return date(int(s[:4]), int(s[4:6]), int(s[6:8]))


def _fin_mes(a, m):
    return (date(a + (m == 12), m % 12 + 1, 1) - timedelta(days=1))


def cubeta(f, grano):
    """Fecha → (etiqueta, inicio, fin) de su cubeta."""
    if grano == "dia": return f.isoformat(), f, f
    if grano == "quincena":
        if f.day <= 15: return f"{f:%Y-%m}-Q1", f.replace(day=1), f.replace(day=15)
        return f"{f:%Y-%m}-Q2", f.replace(day=16), _fin_mes(f.year, f.month)
    n = _MESES[grano]; k = (f.month - 1) // n; m0 = k * n + 1; m1 = m0 + n - 1
    etq = {"mes": f"{f:%Y-%m}", "bimestre": f"{f.year}-B{k + 1}", "trimestre": f"{f.year}-T{k + 1}",
           "semestre": f"{f.year}-S{k + 1}", "anio": f"{f.year}"}[grano]
    return etq, date(f.year, m0, 1), _fin_mes(f.year, m1)


def _meses(i, f):
    a, m = i.year, i.month; out = []
    while (a, m) <= (f.year, f.month):
        out.append(f"{a}-{m:02d}"); a, m = (a + (m == 12), m % 12 + 1)
    return out


def agrupar(eventos, lineas, resultados, desde, hasta, grano, valores=None):
    """eventos: filas EVENTO; lineas: filas LINEA; resultados: {periodo AAAA-MM: contrato de una síntesis};
    valores: {«evento-línea»: importe} del kardex valorizado (los consumos no traen importe en la línea)."""
    from metodos.reparto_etapas import _clave
    valores = valores or {}
    if grano not in GRANOS: raise ValueError(f"grano «{grano}» no es uno de {', '.join(GRANOS)}")
    d0, d1 = _fecha(desde), _fecha(hasta)
    if d1 < d0: raise ValueError("«hasta» es anterior a «desde»")
    ev = {e["EVE_NUM"]: e for e in eventos if e.get("EVE_FEC") and d0 <= _fecha(e["EVE_FEC"]) <= d1}
    cub = {}
    def nueva(f):
        etq, i, fn = cubeta(f, grano)
        return cub.setdefault(etq, dict(etiqueta=etq, inicio=i.isoformat(), fin=fn.isoformat(), hechos={}, costo=None, nota=""))
    f = d0
    while f <= d1:                                          # todas las cubetas del rango, aunque no tengan hechos
        nueva(f); f = date.fromisoformat(cub[cubeta(f, grano)[0]]["fin"]) + timedelta(days=1)
    for l in lineas:
        e = ev.get(l.get("LIN_EVE"))
        if not e: continue
        h = nueva(_fecha(e["EVE_FEC"]))["hechos"].setdefault(str(e.get("EVE_TRX")), dict(eventos=set(), cantidad=0.0, importe=0.0))
        h["eventos"].add(e["EVE_NUM"]); h["cantidad"] += float(l.get("LIN_CAN") or 0)
        k = _clave(l.get("LIN_EVE"), l.get("LIN_NUM"))
        h["importe"] += float(l.get("LIN_MTO") or l.get("LIN_IMP") or valores.get(k)
                              or float(l.get("LIN_CAN") or 0) * float(l.get("LIN_CU_DOC") or 0))
    for c in cub.values():
        c["hechos"] = {t: dict(eventos=len(h["eventos"]), cantidad=round(h["cantidad"], 4), importe=round(h["importe"], 2))
                       for t, h in sorted(c["hechos"].items())}
        i, fn = date.fromisoformat(c["inicio"]), date.fromisoformat(c["fin"])
        if grano in ("dia", "quincena"):
            c["nota"] = "El costo completo (con indirectos) se calcula por mes: aquí solo hechos."; continue
        meses = _meses(i, fn)
        faltan = [m for m in meses if m not in resultados]
        fuera = i < d0 or fn > d1
        prod = {}
        for m in meses:
            for o in (resultados.get(m) or {}).get("objetos", []):
                p = prod.setdefault(o["producto"], dict(producto=o["producto"], cantidad=0.0, costo=0.0, ingreso=0.0))
                p["cantidad"] += o["cantidad"]; p["costo"] += o["costo_total"]; p["ingreso"] += o["ingreso"]
        for p in prod.values():
            p["costo_unitario"] = round(p["costo"] / p["cantidad"], 4) if p["cantidad"] else 0.0
            p["cantidad"], p["costo"], p["ingreso"] = round(p["cantidad"], 4), round(p["costo"], 2), round(p["ingreso"], 2)
        k = [resultados[m]["kpi"] for m in meses if m in resultados]
        c["costo"] = dict(meses=meses, completo=not faltan and not fuera, ventas=round(sum(x["ventas"] for x in k), 2),
                          costo_total=round(sum(x["costo_total"] for x in k), 2), margen_operativo=round(sum(x["margen_operativo"] for x in k), 2),
                          productos=sorted(prod.values(), key=lambda p: p["producto"]))
        if faltan: c["nota"] = "Sin resultado calculado: " + ", ".join(faltan)
        elif fuera: c["nota"] = "La cubeta excede el rango pedido: incluye meses completos fuera de él."
    return dict(grano=grano, desde=d0.isoformat(), hasta=d1.isoformat(), cubetas=[cub[k] for k in sorted(cub)])


def desde_archivos(libro, carpetas, empresa, sintesis, desde, hasta, grano):
    """Lee EVENTO/LINEA del libro y los resultados publicados {empresa}_{AAAA-MM}_{síntesis}.json de las carpetas, en orden."""
    import json
    from pathlib import Path
    import puerto_lectura as P
    t = P.leer(libro, ["EVENTO", "LINEA"]); res = {}
    for c in carpetas:
        for f in sorted(Path(c).glob(f"{empresa}_*_{sintesis}.json")):
            per = f.stem[len(empresa) + 1:len(empresa) + 8]
            if per not in res: res[per] = json.loads(f.read_text(encoding="utf-8"))
    val = {x["evento"]: abs(x["importe"]) for r in res.values() for x in r.get("kardex") or [] if x.get("importe")}
    return agrupar(t.get("EVENTO", []), t.get("LINEA", []), res, desde, hasta, grano, val)
