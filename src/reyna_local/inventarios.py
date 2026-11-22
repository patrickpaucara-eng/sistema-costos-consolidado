"""Inventarios de proceso y de producto terminado, y costo de ventas (NIC 2; D14).
- Una orden acumula costo de producción (MD + MOD + CIF) en cada periodo en que recibe costo.
- Mientras no termina (OBJETO.OBJ_EST distinto de T/L, o su fecha de término es posterior al periodo) su costo acumulado es
  INVENTARIO EN PROCESO. Al terminar, entra al KARDEX DE PRODUCTO TERMINADO (promedio ponderado) con todo lo acumulado.
- Las ventas (VENTA.VTA_CAN) salen del producto terminado al costo promedio: eso es el COSTO DE VENTAS.
- D14 · venta antes de liquidar: si se vende más de lo que hay terminado, el faltante sale a un costo PROVISIONAL (último
  promedio conocido, o el costo unitario de producción del periodo). Cuando entra la producción que lo respalda, la diferencia
  (costo real − provisional) × unidades se reconoce como AJUSTE DEL COSTO DE VENTAS en ese periodo; la venta original no se
  reescribe."""
PROD = ("MD", "PD", "SD", "CIF")


def _termina(o, info, p):
    est = str(info.get("OBJ_EST") or "T").upper(); fin = info.get("OBJ_FEC_TER")
    if est not in ("T", "L"): return False
    if fin in (None, ""): return True
    a, m = p.split("-"); return int(float(fin)) <= int(f"{a}{m}31")


def calcular(por_per, objetos_info, pro, can, ventas_q, periodo):
    """por_per: {periodo: {orden: {elemento: monto}}}; objetos_info: {orden: fila OBJETO}; ventas_q: {(periodo, producto): cantidad}.
    Devuelve dict con kardex_pt (filas del periodo), saldos_pt, en_proceso, costo_ventas, ajustes_d14 y totales."""
    acum, terminada = {}, set()
    stock = {}                              # producto → (cantidad, valor)
    pendiente = {}                          # producto → [(cantidad, cu_provisional, periodo)]
    ultimo_cu = {}
    filas, ajustes, cv = [], [], {}
    for p in sorted(x for x in por_per if x <= periodo):
        cv[p] = 0.0
        for o, v in por_per[p].items():
            if o in terminada: continue
            acum[o] = acum.get(o, 0.0) + sum(float(v.get(e, 0)) for e in PROD)
        # 1) entradas: órdenes que terminan en p
        for o in sorted(acum):
            if o in terminada or not _termina(o, objetos_info.get(o, {}), p): continue
            terminada.add(o); prod = pro.get(o, o); q = float(can.get(o, 0)); val = acum[o]
            cu = val / q if q else 0.0; ultimo_cu[prod] = cu
            # D14: primero se liquidan las ventas provisionales pendientes de este producto
            pend = pendiente.get(prod, [])
            while pend and q > 1e-9:
                pq, pcu, pp = pend[0]; usa = min(pq, q); dif = round((cu - pcu) * usa, 2)
                if abs(dif) >= 0.005:
                    ajustes.append(dict(periodo=p, producto=prod, orden=o, cantidad=usa, cu_provisional=round(pcu, 6), cu_real=round(cu, 6),
                                        ajuste=dif, venta_de=pp))
                    cv[p] += dif
                q -= usa; val -= cu * usa
                if usa >= pq - 1e-9: pend.pop(0)
                else: pend[0] = (pq - usa, pcu, pp)
            sq, sv = stock.get(prod, (0.0, 0.0)); stock[prod] = (sq + q, sv + val)
            if p == periodo:
                filas.append(dict(producto=prod, movimiento="ENTRADA DE PRODUCCIÓN", documento=o, cantidad=round(float(can.get(o, 0)), 4),
                                  costo_unitario=round(cu, 6), importe=round(acum[o], 2), saldo_cantidad=round(stock[prod][0], 4),
                                  saldo_importe=round(stock[prod][1], 2)))
        # 2) salidas: ventas del periodo al promedio
        for (pv, prod), qv in sorted(ventas_q.items()):
            if pv != p or not qv: continue
            sq, sv = stock.get(prod, (0.0, 0.0)); cpu = sv / sq if sq > 1e-9 else ultimo_cu.get(prod, 0.0)
            sale = min(qv, max(sq, 0.0)); falta = qv - sale
            costo = cpu * sale
            if falta > 1e-9:                                       # D14: venta antes de liquidar → costo provisional
                cprov = ultimo_cu.get(prod) or _cu_periodo(por_per, p, pro, can, prod)
                pendiente.setdefault(prod, []).append((falta, cprov, p)); costo += cprov * falta
            stock[prod] = (sq - sale, sv - cpu * sale); cv[p] += costo
            if p == periodo:
                filas.append(dict(producto=prod, movimiento="SALIDA POR VENTA" + (" (parte provisional D14)" if falta > 1e-9 else ""),
                                  documento=f"Ventas {p}", cantidad=-round(qv, 4), costo_unitario=round(costo / qv, 6) if qv else 0,
                                  importe=-round(costo, 2), saldo_cantidad=round(stock[prod][0], 4), saldo_importe=round(stock[prod][1], 2)))
    en_proceso = [dict(orden=o, producto=pro.get(o, o), costo_acumulado=round(v, 2)) for o, v in sorted(acum.items()) if o not in terminada]
    saldos = [dict(producto=k, cantidad=round(q, 4), importe=round(v, 2)) for k, (q, v) in sorted(stock.items())]
    pend = [dict(producto=k, cantidad=round(sum(x[0] for x in v), 4)) for k, v in pendiente.items() if v]
    return dict(kardex_pt=filas, saldos_pt=saldos, en_proceso=en_proceso, costo_ventas=round(cv.get(periodo, 0.0), 2),
                ajustes_d14=[a for a in ajustes if a["periodo"] == periodo], ventas_pendientes_d14=pend,
                total_pt=round(sum(x["importe"] for x in saldos), 2), total_proceso=round(sum(x["costo_acumulado"] for x in en_proceso), 2))


def _vino_antes(o, por_per, p):
    return any(o in por_per[x] for x in por_per if x < p)


def _cu_periodo(por_per, p, pro, can, prod):
    tot = q = 0.0
    for o, v in por_per[p].items():
        if pro.get(o) == prod: tot += sum(float(v.get(e, 0)) for e in PROD); q += float(can.get(o, 0))
    return tot / q if q else 0.0
