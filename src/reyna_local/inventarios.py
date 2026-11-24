"""Inventarios de proceso y de producto terminado, costo de ventas (NIC 2), D14 y coproductos (D-9).
- Una orden acumula costo de producción (MD + MOD + CIF) en cada periodo en que recibe costo.
- Mientras no termina (OBJETO.OBJ_EST distinto de T/L, o su fecha de término es posterior al periodo) su costo acumulado es
  INVENTARIO EN PROCESO. Al terminar, entra al KARDEX DE PRODUCTO TERMINADO (promedio ponderado) con todo lo acumulado.
- COPRODUCTOS: si la orden registra varios productos de salida (transacción T18: EVENTO de la orden + LINEA por producto),
  el costo conjunto se reparte entre ellos: REAL por unidades físicas; CONTABLE por valor de venta relativo (VVR = cantidad ×
  precio de venta del periodo), D-9. Sin T18, la orden produce su OBJ_PRO en la cantidad OBJ_CAN.
- Las ventas (VENTA.VTA_CAN) salen del producto terminado al costo promedio: eso es el COSTO DE VENTAS.
- DEVOLUCIONES DE CLIENTES (VENTA con cantidad negativa): reingresan al producto terminado al costo con que salieron y
  reducen el costo de ventas del periodo; el ingreso se revierte en las ventas netas.
- D14 · venta antes de liquidar: si se vende más de lo que hay terminado, el faltante sale a un costo PROVISIONAL (último
  promedio conocido, o el costo unitario de producción del periodo). Cuando entra la producción que lo respalda, la diferencia
  (costo real − provisional) × unidades se reconoce como AJUSTE DEL COSTO DE VENTAS en ese periodo; la venta original no se
  reescribe."""
PROD = ("MD", "PD", "SD", "CIF")


def _termina(info, p):
    est = str(info.get("OBJ_EST") or "T").upper(); fin = info.get("OBJ_FEC_TER")
    if est not in ("T", "L"): return False
    if fin in (None, ""): return True
    a, m = p.split("-"); return int(float(fin)) <= int(f"{a}{m}31")


def _cu_periodo(por_per, p, pro, can, prod):
    tot = q = 0.0
    for o, v in por_per[p].items():
        if pro.get(o) == prod: tot += sum(float(v.get(e, 0)) for e in PROD); q += float(can.get(o, 0))
    return tot / q if q else 0.0


def reparto_conjunto(costo, salidas, precios, p, base):
    """[(producto, cantidad)] → [(producto, cantidad, costo asignado, peso)]. FISICA: por unidades; VVR: por cantidad × precio
    (valor neto realizable sin costos posteriores registrados). Un producto que nunca tuvo valor de venta es RESIDUO: costo 0 en
    ambas bases (no se costea la roca como el oro). Si el precio falta solo este mes, se usa el más cercano conocido."""
    precios = precios or {}
    def precio(prod):                                   # el del periodo; si no, el último anterior; si no, el primero posterior
        if (p, prod) in precios: return precios[(p, prod)]
        ks = sorted(k for k in precios if k[1] == prod); antes = [k for k in ks if k[0] <= p]
        return precios[antes[-1]] if antes else (precios[ks[0]] if ks else None)
    residuo = {prod for prod, _ in salidas if precio(prod) is None}
    if residuo and len(residuo) < len(salidas):        # decisión 24-nov: lo que nunca tuvo valor de venta es residuo y no se costea
        salidas_v = [(prod, q) for prod, q in salidas if prod not in residuo]
        partes, usada = reparto_conjunto(costo, salidas_v, precios, p, base)
        return partes + [(prod, q, 0.0, 0.0) for prod, q in salidas if prod in residuo], usada + "+RESIDUO"
    if base == "VVR" and not residuo:
        pesos = [q * precio(prod) for prod, q in salidas]; usada = "VVR"
    else:
        pesos = [q for _, q in salidas]; usada = "FISICA"
    T = sum(pesos) or 1.0
    return [(prod, q, costo * w / T, w / T) for (prod, q), w in zip(salidas, pesos)], usada


