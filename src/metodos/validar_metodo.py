# -*- coding: utf-8 -*-
"""Valida que un método cumpla el FORMATO COMPATIBLE (E-105 / OT-022) antes de usarlo.
Uso (desde kit/):
    python -m metodos.validar_metodo metodos/<metodo>.py [ruta/DBD_Fuente.xlsx]

CONSUME por CONCEPTOS (OT-022): {entidad MCD: [concepto, ...]}. El traductor único es metodos.semantica:
    - entidad o concepto inexistente -> FALLA;
    - una columna con Naturaleza RESULTADO es FALLA en CUALQUIER formato (concepto, columna o mixto). La única
      salida en CONSUME es una excepción de ordenes/EXCEPCIONES_RESULTADO.md leída de origin/main, que exige
      coincidir Método (FICHA["nombre"]) y la RUTA RELATIVA a kit/metodos/ (no el basename). DEPENDE_DE NO es
      salida: lo que llega por DEPENDE_DE llega por previos, nunca por CONSUME (E-133);
    - una columna física sin Concepto (deuda de OT-021) -> AVISO OBSOLETO, no FALLA.
Cada DEPENDE_DE se valida: el método nombrado debe existir en kit/metodos/ (por FICHA["nombre"]) y su
ENTREGA[tipo] debe contener el concepto; si no, FALLA `DEPENDE_DE: X no entrega (tipo, concepto)`.
Identidad única (OT-036): dos módulos de kit/metodos/ (cualquier profundidad, excluidos _NO_METODO) con el mismo
FICHA["nombre"] son FALLA para todos: `FICHA: nombre X duplicado en a.py y b.py`.
El formato viejo {tabla: [columna, ...]} sigue funcionando durante la migración y se marca OBSOLETO.
Las cáscaras PENDIENTE no bloquean la puerta, pero sus deudas (RESULTADO o DEPENDE_DE) se publican como DEUDA y
validar() sin permitir_pendiente FALLA."""
import glob
import importlib.util
import os
import re
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(AQUI)
RAIZ = os.path.dirname(KIT)
if KIT not in sys.path:
    sys.path.insert(0, KIT)

try:
    from . import semantica
except ImportError:                                     # ejecución directa: python metodos/validar_metodo.py
    import semantica

def ejes_ficha():   # T-175: los ejes válidos de la FICHA salen del catálogo EJE (EJE_FICHA, varios con «|»), no de una lista a mano
    from openpyxl import load_workbook
    wb = load_workbook(os.path.join(os.environ.get("REYNA_FUENTE") or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "fuente"), "Datos_Iniciales.xlsx"), read_only=True)
    return {x for f in wb["D_EJE"].iter_rows(min_row=2, values_only=True) if f[0] for x in str(f[4]).split("|")}
OBJ = {"REAL", "CONTABLE", "ESTIMADO"}
_NO_METODO = {"__init__", "_plantilla_metodo", "validar_metodo", "probar_metodos", "publicar", "correr_metodos",
              "caso_excel", "puerta", "semantica"}
_EXCEPCIONES = None
_MODULOS = None


def cargar(ruta):
    sp = importlib.util.spec_from_file_location("metodo", ruta)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def columnas_dbd(dbd):
    """Compatibilidad: {tabla: [columnas]} leído por el traductor semántico."""
    m = semantica._leer(dbd)                            # el DBD es la única fuente; no se resuelve aquí
    return {t: list(v["columnas"]) for t, v in m["por_tabla"].items()}


def _leer_excepciones():
    """Lee EXCEPCIONES_RESULTADO.md de origin/main. La fila vale por Método + Archivo (columna nueva, E-133)."""
    global _EXCEPCIONES
    if _EXCEPCIONES is not None:
        return _EXCEPCIONES
    filas = []
    for ref in ("origin/main", "main"):
        try:
            p = subprocess.run(["git", "show", f"{ref}:ordenes/EXCEPCIONES_RESULTADO.md"], cwd=RAIZ,
                               capture_output=True, encoding="utf-8", errors="replace")
        except OSError:
            continue
        if p.returncode != 0 or not p.stdout.strip():
            continue
        hdr = None
        for linea in p.stdout.splitlines():
            s = linea.strip()
            if not s.startswith("|"):
                continue
            cols = [x.strip() for x in s.strip("|").split("|")]
            if cols and cols[0].upper() == "ID":
                hdr = [c.lower() for c in cols]
                continue
            if hdr is None or len(cols) != len(hdr) or set(cols[0]) <= {"-", ":", " "}:
                continue
            fila = dict(zip(hdr, cols))
            if "método" not in fila or "archivo" not in fila or "tabla.columna" not in fila:
                continue
            filas.append(dict(id=fila.get("id", ""), metodo=fila["método"], archivo=fila["archivo"],
                              columna=fila["tabla.columna"], cierra=fila.get("se cierra con", "")))
        break
    _EXCEPCIONES = filas
    return filas


