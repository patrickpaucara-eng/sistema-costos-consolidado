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
    # Gráfico sin dependencias ni acceso de red; usa las cifras del contrato.
    serie = [x for x in resultados['serie'] if isinstance(x.get('margen'), (int, float))]
    chart = ''
    if serie:
        valores = [x['margen'] for x in serie]
        minimo, maximo = min(0, *valores), max(1, *valores)
        puntos = ' '.join(f'{40 + 700*i/max(1,len(serie)-1):.2f},{190 - 150*(v-minimo)/(maximo-minimo):.2f}' for i,v in enumerate(valores))
        chart = '<h2>Margen por periodo</h2><svg viewBox="0 0 780 220" role="img" aria-label="Margen por periodo"><polyline fill="none" stroke="#118067" stroke-width="3" points="' + puntos + '"/></svg>'
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
