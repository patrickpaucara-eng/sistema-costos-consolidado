# -*- coding: utf-8 -*-
"""OT-026 (T-174, E-190) · PUERTO ANALÍTICO: capa de DECISIÓN conectada, sin crear métodos.

Los ejes de decisión (ESTIMACION, PRONOSTICO, DIFERENCIAS, SIMULACION) se atienden con proveedores intercambiables
(kit/analitica/proveedores, que aquí solo son sujetos de prueba). El puerto:
  · lee hechos por concepto (puerto de lectura de la base) y los vuelve extracto canónico (fecha, entidad, clave, concepto, valor, unidad);
  · elige el proveedor VIGENTE del eje con las filas de METODO_REGISTRADO (APROBADO y vigente a la fecha); sin vigente, falla (sin respaldo oculto);
  · rechaza al proveedor que no pasa el kit de conformidad (contrato común + contrato del eje en DBD_7 con el validador T-164);
  · entrega formato largo de RESULTADO_METODO con TIPO = ESTIMADO (R46) y `.P05` / `.P95` / `.CONF`, con proveedor, versión y huella;
  · modo SOMBRA: el retador corre en una ventana de prueba, NO publica, y se compara por backtesting (error y cobertura).
NUNCA escribe en la base ni en hechos ni en el cierre: no importa editar_b ni abre libros para escribir. Puro salvo `leer_extracto`."""
import hashlib
import json
import os
import sys
from types import SimpleNamespace

_KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _KIT not in sys.path:
    sys.path.insert(0, _KIT)
from analitica import proveedores as C          # contrato común (validar_ficha / entrada / salida)

TIPO = "ESTIMADO"                               # R46: lo que sale de aquí es un estimado, nunca un hecho
EJES = {"ESTIMACION": ("ESTIMACION",), "PRONOSTICO": ("PRONOSTICO",),
        "DIFERENCIAS": ("VARIACION",), "SIMULACION": ("SIMULACION", "OPTIMIZACION")}


def base(concepto):
    """Concepto del contrato: `<serie>|PRONOSTICO` → PRONOSTICO; sin barra, el mismo."""
    return str(concepto).rsplit("|", 1)[-1]


# ---------------------------------------------------------------- entrada
def extracto_de_hechos(hechos, fecha):
    """{entidad: [{concepto: valor}]} (salida de puerto_lectura.leer_conceptos) → extracto canónico. Solo valores numéricos.
    clave = CLAVE de la fila o «entidad:n»; fecha = FECHA de la fila o la dada; unidad = UNIDAD de la fila o ''."""
    out = []
    for ent in sorted(hechos):
        for n, fila in enumerate(hechos[ent], 1):
            for con in sorted(fila):
                v = fila[con]
                if con in ("CLAVE", "FECHA", "UNIDAD") or isinstance(v, bool) or not isinstance(v, (int, float)) or v != v:
                    continue
                out.append(dict(fecha=fila.get("FECHA") or fecha, entidad=ent, clave=str(fila.get("CLAVE") or "%s:%d" % (ent, n)),
                                concepto=con, valor=v, unidad=fila.get("UNIDAD") or ""))
    return out


def leer_extracto(libro, consume, fecha, dbd=None):
    """Lee la base SOLO por el puerto de lectura (E-098) y arma el extracto. No escribe nada."""
    import puerto_lectura
    return extracto_de_hechos(puerto_lectura.leer_conceptos(libro, consume, dbd=dbd), fecha)


# ---------------------------------------------------------------- registro y vigencia
def _fecha(v):
    return int(str(v).replace("-", ""))


def vigente(registro, eje, fecha):
    """Fila de METODO_REGISTRADO (APROBADO, del eje, desde <= fecha) con el MRG_DESDE mayor. Sin ninguna: ValueError."""
    if eje not in EJES:
        raise ValueError("eje de decisión desconocido: %r (válidos: %s)" % (eje, ", ".join(sorted(EJES))))
    c = [r for r in registro if r.get("MRG_EJE") == eje and r.get("MRG_EST") == "APROBADO" and _fecha(r["MRG_DESDE"]) <= _fecha(fecha)]
    if not c:
        raise ValueError("El eje %s no tiene proveedor vigente aprobado al %s: no se calcula nada por detrás" % (eje, fecha))
    return max(c, key=lambda r: (_fecha(r["MRG_DESDE"]), str(r["MRG_VER"])))


