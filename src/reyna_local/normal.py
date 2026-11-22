"""Costeo normal y variaciones (punto 4).
COSTEO NORMAL: los CIF se aplican a cada orden con una TASA PREDETERMINADA × base real de la orden. La tasa viene de
TARIFA_CENTRO (tipo PRED, del centro de producción; base = inductor del centro, CEN_INDUCTOR); si el libro no la trae, se
usa la tasa histórica de los periodos anteriores (Σ CIF / Σ base). La diferencia aplicado − real es CIF SOBRE o SUB
APLICADO del periodo, que se cierra contra el costo de ventas.
VARIACIONES DEL MATERIAL: por orden y material, frente al estándar de la lista de materiales (COMPONENTE: cantidad estándar
por unidad y merma normal) y al precio estándar (TARIFA tipo STD; si no hay, el costo promedio del periodo anterior):
cantidad = (Q real − Q estándar) × P estándar; precio = (P real − P estándar) × Q real."""


def _vigente(filas, clave_per, periodo):
    v = [f for f in filas if str(f.get(clave_per) or "") <= periodo]
    return max(v, key=lambda f: str(f.get(clave_per))) if v else None


def costeo_normal(por_per, periodo, libro, P):
    t = P.leer(libro, ["CENTRO", "TARIFA_CENTRO", "MEDIDA"])
    prod = [c for c in t.get("CENTRO", []) if str(c.get("CEN_FUN") or c.get("CEN_TIPO")) == "PRD" and c.get("CEN_INDUCTOR")]
    if not prod: return None
    cen = prod[0]; base_crit = cen["CEN_INDUCTOR"]
    base = {}
    for m in t.get("MEDIDA", []):
        if m.get("MED_CRIT") == base_crit and m.get("MED_NIVEL") == "OBJ":
            base[(str(m["MED_PER"]), m["MED_DEST"])] = base.get((str(m["MED_PER"]), m["MED_DEST"]), 0.0) + float(m.get("MED_CAN") or 0)
    cif = lambda p: sum(float(v.get("CIF", 0)) for v in por_per.get(p, {}).values())
    bas = lambda p: sum(q for (pp, _), q in base.items() if pp == p)
    tar = _vigente([f for f in t.get("TARIFA_CENTRO", []) if f.get("TCE_CEN") == cen["CEN_COD"] and f.get("TCE_TIPO") == "PRED"], "TCE_PER", periodo)
    if tar:
        tasa, fuente = float(tar["TCE_VAL"]), f"TARIFA_CENTRO {tar['TCE_PER']} (presupuestada)"
    else:
        prev = [p for p in sorted(por_per) if p < periodo]
        if not prev or not sum(bas(p) for p in prev): return None
        tasa = sum(cif(p) for p in prev) / sum(bas(p) for p in prev); fuente = f"histórica {prev[0]}–{prev[-1]} (Σ CIF / Σ base)"
    filas = []
    for o, v in sorted(por_per.get(periodo, {}).items()):
        b = base.get((periodo, o), 0.0); ap = round(tasa * b, 2); real = round(float(v.get("CIF", 0)), 2)
        filas.append(dict(orden=o, base=b, cif_aplicado=ap, cif_real=real, variacion=round(ap - real, 2)))
    tv = round(sum(f["variacion"] for f in filas), 2)
    return dict(centro=cen["CEN_COD"], base=base_crit, tasa=round(tasa, 6), fuente_tasa=fuente, ordenes=filas, total_variacion=tv,
                lectura=("CIF sobreaplicado" if tv > 0 else "CIF subaplicado" if tv < 0 else "Sin variación") +
                        f": S/ {abs(tv):,.2f}; se cierra contra el costo de ventas del periodo.")


def variaciones_material(kardex_todo, periodo, libro, P, val_cu):
    """kardex_todo: filas del kardex del periodo (resultados._kardex); val_cu: no usado (precio real = importe / cantidad)."""
    t = P.leer(libro, ["COMPONENTE", "OBJETO", "TARIFA", "EVENTO"])
    cmp_ = {(c["CMP_PRO"], c["CMP_REC"]): c for c in t.get("COMPONENTE", [])}
    if not cmp_: return []
    obj = {o["OBJ_NUM"]: o for o in t.get("OBJETO", [])}
    ev_obj = {}
    for e in t.get("EVENTO", []):
        n = e.get("EVE_NUM")
        if n is not None: ev_obj[str(int(float(n)))] = e.get("EVE_OBJ")
    real = {}
    for k in kardex_todo:
        if k["movimiento"] != "SALIDA": continue
        o = ev_obj.get(str(k.get("evento") or "").split("-")[0])
        if not o: continue
        q, v = real.get((o, k["material"]), (0.0, 0.0)); real[(o, k["material"])] = (q - k["cantidad"], v - k["importe"])
    std_p = {}
    for f in t.get("TARIFA", []):
        if f.get("TAR_TIPO") == "STD" and str(f.get("TAR_PER") or "") <= periodo:
            if f["TAR_REC"] not in std_p or str(f["TAR_PER"]) > std_p[f["TAR_REC"]][0]: std_p[f["TAR_REC"]] = (str(f["TAR_PER"]), float(f["TAR_VAL"]))
    out = []
    for (o, rec), (qr, vr) in sorted(real.items()):
        ob = obj.get(o) or {}; c = cmp_.get((str(ob.get("OBJ_PRO")), rec))
        if not c: continue
        qs = float(c.get("CMP_CAN_EST") or 0) * float(ob.get("OBJ_CAN") or 0) * (1 + float(c.get("CMP_MERMA") or 0) / 100)
        pr = vr / qr if qr else 0.0
        ps, fuente = (std_p[rec][1], f"TARIFA STD {std_p[rec][0]}") if rec in std_p else (_precio_anterior(kardex_todo, rec, pr), "promedio del periodo anterior")
        out.append(dict(orden=o, material=rec, q_estandar=round(qs, 4), q_real=round(qr, 4), p_estandar=round(ps, 6), p_real=round(pr, 6),
                        var_cantidad=round((qr - qs) * ps, 2), var_precio=round((pr - ps) * qr, 2), var_total=round(vr - qs * ps, 2),
                        fuente_precio=fuente))
    return out


def _precio_anterior(kardex_todo, rec, defecto):
    ini = [k for k in kardex_todo if k["material"] == rec]
    if not ini: return defecto
    k = ini[0]; q = k["saldo_cantidad"] - k["cantidad"]; v = k["saldo_importe"] - k["importe"]   # saldo con que abrió el periodo
    return v / q if q else defecto
