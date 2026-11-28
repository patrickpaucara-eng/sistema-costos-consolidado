"""B8 · Síntesis del plan (decisión del dueño, 28-nov).

El plan es la base: un conjunto de líneas de ticket. Cada línea trae recurso, monto, fecha de devengo,
fecha de caja, clase y estado. Todo presupuesto es una SÍNTESIS de esas líneas: un filtro de clases,
un reloj (devengo o caja) y una agrupación. Las síntesis son datos (catálogo), no código: crear un
presupuesto nuevo es agregar una fila a CATALOGO.

Solo biblioteca estándar. No conoce la calculadora ni los eventos: recibe líneas ya armadas.
"""
from collections import defaultdict

CLASES = ("INGRESO", "EGRESO", "INVERSION", "FINANCIAMIENTO", "APORTE", "DIVIDENDO", "IMPUESTO")
ESTADOS = ("programado", "comprometido", "ejecutado")
RELOJES = ("devengo", "caja")
SIGNO = {"INGRESO": 1, "EGRESO": -1, "INVERSION": -1, "FINANCIAMIENTO": 1, "APORTE": 1, "DIVIDENDO": -1, "IMPUESTO": -1}
CAMPOS = ("ticket", "recurso", "monto", "fecha_devengo", "fecha_caja", "clase", "estado")
# Campo opcional «sentido» (agregado 28-nov con lineas.py): FINANCIAMIENTO y APORTE van en los dos sentidos
# (se toma y se devuelve un préstamo; se aporta y se retira capital). Sin «sentido» manda SIGNO[clase].
SENTIDOS = {"entrada": 1, "salida": -1}
DOS_SENTIDOS = ("FINANCIAMIENTO", "APORTE")

# nombre: (reloj, clases o None = todas, agrupar por)
CATALOGO = {
    "Presupuesto operativo": ("devengo", ("INGRESO", "EGRESO"), ("periodo", "clase")),
    "Presupuesto de efectivo": ("caja", None, ("periodo",)),
    "Presupuesto de inversiones": ("devengo", ("INVERSION",), ("periodo", "recurso")),
    "Presupuesto financiero": ("caja", ("FINANCIAMIENTO", "APORTE", "DIVIDENDO", "IMPUESTO"), ("periodo", "clase")),
}


class LineaInvalida(ValueError):
    pass


def validar(linea):
    """Rechaza con mensaje en español; nunca corrige en silencio."""
    faltan = [c for c in CAMPOS if linea.get(c) in (None, "")]
    if faltan:
        raise LineaInvalida(f"Línea {linea.get('ticket', '?')}: falta {', '.join(faltan)}.")
    if linea["clase"] not in CLASES:
        raise LineaInvalida(f"Línea {linea['ticket']}: clase «{linea['clase']}» no existe ({', '.join(CLASES)}).")
    if linea["estado"] not in ESTADOS:
        raise LineaInvalida(f"Línea {linea['ticket']}: estado «{linea['estado']}» no existe.")
    if not isinstance(linea["monto"], (int, float)) or linea["monto"] < 0:
        raise LineaInvalida(f"Línea {linea['ticket']}: el monto debe ser un número ≥ 0 (el signo lo da la clase).")
    s = linea.get("sentido")
    if s is not None:
        if s not in SENTIDOS:
            raise LineaInvalida(f"Línea {linea['ticket']}: sentido «{s}» no existe (entrada, salida).")
        if linea["clase"] not in DOS_SENTIDOS and SENTIDOS[s] != SIGNO[linea["clase"]]:
            raise LineaInvalida(f"Línea {linea['ticket']}: {linea['clase']} no puede ir en sentido «{s}»; "
                                f"solo {', '.join(DOS_SENTIDOS)} van en los dos sentidos.")
    return linea


def signo(linea):
    s = linea.get("sentido")
    return SIGNO[linea["clase"]] if s is None else SENTIDOS[s]


def sintetizar(lineas, nombre, catalogo=CATALOGO, periodo=lambda f: f[:7]):
    """Devuelve {clave de agrupación: monto con signo}. periodo() convierte una fecha AAAA-MM-DD en su periodo."""
    if nombre not in catalogo:
        raise KeyError(f"No existe la síntesis «{nombre}». Disponibles: {', '.join(catalogo)}.")
    reloj, clases, grupo = catalogo[nombre]
    out = defaultdict(float)
    for l in map(validar, lineas):
        if clases is not None and l["clase"] not in clases:
            continue
        val = {"periodo": periodo(l["fecha_" + reloj]), "clase": l["clase"], "recurso": l["recurso"], "ticket": l["ticket"]}
        out[tuple(val[g] for g in grupo)] += signo(l) * l["monto"]
    return {k: round(v, 2) for k, v in sorted(out.items())}


def control_ejecucion(lineas, asignado):
    """Por recurso: asignado (techo), comprometido, ejecutado y disponible = asignado − comprometido − ejecutado.
    Lo «programado» todavía no consume el techo; si el disponible es negativo, se marca exceso."""
    uso = defaultdict(lambda: {"comprometido": 0.0, "ejecutado": 0.0})
    for l in map(validar, lineas):
        if l["estado"] != "programado":
            uso[l["recurso"]][l["estado"]] += l["monto"]
    filas = []
    for rec in sorted(set(asignado) | set(uso)):
        a = float(asignado.get(rec, 0.0)); c = uso[rec]["comprometido"]; e = uso[rec]["ejecutado"]
        d = round(a - c - e, 2)
        filas.append({"recurso": rec, "asignado": a, "comprometido": c, "ejecutado": e, "disponible": d, "exceso": d < 0})
    return filas
