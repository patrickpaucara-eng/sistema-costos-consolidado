"""Entrada única del sistema: un libro Excel con la estructura del DBD (Reyna). El sistema no se adapta a los datos de
cada empresa; cada empresa usa un ADAPTADOR propio (p. ej. casos/frenosa/generar.py) que llena este formato.
Aquí: validación estricta con mensajes en español, huella (sello) y plantilla vacía."""
import hashlib, re, shutil
from pathlib import Path

from openpyxl import load_workbook

from .raiz import RAIZ
PLANTILLA = RAIZ / "casos" / "plantilla_dbd.xlsx"      # plantilla ÚNICA (D-6): operar y costear en el mismo libro
VERSION = "1.0-MN01"

# tablas que la empresa debe llenar (las demás son configuración del método o salidas del sistema)
OBLIGATORIAS = ["EMPRESA", "PERIODO", "OBJETO", "RECURSO", "TIPO_RECURSO", "EVENTO", "LINEA", "REGLA_REPARTO", "CRITERIO", "MEDIDA", "VENTA"]
OPCIONALES = ["CENTRO", "ACTIVIDAD", "KARDEX", "CLIENTE"]
COLUMNAS_OPCIONALES = {"ACT_NIVEL"}     # Modelo 3 (Oria): vacío = actividad operativa; los libros anteriores siguen válidos
ETAPAS_VALIDAS = ("P1", "P2", "P3", "P4A", "P4B", "P4D", "P4E", "P4C", "P5", "P6", "P7", "OCIO")   # OCIO: criterio propio del ocio de un origen
DE_DATOS = OBLIGATORIAS + OPCIONALES + ["INV_PROCESO", "ESTIMACION", "LIN_ESTIM", "RESULTADO_METODO", "ALERTA", "PARAM_CAMBIO"]
DESCRIPCION = {
    "EMPRESA": "Una fila: código, nombre y moneda funcional.",
    "PERIODO": "Un periodo por mes, código AAAA-MM.",
    "OBJETO": "Objetos de costo (órdenes, lotes): número, producto (OBJ_PRO) y cantidad producida.",
    "RECURSO": "Recursos que consumen costo (materiales, personal, servicios, gastos) con su tipo.",
    "TIPO_RECURSO": "Tipo de recurso → elemento de costo (MAT, PER, IND, ADM, VTA, FIN…).",
    "EVENTO": "Cabecera de cada documento del ERP (compra, consumo, planilla, gasto): periodo, fecha, objeto o centro.",
    "LINEA": "Detalle de cada documento: recurso, cantidad, costo unitario e importe.",
    "KARDEX": "Movimientos de almacén de materiales; las entradas llevan su valor (KDX_VAL).",
    "REGLA_REPARTO": "Modelo ABC: en qué etapa (P1…P7; P4D centro→actividad, P4E actividad→actividad escalonado) y con qué inductor se reparte cada origen.",
    "CRITERIO": "Inductores (unidad de medida).",
    "MEDIDA": "Cantidad de cada inductor por destino y periodo (minutos, kg, %, ventas…). Nivel CAP = capacidad práctica de un origen (ocio).",
    "CENTRO": "Centros de costo (producción, apoyo, administración, ventas, financieros).",
    "ACTIVIDAD": "Actividades del modelo ABC; ACT_NIVEL = E estratégica, A apoyo u O operativa (Modelo 3 de Oria, vacío = O).",
    "VENTA": "Ventas del periodo por producto: cantidad e ingreso neto.",
    "CLIENTE": "Clientes o mercados (opcional).",
}


def _tablas(libro, nombres):
    wb = load_workbook(libro, read_only=True, data_only=True); out = {}
    try:
        for n in nombres:
            if n not in wb.sheetnames: continue
            filas = list(wb[n].iter_rows(values_only=True))
            if not filas: out[n] = ([], []); continue
            cab = [c for c in filas[0]]
            datos = [dict(zip(cab, f)) for f in filas[1:] if f and any(v not in (None, "") for v in f)]
            out[n] = (cab, datos)
    finally:
        wb.close()
    return out


