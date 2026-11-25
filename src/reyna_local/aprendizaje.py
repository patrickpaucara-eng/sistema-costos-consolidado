"""Operaciones puras para calibraciones auditables; integración y persistencia pendientes."""
from hashlib import sha256
from statistics import median
import json
import math


def mes_siguiente(periodo):
    year, month = map(int, periodo.split('-'))
    if not 1 <= month <= 12: raise ValueError('Periodo inválido')
    return f'{year + (month == 12):04d}-{month % 12 + 1:02d}'


def calibrar_mediana(valores, valor_libro, periodo, calibrador, objeto):
    data = [float(v) for v in valores]
    baseline = float(valor_libro)
    if len(data) < 2 or not all(math.isfinite(v) for v in [*data, baseline]):
        raise ValueError('Se necesitan dos o más valores finitos')
    learned = median(data); mad = median(abs(x-learned) for x in data)
    threshold = 3*1.4826*mad
    outliers = [{'indice':i, 'valor':x} for i,x in enumerate(data) if abs(x-learned)>threshold]
    mae_book = sum(abs(x-baseline) for x in data[1:])/(len(data)-1)
    mae_new = sum(abs(data[i]-median(data[:i])) for i in range(1,len(data)))/(len(data)-1)
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


def registrar(ruta, candidatos, hoy):
    """Persistencia idempotente: conserva decisiones tomadas con la misma evidencia."""
    import os
    from pathlib import Path
    from tempfile import NamedTemporaryFile
    path = Path(ruta)
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


def decidir(ruta, identificador, decision, hoy, actor=None):
    """Decisiones explícitas; un rechazo no se convierte después en aprobación."""
    from pathlib import Path
    path = Path(ruta)
    if decision not in ('APROBAR','RECHAZAR'): raise ValueError('Decisión inválida')
    data = json.loads(path.read_text(encoding='utf-8'))
    matches = [x for x in data if x.get('id') == identificador]
    if len(matches) != 1: raise ValueError('Calibración inexistente o ambigua')
    row = matches[0]
    if row.get('estado') != 'PENDIENTE': raise ValueError('La calibración ya fue decidida')
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
