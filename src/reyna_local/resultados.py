"""Construye el CONTRATO de resultados (contrato.py) desde el cálculo publicado del caso. Las pantallas solo leen esto.
Etapa 1: síntesis REAL, ABC de producción (MD, MOD, CIF) y serie histórica. Etapas 2-3 agregan admin/ventas/financieros
(NIIF 18), relevancia, hallazgos, proyección, escenarios y propuestas sin cambiar la forma."""
import csv, math, os
from decimal import Decimal as D
import puerto_lectura as P
from metodos import reparto_etapas as R
from integra_env import valuacion_alg01

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _f(x): return float(round(D(x), 2))


def previos(libro):
    """Entradas previas del reparto: valuación del kardex (ALG-01) y merma en exceso registrada por el motor operativo
    (LINEA.LIN_EXC, NIC 2 §16 a): esa parte no va a la orden, es pérdida del periodo."""
    exc = {}
    for l in P.leer(libro, ["LINEA"]).get("LINEA", []):
        try: x = float(l.get("LIN_EXC") or 0)
        except (TypeError, ValueError): x = 0
        if x > 0: exc[R._clave(l["LIN_EVE"], l["LIN_NUM"])] = x
    return {"VALUACION_PROMEDIO": valuacion_alg01(libro), "EXCESO": exc}


def calcular_periodos(libro, emp):
    prev = previos(libro); h = P.leer_conceptos(libro, R.CONSUME)
    pers = sorted({str(r["CODIGO"]) for r in h.get("PERIODO", [])})
    return {p: R.interno(h, dict(PER=p, EMP=emp), prev) for p in pers}, h


PROD = ("MD", "PD", "SD", "CIF"); OPER = ("GAD", "GVT"); FIN = ("GFI",)


def _incluidos(sintesis):
    """Reglas por tipo de síntesis (D-8/D-9): qué elementos forman el costo del objeto."""
    return PROD + OPER + FIN if sintesis in ("REAL", "ESTIMADO") else PROD