def cabeceras_plantilla():
    return {n: cab for n, (cab, _) in _tablas(PLANTILLA, DE_DATOS).items()}


def _num(v):
    try: float(v); return True
    except (TypeError, ValueError): return False


def validar(libro):
    """Lista de errores (vacía = el libro cumple el formato DBD). Nunca corrige: rechaza y explica."""
    err = []
    try:
        t = _tablas(libro, OBLIGATORIAS + OPCIONALES)
    except Exception:
        return ["El archivo no es un libro Excel (.xlsx) legible."]
    modelo = cabeceras_plantilla()
    for n in OBLIGATORIAS + OPCIONALES:
        if n not in t:
            if n in OBLIGATORIAS: err.append(f"Falta la hoja {n}. {DESCRIPCION.get(n, '')}")
            continue
        cab, filas = t[n]
        faltan = [c for c in modelo.get(n, []) if c and c not in cab and c not in COLUMNAS_OPCIONALES]
        if faltan: err.append(f"Hoja {n}: faltan las columnas {', '.join(faltan)}.")
        if n in OBLIGATORIAS and not filas: err.append(f"Hoja {n} está vacía. {DESCRIPCION.get(n, '')}")
    if err: return err
    g = lambda n: t.get(n, ([], []))[1]
    emp = [r["EMP_COD"] for r in g("EMPRESA")]
    if len(emp) != 1: err.append("Hoja EMPRESA: debe tener exactamente una empresa.")
    pers = {str(r["PER_COD"]) for r in g("PERIODO")}
    for p in pers:
        if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", p): err.append(f"Hoja PERIODO: el código «{p}» no tiene la forma AAAA-MM.")
    recs = {r["REC_COD"] for r in g("RECURSO")}; tipos = {r["TRE_COD"] for r in g("TIPO_RECURSO")}
    cris = {r["CRI_COD"] for r in g("CRITERIO")}; cens = {r["CEN_COD"] for r in g("CENTRO")}; acts = {r["ACT_COD"] for r in g("ACTIVIDAD")}
    objs = {r["OBJ_NUM"]: r for r in g("OBJETO")}; prods = {str(r.get("OBJ_PRO")) for r in objs.values()}
    def ref(n, i, col, valor, conjunto, donde):
        if valor not in conjunto: err.append(f"Hoja {n}, fila {i + 2}: {col} = «{valor}» no existe en {donde}.")
    for i, r in enumerate(g("OBJETO")):
        if not r.get("OBJ_PRO"): err.append(f"Hoja OBJETO, fila {i + 2}: falta el producto (OBJ_PRO).")
        if not _num(r.get("OBJ_CAN")) or float(r["OBJ_CAN"]) <= 0: err.append(f"Hoja OBJETO, fila {i + 2}: la cantidad (OBJ_CAN) debe ser mayor que cero.")
    for i, r in enumerate(g("RECURSO")): ref("RECURSO", i, "REC_TRE", r.get("REC_TRE"), tipos, "TIPO_RECURSO")
    eventos = {r["EVE_NUM"] for r in g("EVENTO")}
    for i, r in enumerate(g("EVENTO")): ref("EVENTO", i, "EVE_PER", str(r.get("EVE_PER")), pers, "PERIODO")
    for i, r in enumerate(g("LINEA")):
        ref("LINEA", i, "LIN_EVE", r.get("LIN_EVE"), eventos, "EVENTO"); ref("LINEA", i, "LIN_REC", r.get("LIN_REC"), recs, "RECURSO")
    for i, r in enumerate(g("REGLA_REPARTO")):
        ref("REGLA_REPARTO", i, "RRE_ORIGEN", r.get("RRE_ORIGEN"), recs | cens | acts, "RECURSO, CENTRO ni ACTIVIDAD")
        ref("REGLA_REPARTO", i, "RRE_CRIT", r.get("RRE_CRIT"), cris, "CRITERIO")
        if r.get("RRE_ETAPA") not in ETAPAS_VALIDAS:
            err.append(f"Hoja REGLA_REPARTO, fila {i + 2}: la etapa «{r.get('RRE_ETAPA')}» no es {', '.join(ETAPAS_VALIDAS)}.")
    for i, r in enumerate(g("ACTIVIDAD")):
        if str(r.get("ACT_NIVEL") or "O").strip().upper() not in ("E", "A", "O"):
            err.append(f"Hoja ACTIVIDAD, fila {i + 2}: ACT_NIVEL = «{r.get('ACT_NIVEL')}» debe ser E (estratégica), A (apoyo) u O (operativa).")
    for i, r in enumerate(g("MEDIDA")):
        ref("MEDIDA", i, "MED_CRIT", r.get("MED_CRIT"), cris, "CRITERIO"); ref("MEDIDA", i, "MED_PER", str(r.get("MED_PER")), pers, "PERIODO")
        if not _num(r.get("MED_CAN")) or float(r["MED_CAN"]) < 0: err.append(f"Hoja MEDIDA, fila {i + 2}: la cantidad debe ser un número ≥ 0.")
    for i, r in enumerate(g("KARDEX")):
        ref("KARDEX", i, "KDX_REC", r.get("KDX_REC"), recs, "RECURSO")
        if _num(r.get("KDX_CAN")) and float(r["KDX_CAN"]) > 0 and r.get("KDX_VAL") is None:
            err.append(f"Hoja KARDEX, fila {i + 2}: una entrada necesita su valor (KDX_VAL).")
    for i, r in enumerate(g("VENTA")):
        ref("VENTA", i, "VTA_PER", str(r.get("VTA_PER")), pers, "PERIODO"); ref("VENTA", i, "VTA_REC", str(r.get("VTA_REC")), prods, "los productos de OBJETO")
        if not _num(r.get("VTA_ING")): err.append(f"Hoja VENTA, fila {i + 2}: el ingreso (VTA_ING) debe ser un número.")
    return err[:200]


