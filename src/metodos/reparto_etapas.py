# -*- coding: utf-8 -*-
"""MÉTODO · REPARTO_ETAPAS (ARQUITECTURA_V4_1 §7.4, §7.5 ALG-04, §7.11 trazar/ALG-11, §7.12 ALG-09).
Un solo mecanismo de asignación por etapas para todo elemento de costo:
  P1 MD, P2 PD, P3 SD  → OBJETO o ACTIVIDAD (P2 también INEF)
  P4A IND → CENTRO o ACTIVIDAD · P4B APR → PRO · P4C PRO/ACTIVIDAD → OBJETO · P5 ADM → OBJETO · P6 VTA → OBJETO
Monto del destino = monto del origen × medida del destino / Σ medidas (Decimal). El elemento viaja con el monto
(MD, PD, SD, CIF, GAD, GVT). Estado en memoria; orden por código; I1 por etapa; I8 y R-53 detienen el cálculo.
Publicación con ALG-09 (2 decimales, residuo al mayor bruto; empate, menor código)."""
from decimal import Decimal as D, ROUND_HALF_UP, getcontext
from collections import OrderedDict, defaultdict

getcontext().prec = 28
PENDIENTE = False
REDONDEO = "ALG-09"   # V4.1 §4.3: calcular() entrega valores internos; se redondean al publicar
FICHA = dict(nombre="REPARTO_ETAPAS", version="2.0", vigente_desde="2026-01-01", eje="REPARTO", objetivo="REAL",
    que_hace="Asigna todo elemento de costo por etapas (P1 a P6) a objetos con la matriz de configuración (REGLA_REPARTO + MEDIDA)",
    formula="destino = origen × medida(destino) / Σ medidas; el elemento viaja con el monto; ALG-09 al publicar",
    fuente="ARQUITECTURA_V4_1 ALG-04; Oria (2026) procesos P1-P6 y ABC; Horngren caps. 4 y 15; NIC 2 §13",
    supuestos="Medidas del periodo cargadas; un criterio vigente por (etapa, origen); costo de material valorizado por el eje VALUACION",
    limites="Sin reparto entre centros de apoyo (método directo); escalonado y recíproco son otras versiones del eje")
CONSUME = {
    "(sin MCD) REGLA_REPARTO": ["ETAPA", "ORIGEN", "CRITERIO", "DESDE"],
    "(sin MCD) MEDIDA": ["PERIODO", "EMPRESA", "CRITERIO", "NIVEL", "DESTINO", "CANTIDAD"],
    "(sin MCD) LINEA": ["EVENTO", "NUMERO", "RECURSO", "CANTIDAD", "COSTO_UNITARIO_DOCUMENTO"],
    "EVENTO": ["NUMERO", "PERIODO", "EMPRESA", "OBJETO", "CENTRO"],
    "RECURSO": ["CODIGO", "TIPO_RECURSO"],
    "(sin MCD) TIPO_RECURSO": ["CODIGO", "ELEMENTO_COSTO"],
    "CENTRO": ["CODIGO", "EMPRESA", "TIPO"],
    "(sin MCD) OBJETO": ["NUMERO", "EMPRESA", "TIPO"],
    "ACTIVIDAD": ["CODIGO"],
    "PERIODO": ["CODIGO", "EMPRESA", "INICIO"],
}
DEPENDE_DE = {"VALUACION_PROMEDIO": [("SALIDA", "MONTO")]}
PARAMETROS = [dict(id="PER", etq="Periodo", tipo="texto"), dict(id="EMP", etq="Empresa", tipo="texto")]
ENTREGA = {"OBJETO": ["MD", "PD", "SD", "CIF", "GAD", "GVT", "GFI"],
           "CENTRO": ["COSTO_PROPIO", "RECIBIDO", "CIF_RECIBIDO", "DISTRIBUIDO", "OCIO"], "ACTIVIDAD": ["COSTO"],
           "ORIGEN": ["ELEMENTO", "MONTO", "MEDIDA_TOTAL", "CRITERIO", "CPU_CIERRE", "PRECIO_ULTIMA_COMPRA"], "ARISTA": ["ELEMENTO", "MEDIDA", "MONTO"],
           "RECURSO": ["INEF"]}

