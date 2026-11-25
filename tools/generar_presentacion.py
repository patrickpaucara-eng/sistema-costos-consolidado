"""Presentación de desarrollo; python-pptx no se importa en el ejecutable."""
import argparse
import json
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt


def generar(resultado, destino):
    r = resultado
    deck = Presentation()
    def format_value(value):
        if value is None: return 'No disponible'
        if isinstance(value, (float, int)) and not isinstance(value, bool): return f'{value:,.2f}'
        return str(value)
    def slide(title, lines):
        s = deck.slides.add_slide(deck.slide_layouts[1])
        s.shapes.title.text = title
        tf = s.placeholders[1].text_frame
        tf.clear()
        for i, line in enumerate(lines or ['Sin datos disponibles']):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = str(line); p.font.size = Pt(14)
        return s
    slide('Presentación ejecutiva', [r['empresa'].get('nombre'), r['periodo_actual'], r['sintesis'], 'Sello: ' + format_value(r.get('sello'))])
    slide('Indicadores', [f'{k}: {format_value(v)}' for k, v in r['kpi'].items()])
    slide('Costo por producto', [f"{o['producto']}: costo {format_value(o['costo_total'])} · unitario {format_value(o['costo_unitario'])}" for o in r['objetos']])
    slide('Relevancia (Pareto)', [f"{x.get('elemento')}: {format_value(x.get('importe'))} · acumulado {format_value(x.get('acumulado'))}" for x in r['relevancia']])
    slide('Hallazgos y causa', [f"{x.get('mensaje', '')} · causa: {format_value(x.get('causa'))}" for x in r['hallazgos']])
    bands = {x['periodo']: x for x in r['serie'] if x.get('tipo') == 'PROYECTADO_EST'}
    projected = [x for x in r['serie'] if x.get('tipo') == 'PROYECTADO_DET']
    lines = []
    for x in projected[:6]:
        band = bands.get(x['periodo'])
        interval = f"P05 {format_value(band.get('p05'))} · P95 {format_value(band.get('p95'))}" if band else 'Banda no estimable'
        lines.append(f"{x['periodo']}: margen {format_value(x.get('margen'))} · {interval}")
    slide('Proyección a seis meses', lines or ['Proyección no disponible'])
    slide('Propuestas', [f"{p.get('descripcion', '')} · impacto anual {format_value(p.get('impacto_anual'))} · {format_value(p.get('responsable'))}" for p in r['propuestas']])
    ordered = sorted(r['propuestas'], key=lambda x:float(x.get('impacto_anual') or 0), reverse=True)
    slide('Plan de implementación', [f"{p.get('codigo', '')} · {format_value(p.get('responsable'))} · {format_value(p.get('plazo'))} · impacto {format_value(p.get('impacto_anual'))}" for p in ordered])
    deck.save(str(destino))
    return Path(destino)


def main():
    parser = argparse.ArgumentParser(description='Genera PPTX de desarrollo desde un contrato JSON')
    parser.add_argument('resultado', type=Path); parser.add_argument('salida', type=Path)
    args = parser.parse_args()
    generar(json.loads(args.resultado.read_text(encoding='utf-8')), args.salida)

if __name__ == '__main__': main()
