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


def preparar(libro):
    """Ruta del libro listo para costear: el mismo si el kardex está completo; si no, una copia con el kardex derivado."""
    libro = Path(libro); h = hashlib.sha256(libro.read_bytes()).hexdigest()
    if h in _cache and Path(_cache[h]).is_file(): return _cache[h]
    nuevas = faltantes(libro)
    if not nuevas:
        _cache[h] = str(libro); return str(libro)
    d = Path(tempfile.mkdtemp(prefix="reyna-flujo-")); copia = d / libro.name; shutil.copy(libro, copia)
    wb = load_workbook(copia); ws = wb["KARDEX"]; cab = [c.value for c in ws[1]]
    for k in nuevas: ws.append([k.get(c) for c in cab])
    wb.save(copia); _cache[h] = str(copia); return str(copia)
