"""Operaciones puras para calibraciones auditables; integración y persistencia pendientes."""
from hashlib import sha256
from statistics import median
import json
import math
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
from threading import RLock

_lock_archivos = RLock()

def _sincronizado(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        with _lock_archivos: return fn(*args, **kwargs)
    return wrapper

_contexto = ContextVar("reyna_aprendizaje", default=None)

@contextmanager
def contexto(carpeta, empresa):
    token = _contexto.set((carpeta, empresa))
    try: yield
    finally: _contexto.reset(token)


def mes_siguiente(periodo):
    year, month = map(int, periodo.split('-'))
    if not 1 <= month <= 12: raise ValueError('Periodo inválido')
    return f'{year + (month == 12):04d}-{month % 12 + 1:02d}'


def calibrar_mediana(valores, valor_libro, periodo, calibrador, objeto):
    data = [float(v) for v in valores]
    baseline = float(valor_libro)
    if len(data) < 3 or not all(math.isfinite(v) for v in [*data, baseline]):
        raise ValueError('Se necesitan tres o más valores finitos')
    learned = median(data); mad = median(abs(x-learned) for x in data)
    threshold = 3*1.4826*mad
    outliers = [{'indice':i, 'valor':x} for i,x in enumerate(data) if abs(x-learned)>threshold]
    mae_book = sum(abs(x-baseline) for x in data[2:])/(len(data)-2)
    mae_new = sum(abs(data[i]-median(data[:i])) for i in range(2,len(data)))/(len(data)-2)
    change = (learned-baseline)/abs(baseline) if baseline else None
    status = 'APLICADO' if change is not None and abs(change)<=.20 and mae_new<mae_book else 'PENDIENTE'
    evidence = json.dumps([calibrador,objeto,baseline,data], ensure_ascii=False, separators=(',',':'))
    return {'id':sha256(evidence.encode()).hexdigest(), 'calibrador':calibrador, 'objeto':objeto,
            'valor_libro':baseline, 'valor_aprendido':learned, 'cambio_pct':change,
            'mae_libro':mae_book, 'mae_aprendido':mae_new, 'estado':status,
            'vigente_desde':mes_siguiente(periodo), 'atipicos':outliers}


def probabilidad(cumplimientos):
    values = [float(v) for v in cumplimientos if v is not None]
    return (1 + sum(x >= .8 for x in values))/(2 + len(values))


def umbral(variaciones):
    values = [float(v) for v in variaciones]
    if not values: return .05
    center = median(values)
    return max(.05, 2*median(abs(v-center) for v in values))


def vigente(calibracion, periodo):
    return calibracion.get('estado') == 'APLICADO' and str(calibracion.get('vigente_desde','9999-99')) <= periodo


@_sincronizado
def registrar(ruta, candidatos, hoy):
    """Persistencia idempotente: conserva decisiones tomadas con la misma evidencia."""
    import os
    from pathlib import Path
    from tempfile import NamedTemporaryFile
    path = Path(ruta)
    if path.is_symlink() or path.parent.is_symlink(): raise ValueError('Ruta de aprendizaje inválida')
    current = json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
    if not isinstance(current,list): raise ValueError('Archivo de aprendizaje inválido')
    by_id = {x['id']:x for x in current}
    for row in candidatos:
        if row['id'] in by_id: continue
        by_id[row['id']] = {**row, 'fecha':str(hoy), 'decidido_por':None}
    result = sorted(by_id.values(), key=lambda x: (x['vigente_desde'],x['id']))
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = None
    try:
        with NamedTemporaryFile('w', encoding='utf-8', dir=path.parent, delete=False) as file:
            temp = file.name
            json.dump(result,file,ensure_ascii=False,sort_keys=True,indent=2)
            file.flush(); os.fsync(file.fileno())
        os.replace(temp,path)
    finally:
        if temp and os.path.exists(temp): os.unlink(temp)
    return result


@_sincronizado
def decidir(ruta, identificador, decision, hoy, actor=None):
    """Decisiones explícitas; un rechazo no se convierte después en aprobación."""
    from pathlib import Path
    path = Path(ruta)
    if path.is_symlink() or path.parent.is_symlink(): raise ValueError('Ruta de aprendizaje inválida')
    if decision not in ('APROBAR','RECHAZAR'): raise ValueError('Decisión inválida')
    data = json.loads(path.read_text(encoding='utf-8'))
    matches = [x for x in data if x.get('id') == identificador]
    if len(matches) != 1: raise ValueError('Calibración inexistente o ambigua')
    row = matches[0]
    if row.get('estado') != 'PENDIENTE': raise ValueError('La calibración ya fue decidida')
    if decision == 'APROBAR':
        from datetime import date
        decision_date=date.fromisoformat(str(hoy)[:10])
        start=mes_siguiente(decision_date.strftime('%Y-%m'))
        row['vigente_desde']=max(str(row.get('vigente_desde') or start),start)
    row.update(estado='APLICADO' if decision == 'APROBAR' else 'RECHAZADO', decidido_por=actor, fecha_decision=str(hoy))
    # Reutiliza la escritura atómica sin reinterpretar decisiones.
    import os
    from tempfile import NamedTemporaryFile
    temp = None
    try:
        with NamedTemporaryFile('w', encoding='utf-8', dir=path.parent, delete=False) as file:
            temp=file.name; json.dump(data,file,ensure_ascii=False,sort_keys=True,indent=2);file.flush();os.fsync(file.fileno())
        os.replace(temp,path)
    finally:
        if temp and os.path.exists(temp): os.unlink(temp)
    return row


def calibrar_componentes(libro, empresa, hasta=None):
    """Candidatos de consumo y merma a partir de observaciones mensuales del libro."""
    from collections import defaultdict
    import puerto_lectura as P
    try: data = P.leer(libro, ['DIFERENCIA','COMPONENTE','OBJETO'])
    except KeyError: return []
    objects = {str(o['OBJ_NUM']):o for o in data['OBJETO'] if o.get('OBJ_EMP') in (None,'',empresa)}
    components = {(str(c['CMP_PRO']),str(c['CMP_REC'])):c for c in data['COMPONENTE'] if c.get('CMP_EMP') in (None,'',empresa)}
    monthly = defaultdict(lambda: {'real':0.0,'merma':0.0,'orders':set()})
    for d in data['DIFERENCIA']:
        if d.get('DIF_EMP') not in (None,'',empresa): continue
        obj = objects.get(str(d.get('DIF_OBJ')))
        if not obj or not d.get('DIF_PER') or not d.get('DIF_REC') or (hasta and str(d['DIF_PER']) > hasta): continue
        key = (str(obj.get('OBJ_PRO')),str(d['DIF_REC']),str(d['DIF_PER']))
        monthly[key]['real'] += float(d.get('DIF_QREAL') or 0)
        monthly[key]['merma'] += float(d.get('DIF_QMER') or 0)
        monthly[key]['orders'].add(str(d['DIF_OBJ']))
    series = defaultdict(lambda: {'consumo':[],'merma':[]})
    for (prod,rec,per), data_row in sorted(monthly.items()):
        good = sum(float(objects[o].get('OBJ_CAN') or 0) for o in data_row['orders'])
        if good > 0: series[(prod,rec)]['consumo'].append((per,data_row['real']/good))
        if data_row['real'] > 0: series[(prod,rec)]['merma'].append((per,100*data_row['merma']/data_row['real']))
    out = []
    for key, values in sorted(series.items()):
        base = components.get(key)
        if not base: continue
        for kind, field in [('consumo','CMP_CAN_EST'),('merma','CMP_MERMA')]:
            observations = values[kind]
            if len(observations) < 3 or base.get(field) is None: continue
            out.append(calibrar_mediana([value for _,value in observations],base[field],observations[-1][0],kind,{'empresa':empresa,'producto':key[0],'recurso':key[1]}))
    return out


def _registro(calibrador, objeto, valor, periodo, evidencia, estado='APLICADO', referencia=None):
    payload=json.dumps([calibrador,objeto,evidencia],ensure_ascii=False,sort_keys=True,separators=(',',':'))
    return {'id':sha256(payload.encode()).hexdigest(),'calibrador':calibrador,'objeto':objeto,
            'valor_libro':referencia,'valor_aprendido':valor,'estado':estado,'vigente_desde':mes_siguiente(periodo),
            'evidencia':evidencia}


def calibrar(libro, emp, resultados_publicados):
    """Calibra solo con observaciones publicadas; nunca modifica el libro ni calcula costos."""
    import puerto_lectura as P
    from collections import defaultdict
    from .variable import regresion
    if isinstance(resultados_publicados,dict): results=list(resultados_publicados.values())
    else: results=list(resultados_publicados)
    results=sorted([r for r in results if r.get('sintesis')=='REAL' and r.get('empresa',{}).get('codigo')==emp and r.get('periodo_actual')], key=lambda r:r['periodo_actual'])
    if not results: return []
    periods=[r['periodo_actual'] for r in results]
    if len(periods)!=len(set(periods)): raise ValueError('Resultados duplicados para un mismo periodo')
    last=results[-1]['periodo_actual']
    out=calibrar_componentes(libro,emp,hasta=last)
    histories=defaultdict(list); successes=defaultdict(list); attempts={}
    activity_history=defaultdict(list)
    for r in results:
        period=r['periodo_actual']; by_product=defaultdict(lambda:[0.0,0.0])
        for o in r.get('objetos',[]):
            q=float(o.get('cantidad') or 0);by_product[str(o.get('producto'))][0]+=float(o.get('costo_total') or 0);by_product[str(o.get('producto'))][1]+=q
        for product,(cost,qty) in by_product.items():
            if qty>0: histories[product].append((period,cost/qty))
        for x in r.get('seguimiento') or []:
            if x.get('cumplimiento') is None:continue
            key=(x.get('propuesta'),x.get('decidida_en'),x.get('version'))
            if not key[0]:continue
            attempts[key]=(str(x.get('elemento') or x.get('causa') or ''),float(x['cumplimiento']))
    for kind, outcome in attempts.values(): successes[kind].append(outcome)
    for product, items in histories.items():
        if len(items)<6:continue
        changes=[items[i][1]/items[i-1][1]-1 for i in range(1,len(items)) if items[i-1][1]]
        if changes: out.append(_registro('umbral',{'empresa':emp,'producto':product},umbral(changes),last,changes,referencia=.05))
    for kind,values in successes.items():
        if kind:out.append(_registro('probabilidad',{'empresa':emp,'tipo':kind},probabilidad(values),last,values,referencia=.5))
    info=results[-1].get('proyeccion_info') or {}
    for field in ('modelo_ventas','modelo_costo','modelo_margen'):
        if info.get(field):out.append(_registro('modelo_pronostico',{'empresa':emp,'serie':field},{'modelo':info[field],'mase':info.get('mase_margen') if field=='modelo_margen' else None},last,info,'INFORMATIVO'))
    try: measures=P.leer(libro,['MEDIDA'])['MEDIDA']
    except KeyError: measures=[]
    for r in results:
        period=r['periodo_actual']; rules=(r.get('modelo') or {}).get('reglas') or []
        for a in r.get('actividades') or []:
            crits={x.get('inductor') for x in rules if x.get('etapa')=='P4C' and x.get('origen')==a.get('codigo') and x.get('inductor')}
            if len(crits)!=1: continue
            crit=next(iter(crits)); vals=[m for m in measures if str(m.get('MED_PER'))==period and m.get('MED_EMP') in (None,'',emp) and m.get('MED_CRIT')==crit and m.get('MED_NIVEL')=='OBJ']
            if vals:activity_history[(str(a['codigo']),str(crit))].append((sum(float(m.get('MED_CAN') or 0) for m in vals),float(a.get('costo') or 0)))
    for (activity,criterion),pairs in activity_history.items():
        if len(pairs)<6:continue
        stats=regresion(pairs); stats['alerta']='inductor débil' if stats['r2'] is not None and stats['r2']<.5 else None
        out.append(_registro('inductor',{'empresa':emp,'actividad':activity,'inductor':criterion},stats,last,pairs,'INFORMATIVO'))
    return out


def leer_capa(empresa, carpeta=None):
    import re
    from pathlib import Path
    from .raiz import RAIZ
    if not isinstance(empresa,str) or not re.fullmatch(r'[A-Za-z0-9_]{1,60}',empresa): raise ValueError('Empresa inválida')
    root=Path(carpeta) if carpeta is not None else RAIZ/'datos'
    path=root/'aprendizaje'/f'{empresa}.json'
    if path.is_symlink() or path.parent.is_symlink(): raise ValueError('Archivo de aprendizaje inválido')
    if not path.exists(): return []
    data=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data,list): raise ValueError('Archivo de aprendizaje inválido')
    return data


