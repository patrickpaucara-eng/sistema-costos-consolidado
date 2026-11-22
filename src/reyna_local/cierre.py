"""Cierre del periodo (D9) y paquete de decisión sellado con aprobación (punto 7).
CIERRE = verificar + conciliar + sellar. No se borra nada: reabrir un periodo emite una NUEVA VERSIÓN del paquete que apunta a
la anterior (versionado en lugar de deshacer).
- Verificación: todos los controles del panel de calidad en las tres síntesis. Las deficiencias del dato fuente (inductores
  que no suman 100 %) se informan pero no bloquean, porque el reparto proporcional conserva el costo.
- Conciliación (un solo escritor por cifra): lo que el motor operativo acumuló en sus cuentas contra lo que calcula el costeo:
  EXISTENCIA (saldo por material y almacén) contra el saldo del kardex, y CTA_OBJ_PER.COP_PERD (merma en exceso registrada)
  contra las pérdidas anormales del costeo.
- Paquete sellado: resultados REAL/CONTABLE/ESTIMADO + conciliación + sello del libro + huella SHA-256 del contenido.
- Aprobación (perfiles del libro): EMITIDO (COSTOS) → REVISADO u OBSERVADO (CONTAB) → APROBADO u OBSERVADO (GERENCIA).
  Cada paso queda en el historial con usuario, fecha y comentario; el contenido sellado no cambia."""
from datetime import datetime
import hashlib, json, re
from pathlib import Path

from openpyxl import load_workbook

PERFIL = {"EMITIR": {"COSTOS", "PILOTO"}, "REVISAR": {"CONTAB"}, "APROBAR": {"GERENCIA"}, "OBSERVAR": {"CONTAB", "GERENCIA"}}
PASA = {("EMITIDO", "REVISAR"): "REVISADO", ("EMITIDO", "OBSERVAR"): "OBSERVADO", ("REVISADO", "APROBAR"): "APROBADO",
        ("REVISADO", "OBSERVAR"): "OBSERVADO"}


class Rechazo(Exception):
    pass


def _carpeta(base): d = Path(base) / "resultados" / "cierres"; d.mkdir(parents=True, exist_ok=True); return d


