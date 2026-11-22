"""Flujo único: el mismo libro DBD se OPERA (transacciones del motor operativo: T14 compra, T15 consumo…) y se COSTEA.
El motor operativo registra EVENTO/LINEA y actualiza EXISTENCIA; el kardex es DERIVADO de esos eventos (MCD: el kardex no se
digita, sale de los hechos) según TRX_KARDEX (factor de cantidad y de valor por transacción). Aquí se derivan las filas de
kardex que faltan para que el costeo (ALG-01, P1) vea cada movimiento. No modifica el libro: trabaja sobre una copia."""
import hashlib, json, shutil, tempfile
from pathlib import Path

from openpyxl import load_workbook

RECIBOS = "_ReynaRecibos"
_cache = {}


def _tabla(wb, n):
    if n not in wb.sheetnames: return [], []
    filas = list(wb[n].iter_rows(values_only=True))
    if not filas: return [], []
    cab = list(filas[0]); return cab, [dict(zip(cab, f)) for f in filas[1:] if f and any(v not in (None, "") for v in f)]


def _num(v):
    try: return float(v)
    except (TypeError, ValueError): return None


def faltantes(libro):
    """Filas de KARDEX que corresponden a líneas de transacciones con efecto en almacén y aún no están en el kardex."""
    wb = load_workbook(libro, read_only=True, data_only=True)
    try:
        _, trk = _tabla(wb, "TRX_KARDEX"); _, eve = _tabla(wb, "EVENTO"); _, lin = _tabla(wb, "LINEA"); _, kdx = _tabla(wb, "KARDEX")
        _, rec = _tabla(wb, "RECURSO"); _, tre = _tabla(wb, "TIPO_RECURSO"); _, exi = _tabla(wb, "EXISTENCIA"); _, rcb = _tabla(wb, RECIBOS)
    finally:
        wb.close()
    inv_tipo = {t["TRE_COD"] for t in tre if str(t.get("TRE_INV") or "").upper() == "S"}
    inventariable = {r["REC_COD"] for r in rec if r.get("REC_TRE") in inv_tipo}
    efectos = {}
    for t in trk:
        efectos.setdefault(str(t["TKX_TRX"]), []).append(t)
    ya = {(int(_num(k["KDX_EVE"]) or 0), int(_num(k["KDX_LIN"]) or 0)) for k in kdx if _num(k.get("KDX_EVE")) is not None}
    almacen_de = {}                                      # almacén habitual de cada recurso (kardex y existencias)
    for k in kdx: almacen_de.setdefault(k.get("KDX_REC"), k.get("KDX_ALM"))
    for e in exi: almacen_de.setdefault(e.get("EXI_REC"), e.get("EXI_ALM"))
    cabeceras = {}                                       # la trama original de cada operación (trae ALM, ALM2…)
    for r in rcb:
        try:
            cmd = json.loads(r.get("command") or "{}"); resp = json.loads(r.get("response") or "{}")
            n = resp.get("event") or resp.get("evento") or resp.get("EVE_NUM")
            if n is not None: cabeceras[int(float(n))] = cmd.get("header", {})
        except (TypeError, ValueError):
            continue
    ev = {int(_num(e["EVE_NUM"])): e for e in eve if _num(e.get("EVE_NUM")) is not None}
    nuevas = []
    for l in lin:
        ne, nl = int(_num(l.get("LIN_EVE")) or 0), int(_num(l.get("LIN_NUM")) or 0)
        e = ev.get(ne)
        if not e or (ne, nl) in ya or l.get("LIN_REC") not in inventariable: continue
        for t in efectos.get(str(e.get("EVE_TRX")), []):
            fc = _num(t.get("TKX_FC")) or 0
            if fc == 0: continue
            alm = cabeceras.get(ne, {}).get(t.get("TKX_ALM")) or almacen_de.get(l["LIN_REC"])
            can = fc * (_num(l.get("LIN_CAN")) or 0)
            val = round(_num(l.get("LIN_MTO")) or 0, 2) if can > 0 else None     # las entradas llevan su valor; las salidas se valúan (ALG-01)
            nuevas.append(dict(KDX_EVE=ne, KDX_LIN=nl, KDX_ALM=alm, KDX_PER=e.get("EVE_PER"), KDX_FEC=e.get("EVE_FEC"),
                               KDX_TRX=e.get("EVE_TRX"), KDX_CPB=e.get("EVE_CPB") or f"{e.get('EVE_TRX')}-{ne}", KDX_REC=l["LIN_REC"],
                               KDX_CAN=can, KDX_VAL=val))
    return nuevas