def construir(libro, emp=None, nombre=None, periodo=None, ventas_csv=None, sintesis="REAL", _cache=None):
    """REAL     costo integral = MD + MOD + CIF + administración + ventas + financieros (gerencial, precio objetivo).
    CONTABLE costo del inventario = MD + MOD + CIF (NIC 2 §10-16); el resto es gasto del periodo; estado de resultados NIIF 18.
    ESTIMADO costo más fiel según la historia (estadística, fuera de muestra), con banda; no es un estándar.
    En las tres: descriptivo, diagnóstico, relevancia, proyección 6 meses (determinística y estocástica), escenarios y propuestas."""
    from reyna_local import analisis as A
    if sintesis not in ("REAL", "CONTABLE", "ESTIMADO"): raise ValueError("síntesis desconocida")
    e0 = (P.leer(libro, ["EMPRESA"]).get("EMPRESA") or [{}])[0]          # la empresa sale del libro DBD, no del código
    emp = emp or e0.get("EMP_COD"); nombre = nombre or e0.get("EMP_NOM") or emp
    por_per, h = _cache or calcular_periodos(libro, emp)
    pers = sorted(por_per); periodo = periodo or pers[-1]
    objs = P.leer(libro, ["OBJETO"])["OBJETO"]
    can = {r["OBJ_NUM"]: float(r["OBJ_CAN"] or 0) for r in objs}; pro = {r["OBJ_NUM"]: str(r["OBJ_PRO"] or r["OBJ_NUM"]) for r in objs}
    # ingresos: tabla VENTA del DBD (periodo, producto, ingreso neto); se reparten entre las órdenes del producto por cantidad
    ventas, ventas_q = {}, {}
    for v in P.leer(libro, ["VENTA"]).get("VENTA", []):
        if v.get("VTA_PER") and (v.get("VTA_EMP") in (None, emp)):
            k = (str(v["VTA_PER"]), str(v["VTA_REC"])); ventas[k] = ventas.get(k, 0.0) + float(v.get("VTA_ING") or 0)
            ventas_q[k] = ventas_q.get(k, 0.0) + float(v.get("VTA_CAN") or 0)
    def ingreso(p, o):
        hermanas = [x for x in por_per.get(p, {}) if pro.get(x) == pro.get(o)]; q = sum(can.get(x, 0) for x in hermanas)
        return round(ventas.get((p, pro.get(o)), 0.0) * (can.get(o, 0) / q if q else 1 / max(1, len(hermanas))), 2)
    inc = _incluidos(sintesis)
    series = A.serie_producto(por_per, can, pro)
    est = A.estimado(series, periodo) if sintesis == "ESTIMADO" else {}
    objetos = []
    for o, v in sorted(por_per[periodo].items()):
        el = {e: _f(v.get(e, 0)) for e in PROD + OPER + FIN}
        if sintesis == "ESTIMADO" and pro.get(o) in est:
            el = {e: round(est[pro[o]]["cu_elementos"][e] * can[o], 2) for e in el}
        el = {e: (x if e in inc else 0.0) for e, x in el.items()}
        ct = round(sum(el.values()), 2); ing = ingreso(periodo, o)
        objetos.append(dict(codigo=o, producto=pro.get(o, o), cantidad=can.get(o, 0), md=el["MD"], mod=round(el["PD"] + el["SD"], 2), cif=el["CIF"],
                            admin=el["GAD"], gasto_venta=el["GVT"], financiero=el["GFI"], costo_total=ct,
                            costo_unitario=round(ct / can[o], 4) if can.get(o) else 0, ingreso=ing, margen=round(ing - ct, 2)))
    def tot_per(p): return {e: round(sum(_f(v.get(e, 0)) for v in por_per[p].values()), 2) for e in PROD + OPER + FIN}
    def vta_per(p): return round(sum(ingreso(p, o) for o in por_per[p]), 2)
    serie = []
    for p in [x for x in pers if x <= periodo]:
        t = tot_per(p); ct = round(sum(t[e] for e in inc), 2); vt = vta_per(p)
        serie.append(dict(periodo=p, tipo="ACTUAL" if p == periodo else "HISTORICO", ventas=vt, costo_total=ct, margen=round(vt - ct, 2)))
    proy, info = A.proyectar([(x["periodo"], x["ventas"], x["costo_total"]) for x in serie])
    serie += proy
    t = tot_per(periodo); vt = vta_per(periodo)
    from reyna_local import inventarios as INV
    sal18 = _salidas_t18(libro)
    precios = {k: ventas[k] / q for k, q in ventas_q.items() if q}
    inv = INV.calcular(por_per, {r["OBJ_NUM"]: r for r in objs}, pro, can, ventas_q, periodo, salidas=sal18, precios=precios,
                       base="VVR" if sintesis == "CONTABLE" else "FISICA") if any(ventas_q.values()) or sal18 else None
    # costo de ventas: salidas del producto terminado (NIC 2). Sin cantidades vendidas se asume vendido lo producido.
    cventas = inv["costo_ventas"] if inv else round(sum(t[e] for e in PROD), 2)
    er = [dict(categoria="OPERACION", concepto="Ventas netas", importe=vt),
          dict(categoria="OPERACION", concepto="Costo de ventas (MD + MOD + CIF de lo vendido)", importe=-cventas),
          dict(categoria="OPERACION", concepto="Gastos de administración", importe=-t["GAD"]),
          dict(categoria="OPERACION", concepto="Gastos de ventas", importe=-t["GVT"]),
          dict(categoria="FINANCIACION", concepto="Gastos financieros", importe=-t["GFI"])]
    perd = _perdidas(libro, periodo)
    _, ar_, _ = R.correr(h, dict(PER=periodo, EMP=emp), previos(libro))
    ocio = [dict(origen=a["origen"], etapa=a["etapa"], capacidad_no_usada=float(a["medida"]), capacidad=float(a["total"]), importe=round(float(a["monto"]), 2))
            for a in ar_ if a["nivel"] == "OCIO"]
    to = round(sum(x["importe"] for x in ocio), 2)
    if to: er.insert(4, dict(categoria="OPERACION", concepto="Costo de capacidad ociosa (NIC 2 §13)", importe=-to))
    tp = round(sum(x["importe"] for x in perd), 2)
    if tp: er.insert(4, dict(categoria="OPERACION", concepto="Pérdidas anormales: merma en exceso (NIC 2 §16 a)", importe=-tp))
    r_oper = round(vt - cventas - t["GAD"] - t["GVT"] - tp - to, 2)
    hall = A.diagnostico(series, periodo)
    rel = A.relevancia({e: t[e] for e in inc})
    esc = A.escenarios(dict(ventas=vt, **t))
    prop = A.propuestas(series, periodo, hall, rel)
    prev = previos(libro); val = prev["VALUACION_PROMEDIO"]; par = dict(PER=periodo, EMP=emp)
    nom = _nombres(libro)
    _, aristas, _ = R.correr(h, par, prev)
    acts, ind = [], {}
    for a in aristas:                                   # inductor de cada actividad hacia los objetos (P4C)
        if a["etapa"] == "P4C": ind[a["origen"]] = (a["criterio"], a["total"])
    for (tipo, clave, conc, v_) in R.calcular(h, par, prev)[0]:
        if tipo == "ACTIVIDAD":
            cri, tot = ind.get(clave, ("", 0))
            acts.append(dict(codigo=clave, nombre=nom.get(clave, clave), costo=round(v_, 2), inductor=nom.get(cri, cri),
                             tasa=round(float(v_) / float(tot), 6) if tot and float(tot) > 1.5 else 0.0))   # con pesos (%) no hay tasa unitaria
    ct = sum(o["costo_total"] for o in objetos); q = sum(o["cantidad"] for o in objetos)
    r = dict(empresa=dict(codigo=emp, nombre=nombre), periodo_actual=periodo, sintesis=sintesis, moneda="PEN",
             kpi=dict(ventas=vt, costo_total=round(ct, 2), margen_operativo=r_oper, rentabilidad=round(r_oper / vt, 4) if vt else 0,
                      costo_unitario_prom=round(ct / q, 4) if q else 0, resultado_antes_impuestos=round(r_oper - t["GFI"], 2)),
             objetos=objetos, actividades=acts, serie=serie, estado_resultados=er, relevancia=rel, hallazgos=hall, propuestas=prop,
             escenarios=esc, proyeccion_info=info)
    r["perdidas"] = perd; r["capacidad_ociosa"] = ocio
    if inv: r["inventarios"] = inv
    r["trazas"] = _trazas(h, par, prev, objetos, inc, nom) if sintesis != "ESTIMADO" else []
    r["kardex"] = _kardex(libro, val, periodo, nom)
    r["modelo"] = _modelo(libro)
    r["control"] = _control(aristas, r, nom)
    r["datos_libro"] = _datos_libro(libro, periodo, nom)
    if est:
        r["estimacion"] = {k: dict(cu_total=round(v["cu_total"], 4), p05=round(v["p05"], 4), p95=round(v["p95"], 4), metodo=v["metodo"],
                                   mase=None if v["mase"] in (None, math.inf) else round(v["mase"], 3)) for k, v in est.items()}
    return r