def empresa(libro):
    e = (_tablas(libro, ["EMPRESA"]).get("EMPRESA", ([], [{}]))[1] or [{}])[0]
    return str(e.get("EMP_COD") or ""), str(e.get("EMP_NOM") or e.get("EMP_COD") or "")


def slug(nombre):
    import unicodedata
    s = unicodedata.normalize("NFKD", str(nombre)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_") or "empresa"


def huella(libro):
    """SHA-256 del contenido del libro: la «huella» que sella qué datos entraron al cálculo."""
    h = hashlib.sha256()
    with open(libro, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()


def plantilla_vacia(destino):
    """Copia de la plantilla DBD sin datos de empresa, con hoja LEEME (qué llenar en cada tabla)."""
    shutil.copy(PLANTILLA, destino); wb = load_workbook(destino)
    for n in DE_DATOS:
        if n == "TIPO_RECURSO": continue                         # catálogo de tipos → elementos: se conserva como guía
        if n in wb.sheetnames and wb[n].max_row > 1: wb[n].delete_rows(2, wb[n].max_row - 1)
    ws = wb.create_sheet("LEEME", 0)
    ws.append(["Plantilla del Sistema de Costos Reyna (formato DBD)"]); ws.append([])
    ws.append(["Hoja", "Obligatoria", "Qué contiene"])
    for n in OBLIGATORIAS + OPCIONALES: ws.append([n, "Sí" if n in OBLIGATORIAS else "No", DESCRIPCION.get(n, "")])
    ws.append([]); ws.append(["Las demás hojas son configuración del método o salidas del sistema: no se llenan."])
    ws.append(["Para operar el libro (registrar compras, consumos, cerrar el mes) asigna tu empresa a los usuarios: hoja USUARIO, columna USU_EMP."])
    ws.append(["Si los datos de tu ERP tienen otro formato, escribe un adaptador que llene esta plantilla (ejemplo: casos/frenosa/generar.py)."])
    wb.save(destino); return destino