def recargar_excepciones():
    global _EXCEPCIONES
    _EXCEPCIONES = None


def _modulos_por_nombre():
    """{FICHA['nombre']: [(ruta_relativa, módulo), ...]} de kit/metodos/ a cualquier profundidad."""
    global _MODULOS
    if _MODULOS is not None:
        return _MODULOS
    out = {}
    patron = os.path.join(AQUI, "**", "*.py")
    for ruta in sorted(glob.glob(patron, recursive=True)):
        base = os.path.splitext(os.path.basename(ruta))[0]
        if base in _NO_METODO or base.startswith("_"):
            continue
        try:
            m = cargar(ruta)
        except Exception:
            continue
        nom = str(getattr(m, "FICHA", {}).get("nombre", "")).strip()
        if not nom:
            continue
        rel = os.path.relpath(ruta, AQUI).replace(os.sep, "/")
        out.setdefault(nom, []).append((rel, m))
    _MODULOS = out
    return out


def duplicados():
    """{FICHA['nombre']: [rutas relativas]} de los nombres repetidos en kit/metodos/ (OT-036)."""
    return {nom: [rel for rel, _ in mods] for nom, mods in _modulos_por_nombre().items() if len(mods) > 1}


def _lista_duplicados(rutas):
    rutas = list(rutas)
    if len(rutas) == 1:
        return rutas[0]
    return ", ".join(rutas[:-1]) + " y " + rutas[-1]


def _metodos_por_nombre():
    """{FICHA['nombre']: módulo} SOLO de nombres únicos, para validar DEPENDE_DE."""
    out = {}
    for nom, mods in _modulos_por_nombre().items():
        if len(mods) == 1:
            out[nom] = mods[0][1]
    return out


def recargar_metodos():
    global _MODULOS
    _MODULOS = None


def _ruta_relativa(m):
    """Ruta relativa a kit/metodos/ con '/', para la excepción por Método + Archivo."""
    archivo = os.path.abspath(str(getattr(m, "__file__", "") or ""))
    if not archivo:
        return ""
    try:
        return os.path.relpath(archivo, AQUI).replace(os.sep, "/")
    except ValueError:
        return archivo.replace(os.sep, "/")


def _excepcion(m, tabla, columna):
    """True solo si coinciden Método (FICHA) y ruta relativa a kit/metodos/ con origin/main."""
    nombre = str(getattr(m, "FICHA", {}).get("nombre", "")).strip().upper()
    archivo = _ruta_relativa(m).strip().upper()
    if not nombre or not archivo:
        return False
    for e in _leer_excepciones():
        if str(e["metodo"]).strip().upper() != nombre:
            continue
        if str(e["archivo"]).strip().replace("\\", "/").upper() != archivo:
            continue
        tc = str(e["columna"]).strip()
        if "." not in tc:
            continue
        t, c = tc.split(".", 1)
        if t.strip().upper() == str(tabla).strip().upper() and c.strip().upper() == str(columna).strip().upper():
            return True
    return False


def _clasificar(m, dbd):
    """Devuelve (formato, nuevos, viejos) con formato CONCEPTOS / COLUMNAS / MIXTO / DESCONOCIDO."""
    nuevos, viejos, desconocidos = [], [], []
    for clave, valores in m.CONSUME.items():
        if not isinstance(valores, (list, tuple)):
            desconocidos.append(f"CONSUME: los valores de «{clave}» deben ser una lista")
            continue
        try:
            if all(semantica.es_concepto(clave, c, dbd) for c in valores):
                nuevos.append((clave, valores))
            elif all(semantica.es_columna(clave, c, dbd) for c in valores):
                viejos.append((clave, valores))
            elif semantica.es_entidad(clave, dbd) and any(semantica.es_concepto(clave, c, dbd) for c in valores):
                nuevos.append((clave, valores))          # mixto: conceptos + respaldos físicos
            else:
                desconocidos.append(f"CONSUME: no se pudo resolver «{clave}» con {list(valores)}")
        except semantica.ErrorSemantico:
            desconocidos.append(f"CONSUME: la entidad o tabla «{clave}» no existe en DBD_4")
    if desconocidos:
        return "DESCONOCIDO", desconocidos, []
    if nuevos and viejos:
        return "MIXTO", nuevos, viejos
    if nuevos:
        return "CONCEPTOS", nuevos, []
    if viejos:
        return "COLUMNAS", [], viejos
    return "CONCEPTOS", [], []


