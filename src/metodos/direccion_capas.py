# -*- coding: utf-8 -*-
"""PRUEBA DE DIRECCIÓN ENTRE CAPAS (OT-069 / T-191, E-198). Herramienta de la puerta: NO es un método de costeo.
Regla (informes/OT-063/mapa_capas.md), leída de los DATOS y no copiada a mano:
  · capa de un eje = D_EJE.EJE_CAPA (Datos_Iniciales); capa de una columna = la del eje cuyo contrato ENTREGA
    (DBD_7) la nombra (TABLA.CONCEPTO → columna por DBD_4); lo que el contrato no nombra va en COMPLEMENTO (explícito);
  · transacción EN LÍNEA (DBD_4d ONLINE) que escribe columnas CONTABLE/DECISION (recorriendo 4b, sub-operaciones, SI y
    PARACADA por 4c) = violación ESCRIBE; guarda D_EJE_PUNTO momento L de esas capas = violación GUARDA;
  · transacción de cierre (BATCH): solo puede escribir las capas de SUS ejes (D_EJE_PUNTO) o REAL;
  · lo que llega por M-ALG: propósito de la LEER ASIGNACION previa (INV/CAP) → filas de ASIGNACION (ASI_ALG) → SAD del
    algoritmo ('(algoritmo)' de 4b); si alguno escribe capa CONTABLE/DECISION o capacidad de cierre desde una trx en línea = violación.
Modo AVISO mientras EXCEPCIONES tenga entradas (V1..V14, cada una con sus claves); sin entradas pasa a ESTRICTO (falla).
Excepción nueva = falla. Una excepción que ya no ocurre es solo aviso (la fuente la arregló: se retira de la lista).
Uso:  python -m metodos.direccion_capas   (desde kit/)"""
import json
import os
import sys

from openpyxl import load_workbook

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(AQUI))
import rutas  # noqa: E402