def calcular(por_per, objetos_info, pro, can, ventas_q, periodo, salidas=None, precios=None, base="FISICA", devoluciones=None):
    """por_per: {periodo: {orden: {elemento: monto}}}; objetos_info: {orden: fila OBJETO}; ventas_q: {(periodo, producto): cantidad};
    salidas: {orden: [(producto, cantidad)]} (T18); precios: {(periodo, producto): precio unitario}; base: FISICA | VVR."""
    acum, terminada = {}, set()
    stock, pendiente, ultimo_cu, ultimo_cu_venta = {}, {}, {}, {}
    filas, ajustes, coprod, cv = [], [], [], {}

    def entrada(prod, q, val, o, p):
        cu = val / q if q else 0.0; ultimo_cu[prod] = cu
        pend = pendiente.get(prod, []); resto_q, resto_v = q, val
        while pend and resto_q > 1e-9:                     # D14: liquida primero las ventas provisionales pendientes
            pq, pcu, pp = pend[0]; usa = min(pq, resto_q); dif = round((cu - pcu) * usa, 2)
            if abs(dif) >= 0.005:
                ajustes.append(dict(periodo=p, producto=prod, orden=o, cantidad=usa, cu_provisional=round(pcu, 6),
                                    cu_real=round(cu, 6), ajuste=dif, venta_de=pp))
                cv[p] += dif
            resto_q -= usa; resto_v -= cu * usa
            if usa >= pq - 1e-9: pend.pop(0)
            else: pend[0] = (pq - usa, pcu, pp)
        sq, sv = stock.get(prod, (0.0, 0.0)); stock[prod] = (sq + resto_q, sv + resto_v)
        if p == periodo:
            filas.append(dict(producto=prod, movimiento="ENTRADA DE PRODUCCIÓN", documento=o, cantidad=round(q, 4), costo_unitario=round(cu, 6),
                              importe=round(val, 2), saldo_cantidad=round(stock[prod][0], 4), saldo_importe=round(stock[prod][1], 2)))

    for p in sorted(x for x in por_per if x <= periodo):
        cv[p] = 0.0
        for o, v in por_per[p].items():
            if o not in terminada: acum[o] = acum.get(o, 0.0) + sum(float(v.get(e, 0)) for e in PROD)
        for o in sorted(acum):                              # 1) entradas: órdenes que terminan en p
            if o in terminada or not _termina(objetos_info.get(o, {}), p): continue
            terminada.add(o)
            sal = (salidas or {}).get(o) or [(pro.get(o, o), float(can.get(o, 0)))]
            if len(sal) > 1:                                # coproductos: reparto del costo conjunto (D-9)
                partes, usada = reparto_conjunto(acum[o], sal, precios, p, base)
                for prod, q, val, w in partes:
                    entrada(prod, q, val, o, p)
                    if p == periodo:
                        coprod.append(dict(orden=o, producto=prod, cantidad=q, base=usada, participacion=round(w, 6), costo_asignado=round(val, 2),
                                           costo_unitario=round(val / q, 6) if q else 0.0))
            else:
                entrada(sal[0][0], sal[0][1], acum[o], o, p)
        for (pv, prod), qv in sorted(ventas_q.items()):     # 2) salidas: ventas del periodo al promedio
            if pv != p or not qv: continue
            sq, sv = stock.get(prod, (0.0, 0.0)); cpu = sv / sq if sq > 1e-9 else ultimo_cu.get(prod, 0.0)
            sale = min(qv, max(sq, 0.0)); falta = qv - sale; costo = cpu * sale
            if falta > 1e-9:                                # D14: venta antes de liquidar → costo provisional
                cprov = ultimo_cu.get(prod) or _cu_periodo(por_per, p, pro, can, prod)
                pendiente.setdefault(prod, []).append((falta, cprov, p)); costo += cprov * falta
            stock[prod] = (sq - sale, sv - cpu * sale); cv[p] += costo; ultimo_cu_venta[prod] = costo / qv
            if p == periodo:
                filas.append(dict(producto=prod, movimiento="SALIDA POR VENTA" + (" (parte provisional D14)" if falta > 1e-9 else ""),
                                  documento=f"Ventas {p}", cantidad=-round(qv, 4), costo_unitario=round(costo / qv, 6) if qv else 0,
                                  importe=-round(costo, 2), saldo_cantidad=round(stock[prod][0], 4), saldo_importe=round(stock[prod][1], 2)))
        for (pv, prod), qd in sorted((devoluciones or {}).items()):   # 3) devoluciones de clientes (M-F-DCL)
            if pv != p or not qd: continue
            sq, sv = stock.get(prod, (0.0, 0.0)); cu = ultimo_cu_venta.get(prod) or ultimo_cu.get(prod, 0.0)
            stock[prod] = (sq + qd, sv + qd * cu); cv[p] -= qd * cu        # reingresa al costo con que salió; reduce el costo de ventas
            if p == periodo:
                filas.append(dict(producto=prod, movimiento="DEVOLUCIÓN DE CLIENTE", documento=f"Ventas {p}", cantidad=round(qd, 4),
                                  costo_unitario=round(cu, 6), importe=round(qd * cu, 2), saldo_cantidad=round(stock[prod][0], 4),
                                  saldo_importe=round(stock[prod][1], 2)))
    en_proceso = [dict(orden=o, producto=pro.get(o, o), costo_acumulado=round(v, 2)) for o, v in sorted(acum.items()) if o not in terminada]
    saldos = [dict(producto=k, cantidad=round(q, 4), importe=round(v, 2)) for k, (q, v) in sorted(stock.items())]
    pend = [dict(producto=k, cantidad=round(sum(x[0] for x in v), 4)) for k, v in pendiente.items() if v]
    return dict(kardex_pt=filas, saldos_pt=saldos, en_proceso=en_proceso, costo_ventas=round(cv.get(periodo, 0.0), 2),
                ajustes_d14=[a for a in ajustes if a["periodo"] == periodo], ventas_pendientes_d14=pend, coproductos=coprod,
                total_pt=round(sum(x["importe"] for x in saldos), 2), total_proceso=round(sum(x["costo_acumulado"] for x in en_proceso), 2))