def _columnas_consumidas(m, dbd):
    """[(tabla, columna, concepto)] de TODOS los formatos, sin repetir. No resuelve semántica por su cuenta."""
    out, vistos = [], set()
    for clave, valores in (getattr(m, "CONSUME", {}) or {}).items():
        if not isinstance(valores, (list, tuple)):
            continue
        try:
            if semantica.es_entidad(clave, dbd):
                tabla = semantica.tabla_de(clave, dbd)
                for c in valores:
                    if semantica.es_concepto(clave, c, dbd):
                        _, col = semantica.resolver(clave, c, dbd)
                    elif semantica.es_columna(clave, c, dbd):
                        col = c
                    else:
                        continue
                    if (tabla, col) in vistos:
                        continue
                    vistos.add((tabla, col))
                    _, con = semantica.concepto_de(tabla, col, dbd)
                    out.append((tabla, col, con))
            elif semantica.es_tabla(clave, dbd):
                for c in valores:
                    if not semantica.es_columna(clave, c, dbd):
                        continue
                    if (clave, c) in vistos:
                        continue
                    vistos.add((clave, c))
                    _, con = semantica.concepto_de(clave, c, dbd)
                    out.append((clave, c, con))
        except semantica.ErrorSemantico:
            continue
    return out


def _resultados_no_permitidos(m, dbd):
    """Columnas RESULTADO consumidas: FALLA salvo excepción (Método + Archivo). DEPENDE_DE no es salida."""
    out = []
    for tabla, columna, _concepto in _columnas_consumidas(m, dbd):
        if semantica.naturaleza_de(tabla, columna, dbd) != semantica.NAT_RESULTADO:
            continue
        if _excepcion(m, tabla, columna):
            continue
        out.append((tabla, columna))
    return out


def _depende_no_permitido(m):
    """Valida cada DEPENDE_DE contra kit/metodos/: el método existe y su ENTREGA[tipo] trae el concepto."""
    fallas = []
    metodos = _metodos_por_nombre()
    for nombre, deps in (getattr(m, "DEPENDE_DE", {}) or {}).items():
        objetivo = metodos.get(nombre)
        if objetivo is None:
            fallas.append(f"DEPENDE_DE: {nombre} no existe en kit/metodos/ (FICHA['nombre'])")
            continue
        entrega = getattr(objetivo, "ENTREGA", {}) or {}
        for dep in deps or ():
            if not isinstance(dep, (list, tuple)) or len(dep) < 2:
                fallas.append(f"DEPENDE_DE: {nombre} tiene una dependencia con formato inválido: {dep!r}")
                continue
            tipo, concepto = dep[0], dep[-1]
            if tipo not in entrega or concepto not in entrega[tipo]:
                fallas.append(f"DEPENDE_DE: {nombre} no entrega ({tipo}, {concepto})")
    return fallas


def _mensaje_resultado(tabla, columna):
    return (f"CONSUME: {tabla}.{columna} es RESULTADO y no figura en EXCEPCIONES_RESULTADO.md "
            f"(Método + Archivo)")


# ---------------- T-164 (OT-047): CONTRATO DEL EJE (DBD_7) y CUADRES ----------------
_CONTRATOS = {}
TOL_MONTO = 0.01


