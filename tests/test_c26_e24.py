from pathlib import Path

def test_agrupa_por_responsable_y_descarga_local():
    text=(Path(__file__).resolve().parents[1]/'src/reyna_local/web/index.html').read_text()
    assert "p.responsable||'Sin responsable'" in text
    assert 'URL.createObjectURL(blob)' in text
    assert 'propuestas-por-decisor' in text
