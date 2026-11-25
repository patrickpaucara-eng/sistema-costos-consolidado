"""Proyección granular: clona hechos y ejecuta el motor sin modificar el libro."""
from collections import defaultdict
from copy import deepcopy
from math import ceil, isfinite
from pathlib import Path

from metodos import reparto_etapas as R
from .analisis import pronostico_puntual


def _mes(per, delta):
    year, month = map(int, per.split('-'))
    n = year*12 + month - 1 + delta
    return f'{n//12:04d}-{n%12+1:02d}'


def _factor(value, h, periodo):
    if isinstance(value, list):
        if not value: raise ValueError('La lista de factores no puede estar vacía')
        value = value[h-1] if h <= len(value) else value[-1]
    if isinstance(value, dict): value = value.get(periodo, value.get(str(h), value.get(h, 1)))
    value = float(value)
    if not isfinite(value) or value < 0: raise ValueError('Los factores deben ser finitos y no negativos')
    return value


def _pronosticar(serie, meses):
    if not serie or not serie[-1]: return [1.0]*meses
    forecast, _ = pronostico_puntual(serie, meses)
    return [max(0.0, float(x)/float(serie[-1])) for x in forecast]


def proyectar_hechos(hechos, previos, empresa, periodo_base, objetos, recursos, criterios, ventas, factores, h=1, bloques=()):
    """Proyecta un mes desde hechos y retorna los resultados del motor; no altera los argumentos."""
    future = _mes(periodo_base,h); source = deepcopy(hechos); previous = deepcopy(previos)
    obj_info = {str(o['OBJ_NUM']):o for o in objetos}
    base_result = R.interno(hechos, {'PER':periodo_base,'EMP':empresa}, previos)
    base_orders = {str(k):v for k,v in base_result.items() if str(k) in obj_info}
    ids = {oid:f'{oid}@{future}' for oid in base_orders}
    products = {oid:str(obj_info[oid]['OBJ_PRO']) for oid in ids}
    allf = {}
    for kind in ('vol','pre','pv'):
        allf[kind] = {str(k):_factor(v,h,future) for k,v in (factores.get(kind) or {}).items()}
    vol = lambda p: allf['vol'].get(p,1.0)
    pre = lambda r: allf['pre'].get(r,1.0)
    weights = {oid:sum(float(x) for x in values.values()) for oid,values in base_orders.items()}
    denom = sum(weights.values()); g = sum(weights[o]*vol(products[o]) for o in ids)/denom if denom else 1.0
    recs = {str(x['REC_COD']):x for x in recursos}
    types = {str(x['CODIGO']):str(x.get('ELEMENTO_COSTO') or '') for x in hechos['(sin MCD) TIPO_RECURSO']}
    rec_types = {str(x['CODIGO']):types.get(str(x['TIPO_RECURSO']),'') for x in hechos['RECURSO']}
    def frac(code):
        row = recs.get(code,{}); mode = str(row.get('REC_COMPORT') or '').strip().upper()
        if mode == 'V': return 1.0
        if mode == 'F': return 0.0
        if mode == 'M':
            try: pct = float(row.get('REC_PCT_VAR'))
            except (TypeError, ValueError): raise ValueError(f'Porcentaje variable inválido de {code}') from None
            if not isfinite(pct) or not 0 <= pct <= 100: raise ValueError(f'Porcentaje variable inválido de {code}')
            return pct/100
        if mode: raise ValueError(f'Comportamiento inválido de {code}')
        return 1.0 if rec_types.get(code) in ('MAT','MD') else 0.0
    events = {str(e['NUMERO']):e for e in hechos['EVENTO'] if str(e.get('PERIODO'))==periodo_base and e.get('EMPRESA')==empresa}
    eid = {key:f'P{h}-{key}' for key in events}
    for key, e in events.items():
        new=deepcopy(e); new['NUMERO']=eid[key];new['PERIODO']=future
        if new.get('OBJETO') is not None:
            oid=str(new['OBJETO'])
            if oid not in ids: continue
            new['OBJETO']=ids[oid]
        source['EVENTO'].append(new)
    clone_lines=[]; factors_line={}
    for line in hechos['(sin MCD) LINEA']:
        old=str(line['EVENTO'])
        if old not in eid: continue
        ev=events[old]; oid=str(ev['OBJETO']) if ev.get('OBJETO') is not None else None
        if oid is not None and oid not in ids: continue
        rec=str(line['RECURSO']); mix=frac(rec); scale=1-mix+mix*(vol(products[oid]) if oid else g)
        new=deepcopy(line);new['EVENTO']=eid[old];new['CANTIDAD']=float(line.get('CANTIDAD') or 0)*scale
        if line.get('COSTO_UNITARIO_DOCUMENTO') is not None: new['COSTO_UNITARIO_DOCUMENTO']=float(line['COSTO_UNITARIO_DOCUMENTO'])*pre(rec)
        clone_lines.append(new); factors_line[(old,str(line['NUMERO']))]=(scale*pre(rec),rec)
    units={str(c['CRI_COD']):str(c.get('CRI_UNI') or '') for c in criterios}
    for row in hechos['(sin MCD) MEDIDA']:
        if str(row.get('PERIODO')) != periodo_base or row.get('EMPRESA') != empresa: continue
        new=deepcopy(row);new['PERIODO']=future;level=str(row.get('NIVEL')); dest=str(row.get('DESTINO'))
        if level=='OBJ':
            if dest not in ids: continue
            new['DESTINO']=ids[dest];new['CANTIDAD']=float(row['CANTIDAD'])*vol(products[dest])
        elif level != 'CAP' and '%' not in units.get(str(row.get('CRITERIO')),''):
            new['CANTIDAD']=float(row['CANTIDAD'])*g
        source['(sin MCD) MEDIDA'].append(new)
    for row in hechos['(sin MCD) OBJETO']:
        if str(row.get('NUMERO')) in ids and row.get('EMPRESA')==empresa:
            new=deepcopy(row);new['NUMERO']=ids[str(row['NUMERO'])];source['(sin MCD) OBJETO'].append(new)
    source['PERIODO'].append({'CODIGO':future,'EMPRESA':empresa,'INICIO':int(future.replace('-','')+'01')})
    cloned_valuation=[]
    for typ,key,concept,value in previos.get('VALUACION_PROMEDIO',[]):
        key=str(key)
        for (old,num),(mult,rec) in factors_line.items():
            prefix=f'{old}-{num}-'
            if key.startswith(prefix):
                cloned_valuation.append((typ,f'{eid[old]}-{num}-'+key[len(prefix):],concept,float(value)*mult if concept=='MONTO' else value));break
    block_info=[]
    chosen={}
    for b in bloques:
        rec=str(b['BLQ_REC']);start=int(b['BLQ_DESDE'])
        if start <= int(future.replace('-','')+'01') and (rec not in chosen or start>int(chosen[rec]['BLQ_DESDE'])): chosen[rec]=b
    for rec,b in chosen.items():
        capacity=float(b['BLQ_CAP']); cost=float(b['BLQ_COSTO'])
        if capacity<=0 or cost<0: raise ValueError(f'Bloque inválido de {rec}')
        rows=[m for m in source['(sin MCD) MEDIDA'] if m.get('PERIODO')==future and m.get('EMPRESA')==empresa and m.get('NIVEL')=='OBJ' and m.get('CRITERIO')==b['BLQ_UNI']]
        if not rows: raise ValueError(f'El bloque {rec} no tiene medidas del inductor')
        required=sum(float(m.get('CANTIDAD') or 0) for m in rows)
        count=ceil(required/capacity);target=count*cost
        selected=[line for line in clone_lines if str(line['RECURSO'])==rec]
        prefixes = [R._clave(line['EVENTO'],line['NUMERO'])+'-' for line in selected]
        is_material = rec_types.get(rec) in ('MAT','MD')
        if is_material:
            current=sum(float(v) for typ,key,concept,v in cloned_valuation if typ=='SALIDA' and concept=='MONTO' and any(key.startswith(p) for p in prefixes))
        else:
            current=sum(float(x.get('CANTIDAD') or 0)*float(x.get('COSTO_UNITARIO_DOCUMENTO') or 0) for x in selected)
        if target and current<=0: raise ValueError(f'El bloque {rec} no tiene líneas base valorizadas')
        ratio=target/current if current else 0
        for line in selected:
            if line.get('COSTO_UNITARIO_DOCUMENTO') is not None: line['COSTO_UNITARIO_DOCUMENTO']*=ratio
        if is_material:
            cloned_valuation = [(typ,key,concept,float(v)*ratio if typ=='SALIDA' and concept=='MONTO' and any(key.startswith(p) for p in prefixes) else v) for typ,key,concept,v in cloned_valuation]
        block_info.append({'recurso':rec,'requerido':required,'bloques':count,'monto':round(target,2)})
    source['(sin MCD) LINEA'].extend(clone_lines)
    previous['VALUACION_PROMEDIO']=list(previos.get('VALUACION_PROMEDIO',[]))+cloned_valuation
    # La merma en exceso pasada no se proyecta.
    result = R.interno(source, {'PER':future,'EMP':empresa}, previous)
    output={}
    for old,new in ids.items():
        prod=products[old]; out=output.setdefault(prod,{'producto':prod,'cantidad':0.0,'costo_total':0.0,'ingreso':0.0,'elementos':defaultdict(float)})
        out['cantidad'] += float(obj_info[old].get('OBJ_CAN') or 0)*vol(prod)
        for element,amount in result.get(new,{}).items():
            out['elementos'][element] += float(amount)
    for row in ventas:
        if str(row.get('VTA_PER'))==periodo_base and row.get('VTA_EMP') in (None,'',empresa):
            prod=str(row.get('VTA_REC'));out=output.get(prod)
            if out is not None:out['ingreso'] += float(row.get('VTA_ING') or 0)*vol(prod)*allf['pv'].get(prod,1.0)
    for o in output.values():
        o['elementos']={k:round(v,2) for k,v in o['elementos'].items()};o['costo_total']=round(sum(o['elementos'].values()),2)
        o['cantidad']=round(o['cantidad'],4);o['ingreso']=round(o['ingreso'],2);o['margen']=round(o['ingreso']-o['costo_total'],2)
    items=sorted(output.values(),key=lambda x:x['producto'])
    return {'periodo':future,'factores':allf,'productos':items,'total':{'costo_total':round(sum(x['costo_total'] for x in items),2),'ingreso':round(sum(x['ingreso'] for x in items),2),'margen':round(sum(x['margen'] for x in items),2)},'bloques':block_info}