def _contrato_dbd7(dbd=None):
    """{EJE: [fila]} de la sección «Contrato del eje» de DBD_7_Frontera_Puertos. El contrato vive en el DBD, no en el código."""
    from openpyxl import load_workbook
    ruta = semantica.ruta_dbd(dbd)
    if ruta in _CONTRATOS:
        return _CONTRATOS[ruta]
    out = {}
    wb = load_workbook(ruta, read_only=True, data_only=True)
    try:
        if "DBD_7_Frontera_Puertos" not in wb.sheetnames:
            _CONTRATOS[ruta] = out
            return out
        activo = False
        for fila in wb["DBD_7_Frontera_Puertos"].iter_rows(values_only=True):
            c = [("" if x is None else str(x).strip()) for x in (list(fila) + [""] * 7)[:7]]
            if c[0].upper() == "EJE" and c[1].upper() == "DIRECCION":
                activo = True
                continue
            if activo and c[0] and c[1].upper() in ("RECIBE", "ENTREGA"):
                m = re.match(r"([A-Z][A-Z0-9_]*)\.([A-Z][A-Z0-9_]*)", c[2])
                out.setdefault(c[0].upper(), []).append(dict(
                    direccion=c[1].upper(), concepto=c[2], tipo=m.group(1) if m else None,
                    clave=m.group(2) if m else None, obligatorio=c[5].upper() == "S", regla=c[6]))
    finally:
        wb.close()
    _CONTRATOS[ruta] = out = dict(out, ACUMULACION=out["LIQUIDACION_OBJETO"]) if "LIQUIDACION_OBJETO" in out else out   # T-184 (E-210): alias; la FICHA de un método puede seguir diciendo ACUMULACION
    return out


def _quien(m, eje):
    F = getattr(m, "FICHA", {}) or {}
    return f"MÉTODO {F.get('nombre', '?')} {F.get('version', '?')} (eje {eje})"


