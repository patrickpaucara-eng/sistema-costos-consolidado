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
    evidence = json.dumps([calibrador,objeto,periodo,baseline,data], ensure_ascii=False, separators=(',',':'))
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
