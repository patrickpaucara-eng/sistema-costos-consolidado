# -*- coding: utf-8 -*-
"""CONECTOR DE MÉTODOS (E-106): sin programar, con un doble clic (correr_metodos.bat).
1. Descubre todos los métodos de esta carpeta y valida su formato.
2. Para el periodo pedido elige, por EJE, la versión VIGENTE (Tino): la de mayor «vigente desde» que no pase del inicio
   del periodo, APROBADA en METODO_REGISTRADO y con archivo compatible. Así un periodo pasado se recalcula con el método
   que regía entonces, no con el último.
3. Ordena los métodos por sus dependencias (DEPENDE_DE) y los corre con los hechos del puerto de lectura de la base.
4. Deja un Excel para revisar (estado, resultados, explicación) y, con --publicar, la bandeja para el puerto T25.4.
Uso (desde la carpeta del sistema): python -m metodos.correr_metodos Sistema_Costos.xlsx PERIODO EMPRESA [--publicar] [--incluir-en-prueba]"""
import os, sys, glob, importlib.util, datetime
AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.dirname(AQUI)
for p in (RAIZ, os.path.join(RAIZ, "validacion_python")): sys.path.insert(0, p)
import rutas
from metodos import validar_metodo as VM, publicar as PB
import puerto_lectura

NO_METODO = {"__init__", "_plantilla_metodo", "validar_metodo", "probar_metodos", "publicar", "correr_metodos", "valuacion_base", "caso_excel", "puerta", "semantica"}


def hechos_por_concepto(filas_por_tabla, consume, dbd=None):
    """Envoltorio único base física -> hechos por entidad/concepto. La resolución la hace semantica.
    filas_por_tabla = {tabla: [{columna: valor}]}; consume = {entidad MCD: [concepto]} o el formato viejo."""
    from metodos import semantica
    return semantica.traducir_hechos(filas_por_tabla, consume, dbd=dbd)

def descubrir(dbd=None):
    out = []
    for ruta in sorted(glob.glob(os.path.join(AQUI, "*.py"))):
        n = os.path.splitext(os.path.basename(ruta))[0]
        if n in NO_METODO or n.startswith("_"): continue
        try: m = VM.cargar(ruta); faltas = VM.validar(m, dbd)
        except Exception as ex: m, faltas = None, [f"no se pudo cargar: {ex}"]
        out.append(dict(archivo=os.path.basename(ruta), modulo=m, faltas=faltas, ficha=getattr(m, "FICHA", {}) if m else {}))
    return out

def elegir(metodos, registro, inicio_per, incluir_prueba=False):
    """Por eje: el APROBADO (o EN_PRUEBA si se pide) con mayor vigente_desde ≤ inicio del periodo y archivo compatible (E-168: vigencia numérica AAAAMMDD, sin texto ISO)."""
    ok_est = {"APROBADO"} | ({"EN_PRUEBA"} if incluir_prueba else set())
    reg = {(r["MRG_COD"], str(r["MRG_VER"])): r for r in registro}
    candidatos = {}
    for d in metodos:
        F = d["ficha"]
        if d["faltas"] or not F: continue
        r = reg.get((F["nombre"], str(F["version"])))
        if not r or r.get("MRG_EST") not in ok_est: continue
        desde = int(r.get("MRG_DESDE") or str(F["vigente_desde"]).replace("-", ""))
        if desde > int(inicio_per): continue
        actual = candidatos.get(F["eje"])
        if not actual or desde > actual[0]: candidatos[F["eje"]] = (desde, d)
    return [d for _, d in candidatos.values()]

def ordenar(elegidos):
    por_nombre = {d["ficha"]["nombre"]: d for d in elegidos}; hecho, orden = set(), []
    def visita(d, pila=()):
        n = d["ficha"]["nombre"]
        if n in hecho: return
        if n in pila: raise ValueError("Dependencia circular entre métodos: " + " → ".join(pila + (n,)))
        for dep in d["modulo"].DEPENDE_DE:
            if dep not in por_nombre: raise ValueError(f"{n} necesita {dep}, que no está vigente para el periodo")
            visita(por_nombre[dep], pila + (n,))
        hecho.add(n); orden.append(d)
    for d in elegidos: visita(d)
    return orden

