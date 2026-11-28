# -*- coding: utf-8 -*-
"""OT-015 · Fábrica de datos sintéticos con VERDAD conocida (y OT-044/T-126: CHOQUES).
Genera, desde DBD_4 y con SEMILLA, un estado de HECHOS coherente (PK/FK de DBD_4) + `verdad.json` + `series.csv`.
Salida: carpeta dada (nunca `fuente/`): estado.xlsx (una hoja por tabla), series.csv, verdad.json.
Uso: python -m analitica.fabrica CARPETA [--periodos N] [--ordenes M] [--semilla S] [--deriva K:PCT] [--choques]
HECHOS (nunca resultados): consumo real (LIN_CAN), exceso sobre lo esperado (LIN_EXC), precio del documento (LIN_CU_DOC), horas productivas (CCA_HORAS)
y el gasto del periodo por centro (T17 «Costo de un centro»: EVE_CEN + LIN_CAN=1 + LIN_CU_DOC=monto). El ocio mueve las horas productivas con el mismo gasto.
Los HECHOS NO llevan columnas RESULTADO (CCA_CST, LIN_CU, LIN_MTO van vacías): la verdad vive solo en verdad.json y series.csv."""
import argparse, csv, io, json, os, random, re, shutil, sys, zipfile
from collections import OrderedDict
from openpyxl import Workbook, load_workbook

import rutas                                           # OT-028: resolución única de rutas
DBD = os.path.join(rutas.FUENTE, "DBD_Fuente.xlsx")
EMP = "B"
TIPOS_CHOQUE = ("precio", "cantidad", "eficiencia", "ocio")

# ÚNICO diccionario de la VERDAD (valor por defecto de `generar(..., verdad=None)`; un dict parcial se fusiona nivel a nivel).
VERDAD = {
    "receta": {"MP1": 2.0, "MP2": 0.5, "MP3": 1.2},        # cantidad de receta por unidad de objeto (referencia física, no costo)
    "precio0": {"MP1": 4.0, "MP2": 12.5, "MP3": 7.2},      # costo unitario real inicial por recurso
    "merma0": {"MP1": 0.03, "MP2": 0.05, "MP3": 0.02},     # tasa de merma esperada por recurso
    "centros": {"C01": {"fijo": 8000.0, "var": 14.0, "h_orden": 1.5}, "C02": {"fijo": 5000.0, "var": 9.0, "h_orden": 0.8}},  # CIF fijo y variable/h
    "sigma": {"merma": 0.01, "precio": 0.01, "horas": 0.05},  # ruido de los hechos
    "uso_capacidad": 0.8,                                  # horas medias / capacidad práctica; la normal = uso_capacidad × la práctica
    "magnitud_choque": {"precio": 0.25, "cantidad": 0.30, "eficiencia": 0.04, "ocio": 0.25},   # ocio = fracción de las horas pagadas que no producen
}


def _verdad(v):
    base = json.loads(json.dumps(VERDAD))
    for k, x in (v or {}).items():
        if k not in base: raise ValueError(f"parámetro de verdad desconocido: {k}")
        if isinstance(base[k], dict) and isinstance(x, dict):
            for kk, xx in x.items(): base[k][kk] = dict(base[k].get(kk, {}), **xx) if isinstance(xx, dict) and isinstance(base[k].get(kk), dict) else xx
        else: base[k] = x
    return base


def _tablas():
    """{tabla: [columnas en el orden de DBD_4]} leído de la hoja DBD_4_Modelo_Interno."""
    t = OrderedDict()
    for r in load_workbook(DBD, read_only=True)["DBD_4_Modelo_Interno"].iter_rows(min_row=5, values_only=True):
        if r and r[0]: t.setdefault(r[0], []).append(r[3])
    return t


def _periodos(n):
    return [f"{2026 + i // 12}-{i % 12 + 1:02d}" for i in range(n)]