PROHIBIDAS = ("CONTABLE", "DECISION")
# Columnas que ningún contrato DBD_7 nombra por su nombre físico (mapa_capas.md, reglas 2-3). [INFERIDO] = por semántica y E-142.
# CIERRE = capacidad que solo escribe T23.2 (no es de las capas CONTABLE/DECISION, pero tampoco puede llegar en línea por un algoritmo).
COMPLEMENTO = {
    ("CTA_OBJ_PER", "COP_IND_APL"): ("DECISION", "CIF_APLICADO, DBD_7 f78 (OBJETO.CIF_APLICADO)"),
    ("VENTA", "VTA_MAR"): ("CONTABLE", "margen con el costo de venta (COSTO_VENTAS)"),
    ("CTA_GASTO", "CGA_MTO"): ("CONTABLE", "[INFERIDO] destino del gasto, E-142"),
    ("CTA_GASTO", "CGA_DED"): ("CONTABLE", "[INFERIDO] deducibilidad del gasto, E-142"),
    ("CTA_VTA_PER", "VPE_CST"): ("CONTABLE", "costo de ventas del periodo (COSTO_VENTAS)"),
    ("EST_DECISION", "EDE_PRED"): ("DECISION", "[INFERIDO] calificación del estimado"),
    ("EST_DECISION", "EDE_REAL"): ("DECISION", "[INFERIDO] calificación del estimado"),
    ("EST_DECISION", "EDE_ERR"): ("DECISION", "[INFERIDO] calificación del estimado"),
    ("CTA_CENTRO", "CCE_FIJO"): ("CIERRE", "capacidad solo en T23.2 (DBD_7 f157-159)"),
    ("CTA_CENTRO", "CCE_PROP"): ("CIERRE", "capacidad solo en T23.2"),
    ("CTA_CENTRO", "CCE_VARH"): ("CIERRE", "capacidad solo en T23.2"),
    ("CTA_CENTRO", "CCE_TASA"): ("CIERRE", "capacidad solo en T23.2 (DBD_7 f157)"),
    ("CTA_CENTRO", "CCE_ASIG"): ("CIERRE", "capacidad solo en T23.2 (DBD_7 f158)"),
    ("CTA_CENTRO", "CCE_OCIO"): ("CIERRE", "capacidad solo en T23.2 (DBD_7 f159)"),
}
# V1..V14 del informe OT-063 → claves «TRX|CAPA|ESCRIBE|TABLA.COL» o «TRX|CAPA|GUARDA|EJE». V15 no es cruce de capa (E-194 #3).
# Se va VACIANDO a medida que F2a-c arreglan la fuente; cuando queda vacía el modo es ESTRICTO.
EXCEPCIONES = {
    # V1, V2 retiradas: corregidas por T-188 (OT-066)
    "V3": ["T20|CONTABLE|ESCRIBE|VENTA.VTA_CST", "T20|CONTABLE|ESCRIBE|VENTA.VTA_MAR", "T20|CONTABLE|ESCRIBE|CTA_VTA_PER.VPE_CST"],
    "V4": ["T20|CONTABLE|GUARDA|COSTO_VENTAS"],
    "V5": ["T14.1|CONTABLE|GUARDA|COSTO_VENTAS"],
    "V6": ["T19|CONTABLE|GUARDA|COSTO_VENTAS", "T19|CONTABLE|ESCRIBE|CTA_GASTO.CGA_MTO", "T19|CONTABLE|ESCRIBE|CTA_GASTO.CGA_DED"],
    "V7": ["T29|CONTABLE|GUARDA|COSTO_VENTAS"],
    "V8": ["T20.1|CONTABLE|ESCRIBE|VENTA.VTA_CST", "T20.1|CONTABLE|ESCRIBE|VENTA.VTA_MAR"],
    "V9": ["T15|CONTABLE|ESCRIBE|CTA_GASTO.CGA_MTO"],
    "V10": ["T16|CONTABLE|ESCRIBE|CTA_GASTO.CGA_MTO"],
    "V11": ["T29.1|CONTABLE|ESCRIBE|CTA_GASTO.CGA_MTO", "T29.1|CONTABLE|ESCRIBE|CTA_GASTO.CGA_DED"],
    "V12": ["T23.3|CONTABLE|ESCRIBE|CTA_VTA_PER.VPE_CST"],
    "V13": ["T23.3|DECISION|ESCRIBE|EST_DECISION.EDE_PRED", "T23.3|DECISION|ESCRIBE|EST_DECISION.EDE_REAL", "T23.3|DECISION|ESCRIBE|EST_DECISION.EDE_ERR"],
    "V14": ["T23.0|CONTABLE|ESCRIBE|CTA_VTA_PER.VPE_CST", "T23.0|CONTABLE|ESCRIBE|VENTA.VTA_CST", "T23.0|CONTABLE|ESCRIBE|VENTA.VTA_MAR",
            "T23.0|CONTABLE|ESCRIBE|CTA_GASTO.CGA_MTO", "T23.0|CONTABLE|ESCRIBE|CTA_GASTO.CGA_DED"],
    # V16: NO figura en el informe OT-063; la prueba la halló al leer los datos (M-ACU-CGA-OCIO: T23.2, eje CIF_APLICADO/DECISION, escribe gasto = CONTABLE; E-142: el destino del ocio lo decide el contable).
    "V16": ["T23.2|CONTABLE|ESCRIBE|CTA_GASTO.CGA_MTO"],
}


def _hoja(wb, nombre):
    return [r for r in wb[nombre].iter_rows(values_only=True) if r and any(c not in (None, "") for c in r)]