def _huella(contenido): return hashlib.sha256(json.dumps(contenido, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def _perfil(libro, usuario):
    wb = load_workbook(libro, read_only=True)
    try:
        if "USUARIO" not in wb.sheetnames: return None
        filas = list(wb["USUARIO"].iter_rows(values_only=True)); cab = list(filas[0])
        u = next((dict(zip(cab, f)) for f in filas[1:] if f and str(f[0]) == str(usuario)), None)
        perf = {u["USU_PERFIL"]} if u else set()
        if u and "USUARIO_PERFIL" in wb.sheetnames:
            perf |= {f[1] for f in wb["USUARIO_PERFIL"].iter_rows(min_row=2, values_only=True) if f and f[0] == usuario}
        return perf
    finally:
        wb.close()


def conciliar(libro, resultado):
    """Cuentas del motor operativo frente al costeo. Sin cuentas del motor (libro solo de costeo): no aplica."""
    wb = load_workbook(libro, read_only=True, data_only=True); out = []
    try:
        def tabla(n):
            if n not in wb.sheetnames: return []
            f = list(wb[n].iter_rows(values_only=True)); return [dict(zip(f[0], x)) for x in f[1:] if x and any(v not in (None, "") for v in x)] if f else []
        exi, cop, pers = tabla("EXISTENCIA"), tabla("CTA_OBJ_PER"), sorted(str(p["PER_COD"]) for p in tabla("PERIODO"))
    finally:
        wb.close()
    k = resultado.get("kardex") or []
    if exi and pers and resultado["periodo_actual"] == pers[-1]:          # el saldo del motor es el vigente: se concilia al último mes
        fin = {}
        for x in k: fin[x["material"]] = (x["saldo_cantidad"], x["saldo_importe"])
        for e in exi:
            q, v = fin.get(e["EXI_REC"], (None, None))
            if q is None: continue
            dq, dv = round(float(e["EXI_CAN"] or 0) - q, 4), round(float(e["EXI_VAL"] or 0) - v, 2)
            out.append(dict(cuenta=f"EXISTENCIA {e['EXI_REC']} / {e['EXI_ALM']}", motor=round(float(e["EXI_VAL"] or 0), 2), costeo=round(v, 2),
                            diferencia=dv, ok=abs(dq) < 1e-6 and abs(dv) <= 0.05,
                            detalle=f"cantidad motor {e['EXI_CAN']} vs kardex {q}"))
    perd_motor = sum(float(c.get("COP_PERD") or 0) for c in cop if str(c.get("COP_PER")) == resultado["periodo_actual"])
    perd_cost = sum(p["importe"] for p in resultado.get("perdidas") or [])
    if perd_motor or perd_cost:
        out.append(dict(cuenta="CTA_OBJ_PER.COP_PERD (merma en exceso)", motor=round(perd_motor, 2), costeo=round(perd_cost, 2),
                        diferencia=round(perd_motor - perd_cost, 2), ok=abs(perd_motor - perd_cost) <= 0.05, detalle="NIC 2 §16 a"))
    return out


def _bloqueantes(resultados, conc):
    malos = []
    for s, r in resultados.items():
        for c in r.get("control") or []:
            if not c["ok"] and "suma" not in c["control"]: malos.append(f"{s}: {c['control']}")
    malos += [f"Conciliación: {c['cuenta']} (diferencia {c['diferencia']})" for c in conc if not c["ok"]]
    return malos


def listar(base, empresa=None):
    out = []
    for f in sorted(_carpeta(base).glob("*.json")):
        p = json.loads(f.read_text(encoding="utf-8"))
        if empresa and p["empresa_id"] != empresa: continue
        out.append(dict(id=f.stem, empresa_id=p["empresa_id"], empresa=p["empresa"], periodo=p["periodo"], version=p["version"],
                        estado=p["estado"], huella=p["huella"], previo=p.get("previo"), historial=p["historial"]))
    return out


def emitir(base, empresa, periodo, usuario, calcular, libro, motivo=""):
    """Cierra (o reabre) el periodo: calcula las tres síntesis, verifica, concilia y sella una nueva versión."""
    if "EMITIR" not in PERFIL or not (_perfil(libro, usuario) or set()) & PERFIL["EMITIR"]:
        raise Rechazo(f"El usuario {usuario} no tiene perfil para emitir el cierre (COSTOS).")
    res = {s: calcular(base, periodo, s, empresa) for s in ("REAL", "CONTABLE", "ESTIMADO")}
    conc = conciliar(libro, res["REAL"])
    malos = _bloqueantes(res, conc)
    if malos:
        raise Rechazo("No se puede cerrar: " + "; ".join(malos[:8]))
    previas = [x for x in listar(base, empresa) if x["periodo"] == periodo]
    if previas and not motivo:
        raise Rechazo("El periodo ya tiene un cierre. Para reabrirlo indica el motivo: se emitirá una nueva versión.")
    version = 1 + max((x["version"] for x in previas), default=0)
    contenido = dict(empresa_id=empresa, empresa=res["REAL"]["empresa"]["nombre"], periodo=periodo, version=version,
                     previo=(max(previas, key=lambda x: x["version"])["huella"] if previas else None), motivo=motivo or None,
                     sello=res["REAL"].get("sello"), conciliacion=conc, resultados=res)
    h = _huella(contenido)
    paquete = dict(contenido, huella=h, estado="EMITIDO",
                   historial=[dict(accion="EMITIR", usuario=usuario, fecha=datetime.now().isoformat(timespec="seconds"), comentario=motivo or "Cierre del periodo")])
    pid = f"{empresa}_{periodo}_v{version}"
    (_carpeta(base) / f"{pid}.json").write_text(json.dumps(paquete, ensure_ascii=False), encoding="utf-8")
    return dict(id=pid, version=version, estado="EMITIDO", huella=h, conciliacion=conc)


def accion(base, pid, que, usuario, comentario, libro):
    if not re.fullmatch(r"[a-z0-9_]+_\d{4}-\d{2}_v\d+", pid): raise Rechazo("Paquete inválido.")
    f = _carpeta(base) / f"{pid}.json"
    if not f.is_file(): raise Rechazo("El paquete no existe.")
    p = json.loads(f.read_text(encoding="utf-8"))
    if que not in PERFIL or not (_perfil(libro, usuario) or set()) & PERFIL[que]:
        raise Rechazo(f"El usuario {usuario} no tiene el perfil requerido para {que.lower()} ({', '.join(sorted(PERFIL.get(que, [])))}).")
    nuevo = PASA.get((p["estado"], que))
    if not nuevo:
        requiere = sorted({e for (e, a) in PASA if a == que})
        raise Rechazo(f"No se puede {que.lower()} un paquete en estado {p['estado']} (debe estar {' o '.join(requiere) or 'en otro estado'}).")
    if que == "APROBAR" and any(h["usuario"] == usuario for h in p["historial"]):
        raise Rechazo("Separación de funciones: quien emitió o revisó no puede aprobar.")
    if verificar(base, pid)["estado"] != "INTEGRO": raise Rechazo("El contenido del paquete fue alterado: no se puede continuar.")
    p["estado"] = nuevo
    p["historial"].append(dict(accion=que, usuario=usuario, fecha=datetime.now().isoformat(timespec="seconds"), comentario=comentario or ""))
    f.write_text(json.dumps(p, ensure_ascii=False), encoding="utf-8")
    return dict(id=pid, estado=nuevo)


def verificar(base, pid):
    f = _carpeta(base) / f"{pid}.json"; p = json.loads(f.read_text(encoding="utf-8"))
    contenido = {k: v for k, v in p.items() if k not in ("huella", "estado", "historial")}
    return dict(id=pid, estado="INTEGRO" if _huella(contenido) == p["huella"] else "ALTERADO")