ETAPAS = ["P1", "P2", "P3", "P4A", "P4B", "P4C", "P5", "P6", "P7"]   # P7 FIN → OBJETO (mono, D-9: financieros por capa)
ELEM = {"MD": "MD", "MAT": "MD", "PD": "PD", "MOD": "PD", "SD": "SD", "IND": "IND"}
ELEM_ETAPA = {"MD": "P1", "PD": "P2", "SD": "P3", "IND": "P4A"}
CENTS = D("0.01")


class Rechazo(ValueError):
    """Condición que detiene el cálculo (I1, I8, R-52, R-53): nunca se imputa en silencio."""


def _d(x):
    return D(repr(float(x))) if isinstance(x, float) else D(str(x if x not in (None, "") else 0))


def red(x):
    return x.quantize(CENTS, rounding=ROUND_HALF_UP)


def alg09(brutos):
    """ALG-09: {destino: Decimal bruto} → {destino: Decimal publicado}. Σ publicados = red(Σ brutos) exacto."""
    if not brutos: return {}
    pub = {k: red(v) for k, v in brutos.items()}
    r = red(sum(brutos.values())) - sum(pub.values())
    orden = sorted(brutos, key=lambda k: (-brutos[k], str(k)))
    paso = CENTS if r > 0 else -CENTS
    i = 0
    while r != 0:
        k = orden[i % len(orden)]
        if pub[k] + paso >= 0 or paso > 0:
            pub[k] += paso; r -= paso
        i += 1
        if i > 10 * len(orden) + 1000: raise Rechazo("ALG-09: residuo no distribuible")
    return pub


def _contexto(hechos, per, emp):
    tre = {r["CODIGO"]: ELEM.get(str(r["ELEMENTO_COSTO"]), None) for r in hechos["(sin MCD) TIPO_RECURSO"]}
    ele = {r["CODIGO"]: tre.get(r["TIPO_RECURSO"]) for r in hechos["RECURSO"]}
    cen = {r["CODIGO"]: str(r["TIPO"]) for r in hechos["CENTRO"] if r["EMPRESA"] == emp}
    obj = {r["NUMERO"]: str(r["TIPO"]) for r in hechos["(sin MCD) OBJETO"] if r["EMPRESA"] == emp}
    act = {r["CODIGO"] for r in hechos["ACTIVIDAD"]}
    p = next((r for r in hechos["PERIODO"] if r["CODIGO"] == per and r["EMPRESA"] == emp), None)
    if not p: raise Rechazo(f"No existe el periodo {per} de la empresa {emp}")
    ini = int(p["INICIO"])
    reglas = {}
    for r in sorted(hechos["(sin MCD) REGLA_REPARTO"], key=lambda r: (str(r["ETAPA"]), str(r["ORIGEN"]), int(r["DESDE"] or 0))):
        if int(r["DESDE"] or 0) <= ini: reglas[(str(r["ETAPA"]), str(r["ORIGEN"]))] = str(r["CRITERIO"])   # la vigente: mayor DESDE ≤ inicio
    med = defaultdict(OrderedDict)
    for r in hechos["(sin MCD) MEDIDA"]:
        if r["PERIODO"] == per and r["EMPRESA"] == emp:
            med[str(r["CRITERIO"])][(str(r["NIVEL"]), str(r["DESTINO"]))] = med[str(r["CRITERIO"])].get((str(r["NIVEL"]), str(r["DESTINO"])), D(0)) + _d(r["CANTIDAD"])
    eventos = {r["NUMERO"]: r for r in hechos["EVENTO"] if r["PERIODO"] == per and r["EMPRESA"] == emp}
    return ele, cen, obj, act, reglas, med, eventos


def _clave(evento, numero):
    n = lambda v: str(int(v)) if isinstance(v, float) and v == int(v) else str(v)
    return f"{n(evento)}-{n(numero)}"