def estandar_vigente(empresa, producto, recurso, periodo, carpeta=None):
    """Devuelve consumo y merma aprobados y vigentes, o None si no existe ninguno."""
    candidates=[x for x in leer_capa(empresa,carpeta) if vigente(x,periodo) and isinstance(x.get('objeto'),dict)
                and str(x['objeto'].get('producto'))==str(producto) and str(x['objeto'].get('recurso'))==str(recurso)
                and x.get('calibrador') in ('consumo','merma')]
    if not candidates:return None
    chosen={}
    for row in sorted(candidates,key=lambda x:(x.get('vigente_desde',''),x.get('fecha',''),x.get('id',''))):chosen[row['calibrador']]=row.get('valor_aprendido')
    return chosen.get('consumo'),chosen.get('merma')


def _datos_libro(libro):
    """Ubicación local de la capa y clave estable del libro."""
    from pathlib import Path
    from .raiz import RAIZ
    book=Path(libro).resolve()
    if book.parent == (RAIZ/'casos'/'libros').resolve():return RAIZ/'datos',book.stem
    if book.name == 'libro.xlsx' and len(book.parent.name)==32:return book.parent.parent,'esp_'+book.parent.name[:12]
    if book.parent.name=='libros':return book.parent.parent,book.stem
    return RAIZ/'datos',book.stem