def proyectar_granular(libro, emp, meses=6, factores=None):
    """Calcula escenarios futuros sobre copias temporales en memoria del último periodo."""
    import puerto_lectura as P
    from openpyxl import load_workbook
    from .resultados import calcular_periodos, previos
    if isinstance(meses,bool) or not isinstance(meses,int) or not 1 <= meses <= 24: raise ValueError('Meses debe estar entre 1 y 24')
    book=Path(libro)
    data=P.leer(book,['RECURSO','CRITERIO','OBJETO','VENTA','PERIODO'])
    wb=load_workbook(book,read_only=True,data_only=True)
    try:
        if 'BLOQUE' in wb.sheetnames:
            rows=list(wb['BLOQUE'].values); blocks=[dict(zip(rows[0],row)) for row in rows[1:] if row and row[0]] if rows else []
        else: blocks=[]
    finally: wb.close()
    per=sorted(str(p['PER_COD']) for p in data['PERIODO'] if p.get('PER_EMP') in (None,'',emp))
    if not per: raise ValueError('La empresa no tiene periodos')
    last=per[-1]; por,h=calcular_periodos(book,emp); prev=previos(book)
    objects={str(o['OBJ_NUM']):o for o in data['OBJETO'] if o.get('OBJ_EMP') in (None,'',emp)}
    vol_hist=defaultdict(lambda:defaultdict(float)); price_hist=defaultdict(lambda:defaultdict(list)); sale_hist=defaultdict(lambda:defaultdict(lambda:[0.0,0.0]))
    for p in per:
        for oid in por.get(p,{}):
            o=objects.get(str(oid))
            if o: vol_hist[str(o['OBJ_PRO'])][p]+=float(o.get('OBJ_CAN') or 0)
    events={str(e['NUMERO']):e for e in h['EVENTO'] if e.get('EMPRESA')==emp and str(e.get('PERIODO')) in per}
    valuation={str(k):float(v) for typ,k,c,v in prev.get('VALUACION_PROMEDIO',[]) if typ=='SALIDA' and c=='MONTO'}
    for line in h['(sin MCD) LINEA']:
        event=events.get(str(line['EVENTO']))
        if not event:continue
        p=str(event['PERIODO']);rec=str(line['RECURSO']);qty=float(line.get('CANTIDAD') or 0)
        if qty<=0:continue
        if event.get('OBJETO'):
            prefix=R._clave(line['EVENTO'],line['NUMERO'])+'-'
            v=next((x for k,x in valuation.items() if k.startswith(prefix)),None)
            if v is not None:price_hist[rec][p].append(v/qty);continue
        if line.get('COSTO_UNITARIO_DOCUMENTO') is not None:price_hist[rec][p].append(float(line['COSTO_UNITARIO_DOCUMENTO']))
    for v in data['VENTA']:
        p=str(v.get('VTA_PER'));prod=str(v.get('VTA_REC'))
        if p in per and v.get('VTA_EMP') in (None,'',emp):
            sale_hist[prod][p][0]+=float(v.get('VTA_CAN') or 0);sale_hist[prod][p][1]+=float(v.get('VTA_ING') or 0)
    defaults={'vol':{},'pre':{},'pv':{}}
    for prod, vals in vol_hist.items():defaults['vol'][prod]=_pronosticar([vals[p] for p in per if p in vals],meses)
    for rec, vals in price_hist.items():defaults['pre'][rec]=_pronosticar([sum(vals[p])/len(vals[p]) for p in per if vals.get(p)],meses)
    for prod, vals in sale_hist.items():defaults['pv'][prod]=_pronosticar([vals[p][1]/vals[p][0] for p in per if p in vals and vals[p][0]],meses)
    for kind,rows in (factores or {}).items():
        if kind not in defaults or not isinstance(rows,dict):raise ValueError('Factores inválidos')
        defaults[kind].update(rows)
    def run(factors,h):return proyectar_hechos(hh,prev,emp,last,data['OBJETO'],data['RECURSO'],data['CRITERIO'],data['VENTA'],factors,h,blocks)
    hh=h
    outputs=[run(defaults,i) for i in range(1,meses+1)]
    base=outputs[0]['total']['margen']; sensitivity=[]
    for kind, entries in defaults.items():
        for name,val in entries.items():
            current=_factor(val,1,outputs[0]['periodo']);delta=[]
            for mult in (1.1,.9):
                f=deepcopy(defaults);f[kind][name]=current*mult
                delta.append(round(run(f,1)['total']['margen']-base,2))
            sensitivity.append({'factor':f'{kind}:{name}','mas':delta[0],'menos':delta[1]})
    sensitivity.sort(key=lambda x:max(abs(x['mas']),abs(x['menos'])),reverse=True)
    return {'base':last,'meses':outputs,'sensibilidad':sensitivity,'bloques':outputs[0]['bloques']}