def _origenes(hechos, previos, ele, eventos):
    """Montos de origen por (etapa, recurso) y consumos implícitos (criterio CONSUMO) por destino."""
    monto = defaultdict(D); consumo = defaultdict(lambda: defaultdict(D)); directo_cen = defaultdict(D)
    val = {}
    exceso = {str(k): _d(v) for k, v in (previos.get("EXCESO") or {}).items()}   # merma en exceso (NIC 2 §16 a): no es costo de la orden
    for t, k, c, v in (previos.get("VALUACION_PROMEDIO") or []):
        if t == "SALIDA" and c == "MONTO": val[str(k)] = _d(v)
    for r in hechos["(sin MCD) LINEA"]:
        ev = eventos.get(r["EVENTO"])
        if not ev: continue
        e = ele.get(r["RECURSO"])
        if e is None: continue
        rec, obj, cen = str(r["RECURSO"]), ev["OBJETO"], ev["CENTRO"]
        if e == "MD":
            if not obj: continue          # entradas al almacén (sin OT); una salida de MD sin OT la rechaza K0 (R-51)
            k = next((kk for kk in val if kk.startswith(f"{r['EVENTO']}-{r['NUMERO']}-")), None)
            if k is None: raise Rechazo(f"P1: la salida {r['EVENTO']}-{r['NUMERO']} de {rec} no tiene valorización (eje VALUACION)")
            q = _d(r["CANTIDAD"]); x = exceso.get(_clave(r["EVENTO"], r["NUMERO"]), D(0))
            parte = (q - x) / q if q and x else D(1)
            monto[("P1", rec)] += val[k] * parte; consumo[rec][("OBJ", str(obj))] += q - x
        else:
            m = _d(r["CANTIDAD"]) * _d(r["COSTO_UNITARIO_DOCUMENTO"])
            if e == "IND" and cen and not obj:
                directo_cen[(rec, str(cen))] += m       # K3: el documento ya identifica el centro
            else:
                monto[(ELEM_ETAPA[e], rec)] += m
                if obj: consumo[rec][("OBJ", str(obj))] += _d(r["CANTIDAD"])
    return monto, consumo, directo_cen


NIVELES = {"P1": {"OBJ", "ACT"}, "P2": {"OBJ", "ACT"}, "P3": {"OBJ", "ACT"}, "P4A": {"CEN", "ACT"}, "P4B": {"CEN"},
           "P4C": {"OBJ"}, "P5": {"OBJ"}, "P6": {"OBJ"}, "P7": {"OBJ"}}


def _elemento_llegada(etapa, elemento, nivel, dest, cen):
    if etapa == "P4A":
        if nivel == "CEN" and cen.get(dest) == "ADM": return "GAD"
        if nivel == "CEN" and cen.get(dest) == "VTA": return "GVT"
        if nivel == "CEN" and cen.get(dest) == "FIN": return "GFI"      # gastos financieros (D-9): la síntesis decide si van al costo
        return "CIF"
    return elemento


