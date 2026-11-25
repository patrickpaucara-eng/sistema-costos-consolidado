import json
from pathlib import Path
from importlib.util import module_from_spec, spec_from_file_location
from pptx import Presentation

ROOT = Path(__file__).resolve().parents[1]
spec = spec_from_file_location('presentacion_dev', ROOT / 'tools/generar_presentacion.py')
module = module_from_spec(spec)
spec.loader.exec_module(module)


def test_ocho_diapositivas_y_kpi_del_contrato(tmp_path):
    data = json.loads((ROOT / 'datos/resultados/frenosa_2010-12_REAL.json').read_text())
    path = module.generar(data, tmp_path / 'informe.pptx')
    slides = Presentation(path).slides
    assert len(slides) == 8
    texto = '\n'.join(shape.text for slide in slides for shape in slide.shapes if shape.has_text_frame)
    assert f"{data['kpi']['ventas']:,.2f}" in texto
    assert f"{data['kpi']['costo_total']:,.2f}" in texto
    assert data['empresa']['nombre'] in texto
