"""Cotización TDABC basada solo en resultados y medidas del periodo cerrado."""
import math


def _number(value, label):
    if isinstance(value, bool): raise ValueError(f'{label} debe ser numérico')
    try: result = float(value)
    except (ValueError, TypeError): raise ValueError(f'{label} debe ser numérico') from None
    if not math.isfinite(result) or result < 0: raise ValueError(f'{label} debe ser finito y no negativo')
    return result


def cotizar(resultado, medidas, actividades, materiales, precio_mercado, margen_objetivo, producto=None, carpeta_aprendizaje=None, empresa_aprendizaje=None):
    if producto is not None and (not isinstance(producto,str) or not producto.strip()): raise ValueError('Producto inválido')
    if not isinstance(actividades,dict) or not isinstance(materiales,dict): raise ValueError('Las actividades y materiales deben ser mapas de cantidades')
    price = _number(precio_mercado,'Precio de mercado'); margin = _number(margen_objetivo,'Margen objetivo')
    if margin > 1: raise ValueError('El margen objetivo debe estar entre 0 y 1')
    if resultado.get('sintesis') != 'REAL': raise ValueError('La cotización requiere el resultado REAL')
    period = resultado['periodo_actual']; emp = resultado['empresa']['codigo']
    available = {str(a['codigo']):a for a in resultado.get('actividades',[])}
    if len(available) != len(resultado.get('actividades', [])): raise ValueError('Actividades duplicadas en el resultado')
    rules = (resultado.get('modelo') or {}).get('reglas',[])
    lines, warnings = [], []
    for code, qty0 in actividades.items():
        qty = _number(qty0, f'Cantidad de {code}')
        if code not in available: raise ValueError(f'Actividad inexistente: {code}')
        matches = [r for r in rules if r.get('etapa') == 'P4C' and str(r.get('origen')) == code]
        if len(matches) != 1 or not matches[0].get('inductor'): raise ValueError(f'La actividad {code} no tiene un inductor único')
        criterion = matches[0]['inductor']
        rows = [m for m in medidas if str(m.get('MED_PER')) == period and m.get('MED_EMP') in (None,'',emp) and m.get('MED_CRIT') == criterion]
        capacity = [m for m in rows if m.get('MED_NIVEL') == 'CAP' and str(m.get('MED_DEST')) == code]
        if len(capacity) > 1: raise ValueError(f'Capacidad práctica ambigua para {code}')
        if capacity: base = _number(capacity[0].get('MED_CAN'),f'Capacidad de {code}'); basis='capacidad práctica'
        else:
            base = sum(_number(m.get('MED_CAN'),f'Medida de {code}') for m in rows if m.get('MED_NIVEL') == 'OBJ')
            basis='uso'; warnings.append(f'{code}: sin capacidad práctica: tasa sobre uso')
        if base <= 0: raise ValueError(f'No hay capacidad o uso positivo para {code}')
        rate = _number(available[code].get('costo'),f'Costo de {code}') / base
        unidad = next((str(i.get('unidad') or '') for i in (resultado.get('modelo') or {}).get('inductores', []) if i.get('codigo') == criterion), '')
        if '%' in unidad: warnings.append(f'{code}: su inductor ({criterion}) es un porcentaje, no una cantidad física: la cotización por esta actividad no es confiable (registra la cantidad real del inductor).')
        lines.append({'tipo':'actividad','codigo':code,'cantidad':qty,'tasa':rate,'importe':round(rate*qty,2),'base':basis,'inductor':criterion})
    kdx = resultado.get('kardex') or []
    for code, qty0 in materiales.items():
        qty = _number(qty0, f'Cantidad de {code}')
        candidates = [row for row in kdx if str(row.get('material')) == code and row.get('costo_unitario') is not None and row.get('movimiento') != 'AJUSTE DE VALOR']
        if not candidates: raise ValueError(f'Material sin costo unitario disponible: {code}')
        latest = max(enumerate(candidates), key=lambda x:(str(x[1].get('fecha') or ''),x[0]))[1]
        rate = _number(latest['costo_unitario'],f'Costo unitario de {code}')
        line = {'tipo':'material','codigo':code,'cantidad':qty,'tasa':rate,'importe':round(rate*qty,2)}
        if producto:
            from .aprendizaje import estandar_vigente, mes_siguiente
            standard = estandar_vigente(empresa_aprendizaje or emp, producto, code, mes_siguiente(period), carpeta_aprendizaje)
            if standard is not None:
                line['estandar_aprendido'] = {'consumo':standard[0], 'merma':standard[1]}
                warnings.append(f'{code}: existe un estándar aprendido vigente para {producto}; la cantidad solicitada se conserva.')
        lines.append(line)
    total = round(sum(x['importe'] for x in lines),2); target = round(price*(1-margin),2)
    return {'periodo_base':period,'lineas':lines,'costo_pedido':total,'precio_mercado':price,'margen_objetivo':margin,
            'costo_objetivo':target,'brecha':round(total-target,2),'avisos':warnings}