def correr(hechos, parametros, previos):
    """Ejecuta ALG-04 en memoria. Devuelve (saldos finales de OBJETO por elemento, aristas, resumen de centros)."""
    per, emp = parametros["PER"], parametros["EMP"]
    ele, cen, obj, act, reglas, med, eventos = _contexto(hechos, per, emp)
    monto, consumo, directo_cen = _origenes(hechos, previos, ele, eventos)
    saldo = defaultdict(lambda: defaultdict(D))           # (tipo_nodo, codigo) → {elemento: Decimal}
    origen_ini = {}
    for (et, rec), m in monto.items():
        e = {"P1": "MD", "P2": "PD", "P3": "SD", "P4A": "IND"}[et]
        saldo[("REC", rec)][e] += m; origen_ini[("REC", rec)] = et
    aristas = []
    recibido = defaultdict(D); propio = defaultdict(D); distrib = defaultdict(D)
    for (rec, c), m in sorted(directo_cen.items()):
        e = _elemento_llegada("P4A", "IND", "CEN", c, cen)
        saldo[("CEN", c)][e] += m; propio[c] += m
        aristas.append(dict(etapa="K3", origen=rec, org_tipo="REC", org_ele="IND", destino=c, nivel="CEN", elemento=e, criterio="DOCUMENTO", medida=D(1), total=D(1), monto=m))
    for et in ETAPAS:
        if et in ("P1", "P2", "P3", "P4A"):
            nodos = [n for n in saldo if n[0] == "REC" and origen_ini.get(n) == et]
        elif et == "P4B":
            nodos = [n for n in saldo if n[0] == "CEN" and cen.get(n[1]) == "APR"]
        elif et == "P4C":
            nodos = [n for n in saldo if (n[0] == "CEN" and cen.get(n[1]) == "PRO") or n[0] == "ACT"]
        elif et == "P5":
            nodos = [n for n in saldo if n[0] == "CEN" and cen.get(n[1]) == "ADM"]
        elif et == "P6":
            nodos = [n for n in saldo if n[0] == "CEN" and cen.get(n[1]) == "VTA"]
        else:
            nodos = [n for n in saldo if n[0] == "CEN" and cen.get(n[1]) == "FIN"]
        antes = sum(sum(v.values()) for v in saldo.values())
        for n in sorted(nodos, key=lambda n: (n[0], n[1])):
            tot_n = sum(saldo[n].values())
            if tot_n == 0: continue
            crit = reglas.get((et, n[1]))
            if crit is None: raise Rechazo(f"R-52: {et} {n[1]} tiene monto {red(tot_n)} y no tiene regla de reparto vigente")
            if crit == "CONSUMO":
                dest = OrderedDict(sorted((k, v) for k, v in consumo[n[1]].items() if v > 0))
            else:
                dest = OrderedDict(sorted((k, v) for k, v in med.get(crit, {}).items() if v > 0 and k[0] != "CAP"))
            malos = [k for k in dest if k[0] not in NIVELES[et]]
            if malos: raise Rechazo(f"{et} {n[1]}: el criterio {crit} apunta a niveles no permitidos {sorted({k[0] for k in malos})}")
            if et == "P4A" and {k[0] for k in dest if dest[k]} >= {"CEN", "ACT"}:     # R-26: nunca a centros y actividades a la vez
                raise Rechazo(f"R-26 {et} {n[1]}: el criterio {crit} reparte a centros y a actividades a la vez (contaría el costo dos veces)")
            if et == "P4B" and any(cen.get(k[1]) != "PRO" for k in dest):
                raise Rechazo(f"R-25: P4B {n[1]} reparte a un centro que no es productivo")
            T = sum(dest.values())
            if T == 0: raise Rechazo(f"I8: {et} {n[1]} tiene monto {red(tot_n)} y su criterio {crit} suma cero")
            cap = med.get(crit, {}).get(("CAP", n[1]), D(0))      # capacidad práctica del origen (MEDIDA nivel CAP)
            if cap > T:                                            # capacidad ociosa: no es costo del producto (NIC 2 §13)
                dest[("OCIO", n[1])] = cap - T; T = cap
            if n[0] == "CEN": distrib[n[1]] += tot_n
            for e in sorted(saldo[n]):
                m = saldo[n][e]
                if m == 0: continue
                for (niv, d), q in dest.items():
                    a = m * q / T
                    le = "OCIO" if niv == "OCIO" else _elemento_llegada(et, e, niv, d, cen)
                    tipo = {"OBJ": "OBJ", "ACT": "ACT", "CEN": "CEN", "OCIO": "OCIO"}[niv]
                    saldo[(tipo, d)][le] += a
                    if tipo == "CEN":
                        (propio if et == "P4A" else recibido)[d] += a
                    aristas.append(dict(etapa=et, origen=n[1], org_tipo=n[0], org_ele=e, destino=d, nivel=niv, elemento=le, criterio=crit, medida=q, total=T, monto=a))
                saldo[n][e] = D(0)
        despues = sum(sum(v.values()) for v in saldo.values())
        if abs(despues - antes) > D("1e-12"): raise Rechazo(f"I1: la etapa {et} no conserva ({antes} → {despues})")
    varados = [(n, sum(v.values())) for n, v in saldo.items() if n[0] in ("CEN", "ACT", "REC") and abs(sum(v.values())) > D("1e-12")]
    if varados: raise Rechazo("R-53: monto varado en " + ", ".join(f"{n[1]} ({red(m)})" for n, m in sorted(varados)))
    final = {n[1]: dict(v) for n, v in saldo.items() if n[0] == "OBJ"}
    return final, aristas, dict(propio=propio, recibido=recibido, distribuido=distrib)


