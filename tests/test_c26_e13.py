from pathlib import Path

def test_sensibilidad_viene_de_api():
    text=(Path(__file__).resolve().parents[1]/'src/reyna_local/web/index.html').read_text()
    assert "fetch('/api/proyeccion?'" in text
    assert 'data.sensibilidad||[]' in text
    assert 'sensibilidad-tornado' in text