def correr(libro, per, emp, publicar=False, incluir_prueba=False):
    dbd = os.path.join(rutas.FUENTE, "DBD_Fuente.xlsx"); dbd = dbd if os.path.exists(dbd) else None
    todos = descubrir(dbd)
    base = puerto_lectura.leer(libro, ["METODO_REGISTRADO", "PERIODO"])
    p = next((x for x in base["PERIODO"] if x["PER_COD"] == per and x["PER_EMP"] == emp), None)
    if not p: raise ValueError(f"No existe el periodo {per} de la empresa {emp}")
    ini = int(p["PER_INI"])
    orden = ordenar(elegir(todos, base["METODO_REGISTRADO"], ini, incluir_prueba))
    previos, filas, expl = {}, [], []
    reg = {(r["MRG_COD"], str(r["MRG_VER"])): r for r in base["METODO_REGISTRADO"]}
    for d in orden:
        m = d["modulo"]; hechos = puerto_lectura.leer_conceptos(libro, m.CONSUME, dbd=dbd)
        # T-164: el eje del contrato es el del REGISTRO (MRG_EJE); antes de calcular, ENTREGA contra DBD_7; después, forma y cuadre.
        eje = (reg.get((m.FICHA["nombre"], str(m.FICHA["version"]))) or {}).get("MRG_EJE") or m.FICHA["eje"]
        rechazo = VM.validar_contrato(m, eje, dbd)
        if rechazo: raise ValueError("RECHAZADO por contrato: " + "; ".join(rechazo))
        res, ex = m.calcular(hechos, dict(PER=per, EMP=emp), {k: previos[k] for k in m.DEPENDE_DE})
        rechazo = VM.cuadres_eje(m, hechos, res, eje, dbd)
        if rechazo: raise ValueError("RECHAZADO por cuadre: " + "; ".join(rechazo))
        previos[m.FICHA["nombre"]] = res; filas += [(m.FICHA["nombre"], m.FICHA["version"], *r) for r in res]; expl += [(m.FICHA["nombre"], e) for e in ex]
        if publicar:
            linea = ["T25.4", "(quien procesa)", PB.trama(per, emp, m.FICHA["nombre"], m.FICHA["version"], hechos, PB.redondear_alg09(res) if getattr(m, "REDONDEO", "") == "ALG-09" else res), "", "metodos", datetime.datetime.now().isoformat(timespec="seconds")]
            ban = os.path.join(os.path.dirname(os.path.abspath(libro)), "bandeja_carga.csv"); nuevo = not os.path.exists(ban)
            with open(ban, "a", encoding="utf-8") as fh:
                if nuevo: fh.write("TRX\tUSUARIO\tTRAMA\tESCENARIO\tMOTIVO\tFECHA_HORA\n")
                fh.write("\t".join(linea) + "\n")
    from openpyxl import Workbook
    wb = Workbook(); ws = wb.active; ws.title = "Estado"
    ws.append(["Archivo", "Método", "Versión", "Vigente desde", "Eje", "Objetivo", "Compatible", "Usado en el periodo", "Observación"])
    usados = {d["archivo"] for d in orden}
    for d in todos:
        F = d["ficha"]; ws.append([d["archivo"], F.get("nombre"), F.get("version"), F.get("vigente_desde"), F.get("eje"), F.get("objetivo"),
                                   "SÍ" if not d["faltas"] else "NO", "SÍ" if d["archivo"] in usados else "", "; ".join(d["faltas"])[:300]])
    r = wb.create_sheet("Resultados"); r.append(["Método", "Versión", "Tipo", "Clave", "Concepto", "Valor"]); [r.append(list(f)) for f in filas]
    e = wb.create_sheet("Explicacion"); e.append(["Método", "Paso"]); [e.append(list(x)) for x in expl]
    sal = os.path.join(os.path.dirname(os.path.abspath(libro)), f"Resultados_Metodos_{per}_{emp}.xlsx"); wb.save(sal)
    return sal, todos, orden, filas

if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    sal, todos, orden, filas = correr(a[0], a[1], a[2], "--publicar" in sys.argv, "--incluir-en-prueba" in sys.argv)
    print(f"Métodos en la carpeta: {len(todos)} · compatibles: {sum(not d['faltas'] for d in todos)} · usados en {a[1]}: {', '.join(d['ficha']['nombre'] + ' ' + d['ficha']['version'] for d in orden) or 'ninguno'}")
    print(f"Resultados: {len(filas)} valores → {sal}" + (" · bandeja lista para «Procesar carga»" if "--publicar" in sys.argv else ""))