ELEMENTO_NOMBRE = {"MD": "Material directo", "PD": "Mano de obra directa", "SD": "Servicios directos", "CIF": "Costos indirectos de fabricación",
                   "GAD": "Gastos de administración", "GVT": "Gastos de ventas", "GFI": "Gastos financieros"}
ETAPA_NOMBRE = {"P1": "Material directo por kardex", "P2": "Mano de obra a actividades", "P3": "Servicios directos",
                "P4A": "Recursos indirectos a centros y actividades", "P4B": "Apoyo a productivos", "P4C": "Actividades a órdenes",
                "P5": "Administración a órdenes", "P6": "Ventas a órdenes", "P7": "Financieros a órdenes"}


def _nombres(libro):
    """Código → descripción, leídos del libro DBD (recursos, actividades, centros, criterios)."""
    t = P.leer(libro, ["RECURSO", "ACTIVIDAD", "CENTRO", "CRITERIO"]); n = {}
    for r in t.get("RECURSO", []): n[r["REC_COD"]] = r.get("REC_DES") or r["REC_COD"]
    for r in t.get("ACTIVIDAD", []): n[r["ACT_COD"]] = r.get("ACT_DES") or r["ACT_COD"]
    for r in t.get("CENTRO", []): n.setdefault(r["CEN_COD"], f"Centro {r['CEN_COD']} ({r.get('CEN_TIPO') or r.get('CEN_FUN') or ''})")
    for r in t.get("CRITERIO", []): n.setdefault(r["CRI_COD"], r.get("CRI_DES") or r["CRI_COD"])
    return n


