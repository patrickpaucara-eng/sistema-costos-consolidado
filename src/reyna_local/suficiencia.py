"""Diagnóstico conservador de presencia de datos; no certifica calidad ni capacidad del motor."""
from openpyxl import load_workbook

ETIQUETAS = (
    'Totales de costos y ventas',
    'Consumos y horas asociados a órdenes',
    'Centros, actividades e inductores medidos',
    'Capacidad, estándares, merma y rechazos',
    'Al menos siete meses con hechos',
)


def detectar(tablas):
    def rows(n): return tablas.get(n, [])
    eventos = rows('EVENTO'); lineas = rows('LINEA'); medidas = rows('MEDIDA')
    eventos_ot = {e.get('EVE_NUM') for e in eventos if e.get('EVE_OBJ')}
    consumos = any(x.get('LIN_EVE') in eventos_ot and x.get('LIN_CAN') is not None for x in lineas)
    criterios_tiempo = {c.get('CRI_COD') for c in rows('CRITERIO') if str(c.get('CRI_UNI') or '').strip().lower() in ('h', 'hora', 'horas', 'min', 'minuto', 'minutos')}
    horas = any(x.get('MED_NIVEL') == 'OBJ' and x.get('MED_CAN') is not None and x.get('MED_CRIT') in criterios_tiempo for x in medidas)
    criterios = {x.get('MED_CRIT') for x in medidas if x.get('MED_CAN') is not None}
    periodos = {str(e.get('EVE_PER')) for e in eventos if e.get('EVE_PER')}
    costo = any(x.get('LIN_MTO') is not None or (x.get('LIN_CAN') is not None and x.get('LIN_CU_DOC') is not None) for x in lineas)
    venta = any(x.get('VTA_ING') is not None for x in rows('VENTA'))
    flags = [bool(eventos and costo and venta), bool(consumos and horas),
             bool(rows('CENTRO') and rows('ACTIVIDAD') and criterios),
             bool(any(m.get('MED_NIVEL') == 'CAP' for m in medidas) and
                  any(c.get('CMP_CAN_EST') is not None and c.get('CMP_MERMA') is not None for c in rows('COMPONENTE')) and rows('RECHAZO')),
             len(periodos) >= 7]
    nivel = -1
    for i, ok in enumerate(flags):
        if not ok: break
        nivel = i
    return {'nivel': nivel if nivel >= 0 else None, 'requisitos': [dict(nivel=i, descripcion=x, presente=flags[i]) for i,x in enumerate(ETIQUETAS)],
            'falta': ETIQUETAS[nivel + 1] if nivel < 4 else None,
            'aviso': 'Diagnóstico preliminar de datos presentes; no certifica calidad ni habilita cálculos.'}


def detectar_libro(libro):
    nombres = ('EVENTO','LINEA','MEDIDA','VENTA','CENTRO','ACTIVIDAD','COMPONENTE','RECHAZO','CRITERIO')
    wb=load_workbook(libro, read_only=True, data_only=True)
    try:
        tablas={}
        for nombre in nombres:
            if nombre not in wb: continue
            it=wb[nombre].values; headers=next(it, ())
            tablas[nombre]=[dict(zip(headers,row)) for row in it if any(v is not None for v in row)]
        return detectar(tablas)
    finally: wb.close()