def _numero(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and v == v and abs(v) != float("inf")


def validar_resultados(m, res, eje, dbd=None):
    """Forma de lo que el método entrega: cada fila (tipo, clave, concepto, valor) pertenece al contrato ENTREGA del eje
    en DBD_7, la clave está bien formada y es única y el valor es un número. Cada falla nombra al MÉTODO y la regla rota."""
    q, f, visto = _quien(m, eje), [], set()
    filas = _contrato_dbd7(dbd).get(str(eje).upper())
    if not filas:
        return f
    permitido = {(x["tipo"], x["clave"]) for x in filas if x["direccion"] == "ENTREGA" and x["tipo"]}
    for i, r in enumerate(res or [], 1):
        if not isinstance(r, (list, tuple)) or len(r) != 4:
            f.append(f"{q}: resultado {i} debe ser (tipo, clave, concepto, valor)")
            continue
        t, k, con, v = r
        if (t, con) not in permitido:
            f.append(f"{q}: resultado ({t}, {con}) no está en el contrato ENTREGA del eje (DBD_7)")
        if isinstance(k, bool) or not isinstance(k, (str, int)) or not str(k).strip():
            f.append(f"{q}: clave mal formada {k!r} en ({t}, {con}): debe ser texto o entero no vacío")
        elif isinstance(k, str) and k != k.strip():
            f.append(f"{q}: clave mal formada {k!r} en ({t}, {con}): tiene espacios en los extremos")
        if not _numero(v):
            f.append(f"{q}: valor no numérico {v!r} en ({t}, {k}, {con})")
        if (t, k, con) in visto:
            f.append(f"{q}: resultado repetido ({t}, {k}, {con}): se contaría dos veces")
        visto.add((t, k, con))
    if eje == "VALUACION":
        for t, k, con, _v in (x for x in (res or []) if isinstance(x, (list, tuple)) and len(x) == 4):
            if t == "SALIDA" and _linea_de_clave(k) is None:
                f.append(f"{q}: clave de salida {k!r} mal formada: debe ser numérica EVE_NUM*1000+LIN_NUM "
                         f"(entero, LIN 1..999; E-175/E-178: una línea = una clave, el almacén sale de la línea)")
    return f


def _linea_de_clave(k):
    """(evento, línea) de una clave SALIDA, o None. Clave NUMÉRICA de la línea: EVE_NUM*1000 + LIN_NUM (E-175, contrato
    DBD_7; máx. 999 líneas por evento). Un entero, o el mismo entero como texto de dígitos; el texto «EVE-LIN-ALM» ya no vale."""
    if isinstance(k, bool):
        return None
    try:
        if isinstance(k, int):
            n = k
        elif isinstance(k, float) and k == int(k):
            n = int(k)
        elif isinstance(k, str) and re.fullmatch(r"[0-9]+", k):
            n = int(k)
        else:
            return None
    except (ValueError, OverflowError):
        return None
    e, l = divmod(n, 1000)
    return (e, l) if e >= 1 and 1 <= l <= 999 else None


def validar_contrato(m, eje=None, dbd=None):
    """FICHA y ENTREGA del método contra el contrato del eje en DBD_7: cada concepto OBLIGATORIO de ENTREGA debe estar
    declarado. `eje` es el del contrato (en el registro, MRG_EJE); por omisión, el de la FICHA. Sin contrato para el eje
    → sin exigencias (no se inventa)."""
    F = getattr(m, "FICHA", {}) or {}
    eje = str(eje or F.get("eje") or "").upper()
    filas = _contrato_dbd7(dbd).get(eje)
    if not filas:
        return []
    q, f = _quien(m, eje), []
    ent = getattr(m, "ENTREGA", {}) or {}
    for x in filas:
        if x["direccion"] != "ENTREGA" or not x["obligatorio"] or not x["tipo"]:
            continue
        if x["tipo"] not in ent or x["clave"] not in (ent[x["tipo"]] or ()):
            f.append(f"{q}: ENTREGA no declara ({x['tipo']}, {x['clave']}), obligatorio en el contrato del eje (DBD_7)")
    return f


def _kardex(hechos):
    for filas in (hechos or {}).values():
        if isinstance(filas, list) and filas and isinstance(filas[0], dict) and "KDX_CAN" in filas[0]:
            return filas
    return None


def cuadre_valuacion(m, hechos, res):
    """Eje VALUACION: salidas valorizadas + saldo = ingresos, por recurso y almacén (valor y cantidad). Además, cada salida
    del KARDEX tiene su CU y MONTO, MONTO = cantidad × CU, y no hay salidas inventadas ni repetidas (anti doble conteo)."""
    q = _quien(m, "VALUACION")
    kar = _kardex(hechos)
    if kar is None and not any(isinstance(v, list) and v for v in (hechos or {}).values()):
        kar = []                                          # base sin movimientos: solo cuadra si no entrega nada
    if kar is None:
        return [f"{q}: cuadre de VALUACION no verificable: los hechos no traen KARDEX (KDX_CAN)"]
    f = []
    por_linea = {}
    for r in kar:
        por_linea[(int(r["KDX_EVE"]), int(r["KDX_LIN"]))] = r
    cu, mto, exi = {}, {}, {}
    for t, k, con, v in res:
        if not _numero(v):
            continue                                      # ya lo señala validar_resultados
        if t == "SALIDA":
            ln = _linea_de_clave(k)
            if ln is None:
                continue                                  # ya lo señala validar_resultados
            if ln not in por_linea or float(por_linea[ln]["KDX_CAN"]) >= 0:
                f.append(f"{q}: cuadre: la salida {k!r} no existe en el KARDEX o no es una salida (anti doble conteo)")
                continue
            d = cu if con == "CU" else mto if con == "MONTO" else None
            if d is not None:
                if ln in d:
                    f.append(f"{q}: cuadre: la salida {k!r} trae {con} repetido (anti doble conteo)")
                d[ln] = float(v)
        elif t == "EXISTENCIA":
            exi[(str(k), con)] = float(v)
    grupos = {}
    for ln, r in por_linea.items():
        grupos.setdefault((str(r["RECURSO"]), str(r["ALMACEN"])), []).append((ln, r))
    for (rec, alm), rs in sorted(grupos.items()):
        ent_cant = ent_val = sal_val = sal_cant = 0.0
        for ln, r in rs:
            can = float(r["KDX_CAN"])
            if can > 0:
                ent_cant += can
                ent_val += float(r["KDX_VAL"])
            elif can < 0:
                sal_cant += -can
                if ln not in cu or ln not in mto:
                    f.append(f"{q}: cuadre: la salida del evento {ln[0]} línea {ln[1]} ({rec} en {alm}) no trae CU y MONTO")
                    continue
                if abs(mto[ln] - round(-can * cu[ln], 2)) > TOL_MONTO + abs(can) * 1e-6:
                    f.append(f"{q}: cuadre: MONTO {mto[ln]} ≠ cantidad {-can} × CU {cu[ln]} en la salida del evento {ln[0]} línea {ln[1]}")
                sal_val += mto[ln]
        kx = f"{rec}-{alm}"
        if (kx, "CANTIDAD") not in exi or (kx, "VALOR") not in exi:
            f.append(f"{q}: cuadre: falta EXISTENCIA (CANTIDAD y VALOR) de {kx}")
            continue
        if abs(ent_cant - sal_cant - exi[(kx, "CANTIDAD")]) > 1e-6:
            f.append(f"{q}: cuadre de cantidad en {kx}: ingresos {ent_cant} − salidas {sal_cant} ≠ saldo {exi[(kx, 'CANTIDAD')]}")
        if abs(ent_val - (sal_val + exi[(kx, "VALOR")])) > TOL_MONTO:
            f.append(f"{q}: cuadre de valor en {kx}: ingresos {round(ent_val, 2)} ≠ salidas valorizadas {round(sal_val, 2)} "
                     f"+ saldo {exi[(kx, 'VALOR')]}")
    return f


def cuadres_eje(m, hechos, res, eje=None, dbd=None):
    """Forma de los resultados + cuadre del eje. Lista de rechazos (vacía = pasa); cada uno señala al MÉTODO y la regla rota."""
    F = getattr(m, "FICHA", {}) or {}
    eje = str(eje or F.get("eje") or "").upper()
    f = validar_resultados(m, res, eje, dbd)
    if eje == "VALUACION":
        f += cuadre_valuacion(m, hechos, res)
    return f


def validar(m, dbd=None, permitir_pendiente=False):
    """Lista de FALLAS (vacía = compatible). Los avisos OBSOLETOS van por avisos(), no son fallas."""
    f = []
    F = getattr(m, "FICHA", None)
    if not isinstance(F, dict):
        return ["falta FICHA"]
    # OT-036: la identidad del método es única; el duplicado es FALLA para todos, incluso si es PENDIENTE.
    nombre_ficha = str(F.get("nombre", "")).strip()
    if nombre_ficha:
        mods = _modulos_por_nombre().get(nombre_ficha, [])
        if len(mods) > 1:
            return [f"FICHA: nombre {nombre_ficha} duplicado en "
                    f"{_lista_duplicados([rel for rel, _ in mods])}"]
    f += [f"FICHA sin '{k}'" for k in ("nombre", "version", "vigente_desde", "eje", "objetivo", "que_hace",
                                       "formula", "fuente", "limites") if not F.get(k)]
    if F.get("vigente_desde") and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(F["vigente_desde"])):
        f.append("vigente_desde debe ser AAAA-MM-DD")
    if F.get("eje") not in ejes_ficha(): f.append(f"eje '{F.get('eje')}' no es uno de {sorted(ejes_ficha())}")
    if F.get("objetivo") not in OBJ:
        f.append("objetivo debe ser REAL, CONTABLE o ESTIMADO")
    for k in ("CONSUME", "ENTREGA", "PARAMETROS", "DEPENDE_DE", "CASOS"):
        if not hasattr(m, k):
            f.append(f"falta {k}")
    if not callable(getattr(m, "calcular", None)):
        f.append("falta calcular(hechos, parametros, previos)")
    if f:
        return f

    formato, nuevos, viejos = _clasificar(m, dbd)
    if formato == "DESCONOCIDO":
        f += nuevos
    else:
        if formato in ("CONCEPTOS", "MIXTO"):
            for entidad, valores in nuevos:
                if not semantica.es_entidad(entidad, dbd):
                    f.append(f"CONSUME: la entidad MCD {entidad} no existe en DBD_4")
                    continue
                for concepto in valores:
                    if not semantica.es_concepto(entidad, concepto, dbd) \
                            and not semantica.es_columna(entidad, concepto, dbd):
                        f.append(f"CONSUME: el concepto {concepto} no existe en la entidad {entidad} de DBD_4")
        if formato in ("COLUMNAS", "MIXTO"):
            for tabla, valores in viejos:
                for columna in valores:
                    if not semantica.es_columna(tabla, columna, dbd):
                        f.append(f"CONSUME: {tabla}.{columna} no existe en DBD_4")
    if f:
        return f

    # E-133: DEPENDE_DE se valida aparte y NO abre el control de RESULTADO en CONSUME.
    depende = _depende_no_permitido(m)
    resultados = _resultados_no_permitidos(m, dbd)
    if getattr(m, "PENDIENTE", False):
        if permitir_pendiente:
            return []
        return depende + [_mensaje_resultado(t, c) for t, c in resultados] + \
               ["PENDIENTE: el método aún no tiene su cálculo (cáscara con contrato)"]
    f += depende + [_mensaje_resultado(t, c) for t, c in resultados]
    f += validar_contrato(m, None, dbd)
    if f:
        return f
    if not m.CASOS:
        f.append("CASOS: falta al menos un caso calculado a mano")
    for c in m.CASOS:
        try:
            res, expl = m.calcular(c["hechos"], c["parametros"], c.get("previos", {}))
        except Exception as ex:
            f.append(f"caso «{c['nombre']}»: error {ex}")
            continue
        for t, clave, con, v in res:
            if t not in m.ENTREGA or con not in m.ENTREGA[t]:
                f.append(f"caso «{c['nombre']}»: entrega ({t}, {con}) no declarada en ENTREGA")
        dic = {(t, k, con): v for t, k, con, v in res}
        for t, k, con, v in c["espera"]:
            got = dic.get((t, k, con))
            if got is None or abs(float(got) - float(v)) > 0.005:
                f.append(f"caso «{c['nombre']}»: {t} {k} {con} esperado {v}, obtenido {got}")
        if not expl:
            f.append(f"caso «{c['nombre']}»: falta la explicación paso a paso")
        r2, _ = m.calcular(c["hechos"], c["parametros"], c.get("previos", {}))
        if r2 != res:
            f.append(f"caso «{c['nombre']}»: no es reproducible (dos corridas dan distinto)")
        f += [f"caso «{c['nombre']}»: {x}" for x in cuadres_eje(m, c["hechos"], res, None, dbd)]
    return f