def _trazas(h, par, prev, objetos, inc, nom):
    """Ruta del costo (ALG-11): por objeto y elemento, cada tramo recurso → centro/actividad → objeto con su inductor,
    tasa y monto atribuido. Los tramos raíz (desde un recurso) suman exactamente el elemento del objeto."""
    out = []
    for o in objetos:
        for e in inc:
            for l in R.trazar(h, par, prev, "OBJETO", o["codigo"], e):
                out.append(dict(objeto=o["codigo"], elemento=e, etapa=l["etapa"], origen=l["origen"], origen_nombre=nom.get(l["origen"], l["origen"]),
                                destino=l["destino"], destino_nombre=nom.get(l["destino"], l["destino"]), criterio=l["criterio"],
                                criterio_nombre=nom.get(l["criterio"], l["criterio"]), cantidad_destino=float(l["cantidad_destino"]),
                                total_criterio=float(l["total_criterio"]), tasa=round(float(l["tasa"]), 6),
                                monto=round(float(l["monto_atribuido"]), 2), raiz=bool(l["raiz"])))
    return out


def _kardex(libro, val, periodo, nom):
    """Kardex continuo (promedio ponderado, ALG-01) de los materiales; filas del periodo con saldo corrido."""
    cu = {(k[1], k[2]): v for k in val for v in [k[3]]} if val and len(val[0]) == 4 else {}
    rows = sorted(P.leer(libro, ["KARDEX"]).get("KARDEX", []), key=lambda r: (r["KDX_FEC"], r["KDX_EVE"], r["KDX_LIN"]))
    saldo, out = {}, []
    for r in rows:
        rec = r["KDX_REC"]; q, v = saldo.get(rec, (0.0, 0.0)); can = float(r["KDX_CAN"] or 0)
        clave = f"{r['KDX_EVE']}-{r['KDX_LIN']}-{r['KDX_ALM']}"
        if can >= 0 and r["KDX_VAL"] is not None:
            monto = float(r["KDX_VAL"]); c = monto / can if can else 0.0; mov = "ENTRADA" if r["KDX_CPB"] != "SALDO" else "SALDO INICIAL"
        else:
            monto = -float(cu.get((clave, "MONTO"), 0.0)); c = float(cu.get((clave, "CU"), 0.0))
            mov = "DEVOLUCION" if r["KDX_TRX"] == "T14.1" else "SALIDA"
        q, v = q + can, v + monto; saldo[rec] = (q, v)
        if r["KDX_PER"] == periodo:
            f = str(r["KDX_FEC"]); out.append(dict(fecha=f"{f[:4]}-{f[4:6]}-{f[6:8]}" if len(f) == 8 else f, material=rec, material_nombre=nom.get(rec, rec), movimiento=mov, comprobante=r["KDX_CPB"],
                            cantidad=can, costo_unitario=round(c, 6), importe=round(monto, 2), saldo_cantidad=round(q, 4), saldo_importe=round(v, 2)))
    return out


def _modelo(libro):
    """El modelo ABC tal como está definido en el libro DBD: es dato, no código (los «N modelos» de cualquier empresa)."""
    t = P.leer(libro, ["RECURSO", "TIPO_RECURSO", "ACTIVIDAD", "CENTRO", "CRITERIO", "REGLA_REPARTO"])
    ele = {r["TRE_COD"]: r.get("TRE_ELE") for r in t.get("TIPO_RECURSO", [])}
    return dict(
        recursos=[dict(codigo=r["REC_COD"], nombre=r.get("REC_DES"), tipo=r.get("REC_TRE"), elemento=ele.get(r.get("REC_TRE")), unidad=r.get("REC_UNI"))
                  for r in t.get("RECURSO", [])],
        actividades=[dict(codigo=r["ACT_COD"], nombre=r.get("ACT_DES"), unidad=r.get("ACT_UNI")) for r in t.get("ACTIVIDAD", [])],
        centros=[dict(codigo=r["CEN_COD"], tipo=r.get("CEN_TIPO") or r.get("CEN_FUN"), inductor=r.get("CEN_INDUCTOR")) for r in t.get("CENTRO", [])],
        inductores=[dict(codigo=r["CRI_COD"], nombre=r.get("CRI_DES"), unidad=r.get("CRI_UNI")) for r in t.get("CRITERIO", [])],
        reglas=[dict(etapa=r["RRE_ETAPA"], etapa_nombre=ETAPA_NOMBRE.get(r["RRE_ETAPA"], r["RRE_ETAPA"]), origen=r["RRE_ORIGEN"],
                     inductor=r["RRE_CRIT"], fuente=r.get("RRE_FUENTE")) for r in t.get("REGLA_REPARTO", [])])


