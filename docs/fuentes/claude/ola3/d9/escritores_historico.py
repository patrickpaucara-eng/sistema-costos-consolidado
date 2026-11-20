# -*- coding: utf-8 -*-
"""Deuda grupo B (D-I0b-1): inventario de ESCRITORES de las 7 cuentas y cuadre cuenta ↔ RESULTADO_METODO.
Solo lectura: no toca motor, base ni servicios.
Uso (desde la raíz): python3 -I informes/DEUDA/escritores.py   → reescribe informes/DEUDA/escritores_cuentas.md

Fuentes:
- fuente/DBD_Fuente.xlsx · DBD_4c_Servicios_Datos: servicio con operación CREAR/ACUMULAR/ACTUALIZAR/ELIMINAR sobre la cuenta.
- DBD_4b_Rutinas_SOA: SN → SAD; los SN «(sub)» se suben hasta la transacción raíz por los servicios PARACADA/SI que los llaman.
- DBD_4d_Transacciones: descripción y modalidad (ONLINE/BATCH) de la transacción.
- kit/: escritura Python por nombre de la cuenta (líneas con la cuenta y .append( / .cell( / setc( / asignación a celda),
  más los escritores GENÉRICOS revisados a mano (motores y sembrado), que no nombran la cuenta."""
import json
import os
import re
import sys
from collections import defaultdict

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DBD = os.path.join(RAIZ, "fuente", "DBD_Fuente.xlsx")
KIT = os.path.join(RAIZ, "kit")
CUENTAS = ["CTA_ACTOR", "CTA_CENTRO", "CTA_GASTO", "CTA_OBJ_PER", "CTA_OBJ_REC", "CTA_FUNCION", "CTA_VTA_PER"]
OPS_ESCRITURA = ("CREAR", "ACUMULAR", "ACTUALIZAR", "ELIMINAR")
# El escritor ÚNICO que pide D-I0b-1: el paso del cierre que publica RESULTADO_METODO.
CIERRE_PUBLICA = "kit/v41/correr_caso.py"

# Escritores genéricos (no nombran la cuenta): revisados a mano el 2026-11-16 sobre desarrollo/deuda.
GENERICOS = [
    ("kit/motor_espejo.py", "Motor.m_ACUMULAR / m_ACTUALIZAR / CREAR",
     "Ejecuta los servicios de DBD_4c: no es un escritor propio, materializa los servicios listados arriba."),
    ("kit/vba/motor.bas", "MActualizar (Case \"ACUMULAR\"/\"ACTUALIZAR\"/\"CREAR\")",
     "Motor VBA: igual que el espejo, ejecuta los servicios de DBD_4c."),
    ("kit/casos/sembrar_caso.py", "sembrar()",
     "Copia a la base toda hoja del caso que exista en ella (solo excluye RESULTADO_METODO y ALERTA): escribiría la cuenta "
     "si el caso trae la hoja. ENV.xlsx (O-1) no trae ninguna CTA_*."),
]
_PAT_ESCRIBE = re.compile(r"\.append\(|\.cell\(|setc\(|\]\s*=[^=]|\.Value\s*=\s*[^=]")
_PAT_LEE = re.compile(r"^\s*(If|ElseIf)\b", re.I)


def _wb():
    from openpyxl import load_workbook
    return load_workbook(DBD, read_only=True)


def servicios(wb=None):
    wb = wb or _wb(); out = {}
    for r in wb["DBD_4c_Servicios_Datos"].iter_rows(min_row=5, values_only=True):
        if r and r[0] and r[1]:
            try:
                out[r[0]] = json.loads(r[1])
            except ValueError:
                pass
    return out


def transacciones(wb=None):
    wb = wb or _wb(); out = {}
    for r in wb["DBD_4d_Transacciones"].iter_rows(min_row=5, values_only=True):
        if r and r[0] and r[0] not in out:
            out[r[0]] = (r[1], r[2])
    return out


def rutas_raiz(wb=None, svc=None):
    """{SAD: {(transacción raíz, cadena 'SN>...>SN')}} siguiendo los PARACADA/SI que llaman a un SN «(sub)»."""
    wb = wb or _wb(); svc = svc or servicios(wb)
    sn_sad, raiz_sn = defaultdict(list), defaultdict(set)
    for r in wb["DBD_4b_Rutinas_SOA"].iter_rows(min_row=5, values_only=True):
        if r and r[0] and r[2] and r[5]:
            sn_sad[r[2]].append(r[5])
            if r[0] != "(sub)":
                raiz_sn[r[2]].add(r[0])
    out = defaultdict(set)

    def baja(trx, sn, cam, vis):
        if sn in vis:
            return
        for s in sn_sad.get(sn, []):
            out[s].add((trx, ">".join(cam)))
            sub = (svc.get(s, {}).get("MET") or ["", "", "", ""])[3]
            if sub and str(sub).startswith("OP-"):
                baja(trx, sub, cam + [sub], vis | {sn})
    for sn, trxs in raiz_sn.items():
        for t in trxs:
            baja(t, sn, [sn], set())
    return out


