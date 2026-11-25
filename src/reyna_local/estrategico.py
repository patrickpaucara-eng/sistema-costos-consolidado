"""Indicadores estratégicos derivados del contrato y los catálogos del libro."""


def calcular(resultado, recursos, criterios):
    categories = {str(r['REC_COD']): str(r.get('REC_COQ') or '').strip().upper() for r in recursos}
    invalid = [key for key,value in categories.items() if value not in ('','PREVENCION','EVALUACION')]
    if invalid: raise ValueError('Categoría de calidad inválida: ' + ', '.join(invalid))
    traces = resultado.get('trazas') or []
    roots = [t for t in traces if t.get('raiz')]
    missing = bool(any(categories.values()) and not roots)
    amounts = {'PREVENCION':0.0,'EVALUACION':0.0}
    for t in roots:
        category = categories.get(str(t.get('origen')), '')
        if category and '|' not in str(t.get('elemento') or ''):
            amounts[category] += float(t.get('monto') or 0)
    internal = sum(float(x.get('importe') or 0) for group in ('rechazos','perdidas') for x in resultado.get(group, []))
    returns = sum(float(x.get('importe') or 0) for x in (resultado.get('inventarios') or {}).get('kardex_pt',[]) if x.get('movimiento') == 'DEVOLUCIÓN DE CLIENTE')
    total = None if missing else round(sum(amounts.values()) + internal + returns, 2)
    sales = float((resultado.get('kpi') or {}).get('ventas') or 0)
    coq = {'prevencion':None if missing else round(amounts['PREVENCION'],2), 'evaluacion':None if missing else round(amounts['EVALUACION'],2),
           'falla_interna':round(internal,2), 'falla_externa':round(returns,2), 'total':total,
           'pct_ventas':round(total/sales*100,2) if total is not None and sales else None}
    if missing: coq['nota'] = 'No hay trazas raíz para clasificar los recursos de calidad.'
    catalog = {str(c['CRI_COD']): c for c in criterios}
    used = sorted({str(t.get('criterio')).split('+RECIPROCO')[0] for t in traces if t.get('criterio')})
    incomplete = []
    for code in used:
        item = catalog.get(code,{})
        responsible = bool(str(item.get('CRI_RESP') or '').strip()); evidence = bool(str(item.get('CRI_EVID') or '').strip())
        if not responsible or not evidence:
            incomplete.append({'criterio':code,'falta_responsable':not responsible,'falta_evidencia':not evidence})
    governance = {'usados':len(used), 'completos':len(used)-len(incomplete),
                  'porcentaje':round((len(used)-len(incomplete))/len(used)*100,2) if used else None,
                  'faltantes':incomplete}
    if not traces: governance['nota'] = 'Sin trazas: no es posible determinar los criterios usados.'
    return {'coq':coq, 'gobierno_dato':governance}


def desde_libro(resultado, libro):
    import puerto_lectura as P
    data = P.leer(libro, ['RECURSO','CRITERIO'])
    return calcular(resultado, data['RECURSO'], data['CRITERIO'])
