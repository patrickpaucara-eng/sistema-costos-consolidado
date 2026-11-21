# -*- coding: utf-8 -*-
"""I-10 · C · COSTO A LA FECHA (OT-097, «Contratos para las pruebas» §C). Consulta de SOLO LECTURA.

calcular(hechos, per, emp, corte) → {OT: {MD, MOD, SD, CIF_ESTIMADO, REAL_A_LA_FECHA, TOTAL_CON_ESTIMADO, corte, rotulo}}

- hechos = {tabla física: [ {columna: valor} ]} como quedan en el motor (H-1).
- Solo cuentan LINEA cuyo EVENTO (EVE_EMP = emp, EVE_PER = per, EVE_OBJ = un OBJETO de emp) tiene EVE_FEC ≤ corte.
- MD (TRE_ELE MAT), MOD (TRE_ELE MOD o PD, H-6), SD (TRE_ELE SD): LIN_MTO tal cual lo dejó el motor
  (promedio móvil para materiales, tarifa REAL vigente para personal). No se revaloriza nada.
- CIF_ESTIMADO = Σ por recurso de capacidad (TRE_CAP = 1, no MOD/PD; H-3) de tasa TARIFA(TAR_TIPO = EST,
  TAR_REC = recurso, TAR_PER = per, TAR_EMP = emp) × LIN_CAN fechada ≤ corte. MEDIDA es mensual y sin fecha:
  nunca se usa para el monto; si el objeto solo tiene el inductor en MEDIDA → 0 y «inductor sin fecha».
  Hay horas fechadas pero no hay tasa EST → 0 y «sin tasa estimada». Nunca prorratea ni inventa.
- Una OT sin eventos ≤ corte no aparece (H-5). Puro: no escribe, no modifica `hechos`.
"""
FICHA = dict(nombre="COSTO_A_LA_FECHA", version="1.0", vigente_desde="2026-11-15", eje="EVENTO", objetivo="ESTIMADO",
             que_hace="Costo provisional de cada OT hasta una fecha de corte: real (MD+MOD+SD) + indirecto estimado",
             formula="REAL = Σ LIN_MTO (EVE_FEC ≤ corte); CIF_EST = Σ tasa EST × horas de capacidad fechadas ≤ corte",
             fuente="OT-097 §C; Horngren cap. 4 (tasa predeterminada); NIC 2 §25 (promedio)",
             supuestos="Valuación promedio móvil ya aplicada por el motor; MEDIDA no tiene fecha",
             limites="No publica ni escribe; el CIF estimado no es costo oficial")

R = 2  # redondeo de montos publicados


DEVUELVEN = {"T16"}          # [ARQ] X3-2: la devolución al almacén resta del objeto (el motor guarda LIN_MTO positivo)


def _f(x):
    try:
        return float(x or 0)
    except (TypeError, ValueError):
        return 0.0


def _i(x):
    try:
        return int(float(x))
    except (TypeError, ValueError):
        return None


def _s(x):
    return "" if x is None else str(x).strip()


def calcular(hechos, per, emp, corte):
    corte_i = _i(corte)
    per, emp = _s(per), _s(emp)
    g = lambda t: hechos.get(t) or []

    objetos = {_s(o.get("OBJ_NUM")) for o in g("OBJETO")
               if _s(o.get("OBJ_NUM")) and (not _s(o.get("OBJ_EMP")) or _s(o.get("OBJ_EMP")) == emp)}
    tre = {_s(t.get("TRE_COD")): t for t in g("TIPO_RECURSO")}
    rec_tre = {_s(r.get("REC_COD")): tre.get(_s(r.get("REC_TRE")), {}) for r in g("RECURSO")}
    tasa = {}
    for t in g("TARIFA"):
        if (_s(t.get("TAR_TIPO")) == "EST" and _s(t.get("TAR_PER")) == per
                and (not _s(t.get("TAR_EMP")) or _s(t.get("TAR_EMP")) == emp)):
            tasa[_s(t.get("TAR_REC"))] = _f(t.get("TAR_VAL"))

    eventos = {}
    for e in g("EVENTO"):
        fec = _i(e.get("EVE_FEC"))
        ot = _s(e.get("EVE_OBJ"))
        if (ot in objetos and _s(e.get("EVE_EMP")) == emp and _s(e.get("EVE_PER")) == per
                and fec is not None and corte_i is not None and fec <= corte_i):
            eventos[_i(e.get("EVE_NUM"))] = (ot, -1.0 if _s(e.get("EVE_TRX")) in DEVUELVEN else 1.0)

    acum = {}
    for l in g("LINEA"):
        ev = eventos.get(_i(l.get("LIN_EVE")))
        if ev is None:
            continue
        ot, sg = ev
        t = rec_tre.get(_s(l.get("LIN_REC")), {})
        ele = _s(t.get("TRE_ELE")).upper()
        a = acum.setdefault(ot, dict(MD=0.0, MOD=0.0, SD=0.0, horas={}))
        if ele == "MAT":
            a["MD"] += sg * _f(l.get("LIN_MTO"))
        elif ele in ("MOD", "PD"):
            a["MOD"] += sg * _f(l.get("LIN_MTO"))
        elif ele == "SD":
            a["SD"] += sg * _f(l.get("LIN_MTO"))
        elif ele == "IND" and _i(t.get("TRE_CAP")) == 1:
            r = _s(l.get("LIN_REC"))
            a["horas"][r] = a["horas"].get(r, 0.0) + sg * _f(l.get("LIN_CAN"))
        # PT (entrada de producción) y otros: no son costo del objeto

    con_medida = {}
    for m in g("MEDIDA"):
        if (_s(m.get("MED_PER")) == per and _s(m.get("MED_EMP")) == emp
                and _s(m.get("MED_NIVEL")) == "OBJ" and _f(m.get("MED_CAN"))):
            con_medida.setdefault(_s(m.get("MED_DEST")), set()).add(_s(m.get("MED_CRIT")))

    prefijo = f"Provisional al {corte_i}: real + indirecto estimado"
    out = {}
    for ot in sorted(acum):
        a = acum[ot]
        cif, avisos = 0.0, []
        sin_tasa = sorted(r for r in a["horas"] if r not in tasa)
        cif = sum(tasa[r] * q for r, q in a["horas"].items() if r in tasa)
        if sin_tasa:
            avisos.append("sin tasa estimada (" + ", ".join(sin_tasa) + ")")
        solo_medida = sorted(c for c in con_medida.get(ot, ()) if c not in a["horas"])
        if solo_medida:
            avisos.append("inductor sin fecha (" + ", ".join(solo_medida) + ")")
        md, mod, sd = round(a["MD"], R), round(a["MOD"], R), round(a["SD"], R)
        real = round(md + mod + sd, R)
        cif = round(cif, R)
        out[ot] = dict(MD=md, MOD=mod, SD=sd, CIF_ESTIMADO=cif, REAL_A_LA_FECHA=real,
                       TOTAL_CON_ESTIMADO=round(real + cif, R), corte=corte_i,
                       rotulo=prefijo + ("" if not avisos else " · " + " · ".join(avisos)))
    return out
