"""Costeo variable sobre trazas reales; no modifica el motor ni sus datos."""
from collections import defaultdict
from math import isfinite

ELEMENTOS = ('MD', 'PD', 'SD', 'CIF', 'GAD', 'GVT', 'GFI')


def regresion(pares):
    """Mínimos cuadrados: solo usa el inductor indicado, nunca lo selecciona."""
    puntos = [(float(x), float(y)) for x, y in pares if x is not None and y is not None and isfinite(float(x)) and isfinite(float(y))]
    out = {'n': len(puntos), 'r2': None, 'a': None, 'b': None, 'fraccion_variable': 0.0}
    if len(puntos) < 6: return out
    xm = sum(x for x, _ in puntos) / len(puntos); ym = sum(y for _, y in puntos) / len(puntos)
    sx = sum((x - xm)**2 for x, _ in puntos); sy = sum((y - ym)**2 for _, y in puntos)
    if not sx or not sy or not ym: return out
    b = sum((x-xm)*(y-ym) for x,y in puntos) / sx; a = ym - b*xm
    r2 = max(0.0, min(1.0, 1 - sum((y-a-b*x)**2 for x,y in puntos)/sy))
    out.update(r2=r2, a=a, b=b)
    if r2 >= .7: out['fraccion_variable'] = max(0.0, min(1.0, b*xm/ym))
    return out


def calcular(objetos, montos, trazas, recursos, propuestas, historia=None, gastos_fijos=None):
    """montos: {orden:{elemento:monto de la síntesis}}; trazas: raíces REAL por recurso."""
    history = historia or {}; gastos_fijos = gastos_fijos or {}; configs = {str(x['REC_COD']): x for x in recursos}
    fractions, controls, regressions = {}, {}, []
    for code, r in configs.items():
        mode = str(r.get('REC_COMPORT') or '').strip().upper()
        if mode not in ('', 'F', 'V', 'M'): raise ValueError(f'Comportamiento inválido de {code}')
        if mode == 'M':
            pct = r.get('REC_PCT_VAR')
            if pct is None or not 0 <= float(pct) <= 100: raise ValueError(f'Porcentaje variable inválido de {code}')
            fractions[code] = float(pct) / 100
        elif mode == 'V': fractions[code] = 1.0
        elif mode == 'F': fractions[code] = 0.0
        else:
            reg = regresion(history.get(code, [])); fractions[code] = reg['fraccion_variable']
            regressions.append({'recurso':code, **reg})
        control = str(r.get('REC_CTRL') or 'S').strip().upper()
        if control not in ('S', 'N'): raise ValueError(f'Controlabilidad inválida de {code}')
        controls[code] = control == 'S'
    roots = defaultdict(list)
    for t in trazas:
        if not t.get('raiz'): continue
        e = str(t.get('elemento') or '')
        if '|' in e: continue
        resource = str(t['origen'])
        if resource not in configs: raise ValueError(f'Traza con recurso no definido: {resource}')
        roots[(str(t['objeto']), e)].append((resource, float(t.get('monto') or 0)))
    products = {}; group = defaultdict(lambda: [0.0, 0.0]); sin_trazas = []
    for o in objetos:
        oid = str(o['codigo']); prod = str(o['producto']); variable = 0.0
        for element, amount in montos.get(oid, {}).items():
            amount = float(amount); links = roots.get((oid,element), []); total = sum(v for _,v in links)
            if total <= 0:
                if amount: sin_trazas.append({'orden':oid,'elemento':element})
                continue
            vf = sum(v * fractions.get(rec,0.0) for rec,v in links) / total
            variable += amount * vf
            for rec,v in links:
                group[(prod,element)][0] += v
                if controls.get(rec, True): group[(prod,element)][1] += v
        p = products.setdefault(prod, {'producto':prod,'ventas':0.0,'cantidad':0.0,'costo_variable':0.0,'fijos':0.0})
        p['ventas'] += float(o.get('ingreso') or 0); p['cantidad'] += float(o.get('cantidad') or 0)
        p['costo_variable'] += variable; p['fijos'] += float(o.get('costo_total') or 0) - variable + float(gastos_fijos.get(oid, 0))
    out_products = []
    for p in products.values():
        p['margen_contribucion'] = p['ventas'] - p['costo_variable']
        p['costo_variable_unitario'] = p['costo_variable']/p['cantidad'] if p['cantidad'] else None
        for k in ('ventas','cantidad','costo_variable','fijos','margen_contribucion','costo_variable_unitario'):
            if p[k] is not None: p[k] = round(p[k],2)
        out_products.append(p)
    fixed = round(sum(p['fijos'] for p in out_products),2); sales = sum(p['ventas'] for p in out_products); contribution = sum(p['margen_contribucion'] for p in out_products)
    breakeven = round(fixed / (contribution/sales),2) if sales > 0 and contribution > 0 and not sin_trazas else None
    kept, blocked = [], []
    for proposal in propuestas:
        p = dict(proposal); key = (str(p.get('producto')), str(p.get('elemento'))); total, controllable = group.get(key,(0,0))
        if not total:
            p['nota_controlabilidad'] = 'Controlabilidad no verificable: sin trazas del elemento'; kept.append(p); continue
        fraction = max(0.0, min(1.0, controllable/total))
        if fraction == 0:
            blocked.append({**p,'motivo':'costo compartido no controlable (Oria)'}); continue
        if fraction < 1:
            for field in ('impacto_anual','impacto_esperado'):
                if p.get(field) is not None: p[field] = round(float(p[field])*fraction,2)
            p['nota_controlabilidad'] = f'impacto ajustado a la parte controlable ({fraction*100:.2f} %)'
        kept.append(p)
    return {'productos':out_products,'fijos_periodo':fixed,'punto_equilibrio_ventas':breakeven,'regresiones':regressions,'no_controlables':blocked,'sin_trazas':sin_trazas,'gastos_fijos_fuera_costo':round(sum(gastos_fijos.values()),2)}, kept