def escritores_dbd(wb=None):
    """{cuenta: [dict(sad, op, desc, rutas=[(trx, desc_trx, modalidad, cadena)])]}"""
    wb = wb or _wb(); svc = servicios(wb); trx = transacciones(wb); rr = rutas_raiz(wb, svc)
    out = {c: [] for c in CUENTAS}
    for s, e in svc.items():
        m = e.get("MET") or []
        if len(m) > 2 and m[2] in out and m[1] in OPS_ESCRITURA:
            rutas = sorted((t, trx.get(t, ("¿?", "¿?"))[0], trx.get(t, ("¿?", "¿?"))[1], c) for t, c in rr.get(s, set()))
            out[m[2]].append(dict(sad=s, op=m[1], desc=m[0], rutas=rutas))
    return out


def escritores_kit():
    """{cuenta: [(archivo, línea, texto)]} escritura Python/VBA por nombre de la cuenta en kit/ (sin las copias kit/entrega y kit/kit)."""
    out = {c: [] for c in CUENTAS}
    for d, subs, fs in os.walk(KIT):
        rel = os.path.relpath(d, RAIZ).replace(os.sep, "/")
        if rel.startswith(("kit/entrega", "kit/kit")) or "__pycache__" in rel:
            subs[:] = []; continue
        for f in fs:
            if not f.endswith((".py", ".bas", ".cls")):
                continue
            p = os.path.join(d, f)
            for i, lin in enumerate(open(p, encoding="utf-8", errors="replace"), 1):
                for c in CUENTAS:
                    if c in lin and _PAT_ESCRIBE.search(lin) and not _PAT_LEE.search(lin):
                        out[c].append((f"{rel}/{f}", i, lin.strip()[:140]))
    return out


# ------------------------------------------------------------------ cuadre cuenta ↔ RESULTADO_METODO (O-1, ENVASE)
# Correspondencia [PROPUESTA] columna de la cuenta → (método, tipo, concepto) publicados en RESULTADO_METODO.
# Total del periodo y elemento = suma de la columna en la cuenta (filas del periodo/empresa) frente a la suma de los
# valores publicados. Una cuenta sin ningún concepto publicado no puede cuadrar (lista vacía).
CUADRE = {
    "CTA_OBJ_PER": [("COP_MAT", "LIQUIDACION_OT", "OBJETO", "PER_MD"), ("COP_MOD", "LIQUIDACION_OT", "OBJETO", "PER_PD"),
                    ("COP_IND", "LIQUIDACION_OT", "OBJETO", "PER_CIF")],
    "CTA_CENTRO": [("CCE_SUM", "REPARTO_ETAPAS", "CENTRO", "COSTO_PROPIO"), ("CCE_RECIB", "REPARTO_ETAPAS", "CENTRO", "RECIBIDO"),
                   ("CCE_DIST", "REPARTO_ETAPAS", "CENTRO", "DISTRIBUIDO"), ("CCE_OCIO", "REPARTO_ETAPAS", "CENTRO", "OCIO")],
    "CTA_GASTO": [("CGA_MTO", "LIQUIDACION_OT", "PERIODO", "GAD"), ("CGA_MTO", "LIQUIDACION_OT", "PERIODO", "GVT")],
    "CTA_FUNCION": [("CFU_MTO", "LIQUIDACION_OT", "PERIODO", "GAD"), ("CFU_MTO", "LIQUIDACION_OT", "PERIODO", "GVT"),
                    ("CFU_MTO", "LIQUIDACION_OT", "PERIODO", "CPT")],
    "CTA_VTA_PER": [("VPE_ING", "COSTO_VENTAS_OT", "PERIODO", "VENTAS"), ("VPE_CST", "COSTO_VENTAS_OT", "PERIODO", "CV")],
    "CTA_OBJ_REC": [("COR_MTO", "REPARTO_ETAPAS", "OBJETO", "MD")],
    "CTA_ACTOR": [],
}
CASO_O1 = os.path.join(RAIZ, "casos", "V41", "ENV.xlsx")
PAR_O1 = dict(PER="2021-01", EMP="ENV")


def correr_o1(libro=CASO_O1):
    """Cadena K1→K7 de O-1 en memoria, como informes/V41/integra_env.py (cadena): {método: [(tipo, clave, concepto, valor)]}."""
    sys.path.insert(0, KIT); sys.path.insert(0, os.path.join(RAIZ, "informes", "V41"))
    import integra_env as I
    import puerto_lectura as P
    from metodos import reparto_etapas as R, liquidacion as L, costo_ventas_gastos as CV
    prev = {"VALUACION_PROMEDIO": I.valuacion_alg01(libro)}
    prev["REPARTO_ETAPAS"] = R.calcular(P.leer_conceptos(libro, R.CONSUME), PAR_O1, prev)[0]
    prev["LIQUIDACION_OT"] = L.calcular(P.leer_conceptos(libro, L.CONSUME), PAR_O1, prev)[0]
    prev["COSTO_VENTAS_OT"] = CV.calcular(P.leer_conceptos(libro, CV.CONSUME), PAR_O1, prev)[0]
    return prev