def calcular(hechos, parametros, previos):
    final, aristas, cen = correr(hechos, parametros, previos)
    res, expl = [], []
    # Valores INTERNOS (sin redondear): así viajan entre métodos (DEPENDE_DE). El redondeo ALG-09 se aplica al publicar
    # (metodos.publicar.redondear_alg09), por grupo (método, tipo, concepto).
    for e in ENTREGA["OBJETO"]:
        for o in sorted(final):
            x = final[o].get(e, D(0))
            if x != 0: res.append(("OBJETO", o, e, float(x)))
    for c in sorted(set(cen["propio"]) | set(cen["recibido"])):
        res += [("CENTRO", c, "COSTO_PROPIO", float(cen["propio"][c])), ("CENTRO", c, "RECIBIDO", float(cen["recibido"][c])),
                ("CENTRO", c, "CIF_RECIBIDO", float(cen["recibido"][c])), ("CENTRO", c, "DISTRIBUIDO", float(cen["distribuido"][c])),
                ("CENTRO", c, "OCIO", 0.0)]   # el ocio de centros es [POSTERIOR] (método de capacidad); la ineficiencia de P2 va a INEF
    # ORIGEN y ARISTA: insumo de PROYECCION_OT (tarifas) y de la consulta (contrato de B0)
    org = defaultdict(lambda: [None, D(0), D(0), None]); vistos = set()
    for a in aristas:
        if a["org_tipo"] != "REC": continue
        o = org[a["origen"]]; o[0] = a["org_ele"]; o[1] += a["monto"]; o[3] = a["criterio"]
        if (a["origen"], a["destino"]) not in vistos: o[2] += a["medida"]; vistos.add((a["origen"], a["destino"]))
    ultima = {}
    for r in sorted(hechos["(sin MCD) LINEA"], key=lambda r: (int(r["EVENTO"] or 0), int(r["NUMERO"] or 0))):
        if r["COSTO_UNITARIO_DOCUMENTO"] not in (None, ""): ultima[r["RECURSO"]] = _d(r["COSTO_UNITARIO_DOCUMENTO"])
    for k in sorted(org):
        e, m, q, c = org[k]
        res += [("ORIGEN", k, "ELEMENTO", e), ("ORIGEN", k, "MONTO", float(m)), ("ORIGEN", k, "MEDIDA_TOTAL", float(q)), ("ORIGEN", k, "CRITERIO", c)]
        if e == "MD" and q: res.append(("ORIGEN", k, "CPU_CIERRE", float(m / q)))   # costo promedio de lo consumido en el periodo (ALG-07)
        if e == "SD" and k in ultima: res.append(("ORIGEN", k, "PRECIO_ULTIMA_COMPRA", float(ultima[k])))
    for a in aristas:
        if a["org_tipo"] == "REC" and a["etapa"] in ("P1", "P2", "P3"):
            k = f"{a['origen']}>{a['destino']}"
            res += [("ARISTA", k, "ELEMENTO", a["elemento"]), ("ARISTA", k, "MEDIDA", float(a["medida"])), ("ARISTA", k, "MONTO", float(a["monto"]))]
    if "INEF" in final:
        res.append(("RECURSO", "INEF", "INEF", float(sum(final["INEF"].values()))))
    acts = defaultdict(D)
    for a in aristas:
        if a["nivel"] == "ACT": acts[a["destino"]] += a["monto"]
    for k in sorted(acts): res.append(("ACTIVIDAD", k, "COSTO", float(acts[k])))
    for et in ETAPAS:
        n = sum(1 for a in aristas if a["etapa"] == et)
        if n: expl.append(f"{et}: {n} asignaciones; total {red(sum(a['monto'] for a in aristas if a['etapa'] == et))}")
    return res, expl


def interno(hechos, parametros, previos):
    """Valores internos (Decimal, sin redondear) por (objeto, elemento): lo que comparan las pruebas de oráculo (§4.3)."""
    return correr(hechos, parametros, previos)[0]