def _cargar(fuente, datos):
    wb = load_workbook(fuente, read_only=True)
    d = {n: _hoja(wb, n) for n in ("DBD_4_Modelo_Interno", "DBD_4b_Rutinas_SOA", "DBD_4c_Servicios_Datos", "DBD_4d_Transacciones", "DBD_7_Frontera_Puertos")}
    wb.close()
    wd = load_workbook(datos, read_only=True)
    for n in ("D_EJE", "D_EJE_PUNTO", "D_ASIGNACION"):
        d[n] = _hoja(wd, n)[1:]
    wd.close()
    return d


def _capa_columnas(d, capa_eje):
    """(tabla, columna) → (capa, origen): contrato ENTREGA de los ejes CONTABLE/DECISION resuelto por (Tabla, Concepto) de DBD_4; luego COMPLEMENTO."""
    conc = {(r[0], r[11]): r[3] for r in d["DBD_4_Modelo_Interno"] if r[0] and r[11]}
    out = {}
    for r in d["DBD_7_Frontera_Puertos"]:
        if len(r) > 2 and r[1] == "ENTREGA" and capa_eje.get(r[0]) in PROHIBIDAS and r[2] and "." in str(r[2]):
            t, c = str(r[2]).split(".", 1)
            col = conc.get((t, c.split(" ")[0]))
            if col:
                out[(t, col)] = (capa_eje[r[0]], f"contrato {r[0]} {r[2]}")
    for k, v in COMPLEMENTO.items():
        out.setdefault(k, v)
    return out


def _escrituras(sad, spec, subops, visto=frozenset()):
    """(tabla, columna, SAD) que escribe un SAD, expandiendo SI/PARACADA a su sub-operación."""
    s = spec.get(sad)
    if not s:
        return []
    tipo, tabla, sub = s["MET"][1], s["MET"][2], s["MET"][3]
    if tipo in ("SI", "PARACADA") and sub:
        return [] if sub in visto else [e for x in subops.get(sub, []) for e in _escrituras(x, spec, subops, visto | {sub})]
    if tipo in ("ACUMULAR", "ACTUALIZAR", "CREAR") and tabla:
        return [(tabla, m[0], sad) for m in s["MCA"] if m[1] == "V"]
    return []


def _propositos_alg(sad, spec, subops, visto=frozenset()):
    """Propósitos (INV/CAP) de cada M-ALG alcanzable desde un SAD: el de la LEER ASIGNACION anterior en su operación."""
    s = spec.get(sad)
    if not s or s["MET"][1] not in ("SI", "PARACADA") or not s["MET"][3] or s["MET"][3] in visto:
        return set()
    out, prop = set(), None
    for x in subops.get(s["MET"][3], []):
        sx = spec.get(x)
        if sx and sx["MET"][1] == "LEER" and sx["MET"][2] == "ASIGNACION":
            prop = next((m[4] for m in sx["MCA"] if m[0] == "ASI_PROP"), prop)
        elif sx and sx["MET"][1] == "ALGORITMO":
            out.add(prop)
        else:
            out |= _propositos_alg(x, spec, subops, visto | {s["MET"][3]})
    return out