def ajustes_compra(libro, sintesis="REAL"):
    """Costo de adquisición completo (D-11, punto 5). Devuelve (filas de ajuste de valor para el kardex, ajustes a gasto,
    centros de compras a excluir del reparto en esta síntesis).
    - FLETE del documento: líneas de recursos capitalizables (TIPO_RECURSO.TRE_ELE = CAP) en el mismo evento de compra se
      prorratean por valor entre sus líneas de inventario (ambas síntesis: costo directamente atribuible, NIC 2 §11).
    - T14.2 ajuste tardío (flete u otro costo que llega después): se prorratea por valor entre las líneas de inventario del
      evento de origen (LINEA.LIN_ORI); la parte del lote que sigue en existencia aumenta su valor en la fecha del ajuste; la
      parte ya consumida no reabre meses cerrados: va a gasto del periodo del ajuste.
    - Centro de COMPRAS (CENTRO tipo COM): en REAL su costo del periodo se reparte entre las compras del periodo por valor y
      queda en el inventario (se rastrea hasta las órdenes vía kardex). En CONTABLE no se capitaliza (indirecto): es gasto."""
    wb = load_workbook(libro, read_only=True, data_only=True)
    try:
        _, eve = _tabla(wb, "EVENTO"); _, lin = _tabla(wb, "LINEA"); _, kdx = _tabla(wb, "KARDEX"); _, rec = _tabla(wb, "RECURSO")
        _, tre = _tabla(wb, "TIPO_RECURSO"); _, cen = _tabla(wb, "CENTRO")
    finally:
        wb.close()
    ele = {t["TRE_COD"]: str(t.get("TRE_ELE") or "") for t in tre}; inv_t = {t["TRE_COD"] for t in tre if str(t.get("TRE_INV") or "").upper() == "S"}
    tipo = {r["REC_COD"]: r.get("REC_TRE") for r in rec}
    es_cap = lambda r_: ele.get(tipo.get(r_)) == "CAP"; es_inv = lambda r_: tipo.get(r_) in inv_t
    ev = {int(_num(e["EVE_NUM"])): e for e in eve if _num(e.get("EVE_NUM")) is not None}
    por_ev = {}
    for l in lin: por_ev.setdefault(int(_num(l.get("LIN_EVE")) or 0), []).append(l)
    alm_de = {}
    for k in kdx: alm_de.setdefault(k.get("KDX_REC"), k.get("KDX_ALM"))
    mto = lambda l: _num(l.get("LIN_MTO")) if _num(l.get("LIN_MTO")) is not None else (_num(l.get("LIN_CAN")) or 0) * (_num(l.get("LIN_CU_DOC")) or 0)
    filas, gasto = [], []
    def prorratear(n_ev, monto, fecha, periodo, motivo, n_ajuste, split=False, trx="AJV"):
        dest = [l for l in por_ev.get(n_ev, []) if es_inv(l.get("LIN_REC"))]
        T = sum(mto(l) or 0 for l in dest)
        if not dest or not T: return
        for j, l in enumerate(dest, 1):
            parte = monto * (mto(l) or 0) / T; r_ = l["LIN_REC"]; alm = (ev.get(n_ev) or {}).get("EVE_ALM") or alm_de.get(r_)
            queda = 1.0
            if split:                                  # fracción del lote aún en existencia a la fecha del ajuste
                q0 = _num(l.get("LIN_CAN")) or 0
                stock = sum(_num(k.get("KDX_CAN")) or 0 for k in kdx if k.get("KDX_REC") == r_ and int(_num(k.get("KDX_FEC")) or 0) <= int(fecha))
                queda = max(0.0, min(1.0, stock / q0)) if q0 else 0.0
            if parte * queda:
                filas.append(dict(KDX_EVE=n_ajuste, KDX_LIN=9000 + j, KDX_ALM=alm, KDX_PER=periodo, KDX_FEC=fecha, KDX_TRX=trx,
                                  KDX_CPB=motivo, KDX_REC=r_, KDX_CAN=0, KDX_VAL=round(parte * queda, 2)))
            if split and parte * (1 - queda):
                gasto.append(dict(periodo=periodo, recurso=r_, motivo=motivo, importe=round(parte * (1 - queda), 2)))
    # 1) flete en el mismo documento
    for n, ls in por_ev.items():
        cap = sum(mto(l) or 0 for l in ls if es_cap(l.get("LIN_REC")))
        e = ev.get(n)
        if cap and e and str(e.get("EVE_TRX")) == "T14":
            prorratear(n, cap, e.get("EVE_FEC"), e.get("EVE_PER"), f"Flete del documento {e.get('EVE_CPB') or n}", n)
    # 2) T14.2 ajuste tardío
    for n, e in ev.items():
        if str(e.get("EVE_TRX")) != "T14.2": continue
        for l in por_ev.get(n, []):
            ori = int(_num(l.get("LIN_ORI")) or 0)
            if ori: prorratear(ori, mto(l) or 0, e.get("EVE_FEC"), e.get("EVE_PER"), f"T14.2 ajuste del documento {ori}", n, split=True)
    # 3) centro de compras
    com = {c["CEN_COD"] for c in cen if str(c.get("CEN_TIPO") or c.get("CEN_FUN")) == "COM"}
    if com and sintesis != "CONTABLE":
        costo_per = {}
        for n, e in ev.items():
            if e.get("EVE_CEN") in com:
                costo_per[e.get("EVE_PER")] = costo_per.get(e.get("EVE_PER"), 0.0) + sum(mto(l) or 0 for l in por_ev.get(n, []))
        for per, total in costo_per.items():
            compras = [(n, e) for n, e in ev.items() if str(e.get("EVE_TRX")) == "T14" and e.get("EVE_PER") == per]
            T = sum(mto(l) or 0 for n, _ in compras for l in por_ev.get(n, []) if es_inv(l.get("LIN_REC")))
            for n, e in compras:
                v = sum(mto(l) or 0 for l in por_ev.get(n, []) if es_inv(l.get("LIN_REC")))
                if T and v: prorratear(n, total * v / T, e.get("EVE_FEC"), per, "Costo indirecto de compras (centro COM)", n, trx="AJV_IND")
    return filas, gasto, (com if sintesis != "CONTABLE" else set())