def cargar(fila, eje):
    """Importa el módulo de la fila y comprueba que su FICHA coincide con el registro y con la familia del eje."""
    mod = C.cargar(os.path.splitext(os.path.basename(str(fila["MRG_ARCHIVO"])))[0])
    F = mod.FICHA
    if (F["nombre"], str(F["version"])) != (fila["MRG_COD"], str(fila["MRG_VER"])):
        raise ValueError("el registro dice %s %s pero la FICHA dice %s %s" % (fila["MRG_COD"], fila["MRG_VER"], F["nombre"], F["version"]))
    if F["familia"] not in EJES[eje]:
        raise ValueError("%s es de la familia %s y no atiende el eje %s" % (F["nombre"], F["familia"], eje))
    return mod


# ---------------------------------------------------------------- resultado largo
def huella(ficha, extracto, parametros):
    """16 hex del proveedor, su versión, los parámetros y el extracto: la misma entrada da la misma huella."""
    t = json.dumps([ficha["nombre"], str(ficha["version"]), parametros or {}, extracto], sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(t.encode("utf-8")).hexdigest()[:16]


def a_resultado(ficha, salida, per, emp, hue):
    """Formato largo de RESULTADO_METODO: (RES_METODO, RES_VER, RES_PER, RES_EMP, RES_HUELLA, RES_TIPO, RES_CLAVE, RES_CONC, RES_VALOR).
    Por cada fila del proveedor: <concepto>, .P05, .P95 y .CONF (esta última solo si el proveedor informa confianza)."""
    out = []
    for f in salida:
        k = str(f["clave"])
        for suf, v in (("", f["valor"]), (".P05", f["p05"]), (".P95", f["p95"]), (".CONF", f["conf"])):
            if v is not None:
                out.append((ficha["nombre"], str(ficha["version"]), per, emp, hue, TIPO, k, f["concepto"] + suf, v))
    return out


# ---------------------------------------------------------------- kit de conformidad
def _shim(mod, eje):
    """Objeto con la forma que espera el validador T-164 (FICHA + ENTREGA) a partir de la FICHA del proveedor."""
    F = mod.FICHA
    return SimpleNamespace(FICHA=dict(nombre=F["nombre"], version=F["version"], eje=eje), ENTREGA={TIPO: sorted({base(c) for c in F["produce"]})})


def conformidad(mod, eje, extracto, parametros=None, dbd=None):
    """Casos que TODO proveedor debe pasar. Devuelve la lista de fallas (vacía = conforme):
    ficha válida · entrada rechazada si está mal formada · salida con p05 <= valor <= p95 y conf en [0,1] · conceptos dentro de FICHA.produce ·
    determinista (dos corridas iguales) · no altera el extracto · cada fila (tipo, clave, concepto, valor) pasa el contrato ENTREGA del eje en DBD_7 (T-164)."""
    from metodos import validar_metodo as VM
    f, q = [], "%s %s" % (getattr(mod, "FICHA", {}).get("nombre", "?"), getattr(mod, "FICHA", {}).get("version", "?"))
    try:
        C.validar_ficha(mod.FICHA)
        if not callable(getattr(mod, "ejecutar", None)):
            raise ValueError("no define ejecutar()")
        if mod.FICHA["familia"] not in EJES[eje]:
            raise ValueError("su familia %s no atiende el eje %s" % (mod.FICHA["familia"], eje))
    except (ValueError, KeyError) as e:
        return ["%s: ficha: %s" % (q, e)]
    try:
        mod.ejecutar([{"fecha": "2026-01"}], dict(parametros or {}))
        f.append("%s: aceptó una fila de entrada sin entidad, clave, concepto, valor ni unidad" % q)
    except (ValueError, KeyError, TypeError):
        pass
    copia = json.dumps(extracto, sort_keys=True, default=str)
    try:
        s1 = C.ejecutar_validado(mod, extracto, parametros)
        s2 = C.ejecutar_validado(mod, extracto, parametros)
    except Exception as e:                                            # cualquier error con entrada válida es no conformidad
        return f + ["%s: falló con una entrada válida: %s" % (q, e)]
    if json.dumps(s1, sort_keys=True, default=str) != json.dumps(s2, sort_keys=True, default=str):
        f.append("%s: no es determinista (dos corridas con la misma entrada difieren)" % q)
    if json.dumps(extracto, sort_keys=True, default=str) != copia:
        f.append("%s: modificó el extracto de entrada" % q)
    perm = {base(c) for c in mod.FICHA["produce"]}
    for r in s1:
        if base(r["concepto"]) not in perm:
            f.append("%s: entrega %r, que no declara en FICHA.produce" % (q, r["concepto"]))
    filas = [(TIPO, str(r["clave"]) if "|" not in str(r["concepto"]) else "%s|%s" % (r["clave"], str(r["concepto"]).rsplit("|", 1)[0]),
              base(r["concepto"]), r["valor"]) for r in s1]
    f += VM.validar_resultados(_shim(mod, eje), filas, eje, dbd)
    f += VM.validar_contrato(_shim(mod, eje), eje, dbd)
    return f


# ---------------------------------------------------------------- correr
def correr(registro, eje, extracto, per, emp, fecha, parametros=None, dbd=None):
    """Corre SOLO el proveedor vigente del eje. Si no es conforme, lo rechaza (ValueError con las fallas). Devuelve
    {proveedor, version, huella, filas}: filas en formato largo con TIPO = ESTIMADO. No escribe en ninguna parte."""
    fila = vigente(registro, eje, fecha)
    mod = cargar(fila, eje)
    mal = conformidad(mod, eje, extracto, parametros, dbd)
    if mal:
        raise ValueError("RECHAZADO por conformidad: " + "; ".join(mal))
    salida = C.ejecutar_validado(mod, extracto, parametros)
    hue = huella(mod.FICHA, extracto, parametros)
    return dict(proveedor=mod.FICHA["nombre"], version=str(mod.FICHA["version"]), huella=hue,
                filas=a_resultado(mod.FICHA, salida, per, emp, hue))


# ---------------------------------------------------------------- backtesting y sombra
def backtest(mod, extracto, parametros=None, desde=None):
    """Origen móvil: para cada fecha de corte con al menos `desde` fechas anteriores, corre el proveedor con la historia previa y compara cada
    fila `<serie>|PRONOSTICO` con el valor real de la fecha siguiente. Devuelve {n, mae, cobertura} (cobertura = parte de reales dentro de [p05, p95]).
    Proveedores sin filas comparables dan n = 0 (no hay nada que contrastar)."""
    fechas = sorted({e["fecha"] for e in extracto})
    desde = desde or max(3, len(fechas) // 2)
    errs, dentro = [], 0
    for i in range(desde, len(fechas)):
        hist = [e for e in extracto if e["fecha"] < fechas[i]]
        reales = {(e["clave"], e["concepto"]): e["valor"] for e in extracto if e["fecha"] == fechas[i]}
        for r in mod.ejecutar(hist, dict(parametros or {})):
            if not str(r["concepto"]).endswith("|PRONOSTICO"):
                continue
            v = reales.get((r["clave"], r["concepto"].rsplit("|", 1)[0]))
            if v is None:
                continue
            errs.append(abs(r["valor"] - v))
            dentro += r["p05"] - 1e-9 <= v <= r["p95"] + 1e-9
    n = len(errs)
    return dict(n=n, mae=(sum(errs) / n if n else None), cobertura=(dentro / n if n else None))


def sombra(registro, eje, retador, extracto, per, emp, fecha, ventana, parametros=None, par_retador=None, dbd=None):
    """El vigente publica; el retador (cod, ver) corre SOLO si `fecha` está en la ventana (desde, hasta) y NUNCA publica:
    su resultado es un informe de backtesting contra el del vigente. Devuelve {publicadas, sombra}; sombra = None fuera de la ventana."""
    pub = correr(registro, eje, extracto, per, emp, fecha, parametros, dbd)
    d, h = ventana
    if not (_fecha(d) <= _fecha(fecha) <= _fecha(h)):
        return dict(publicadas=pub, sombra=None)
    fila = next((r for r in registro if (r["MRG_COD"], str(r["MRG_VER"])) == (retador[0], str(retador[1])) and r.get("MRG_EJE") == eje), None)
    if fila is None:
        raise ValueError("el retador %s %s no está registrado en el eje %s" % (retador[0], retador[1], eje))
    mod = cargar(fila, eje)
    mal = conformidad(mod, eje, extracto, par_retador, dbd)
    if mal:
        return dict(publicadas=pub, sombra=dict(retador=retador[0], version=str(retador[1]), estado="RECHAZADO", fallas=mal, publica=False))
    mv, mr = cargar(vigente(registro, eje, fecha), eje), mod
    bv, br = backtest(mv, extracto, parametros), backtest(mr, extracto, par_retador)
    return dict(publicadas=pub, sombra=dict(retador=retador[0], version=str(retador[1]), estado="EN_SOMBRA", publica=False,
                                          vigente=bv, retador_backtest=br,
                                          mejor_error=bool(br["mae"] is not None and bv["mae"] is not None and br["mae"] < bv["mae"]),
                                          huella=huella(mod.FICHA, extracto, par_retador)))