def analizar(fuente=None, datos=None):
    """{«claves»: {clave: detalle}, «alg»: [texto]}: toda violación de dirección y lo que llega por M-ALG."""
    d = _cargar(fuente or os.path.join(rutas.FUENTE, "DBD_Fuente.xlsx"), datos or os.path.join(rutas.FUENTE, "Datos_Iniciales.xlsx"))
    capa_eje = {r[0]: r[2] for r in d["D_EJE"]}
    cols = _capa_columnas(d, capa_eje)
    spec = {r[0]: json.loads(r[1]) for r in d["DBD_4c_Servicios_Datos"] if r[0] and r[1] and str(r[1]).startswith("{")}
    modal = {r[0]: r[2] for r in d["DBD_4d_Transacciones"] if r[0] and r[2] in ("ONLINE", "BATCH")}
    subops, trx_sads, algs = {}, {}, {}
    for r in d["DBD_4b_Rutinas_SOA"]:
        if r[0] == "(sub)":
            subops.setdefault(r[2], []).append(r[5])
        elif r[0] == "(algoritmo)":
            algs[r[2]] = json.loads(r[5])
        elif r[0] and r[5] and r[0] in modal:
            trx_sads.setdefault(r[0], []).append(r[5])
    ejes = {}
    for r in d["D_EJE_PUNTO"]:
        ejes.setdefault(r[1], []).append((r[0], r[3]))
    claves, alg = {}, []

    def marcar(trx, online, permitidas, t, c, info):
        capa = cols.get((t, c), (None,))[0]
        if capa in PROHIBIDAS and (online or capa not in permitidas) or capa == "CIERRE" and online:
            claves[f"{trx}|{capa}|ESCRIBE|{t}.{c}"] = info
        return capa

    for trx in sorted(trx_sads):
        online = modal[trx] == "ONLINE"
        permitidas = {capa_eje.get(e) for e, _ in ejes.get(trx, [])} | {"REAL"}
        for sad in trx_sads[trx]:
            for t, c, s in _escrituras(sad, spec, subops):
                marcar(trx, online, permitidas, t, c, f"{s}: {cols.get((t, c), ('', ''))[1]}")
        if online:
            for eje, mom in ejes.get(trx, []):
                if mom == "L" and capa_eje.get(eje) in PROHIBIDAS:
                    claves[f"{trx}|{capa_eje[eje]}|GUARDA|{eje}"] = "D_EJE_PUNTO momento L"
        for prop in sorted({p for sad in trx_sads[trx] for p in _propositos_alg(sad, spec, subops)}, key=str):
            for a in (a for a in d["D_ASIGNACION"] if a[2] == prop):
                esc = [e for x in algs.get(a[3], []) for e in _escrituras(x, spec, subops)]
                alg.append(f"{trx}: M-ALG({prop}) → ASIGNACION {a[0]}/{a[1]} → {a[3]} → " + (", ".join(f"{t}.{c}" for t, c, _ in esc) or "sin escrituras"))
                for t, c, s in esc:
                    marcar(trx, online, permitidas, t, c, f"{trx}: M-ALG({prop}) → ASIGNACION {a[0]}/{a[1]}/{a[2]} → {a[3]} → {s} escribe {t}.{c}")
    return {"claves": claves, "alg": alg}


def _alcanzables(sad, spec, subops, visto=frozenset()):
    """Todos los SAD que corren desde uno, expandiendo SI/PARACADA a su sub-operación."""
    s = spec.get(sad)
    out = [sad]
    if s and s["MET"][1] in ("SI", "PARACADA") and s["MET"][3] and s["MET"][3] not in visto:
        for x in subops.get(s["MET"][3], []):
            out += _alcanzables(x, spec, subops, visto | {s["MET"][3]})
    return out