def preparar(libro, sintesis="REAL"):
    """Ruta del libro listo para costear en la síntesis dada: kardex derivado de las transacciones, ajustes de valor del costo
    de adquisición y, en REAL, el centro de compras fuera del reparto (ya está en el inventario). Sin cambios: el mismo libro."""
    libro = Path(libro); h = hashlib.sha256(libro.read_bytes()).hexdigest() + ("C" if sintesis == "CONTABLE" else "R")
    if h in _cache and Path(_cache[h]).is_file(): return _cache[h]
    nuevas = faltantes(libro)
    ajustes, gasto, com_fuera = ajustes_compra(libro, sintesis)
    com_todos = _centros_com(libro)
    if not nuevas and not ajustes and not gasto and not com_todos:
        _cache[h] = str(libro); return str(libro)
    d = Path(tempfile.mkdtemp(prefix="reyna-flujo-")); copia = d / libro.name; shutil.copy(libro, copia)
    wb = load_workbook(copia); ws = wb["KARDEX"]; cab = [c.value for c in ws[1]]
    for k in nuevas + ajustes: ws.append([k.get(c) for c in cab])
    if com_fuera:                                    # REAL: el costo de compras ya vive en el inventario
        ce = [c.value for c in wb["EVENTO"][1]]; fuera = set()
        for f in wb["EVENTO"].iter_rows(min_row=2):
            if f[ce.index("EVE_CEN")].value in com_fuera: fuera.add(int(_num(f[ce.index("EVE_NUM")].value) or 0))
        cl = [c.value for c in wb["LINEA"][1]]
        for f in wb["LINEA"].iter_rows(min_row=2):
            if int(_num(f[cl.index("LIN_EVE")].value) or 0) in fuera:
                f[cl.index("LIN_CAN")].value = 0; f[cl.index("LIN_MTO")].value = 0
    elif com_todos:                                  # CONTABLE: el centro de compras es gasto administrativo del periodo
        cc = [c.value for c in wb["CENTRO"][1]]
        for f in wb["CENTRO"].iter_rows(min_row=2):
            if f[cc.index("CEN_COD")].value in com_todos:
                for col in ("CEN_TIPO", "CEN_FUN"):
                    if col in cc: f[cc.index(col)].value = "ADM"
    if gasto:
        g = wb.create_sheet("_AJUSTES_GASTO"); g.append(["periodo", "recurso", "motivo", "importe"])
        for x in gasto: g.append([x["periodo"], x["recurso"], x["motivo"], x["importe"]])
    wb.save(copia); _cache[h] = str(copia); return str(copia)


def _centros_com(libro):
    wb = load_workbook(libro, read_only=True)
    try:
        _, cen = _tabla(wb, "CENTRO")
    finally:
        wb.close()
    return {c["CEN_COD"] for c in cen if str(c.get("CEN_TIPO") or c.get("CEN_FUN")) == "COM"}
