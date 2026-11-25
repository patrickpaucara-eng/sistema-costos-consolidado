"""Cotización TDABC basada solo en resultados y medidas del periodo cerrado."""
import math


def _number(value, label):
    if isinstance(value, bool): raise ValueError(f'{label} debe ser numérico')
    try: result = float(value)
    except (ValueError, TypeError): raise ValueError(f'{label} debe ser numérico') from None
    if not math.isfinite(result) or result < 0: raise ValueError(f'{label} debe ser finito y no negativo')
    return result


def cotizar(resultado, medidas, actividades, materiales, precio_mercado, margen_objetivo):
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
        lines.append({'tipo':'actividad','codigo':code,'cantidad':qty,'tasa':rate,'importe':round(rate*qty,2),'base':basis,'inductor':criterion})
    kdx = resultado.get('kardex') or []
    for code, qty0 in materiales.items():
        qty = _number(qty0, f'Cantidad de {code}')
        candidates = [row for row in kdx if str(row.get('material')) == code and row.get('costo_unitario') is not None and row.get('movimiento') != 'AJUSTE DE VALOR']
        if not candidates: raise ValueError(f'Material sin costo unitario disponible: {code}')
        latest = max(enumerate(candidates), key=lambda x:(str(x[1].get('fecha') or ''),x[0]))[1]
        rate = _number(latest['costo_unitario'],f'Costo unitario de {code}')
        lines.append({'tipo':'material','codigo':code,'cantidad':qty,'tasa':rate,'importe':round(rate*qty,2)})
    total = round(sum(x['importe'] for x in lines),2); target = round(price*(1-margin),2)
    return {'periodo_base':period,'lineas':lines,'costo_pedido':total,'precio_mercado':price,'margen_objetivo':margin,
            'costo_objetivo':target,'brecha':round(total-target,2),'avisos':warnings}