def deudas(m, dbd=None):
    """Deudas de una cáscara PENDIENTE: no bloquean hoy, bloquean al quitar PENDIENTE."""
    if not getattr(m, "PENDIENTE", False):
        return []
    out = ["DEUDA (bloquea al quitar PENDIENTE): " + x for x in _depende_no_permitido(m)]
    out += [f"DEUDA (bloquea al quitar PENDIENTE): {t}.{c} es RESULTADO y no figura en "
            f"EXCEPCIONES_RESULTADO.md (Método + Archivo)" for t, c in _resultados_no_permitidos(m, dbd)]
    return out


def avisos(m, dbd=None):
    """Avisos que NO bloquean: formato viejo por columnas y respaldos físicos (deuda de OT-021, V6)."""
    a = []
    F = getattr(m, "FICHA", None)
    if not isinstance(F, dict) or not hasattr(m, "CONSUME"):
        return a
    formato, nuevos, viejos = _clasificar(m, dbd)
    if formato == "COLUMNAS":
        a.append("OBSOLETO: CONSUME por columnas (tabla -> columna); migre a {entidad MCD: [concepto]} (OT-022)")
    elif formato == "MIXTO":
        a.append("OBSOLETO: CONSUME mezcla conceptos y nombres físicos; complete la migración a conceptos (OT-022)")
    if formato in ("CONCEPTOS", "MIXTO"):
        vistos = set()
        for entidad, valores in nuevos:
            for concepto in valores:
                if not semantica.es_concepto(entidad, concepto, dbd) and semantica.es_columna(entidad, concepto, dbd):
                    if (entidad, concepto) in vistos:
                        continue
                    vistos.add((entidad, concepto))
                    tabla = semantica.tabla_de(entidad, dbd)
                    nat = semantica.naturaleza_de(tabla, concepto, dbd)
                    if nat == semantica.NAT_RESULTADO:
                        a.append(f"OBSOLETO: {entidad}.{concepto} usa el nombre físico de una columna RESULTADO "
                                 f"(deuda V6: falta Concepto/HECHO en DBD_4)")
                    else:
                        a.append(f"OBSOLETO: {entidad}.{concepto} usa el nombre físico de una columna sin Concepto "
                                 f"en DBD_4 (deuda V6)")
    return a


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python -m metodos.validar_metodo metodos/<metodo>.py [DBD_Fuente.xlsx]")
        sys.exit(2)
    m = cargar(sys.argv[1])
    dbd = sys.argv[2] if len(sys.argv) > 2 else None
    fallas, avisos_ = validar(m, dbd), avisos(m, dbd)
    for aviso in avisos_:
        print("AVISO: " + aviso)
    for deuda in deudas(m, dbd):
        print("DEUDA: " + deuda)
    print("FORMATO COMPATIBLE" if not fallas else "NO COMPATIBLE:\n  - " + "\n  - ".join(fallas))
    sys.exit(1 if fallas else 0)
