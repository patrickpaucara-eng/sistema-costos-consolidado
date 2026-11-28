"""Arnés común de la auditoría MN 1 (pruebas_auditoria/).

Toma una COPIA de SERVITEC_sintetico.xlsx, le aplica un cambio con openpyxl, la registra y la calcula con el motor real
(reyna_local.calculo_local.registrar / calcular) en una carpeta temporal. No modifica el repo ni el libro original.

Rutas (variables de entorno, o argumentos de correr_auditoria.py):
    AUDIT_REPO      raíz del repo, con fuente/DBD_Fuente.xlsx y casos/plantilla_dbd.xlsx
    AUDIT_SERVITEC  ruta de SERVITEC_sintetico.xlsx (por defecto, la copia que viene en esta carpeta)

Convención de las pruebas: cada test_S<n> afirma el comportamiento CORRECTO. Si falla con el motor de hoy, la sospecha
queda CONFIRMADA. Cada archivo tiene además un test_control_* que debe pasar: comprueba que el escenario se armó bien
(si el control falla, la prueba de la sospecha no es concluyente).
"""
import os
import shutil
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
REPO = Path(os.environ.get("AUDIT_REPO", AQUI.parent / "repo")).resolve()
SERVITEC = Path(os.environ.get("AUDIT_SERVITEC", AQUI / "datos" / "SERVITEC_sintetico.xlsx")).resolve()

for falta in (REPO / "src", REPO / "fuente" / "DBD_Fuente.xlsx", REPO / "casos" / "plantilla_dbd.xlsx", SERVITEC):
    if not falta.exists():
        raise SystemExit(f"Falta {falta}. Indica AUDIT_REPO (repo con fuente/ y casos/) y AUDIT_SERVITEC.")

if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

from openpyxl import load_workbook                      # noqa: E402
import reyna_local.calculo_local as CL                  # noqa: E402

PERIODO = "2025-07"
# Resultado de julio con el libro sin cambios (comprobado en las piezas 24 y 30)
BASE = {"OT-SRV-REB-2025-07": 22975.0, "OT-SRV-MPR-2025-07": 5165.0}
BASE_TOTAL = 28140.0


def _tmp(prefijo):
    return Path(tempfile.mkdtemp(prefix=f"audit_{prefijo}_"))


def columna(ws, nombre):
    """Número de columna (1-based) de la cabecera `nombre` en la fila 1."""
    for c in ws[1]:
        if c.value == nombre:
            return c.column
    raise KeyError(f"La hoja {ws.title} no tiene la columna {nombre}")


def fila(ws, **filtro):
    """Número de fila (1-based) de la única fila que cumple el filtro {columna: valor}."""
    cols = {k: columna(ws, k) for k in filtro}
    hall = [r for r in range(2, ws.max_row + 1) if all(ws.cell(r, c).value == filtro[k] for k, c in cols.items())]
    if len(hall) != 1:
        raise LookupError(f"{ws.title}: {len(hall)} filas cumplen {filtro} (se esperaba 1)")
    return hall[0]


def poner(ws, n_fila, col, valor):
    ws.cell(n_fila, columna(ws, col)).value = valor


def agregar(ws, **valores):
    """Agrega una fila con los valores por nombre de columna."""
    r = ws.max_row + 1
    for k, v in valores.items():
        ws.cell(r, columna(ws, k)).value = v
    return r


def libro(cambio=None, nombre="SERVITEC_audit.xlsx"):
    """Copia de SERVITEC con `cambio(wb)` aplicado. Devuelve la ruta de la copia."""
    d = _tmp("libro"); p = d / nombre
    shutil.copy(SERVITEC, p)
    if cambio is not None:
        wb = load_workbook(p)
        cambio(wb)
        wb.save(p)
    return p


def calcular(ruta_libro, periodo=PERIODO, sintesis="REAL", carpeta=None):
    """Registra y calcula como lo hace el sistema. Devuelve un dict:
    {"etapa": "registrar", "mensaje": [...]}  si validar() lo rechaza;
    {"etapa": "calcular", "mensaje": "..."}   si calcular() lo detiene (mensaje, sin traza);
    {"etapa": "ok", "resultado": r, "carpeta": c, "id": s} si calcula."""
    c = Path(carpeta) if carpeta else _tmp("calc")
    ficha, err = CL.registrar(c, Path(ruta_libro).read_bytes(), Path(ruta_libro).name)
    if err:
        return {"etapa": "registrar", "mensaje": err}
    try:
        r = CL.calcular(c, periodo, sintesis, ficha["id"])
    except Exception as e:                              # se informa el mensaje que vería el usuario
        return {"etapa": "calcular", "mensaje": f"{type(e).__name__}: {e}"}
    return {"etapa": "ok", "resultado": r, "carpeta": c, "id": ficha["id"]}


def costos(res):
    """{orden: costo_total} de un resultado calculado."""
    return {o["codigo"]: o["costo_total"] for o in res["resultado"]["objetos"]}


def objeto(res, codigo):
    return next(o for o in res["resultado"]["objetos"] if o["codigo"] == codigo)


def control(res, empieza):
    """Primer control del panel «Calidad y cuadre» cuyo nombre empieza con `empieza`."""
    return next(k for k in res["resultado"]["control"] if k["control"].startswith(empieza))


def resumen(res):
    """Texto corto para los mensajes de falla (lo que hace el motor hoy)."""
    if res["etapa"] != "ok":
        return f"{res['etapa']}: {res['mensaje']}"
    r = res["resultado"]
    cons = control(res, "Conservación del reparto")
    return (f"calcula sin rechazo; costos {costos(res)}; total {round(sum(costos(res).values()), 2)}; "
            f"control de conservación ok={cons['ok']} ({cons['esperado']} vs {cons['obtenido']})")