def _choques(semilla, n_per, activos, V):
    """Choques inyectados: uno por tipo, en periodos distintos (≥ 1) y de un flujo aleatorio INDEPENDIENTE del de los datos."""
    if not activos: return []
    if n_per < len(TIPOS_CHOQUE) + 1: raise ValueError(f"los choques piden al menos {len(TIPOS_CHOQUE) + 1} periodos (el 0 queda limpio)")
    g = random.Random(f"choques-{semilla}")
    ks = g.sample(range(1, n_per), len(TIPOS_CHOQUE))
    mag = V["magnitud_choque"]
    out = []
    for tipo, k in zip(TIPOS_CHOQUE, ks):
        c = {"tipo": tipo, "periodo_idx": k, "magnitud": mag[tipo]}
        if tipo in ("precio", "eficiencia"): c["recurso"] = g.choice(sorted(V["receta"]))
        if tipo == "ocio": c["centro"] = g.choice(sorted(V["centros"]))
        out.append(c)
    return out


def generar(carpeta, periodos=6, ordenes=50, semilla=7, deriva=None, choques=False, verdad=None):
    """deriva = (k, pct): desde el periodo k todos los precios cambian de nivel en pct. verdad = dict parcial que pisa a VERDAD. Devuelve la verdad (dict)."""
    V = _verdad(verdad); RECETA, PRECIO0, MERMA0, CENTROS, SG = V["receta"], V["precio0"], V["merma0"], V["centros"], V["sigma"]
    rng = random.Random(semilla); tablas = _tablas(); T = {t: [] for t in tablas}
    def fila(t, **kv):
        mal = set(kv) - set(tablas[t])
        if mal: raise ValueError(f"columnas que no están en DBD_4.{t}: {sorted(mal)}")
        T[t].append([kv.get(c) for c in tablas[t]])
    pers = _periodos(periodos); ch = _choques(semilla, periodos, choques, V)
    fila("EMPRESA", EMP_COD=EMP, EMP_NOM="Empresa sintética", EMP_MON_FUN="PEN")
    fila("TIPO_RECURSO", TRE_COD="MAT", TRE_ELE="MAT", TRE_CAP=0, TRE_INV="S")
    for r in RECETA: fila("RECURSO", REC_COD=r, REC_DES=f"Insumo {r}", REC_TRE="MAT", REC_UNI="KG", REC_COMP="VARIABLE", REC_ACTIVO="S")
    cap = {c: round(ordenes * v["h_orden"] / V["uso_capacidad"], 2) for c, v in CENTROS.items()}   # capacidad práctica: 80 % de uso medio
    for c in CENTROS: fila("CENTRO", CEN_COD=c, CEN_EMP=EMP, CEN_FUN="PRD", CEN_CAP_PRA=cap[c], CEN_CAP_NOR=round(cap[c] * V["uso_capacidad"], 2), CEN_ORD=0, CEN_ACTIVO="S", CEN_TIPO="PRO")
    for r, q in RECETA.items(): fila("COMPONENTE", CMP_PRO="PROD1", CMP_REC=r, CMP_CAN_EST=q, CMP_MERMA=round(MERMA0[r] * 100, 2))
    cmp_merma = {r: round(MERMA0[r] * 100, 2) for r in RECETA}
    for i, p in enumerate(pers): fila("PERIODO", PER_COD=p, PER_EMP=EMP, PER_INI=int(p[:4]) * 10000 + int(p[5:]) * 100 + 1, PER_FIN=int(p[:4]) * 10000 + int(p[5:]) * 100 + 28, PER_EST="A")
    def hay(tipo, k, **w): return [c for c in ch if c["tipo"] == tipo and c["periodo_idx"] == k and all(c.get(a) == b for a, b in w.items())]
    sv, ev, obj = [], 0, 0
    verdad_out = {"semilla": semilla, "parametros": V, "periodos": pers, "ordenes_por_periodo": ordenes,
              "recursos": {r: {"precio_base": PRECIO0[r], "merma": MERMA0[r], "receta_unitaria": RECETA[r]} for r in RECETA},
              "centros": {c: dict(v, cap_practica=cap[c]) for c, v in CENTROS.items()},
              "deriva": None if not deriva else {"periodo_idx": deriva[0], "pct": deriva[1]}, "choques": ch,
              "por_periodo": {}, "nota": "choque ocio = fracción de las horas pagadas que no producen (CCA_HORAS baja, el gasto T17 no); ocio_h = capacidad práctica − horas productivas"}
    for k, per in enumerate(pers):
        fec = int(per[:4]) * 10000 + int(per[5:]) * 100 + 15
        nivel = 1 + (deriva[1] if deriva and k >= deriva[0] else 0)
        vp = {"precio": {}, "merma": {}, "consumo": {}, "cif": {}, "horas": {}, "ocio_h": {}, "horas_pagadas": {}}
        cant_f = 1 + sum(c["magnitud"] for c in hay("cantidad", k))
        unidades, consumo = 0.0, dict.fromkeys(RECETA, 0.0)
        merma_k = {r: MERMA0[r] + sum(c["magnitud"] for c in hay("eficiencia", k, recurso=r)) for r in RECETA}
        precio_k = {r: PRECIO0[r] * nivel * (1 + sum(c["magnitud"] for c in hay("precio", k, recurso=r))) for r in RECETA}
        for r in RECETA:                                                         # compras T14: 2 por recurso y periodo
            for j in range(2):
                ev += 1; cu = precio_k[r] * (1 + rng.gauss(0, SG["precio"])); q = round(ordenes * 100 * RECETA[r] * cant_f / 2, 2)
                fila("EVENTO", EVE_NUM=ev, EVE_TRX="T14", EVE_FEC=fec, EVE_EMP=EMP, EVE_PER=per, EVE_MON="PEN", EVE_TC=1, EVE_ALM="ALM1")
                fila("LINEA", LIN_EVE=ev, LIN_NUM=1, LIN_REC=r, LIN_CAN=q, LIN_CU_DOC=round(cu, 4))
                sv.append(("PRECIO_COMPRA", per, r, round(cu, 4)))
        horas, pagadas = dict.fromkeys(CENTROS, 0.0), dict.fromkeys(CENTROS, 0.0)
        of = {c: sum(x["magnitud"] for x in hay("ocio", k, centro=c)) for c in CENTROS}      # fracción de las horas pagadas sin producir
        for o in range(ordenes):                                                 # órdenes y consumos
            obj += 1; on = f"OP{obj:07d}"; can = round(rng.randint(50, 150) * cant_f); unidades += can
            fila("OBJETO", OBJ_NUM=on, OBJ_EMP=EMP, OBJ_PRO="PROD1", OBJ_CAN=can, OBJ_EST="C", OBJ_TIPO="ORDEN")
            for c, v in CENTROS.items():
                hp = round(v["h_orden"] * (1 + rng.gauss(0, SG["horas"])), 3); h = round(hp * (1 - min(1.0, of[c])), 3); pagadas[c] += hp; horas[c] += h
                fila("CONS_CAP", CCA_OBJ=on, CCA_CEN=c, CCA_PER=per, CCA_EMP=EMP, CCA_HORAS=h)
            for n, r in enumerate(RECETA):
                ev += 1; rec = RECETA[r] * can; real = round(rec * (1 + merma_k[r] + rng.gauss(0, SG["merma"])), 4); consumo[r] += real
                exc = round(real - RECETA[r] * can * (1 + cmp_merma[r] / 100), 4)           # exceso sobre lo esperado (con signo), como M-F-EXCESO
                fila("EVENTO", EVE_NUM=ev, EVE_TRX="T20", EVE_FEC=fec, EVE_EMP=EMP, EVE_PER=per, EVE_OBJ=on, EVE_MON="PEN", EVE_TC=1, EVE_ALM="ALM1")
                fila("LINEA", LIN_EVE=ev, LIN_NUM=1, LIN_REC=r, LIN_CAN=real, LIN_EXC=exc)
        for r in RECETA:
            vp["precio"][r], vp["merma"][r], vp["consumo"][r] = round(precio_k[r], 4), round(merma_k[r], 4), round(consumo[r], 2)
            sv += [("PRECIO_VERDAD", per, r, round(precio_k[r], 4)), ("CONSUMO", per, r, round(consumo[r], 2)), ("MERMA_VERDAD", per, r, round(merma_k[r], 4))]
        cif_tot = 0.0
        for c, v in CENTROS.items():
            ocio = max(0.0, cap[c] - horas[c]); cif = v["fijo"] + v["var"] * pagadas[c]; cif_tot += cif      # el CIF se paga por las horas pagadas, produzcan o no
            vp["cif"][c], vp["horas"][c], vp["ocio_h"][c], vp["horas_pagadas"][c] = round(cif, 2), round(horas[c], 3), round(ocio, 3), round(pagadas[c], 3)
            ev += 1; fila("EVENTO", EVE_NUM=ev, EVE_TRX="T17", EVE_FEC=fec, EVE_EMP=EMP, EVE_PER=per, EVE_CEN=c, EVE_MON="PEN", EVE_TC=1)     # gasto del periodo por centro (HECHO)
            fila("LINEA", LIN_EVE=ev, LIN_NUM=1, LIN_CAN=1, LIN_CU_DOC=round(cif, 2))
            sv += [("CIF", per, c, round(cif, 2)), ("HORAS", per, c, round(horas[c], 3)), ("OCIO_H", per, c, round(ocio, 3))]
        costo = (sum(consumo[r] * precio_k[r] for r in RECETA) + cif_tot) / unidades
        vp["costo_unitario"], vp["unidades"] = round(costo, 4), unidades; sv.append(("COSTO_UNITARIO", per, "PROD1", round(costo, 4)))
        verdad_out["por_periodo"][per] = vp
    os.makedirs(carpeta, exist_ok=True)
    wb = Workbook(write_only=True)
    for t, filas in T.items():
        ws = wb.create_sheet(t[:31]); ws.append(tablas[t]); [ws.append(f) for f in filas]
    wb.properties.created = wb.properties.modified = __import__("datetime").datetime(2026, 1, 1)
    buf = io.BytesIO(); wb.save(buf); buf.seek(0)
    with zipfile.ZipFile(buf) as zi, zipfile.ZipFile(os.path.join(carpeta, "estado.xlsx"), "w", zipfile.ZIP_DEFLATED) as zo:   # fecha fija en el zip: archivos idénticos
        for it in zi.infolist():
            dato = zi.read(it.filename)
            if it.filename == "docProps/core.xml":      # openpyxl reescribe la hora de guardado al salvar: se fija (determinismo sin reloj)
                dato = re.sub(rb"(<dcterms:(?:created|modified)[^>]*>)[^<]*", rb"\g<1>2026-01-01T00:00:00Z", dato)
            zo.writestr(zipfile.ZipInfo(it.filename, (2026, 1, 1, 0, 0, 0)), dato, zipfile.ZIP_DEFLATED)
    with open(os.path.join(carpeta, "series.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n"); w.writerow(["TIPO", "PERIODO", "CLAVE", "VALOR"]); w.writerows(sv)
    with open(os.path.join(carpeta, "verdad.json"), "w", encoding="utf-8") as f: json.dump(verdad_out, f, indent=1, sort_keys=True, ensure_ascii=False)
    return verdad_out


def main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("carpeta"); p.add_argument("--periodos", type=int, default=6); p.add_argument("--ordenes", type=int, default=50)
    p.add_argument("--semilla", type=int, default=7); p.add_argument("--deriva"); p.add_argument("--choques", action="store_true"); a = p.parse_args(argv)
    d = tuple(float(x) if i else int(x) for i, x in enumerate(a.deriva.split(":"))) if a.deriva else None
    v = generar(a.carpeta, a.periodos, a.ordenes, a.semilla, d, a.choques)
    print(f"fábrica: {a.periodos} periodos × {a.ordenes} órdenes, semilla {a.semilla}, choques {len(v['choques'])} → {a.carpeta}")


if __name__ == "__main__":
    main()