def _control(aristas, r, nom):
    """Panel de calidad: verificaciones calculadas sobre el propio resultado (no declaraciones)."""
    from reyna_local.contrato import validar
    chk = []
    def add(nombre, esperado, obtenido, tol=0.05, detalle=""):
        dif = round(obtenido - esperado, 2); chk.append(dict(control=nombre, esperado=round(esperado, 2), obtenido=round(obtenido, 2),
                                                               diferencia=dif, ok=abs(dif) <= tol, detalle=detalle))
    # 1. Conservación: lo que entra como recurso termina íntegro en las órdenes (P1..P7)
    entra = sum(float(a["monto"]) for a in aristas if a["org_tipo"] == "REC")
    llega = sum(float(a["monto"]) for a in aristas if a["nivel"] in ("OBJ", "OCIO"))
    sale_int = sum(float(a["monto"]) for a in aristas if a["org_tipo"] != "REC")
    llega_int = sum(float(a["monto"]) for a in aristas if a["nivel"] not in ("OBJ", "OCIO"))
    add("Conservación del reparto: recursos del periodo = costo llegado a las órdenes + capacidad ociosa", entra, llega,
        detalle="Ningún sol se pierde ni se crea al repartir por etapas (I9).")
    add("Centros y actividades quedan en cero (todo lo recibido se reparte)", llega_int, sale_int)
    # 2. Ruta del costo: los tramos raíz explican cada elemento de cada orden
    if r.get("trazas"):
        for o in r["objetos"]:
            raiz = sum(t["monto"] for t in r["trazas"] if t["objeto"] == o["codigo"] and t["raiz"])
            add(f"Ruta del costo explica toda la orden {o['producto']}", o["costo_total"], raiz, tol=0.05 * 7)
    # 3. Kardex: saldo inicial + entradas − salidas = saldo final; nunca negativo
    k = r.get("kardex") or []
    for mat in sorted({x["material"] for x in k}):
        fil = [x for x in k if x["material"] == mat]; ini = fil[0]["saldo_importe"] - fil[0]["importe"]
        add(f"Kardex {nom.get(mat, mat)}: saldo inicial + movimientos = saldo final", ini + sum(x["importe"] for x in fil), fil[-1]["saldo_importe"])
        neg = min(x["saldo_cantidad"] for x in fil)
        chk.append(dict(control=f"Kardex {nom.get(mat, mat)}: sin saldos negativos", esperado=0, obtenido=round(neg, 4), diferencia=0, ok=neg >= -1e-6, detalle=""))
    # 3b. Lo que salió del almacén hacia órdenes = material de las órdenes + merma en exceso (pérdida del periodo)
    if k:
        sal = -sum(x["importe"] for x in k if x["movimiento"] == "SALIDA")
        md = sum(o["md"] for o in r["objetos"]) if r["sintesis"] != "ESTIMADO" else None
        if md is not None:
            add("Salidas del kardex = material de las órdenes + merma en exceso", sal, md + sum(p["importe"] for p in r.get("perdidas") or []),
                tol=0.05 * max(1, len(k)), detalle="La merma que excede el estándar (COMPONENTE) se separa como pérdida del periodo (NIC 2 §16 a).")
    # 4. Inductores en % deben sumar 100 %
    tot = {}
    for a in aristas:
        if a["etapa"] in ("P4A", "P4B", "P4C"): tot[(a["origen"], a["criterio"])] = float(a["total"])
    for (org, cri), v in sorted(tot.items()):
        if 0.5 < v < 1.5 and abs(v - 1) > 0.0005:
            chk.append(dict(control=f"{nom.get(cri, cri)} (recurso «{nom.get(org, org)}») suma {v * 100:.0f} %, no 100 %", esperado=1, obtenido=v,
                            diferencia=round(v - 1, 4), ok=False,
                            detalle="Deficiencia del dato fuente. El sistema reparte en proporción (Σ medidas) y conserva el costo; "
                                    "un reparto por porcentaje directo habría perdido o creado dinero."))
    # 5. Reglas de la síntesis
    if r["sintesis"] == "CONTABLE":
        fin = sum(o["financiero"] + o["admin"] + o["gasto_venta"] for o in r["objetos"])
        add("CONTABLE: el inventario no incluye administración, ventas ni financieros (NIC 2 §16)", 0, fin)
    add("Contrato de resultados válido (errores encontrados)", 0, len(validar({**r, "control": []})), tol=0)
    return chk