def alarmas_fuera_de_capa(fuente=None, datos=None):
    """OT-072 (AL-1, I4, V-07): errores de las reglas de alarma (D_REGLA_ALARMA) cuya variable llega de una capa superior.
    Una variable de la transacción es de otra capa si la lee un LEER de una columna CONTABLE/DECISION (en línea, también CIERRE),
    o si sale de una FÓRMULA que usa una variable así (se propaga). Sin reglas: lista vacía."""
    fuente = fuente or os.path.join(rutas.FUENTE, "DBD_Fuente.xlsx"); datos = datos or os.path.join(rutas.FUENTE, "Datos_Iniciales.xlsx")
    wd = load_workbook(datos, read_only=True)
    reglas = _hoja(wd, "D_REGLA_ALARMA")[1:] if "D_REGLA_ALARMA" in wd.sheetnames else []
    wd.close()
    if not reglas:
        return []
    d = _cargar(fuente, datos)
    capa_eje = {r[0]: r[2] for r in d["D_EJE"]}
    cols = _capa_columnas(d, capa_eje)
    spec = {r[0]: json.loads(r[1]) for r in d["DBD_4c_Servicios_Datos"] if r[0] and r[1] and str(r[1]).startswith("{")}
    modal = {r[0]: r[2] for r in d["DBD_4d_Transacciones"] if r[0] and r[2] in ("ONLINE", "BATCH")}
    subops, trx_sads = {}, {}
    for r in d["DBD_4b_Rutinas_SOA"]:
        if r[0] == "(sub)":
            subops.setdefault(r[2], []).append(r[5])
        elif r[0] and r[5] and r[0] in modal:
            trx_sads.setdefault(r[0], []).append(r[5])
    errores = []
    for r in reglas:
        cod, trx, var = r[0], r[1], str(r[2])
        if trx not in trx_sads:
            continue                                   # la transacción inexistente la rechaza check_config
        online = modal[trx] == "ONLINE"
        permitidas = {capa_eje.get(r2[0]) for r2 in d["D_EJE_PUNTO"] if r2[1] == trx} | {"REAL"}
        sads = [x for sad in trx_sads[trx] for x in _alcanzables(sad, spec, subops)]
        tainted = {}
        for _ in range(4):                             # propagación por fórmulas (punto fijo corto)
            for sad in sads:
                s = spec.get(sad)
                if not s:
                    continue
                tipo, tabla = s["MET"][1], s["MET"][2]
                if tipo == "LEER":
                    for m in s["MCA"]:
                        capa = cols.get((tabla, m[0]), (None,))[0]
                        if m[1] == "V" and capa and (capa in PROHIBIDAS and (online or capa not in permitidas) or capa == "CIERRE" and online):
                            tainted.setdefault(m[4], f"{capa}: LEER {tabla}.{m[0]} ({sad})")
                elif tipo == "FORMULA":
                    origen = None
                    for op, v, _lit in s["FRM"]:
                        if op == "ASIGNA":
                            if origen:
                                tainted.setdefault(v, origen)
                            continue
                        if v in tainted and (op == "INICIA" or origen is None):
                            origen = tainted[v]
        if var in tainted:
            errores.append(f"REGLA_ALARMA {cod}: la variable {var} de {trx} llega de otra capa ({tainted[var]}): una alarma en línea no la puede leer (I4)")
    return errores


def evaluar(res=None):
    """(ok, modo, vivas {V: [claves]}, nuevas, obsoletas). Falla si hay violación fuera de EXCEPCIONES (en ESTRICTO: cualquiera)."""
    res = res or analizar()
    hay = set(res["claves"])
    listadas = {k for ks in EXCEPCIONES.values() for k in ks}
    nuevas = sorted(hay - listadas)
    vivas = {v: [k for k in ks if k in hay] for v, ks in EXCEPCIONES.items()}
    return (not nuevas), ("AVISO" if EXCEPCIONES else "ESTRICTO"), vivas, nuevas, sorted(listadas - hay)


def fila_puerta():
    """(ok, texto) para la tabla de la puerta."""
    ok, modo, vivas, nuevas, obsoletas = evaluar()
    txt = f"modo {modo} · {sum(1 for ks in vivas.values() if ks)} de {len(EXCEPCIONES)} excepciones conocidas vivas"
    if obsoletas:
        txt += f" · AVISO: {len(obsoletas)} clave(s) ya arregladas, retirar de EXCEPCIONES"
    return ok, ("OK · " + txt) if ok else "FALLA: violación NUEVA de dirección → " + "; ".join(nuevas) + " · " + txt


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    r = analizar()
    ok, modo, vivas, nuevas, obsoletas = evaluar(r)
    print("MODO", modo)
    for k, v in sorted(r["claves"].items()):
        print(" ", k, "←", v)
    print("NUEVAS:", nuevas, "\nOBSOLETAS:", obsoletas, "\nM-ALG:", *r["alg"], sep="\n  ")
    sys.exit(0 if ok else 1)
