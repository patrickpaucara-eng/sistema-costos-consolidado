"""Exporta exclusivamente datos de un contrato de resultados ya calculado."""
from html import escape
import json
from pathlib import Path
from uuid import uuid4

from openpyxl import Workbook
from openpyxl.styles import Font
from .contrato import validar

TIPOS = {'resultados': '.xlsx', 'analitica': '.xlsx', 'proyeccion': '.xlsx', 'html': '.html', 'codigo': '.docx'}
SECCIONES = {
    'resultados': [('Objetos', 'objetos'), ('Actividades', 'actividades'), ('Estado NIIF 18', 'estado_resultados')],
    'analitica': [('Relevancia', 'relevancia'), ('Hallazgos', 'hallazgos')],
    'proyeccion': [('Serie', 'serie'), ('Escenarios', 'escenarios'), ('Propuestas', 'propuestas')],
}


def _celda(value):
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True)
    # Excel no debe interpretar contenido procedente del contrato como fórmula.
    if isinstance(value, str) and value.startswith(('=', '+', '-', '@')):
        return "'" + value
    return value


def _columnas(rows):
    return list(dict.fromkeys(key for row in rows for key in row))


def _libro(resultados, tipo, destino):
    libro = Workbook()
    resumen = libro.active
    resumen.title = 'Identificación'
    for key, value in [('Empresa', resultados['empresa'].get('nombre')), ('Periodo', resultados['periodo_actual']),
                       ('Síntesis', resultados['sintesis']), ('Moneda', resultados['moneda']),
                       ('Origen', resultados.get('_nota', 'Resultado suministrado'))]:
        resumen.append([key, _celda(value)])
    for nombre, campo in SECCIONES[tipo]:
        hoja = libro.create_sheet(nombre)
        rows = resultados[campo]
        columnas = _columnas(rows)
        if not columnas:
            hoja.append(['Sin datos disponibles'])
            continue
        hoja.append(columnas)
        for cell in hoja[1]:
            cell.font = Font(bold=True)
        hoja.freeze_panes = 'A2'
        for row in rows:
            hoja.append([_celda(row.get(col)) for col in columnas])
    libro.save(destino)
    libro.close()