def cotizar_intervalos_parejos(cantidades, tasas_por_intervalo, meses, intervalo):
    """Prototipo explícito: intervalos uniformes y tasas ya suministradas.

    No registra ni acepta órdenes. Las tasas deben venir de una fuente validada.
    """
    from decimal import Decimal
    from .intervalos_proyectados import importe_intervalos
    if isinstance(meses, bool) or isinstance(intervalo, bool) or not isinstance(meses, int) or not isinstance(intervalo, int) or meses <= 0 or intervalo <= 0 or meses % intervalo:
        raise ValueError('Los meses deben formar intervalos completos.')
    if not isinstance(cantidades, dict) or not cantidades or len(tasas_por_intervalo) != meses // intervalo:
        raise ValueError('Faltan cantidades o tasas por intervalo.')
    partes = len(tasas_por_intervalo)
    filas = []
    for tasas in tasas_por_intervalo:
        if set(tasas) != set(cantidades):
            raise ValueError('Cada intervalo requiere una tasa por recurso.')
        filas.append([{'cantidad': Decimal(str(_number(cantidad, codigo))) / partes,
                       'tasa': _number(tasas[codigo], codigo)} for codigo, cantidad in cantidades.items()])
    importes, total = importe_intervalos(filas)
    return {'intervalos': importes, 'total': total}


def costo_por_intervalos(cantidades, tasa_mes, meses, intervalo, curva='pareja'):
    """Costo proyectado de la OT (decisión 25-nov): las cantidades totales se reparten entre intervalos según la curva
    (pareja / inicio / final) y cada intervalo se valora con la tasa proyectada de su MES MEDIO.
    tasa_mes(codigo, mes) → tasa del mes (1 = primer mes de ejecución)."""
    if isinstance(meses, bool) or isinstance(intervalo, bool) or not isinstance(meses, int) or not isinstance(intervalo, int) or meses <= 0 or intervalo <= 0:
        raise ValueError('Duración e intervalo deben ser enteros positivos.')
    if curva not in ('pareja', 'inicio', 'final'): raise ValueError('Curva inválida.')
    tramos = [(i + 1, min(i + intervalo, meses)) for i in range(0, meses, intervalo)]; k = len(tramos)
    pesos = [(b - a + 1) * ({'pareja': 1, 'inicio': k - i, 'final': i + 1}[curva]) for i, (a, b) in enumerate(tramos)]
    total_p = sum(pesos); filas = []
    for (a, b), w in zip(tramos, pesos):
        medio = a + (b - a) // 2; parte = w / total_p
        det = {c: _number(q, c) * parte * tasa_mes(c, medio) for c, q in cantidades.items()}
        filas.append({'desde_mes': a, 'hasta_mes': b, 'mes_medio': medio, 'proporcion': round(parte, 6),
                      'costo': round(sum(det.values()), 2), 'detalle': {c: round(v, 2) for c, v in det.items()}})
    return {'intervalos': filas, 'total': round(sum(f['costo'] for f in filas), 2)}


def cotizar_proyectado(libro, emp, resultado, medidas, actividades, materiales, precio_mercado, margen_objetivo,
                       meses, intervalo=3, curva='pareja', contrato='CERRADO', familia=None, unidades=None):
    """Cotizador por intervalos + familias (bloques B y G). Las tasas de cada mes salen del costo PROYECTADO por el mismo
    motor (bloque A): actividad = tasa base × (costo proyectado de la actividad / costo base); material = costo unitario × factor de precio.
    familia: {inductor: receta} (familias.receta); con unidades, explota la receta y da el rango al 95 %."""
    from .proyeccion import proyectar_granular
    rango_fam = None
    if familia:
        from .familias import explotar
        if not unidades: raise ValueError('Indica cuántas unidades del componente')
        ex = explotar(familia, _number(unidades, 'Unidades'))
        actividades = {k: v['cantidad'] for k, v in ex.items() if k in {str(a['codigo']) for a in resultado.get('actividades', [])}}
        materiales = {**(materiales or {}), **{k: v['cantidad'] for k, v in ex.items() if k not in actividades}}
        rango_fam = ex
    base = cotizar(resultado, medidas, actividades, materiales or {}, precio_mercado, margen_objetivo)
    proy = proyectar_granular(libro, emp, meses=meses)['meses']
    costo_base = {str(a['codigo']): float(a.get('costo') or 0) for a in resultado.get('actividades', [])}
    tasa0 = {l['codigo']: (l['tipo'], l['tasa']) for l in base['lineas']}
    def tasa_mes(c, m):
        mes = proy[min(m, len(proy)) - 1]; tipo, t = tasa0[c]
        if tipo == 'actividad':
            act = {x['actividad']: x['monto'] for x in mes['desglose']['actividades']}
            return t * (act.get(c, costo_base.get(c, 0)) / costo_base[c]) if costo_base.get(c) else t
        return t * float(mes['factores'].get('pre', {}).get(c, 1.0))
    cant = {**actividades, **(materiales or {})}
    r = costo_por_intervalos(cant, tasa_mes, meses, intervalo, curva)
    lo = hi = None
    if rango_fam:
        lo = costo_por_intervalos({k: v['minimo'] for k, v in rango_fam.items()}, tasa_mes, meses, intervalo, curva)['total']
        hi = costo_por_intervalos({k: v['maximo'] for k, v in rango_fam.items()}, tasa_mes, meses, intervalo, curva)['total']
    objetivo = base['costo_objetivo']
    return {**r, 'costo_base_mes_actual': base['costo_pedido'], 'costo_objetivo': objetivo, 'brecha': round(r['total'] - objetivo, 2),
            'rango_95': [lo, hi] if lo is not None else None, 'contrato': contrato,
            'recomendacion': ('Precio cerrado: cotiza cerca del límite alto del rango; la empresa asume el riesgo de precios.' if contrato == 'CERRADO'
                              else 'Con reajuste: el riesgo de precios pasa al cliente; cotiza sobre el costo esperado.'),
            'avisos': base['avisos'], 'intervalo_meses': intervalo, 'curva': curva}