def analizar_libro(libro, resultado, hechos, par, previos, por_periodo, estimacion, incluidos, naturalezas):
    """Obtiene historia y trazas por recurso de la fuente REAL del periodo seleccionado."""
    import puerto_lectura as P
    from metodos import reparto_etapas as R
    tablas = P.leer(libro, ['RECURSO','TIPO_RECURSO','REGLA_REPARTO','MEDIDA','EVENTO','LINEA','PERIODO'])
    periodo, emp = par['PER'], par['EMP']
    resources = [r for r in tablas['RECURSO'] if r.get('REC_EMP') in (None, '', emp)]
    types = {str(t['TRE_COD']): str(t.get('TRE_ELE') or '') for t in tablas['TIPO_RECURSO']}
    material = {str(r['REC_COD']) for r in resources if types.get(str(r.get('REC_TRE'))) in ('MAT', 'MD')}
    periods = {str(p['PER_COD']): int(p['PER_INI']) for p in tablas['PERIODO'] if p.get('PER_EMP') in (None, '', emp) and str(p.get('PER_COD')) <= periodo}
    events = {e['EVE_NUM']: e for e in tablas['EVENTO'] if e.get('EVE_EMP') in (None, '', emp) and str(e.get('EVE_PER')) in periods}
    costs, quantities = defaultdict(float), defaultdict(float)
    valuation = {str(key): float(value) for typ,key,concept,value in previos.get('VALUACION_PROMEDIO',[]) if typ == 'SALIDA' and concept == 'MONTO'}
    for line in tablas['LINEA']:
        event = events.get(line.get('LIN_EVE'))
        if not event: continue
        per, rec = str(event['EVE_PER']), str(line.get('LIN_REC'))
        qty = float(line.get('LIN_CAN') or 0); quantities[(per,rec)] += qty if event.get('EVE_OBJ') else 0
        if rec in material and not event.get('EVE_OBJ'): continue
        prefix = R._clave(line['LIN_EVE'],line['LIN_NUM']) + '-'
        value = next((v for k,v in valuation.items() if k.startswith(prefix)), None)
        costs[(per,rec)] += value if value is not None else qty * float(line.get('LIN_CU_DOC') or 0)
    history = {}
    for resource in resources:
        rec = str(resource['REC_COD']); pairs = []
        rules = [r for r in tablas['REGLA_REPARTO'] if str(r.get('RRE_ORIGEN')) == rec and r.get('RRE_EMP') in (None,'',emp)]
        for per,start in sorted(periods.items()):
            active = [r for r in rules if int(r.get('RRE_DESDE') or 0) <= start]
            if not active: continue
            rule = max(active, key=lambda r:int(r.get('RRE_DESDE') or 0)); crit = str(rule.get('RRE_CRIT') or '')
            if crit == 'CONSUMO': x = quantities[(per,rec)]
            else:
                measures = [m for m in tablas['MEDIDA'] if str(m.get('MED_PER')) == per and m.get('MED_EMP') in (None,'',emp) and str(m.get('MED_CRIT')) == crit and m.get('MED_NIVEL') != 'CAP']
                if not measures: continue
                x = sum(float(m.get('MED_CAN') or 0) for m in measures)
            pairs.append((x,costs[(per,rec)]))
        history[rec] = pairs
    traces = [t for t in resultado.get('trazas', []) if t.get('raiz')]
    need_real_traces = not resultado.get('trazas')
    amounts = {}; gastos_fijos = {}
    for o in resultado['objetos']:
        oid = o['codigo']; current = por_periodo[periodo].get(oid,{})
        amounts[oid] = {e: 0.0 for e in ELEMENTOS}
        gastos_fijos[oid] = sum(float(value) for key,value in current.items() if R.separar(key)[0] in incluidos and R.separar(key)[1] in ('PERDIDA','OCIO') and R.separar(key)[1] not in naturalezas)
        for key,value in current.items():
            base,nature = R.separar(key)
            if base in amounts[oid] and nature == 'NORMAL' and base in incluidos: amounts[oid][base] += float(value)
        if resultado['sintesis'] == 'ESTIMADO' and o['producto'] in estimacion:
            for e in ELEMENTOS:
                amounts[oid][e] = float(estimacion[o['producto']]['cu_elementos'][e])*float(o['cantidad']) if e in incluidos else 0.0
        if need_real_traces:
            for e in ELEMENTOS:
                for t in R.trazar(hechos, par, previos, 'OBJETO', oid, e):
                    if t.get('raiz'):
                        traces.append({'objeto':oid,'elemento':e,'origen':t['origen'],'monto':float(t['monto_atribuido']),'raiz':True})
    return calcular(resultado['objetos'], amounts, traces, resources, resultado['propuestas'], history, gastos_fijos)