def _html(resultados, destino):
    def tabla(rows):
        columnas = _columnas(rows)
        if not columnas:
            return '<p>Sin datos disponibles.</p>'
        head = ''.join('<th>' + escape(str(c)) + '</th>' for c in columnas)
        body = ''.join('<tr>' + ''.join('<td>' + escape(str(r.get(c, ''))) + '</td>' for c in columnas) + '</tr>' for r in rows)
        return '<table><thead><tr>' + head + '</tr></thead><tbody>' + body + '</tbody></table>'
    kpis = ''.join('<li><b>' + escape(k) + ':</b> ' + escape(str(v)) + '</li>' for k, v in resultados['kpi'].items())
    secciones = ''.join('<h2>' + escape(nombre) + '</h2>' + tabla(resultados[campo])
                        for nombre, campo in [*SECCIONES['resultados'], *SECCIONES['analitica'], *SECCIONES['proyeccion']])
    # Dibuja valores publicados; la banda corresponde al margen P05–P95.
    serie = resultados['serie']
    chart = ''
    if serie:
        periodos = sorted({str(x['periodo']) for x in serie})
        valores = [float(x[k]) for x in serie for k in ('ventas','costo_total','margen','p05','p50','p95') if isinstance(x.get(k), (int,float))]
        minimo, maximo = min(0, *valores), max(1, *valores)
        x = lambda periodo: 40 + 700 * periodos.index(str(periodo)) / max(1, len(periodos)-1)
        y = lambda value: 190 - 150 * (value-minimo) / (maximo-minimo)
        grupos = []
        banda = sorted((r for r in serie if r.get('tipo')=='PROYECTADO_EST' and isinstance(r.get('p05'),(int,float)) and isinstance(r.get('p95'),(int,float))), key=lambda r:r['periodo'])
        if banda:
            puntos = [f"{x(r['periodo']):.2f},{y(r['p95']):.2f}" for r in banda] + [f"{x(r['periodo']):.2f},{y(r['p05']):.2f}" for r in reversed(banda)]
            grupos.append('<polygon data-banda="p05-p95" fill="#c1e4db" points="'+' '.join(puntos)+'"/>')
            grupos.append('<polyline fill="none" stroke="#118067" stroke-dasharray="3 3" points="'+' '.join(f"{x(r['periodo']):.2f},{y(r['p50']):.2f}" for r in banda if isinstance(r.get('p50'),(int,float)))+'"/>')
        for campo, color in [('ventas','#315d6f'),('costo_total','#ce8334'),('margen','#118067')]:
            for tipo in ('HISTORICO','PROYECTADO_DET'):
                filas = sorted((r for r in serie if r.get('tipo') in (tipo,'ACTUAL') and isinstance(r.get(campo),(int,float))),key=lambda r:r['periodo'])
                puntos = ' '.join(f"{x(r['periodo']):.2f},{y(r[campo]):.2f}" for r in filas)
                grupos.append(f'<polyline fill="none" stroke="{color}" stroke-width="2" stroke-dasharray="{("5 5" if tipo == "PROYECTADO_DET" else "none")}" points="{puntos}"/>')
        chart = '<h2>Ventas, costo y margen</h2><p>Histórico sólido · determinístico punteado · banda estocástica P05–P95 y línea P50</p><svg viewBox="0 0 780 220" role="img" aria-label="Evolución">'+''.join(grupos)+'</svg>'
    info = resultados.get('proyeccion_info') or {}
    chart += '<p>' + escape(' · '.join(f'{k}: {v}' for k,v in info.items())) + '</p>'
    if not any(str(r.get('tipo','')).startswith('PROYECTADO') for r in serie):
        chart += '<p>Se necesitan más de 6 meses para proyectar</p>'
    if resultados.get('sintesis') == 'CONTABLE':
        chart += '<p>Financieros fuera del inventario (NIC 2 / NIIF 18)</p>'
    if resultados.get('sintesis') == 'ESTIMADO':
        chart += '<h2>Estimación estadística fuera de muestra (no es un estándar)</h2>' + tabla([dict(producto=k, **v) for k,v in (resultados.get('estimacion') or {}).items()])
    escenarios = resultados['escenarios']
    rangos = [r for r in escenarios if all(isinstance(r.get(k),(int,float)) for k in ('margen_p05','margen_p50','margen_p95'))]
    if rangos:
        bajo = min(0, *(r['margen_p05'] for r in rangos))
        alto = max(1, *(r['margen_p95'] for r in rangos))
        escala = lambda v: 150 + 570 * (v-bajo)/(alto-bajo)
        figuras = []
        for i,r in enumerate(rangos):
            y_r = 25 + i * 170 / max(1,len(rangos))
            figuras.append(f'<text x="5" y="{y_r+4:.2f}">{escape(str(r.get("nombre", "")))}</text><line x1="{escala(r["margen_p05"]):.2f}" x2="{escala(r["margen_p95"]):.2f}" y1="{y_r:.2f}" y2="{y_r:.2f}" stroke="#118067" stroke-width="5"/><circle cx="{escala(r["margen_p50"]):.2f}" cy="{y_r:.2f}" r="5" fill="#243f80"/>')
        chart += '<h2>Rango de escenarios</h2><svg viewBox="0 0 780 220" role="img" aria-label="Escenarios">'+''.join(figuras)+'</svg>'
    chart += '<p>Impacto anual total: S/ ' + escape(str(round(sum(float(x.get('impacto_anual',0)) for x in resultados['propuestas']),2))) + '</p>'
    objetos = resultados['objetos']
    if objetos:
        keys = ('md', 'mod', 'cif', 'admin', 'gasto_venta', 'financiero')
        colors = ('#116b61', '#47988b', '#82bdb1', '#d0a35c', '#dc7650', '#845a78')
        maximum = max(1, *(float(o.get('costo_total', 0)) for o in objetos))
        width = 650 / len(objetos)
        bars = []
        for index, obj in enumerate(objetos):
            y = 190
            for key, color in zip(keys, colors):
                height = max(0, float(obj.get(key, 0))) * 150 / maximum
                y -= height
                bars.append(f'<rect x="{60+index*width:.2f}" y="{y:.2f}" width="{width*.6:.2f}" height="{height:.2f}" fill="{color}"/>')
            bars.append(f'<text x="{60+index*width:.2f}" y="215">{escape(str(obj.get("codigo", "")))}</text>')
        chart += '<h2>Costos por objeto</h2><svg viewBox="0 0 780 230" role="img" aria-label="Costos por objeto">' + ''.join(bars) + '</svg>'
    relevancia = resultados['relevancia']
    if relevancia:
        maximum = max(1, *(float(x.get('importe', 0)) for x in relevancia))
        width = 650 / len(relevancia)
        barras, puntos = [], []
        for index, item in enumerate(relevancia):
            x = 60 + index * width
            height = max(0, float(item.get('importe', 0))) * 150 / maximum
            color = '#b85142' if item.get('critico') else '#47988b'
            barras.append(f'<rect x="{x:.2f}" y="{190-height:.2f}" width="{width*.6:.2f}" height="{height:.2f}" fill="{color}"/>')
            puntos.append(f'{x+width*.3:.2f},{190-float(item.get("acumulado",0))*150:.2f}')
        chart += '<h2>Relevancia</h2><svg viewBox="0 0 780 220" role="img" aria-label="Relevancia">' + ''.join(barras) + '<polyline fill="none" stroke="#243f80" stroke-width="2" points="' + ' '.join(puntos) + '"/></svg>'
    documento = ('<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width">'
                 '<title>Resultados de costos</title><style>body{font:16px system-ui;margin:2rem;color:#15253d}'
                 'table{border-collapse:collapse;display:block;overflow:auto;margin-bottom:2rem}td,th{border:1px solid #ccd6e0;'
                 'padding:.5rem;text-align:left}th{background:#e8eff8}li{margin:.5rem}</style><h1>Resultados de costos</h1><p>'
                 + escape(str(resultados.get('_nota', 'Resultado suministrado'))) + ' · ' + escape(resultados['periodo_actual'])
                 + ' · ' + escape(resultados['sintesis']) + '</p><ul>' + kpis + '</ul>' + chart + secciones + '</html>')
    destino.write_text(documento, encoding='utf-8')


def exportar(resultados, tipo, carpeta):
    if tipo not in TIPOS:
        raise ValueError('El tipo de reporte no existe.')
    if tipo != 'codigo':
        if not isinstance(resultados, dict):
            raise ValueError('Se requieren resultados para exportar.')
        try:
            errores = validar(resultados)
        except (TypeError, KeyError, ValueError):
            raise ValueError('Los resultados no cumplen el contrato.') from None
        if errores:
            raise ValueError('Los resultados no cumplen el contrato: ' + '; '.join(errores))
    carpeta = Path(carpeta).resolve()
    carpeta.mkdir(parents=True, exist_ok=True, mode=0o700)
    destino = carpeta / (tipo + '-' + uuid4().hex + TIPOS[tipo])
    try:
        if tipo in SECCIONES:
            _libro(resultados, tipo, destino)
        elif tipo == 'html':
            _html(resultados, destino)
        else:
            from .codigo_fuente import generar_word
            generar_word(destino)
    except Exception:
        destino.unlink(missing_ok=True)
        raise
    return destino