def total_resultado(rm, metodo, tipo, concepto):
    from decimal import Decimal
    return sum(float(v) for t, k, c, v in rm.get(metodo, [])
               if t == tipo and c == concepto and isinstance(v, (int, float, Decimal)) and not isinstance(v, bool))


def hojas_libro(libro=CASO_O1):
    from openpyxl import load_workbook
    return load_workbook(libro, read_only=True).sheetnames


# ------------------------------------------------------------------ informe
def informe():
    wb = _wb(); dbd = escritores_dbd(wb); kit = escritores_kit(); hojas = hojas_libro()
    L = ["# Escritores de las 7 cuentas (deuda grupo B, D-I0b-1)", "",
         "Generado por `python3 -I informes/DEUDA/escritores.py` (no editar a mano; la prueba "
         "`pruebas/deuda/test_cuadre_cuentas.py` comprueba que este informe coincide con DBD_4c).", "",
         "**Regla D-I0b-1** (`informes/I0b/TABLA_FINAL.md`): cada cuenta tiene **un solo escritor**, el paso del cierre que publica "
         f"RESULTADO_METODO (`{CIERRE_PUBLICA}`, K1→K9), y una prueba de cuadre entre ambos.", "",
         "## Resumen", "",
         "| Cuenta | Servicios que escriben (DBD_4c) | Transacciones raíz | Escritura Python/VBA por nombre en kit/ | ¿Escribe el cierre que publica RESULTADO_METODO? | ¿Hoja en ENV.xlsx (O-1)? |",
         "|---|---|---|---|---|---|"]
    for c in CUENTAS:
        trxs = sorted({r[0] for s in dbd[c] for r in s["rutas"]})
        L.append(f"| {c} | {len(dbd[c])} | {', '.join(trxs) or '—'} | {len(kit[c])} | No | {'Sí' if c in hojas else 'No'} |")
    L += ["", "**Conclusión [VERIFICADO 2026-11-16]:** ninguna cuenta cumple D-I0b-1 hoy. Todas se escriben desde varias "
          "transacciones del motor (en línea T15–T29 y lotes T23.x) y **ninguna** desde el cierre V4.1 que publica "
          "RESULTADO_METODO: `correr_caso.py` publica RESULTADO_METODO e INV_PROCESO (K9, por CARGA) pero no toca ninguna CTA_*. "
          "El caso O-1 (`casos/V41/ENV.xlsx`) ni siquiera trae las hojas, así que el cuadre no puede hacerse. "
          "Las pruebas quedan en `xfail(strict=True)` con esta razón.", ""]
    for c in CUENTAS:
        L += [f"## {c}", "", "### Servicios de DBD_4c que escriben", "",
              "| Servicio | Operación | Qué hace | Transacción raíz (modalidad) · cadena de SN |", "|---|---|---|---|"]
        for s in dbd[c]:
            rutas = "<br>".join(f"{t} «{d}» ({m}) · {cad}" for t, d, m, cad in s["rutas"]) or "**ninguna** (servicio huérfano: no lo llama ningún SN)"
            L.append(f"| {s['sad']} | {s['op']} | {s['desc']} | {rutas} |")
        L += ["", "### Escritura Python/VBA por nombre en kit/", ""]
        L += [f"- `{a}:{i}` — `{t}`" for a, i, t in kit[c]] or ["- ninguna"]
        L += ["", "### Correspondencia de cuadre con RESULTADO_METODO [PROPUESTA]", ""]
        if CUADRE[c]:
            L += [f"- `{col}` ↔ `{m}` · {t} · {k}" for col, m, t, k in CUADRE[c]]
        else:
            L += ["- **ninguna**: ningún método de la cadena V4.1 publica en RESULTADO_METODO un concepto que alimente esta cuenta."]
        L.append("")
    L += ["## Escritores genéricos en kit/ (no nombran la cuenta)", "", "| Archivo | Punto | Nota |", "|---|---|---|"]
    L += [f"| `{a}` | {p} | {n} |" for a, p, n in GENERICOS]
    L += ["", "Las copias `kit/entrega/` y `kit/kit/` repiten los mismos archivos y se excluyen del recuento.", "",
          "## Método", "", "- Escritor en DBD_4c = servicio cuya operación (MET[1]) es " + ", ".join(OPS_ESCRITURA) +
          " y cuya tabla (MET[2]) es la cuenta. LEER, PARACADA, VALIDA, SI y FORMULA no escriben.",
          "- Transacción raíz: DBD_4b da SN→SAD; un SN «(sub)» se sube por el servicio PARACADA/SI que lo nombra en MET[3].",
          "- Escritura por nombre en kit/: línea con la cuenta y `.append(`, `.cell(`, `setc(`, `]=` o `.Value=`, excluidas las condiciones `If`.", ""]
    return "\n".join(L)


if __name__ == "__main__":
    ruta = os.path.join(RAIZ, "informes", "DEUDA", "escritores_cuentas.md")
    open(ruta, "w", encoding="utf-8").write(informe())
    print("escrito", ruta)