def aplicar(resultado, libro, series, pro, hechos, par, prev, por_per, est, inc, naturalezas, contexto=None):
    """Aplica solamente capas vigentes a hallazgos y propuestas; nunca cambia costos."""
    from . import analisis as A
    root,key=contexto or _contexto.get() or _datos_libro(libro);periodo=resultado['periodo_actual']
    active=[x for x in leer_capa(key,root) if vigente(x,periodo)]
    if not active:return resultado
    thresholds={}
    for x in sorted(active,key=lambda x:(x.get('vigente_desde',''),x.get('id',''))):
        obj=x.get('objeto') or {}
        if x.get('calibrador')=='umbral' and isinstance(obj,dict) and obj.get('producto'):
            thresholds[str(obj['producto'])]=float(x['valor_aprendido'])
    if thresholds:
        hall=[]
        for product, points in sorted(series.items()): hall.extend(A.diagnostico({product:points},periodo,umbral=thresholds.get(product,.05)))
        resultado['hallazgos']=hall
        resultado['propuestas']=A.propuestas(series,periodo,hall,resultado['relevancia'])
        from .resultados import _propuesta_por_causa
        _propuesta_por_causa(resultado['propuestas'],resultado.get('variaciones') or [],pro)
        from .variable import analizar_libro
        resultado['costeo_variable'],resultado['propuestas']=analizar_libro(libro,resultado,hechos,par,prev,por_per,est,inc,naturalezas)
    probs={}
    for x in sorted(active,key=lambda x:(x.get('vigente_desde',''),x.get('id',''))):
        obj=x.get('objeto') or {}
        if x.get('calibrador')=='probabilidad' and isinstance(obj,dict) and obj.get('tipo'):
            probs[str(obj['tipo'])]=float(x['valor_aprendido'])
    for proposal in resultado['propuestas']:
        probability=probs.get(str(proposal.get('causa')),probs.get(str(proposal.get('elemento')),.5))
        if probability is None:continue
        proposal['probabilidad']=probability
        proposal['prioridad']=round(float(proposal.get('impacto_anual') or 0)*probability,2)
    resultado['propuestas'].sort(key=lambda p:-float(p.get('prioridad',p.get('impacto_anual',0))))
    return resultado


def factor_estandar(empresa, producto, recurso, periodo, consumo_libro, merma_libro, carpeta=None):
    """Factor para una proyección futura; None indica ausencia de estándar aplicado."""
    standard=estandar_vigente(empresa,producto,recurso,periodo,carpeta)
    if standard is None:return None
    base=float(consumo_libro); waste=float(merma_libro or 0)
    if not math.isfinite(base) or not math.isfinite(waste) or base<=0 or waste<0: raise ValueError('Estándar del libro inválido')
    consumption=base if standard[0] is None else float(standard[0]); learned_waste=waste if standard[1] is None else float(standard[1])
    if not math.isfinite(consumption) or not math.isfinite(learned_waste) or consumption<0 or learned_waste<0: raise ValueError('Estándar aprendido inválido')
    return consumption*(1+learned_waste/100)/(base*(1+waste/100))