def _datos_libro(libro, periodo, nom):
    """DBD p. 24: todo dato guardado debe verse en alguna interfaz. Tablas del libro del periodo que no tienen otra pantalla."""
    t = P.leer(libro, ["VENTA", "MEDIDA", "CENTRO", "CLIENTE", "OBJETO"])
    return dict(
        ventas=[dict(producto=v.get("VTA_REC"), cliente=v.get("VTA_CLI"), canal=v.get("VTA_CANAL"), cantidad=v.get("VTA_CAN"),
                     ingreso=v.get("VTA_ING")) for v in t.get("VENTA", []) if str(v.get("VTA_PER")) == periodo],
        medidas=[dict(inductor=m.get("MED_CRIT"), inductor_nombre=nom.get(m.get("MED_CRIT"), m.get("MED_CRIT")), nivel=m.get("MED_NIVEL"),
                      destino=m.get("MED_DEST"), destino_nombre=nom.get(m.get("MED_DEST"), m.get("MED_DEST")), cantidad=m.get("MED_CAN"))
                 for m in t.get("MEDIDA", []) if str(m.get("MED_PER")) == periodo],
        ordenes=[dict(orden=o.get("OBJ_NUM"), producto=o.get("OBJ_PRO"), cantidad=o.get("OBJ_CAN"), estado=o.get("OBJ_EST"))
                 for o in t.get("OBJETO", [])][:1000],
        centros=[dict(codigo=c.get("CEN_COD"), tipo=c.get("CEN_TIPO") or c.get("CEN_FUN"), inductor=c.get("CEN_INDUCTOR")) for c in t.get("CENTRO", [])],
        clientes=[dict(codigo=c.get("CLI_COD"), nombre=c.get("CLI_NOM"), canal=c.get("CLI_CANAL"), region=c.get("CLI_REGION")) for c in t.get("CLIENTE", [])])


def _perdidas(libro, periodo):
    """Merma en exceso del estándar (COMPONENTE: estándar × unidades × (1 + merma normal)) que el motor operativo separó al
    registrar el consumo: es gasto del periodo, nunca costo del producto (NIC 2 §16 a), en REAL y en CONTABLE."""
    prev = previos(libro); val = {}
    for t, k, c, v in prev["VALUACION_PROMEDIO"]:
        if c == "MONTO": val["-".join(str(k).split("-")[:2])] = float(v)
    t = P.leer(libro, ["EVENTO", "LINEA"]); ev = {R._clave(e["EVE_NUM"], 0).split("-")[0]: e for e in t.get("EVENTO", [])}
    out = []
    for l in t.get("LINEA", []):
        k = R._clave(l["LIN_EVE"], l["LIN_NUM"]); x = prev["EXCESO"].get(k)
        e = ev.get(k.split("-")[0])
        if not x or not e or str(e.get("EVE_PER")) != periodo: continue
        q = float(l.get("LIN_CAN") or 0); v = val.get(k)
        if v is None: v = float(l.get("LIN_MTO") or 0)
        out.append(dict(orden=e.get("EVE_OBJ"), recurso=l["LIN_REC"], cantidad_exceso=x, cantidad_total=q,
                        importe=round(v * x / q, 2) if q else 0.0, evento=k))
    return out


def _salidas_t18(libro):
    """Productos de salida de cada orden (T18: resultado del objeto). Varias salidas = coproductos (D-9)."""
    t = P.leer(libro, ["EVENTO", "LINEA"]); ev = {}
    for e in t.get("EVENTO", []):
        if str(e.get("EVE_TRX")) == "T18" and e.get("EVE_OBJ"): ev[R._clave(e["EVE_NUM"], 0).split("-")[0]] = e["EVE_OBJ"]
    out = {}
    for l in t.get("LINEA", []):
        o = ev.get(R._clave(l["LIN_EVE"], 0).split("-")[0])
        if o and l.get("LIN_REC"):
            d = dict(out.get(o, [])); d[str(l["LIN_REC"])] = d.get(str(l["LIN_REC"]), 0.0) + float(l.get("LIN_CAN") or 0); out[o] = list(d.items())
    return out
