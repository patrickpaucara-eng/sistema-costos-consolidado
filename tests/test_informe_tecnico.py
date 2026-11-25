import json
from pathlib import Path
from docx import Document
from reyna_local.exportar import exportar

ROOT = Path(__file__).resolve().parents[1]


def test_informe_frenosa_contrato_y_limitaciones(tmp_path):
    r = json.loads((ROOT / 'datos/resultados/frenosa_2010-12_REAL.json').read_text())
    doc = Document(exportar(r, 'informe', tmp_path))
    text = '\n'.join(p.text for p in doc.paragraphs) + '\n' + '\n'.join(c.text for t in doc.tables for row in t.rows for c in row.cells)
    for heading in ('1. Resumen ejecutivo', '2. Análisis', '3. Conclusiones', '4. Propuestas', '5. Plan de implementación', '6. Impacto económico futuro', '6b. Gestión estratégica del costo', '7. Anexos'):
        assert heading in text
    assert f"{r['kpi']['ventas']:,.2f}" in text
    assert f"{r['propuestas'][0]['impacto_anual']:,.2f}" in text
    assert str(r['propuestas'][0]['cu_objetivo']) in text
    assert str(r['kpi']['rentabilidad']) in text
    assert 'Resultado con propuestas: no disponible' in text
    assert 'Controlabilidad no informada' in text


def test_no_muestra_propuestas_si_exclusion_no_se_puede_identificar(tmp_path):
    r = json.loads((ROOT / 'datos/resultados/frenosa_2010-12_REAL.json').read_text())
    r['costeo_variable'] = {'no_controlables': [{'codigo': 'MAT_SW50'}]}
    doc = Document(exportar(r, 'informe', tmp_path))
    text = '\n'.join(p.text for p in doc.paragraphs) + '\n' + '\n'.join(c.text for t in doc.tables for row in t.rows for c in row.cells)
    assert 'Propuestas omitidas' in text
    assert r['propuestas'][0]['descripcion'] not in text