def trazar(hechos, parametros, previos, tipo, clave, concepto):
    """ALG-11: líneas que explican (tipo, clave, concepto). Cada arista lleva su monto atribuido: la parte de su monto que
    termina en el valor pedido. Las líneas con raiz=True (origen = recurso) suman exactamente el valor interno pedido (I9)."""
    _, aristas, _ = correr(hechos, parametros, previos)
    if tipo != "OBJETO": raise ValueError("trazar: en esta versión se traza tipo OBJETO")
    share = defaultdict(D); share[(("OBJ", str(clave)), concepto)] = D(1)
    salida = defaultdict(D)
    for a in aristas: salida[((a["org_tipo"], a["origen"]), a["org_ele"])] += a["monto"]
    lineas = []
    for a in reversed(aristas):
        s_ = share.get(((a["nivel"], a["destino"]), a["elemento"]), D(0))
        if s_ == 0: continue
        org = ((a["org_tipo"], a["origen"]), a["org_ele"])
        att = a["monto"] * s_
        share[org] += att / salida[org]
        lineas.append(dict(etapa=a["etapa"], origen=a["origen"], destino=a["destino"], elemento=a["elemento"], criterio=a["criterio"],
                           cantidad_destino=a["medida"], total_criterio=a["total"], tasa=(a["monto"] / a["medida"]) if a["medida"] else D(0),
                           monto_atribuido=att, raiz=a["org_tipo"] == "REC",
                           hechos_fuente=([f"LINEA:{a['origen']}"] if a["org_tipo"] == "REC" else []) +
                                         ([f"MEDIDA:{a['criterio']}|{a['destino']}"] if a["criterio"] not in ("CONSUMO", "DOCUMENTO") else [])))
    lineas.reverse()
    return lineas


CASOS = [dict(
    nombre="Dos recursos, un apoyo, dos productivos, dos OT (conservación y elemento)",
    hechos={
        "(sin MCD) REGLA_REPARTO": [dict(ETAPA="P4A", ORIGEN="LUZ", CRITERIO="KWH", DESDE=19000101),
                                     dict(ETAPA="P4B", ORIGEN="MANT", CRITERIO="HM", DESDE=19000101),
                                     dict(ETAPA="P4C", ORIGEN="CORTE", CRITERIO="CORTES", DESDE=19000101),
                                     dict(ETAPA="P4C", ORIGEN="SOLD", CRITERIO="HS", DESDE=19000101)],
        "(sin MCD) MEDIDA": [dict(PERIODO="X", EMPRESA="E", CRITERIO="KWH", NIVEL="CEN", DESTINO=d, CANTIDAD=q) for d, q in (("MANT", 100), ("CORTE", 300), ("SOLD", 600))]
                            + [dict(PERIODO="X", EMPRESA="E", CRITERIO="HM", NIVEL="CEN", DESTINO=d, CANTIDAD=q) for d, q in (("CORTE", 1), ("SOLD", 3))]
                            + [dict(PERIODO="X", EMPRESA="E", CRITERIO="CORTES", NIVEL="OBJ", DESTINO=d, CANTIDAD=q) for d, q in (("OT1", 1), ("OT2", 1))]
                            + [dict(PERIODO="X", EMPRESA="E", CRITERIO="HS", NIVEL="OBJ", DESTINO=d, CANTIDAD=q) for d, q in (("OT1", 1), ("OT2", 2))],
        "(sin MCD) LINEA": [dict(EVENTO=1, NUMERO=1, RECURSO="LUZ", CANTIDAD=1, COSTO_UNITARIO_DOCUMENTO=1000)],
        "EVENTO": [dict(NUMERO=1, PERIODO="X", EMPRESA="E", OBJETO=None, CENTRO=None)],
        "RECURSO": [dict(CODIGO="LUZ", TIPO_RECURSO="IND_T")],
        "(sin MCD) TIPO_RECURSO": [dict(CODIGO="IND_T", ELEMENTO_COSTO="IND")],
        "CENTRO": [dict(CODIGO="MANT", EMPRESA="E", TIPO="APR"), dict(CODIGO="CORTE", EMPRESA="E", TIPO="PRO"), dict(CODIGO="SOLD", EMPRESA="E", TIPO="PRO")],
        "(sin MCD) OBJETO": [dict(NUMERO="OT1", EMPRESA="E", TIPO="OT"), dict(NUMERO="OT2", EMPRESA="E", TIPO="OT")],
        "ACTIVIDAD": [], "PERIODO": [dict(CODIGO="X", EMPRESA="E", INICIO=20260101)]},
    parametros=dict(PER="X", EMP="E"), previos={"VALUACION_PROMEDIO": []},
    # LUZ 1000 → MANT 100, CORTE 300, SOLD 600; MANT 100 → CORTE 25, SOLD 75; CORTE 325 → 162.5/162.5; SOLD 675 → 225/450
    espera=[("OBJETO", "OT1", "CIF", 387.5), ("OBJETO", "OT2", "CIF", 612.5)])]
