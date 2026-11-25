from pathlib import Path

def test_periodos_explica_alcance_y_aviso():
    text=(Path(__file__).resolve().parents[1]/'src/reyna_local/web/index.html').read_text()
    assert 'día y quincena muestran solo hechos' in text
    assert 'bucket.nota' in text
