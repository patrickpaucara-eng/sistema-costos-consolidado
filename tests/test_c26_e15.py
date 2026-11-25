from pathlib import Path

def test_cotizador_usa_api_y_muestra_avisos():
    text=(Path(__file__).resolve().parents[1]/'src/reyna_local/web/index.html').read_text()
    assert 'id="cotizar-form"' in text
    assert "fetch('/api/cotizar'" in text
    assert "data.avisos||[]" in text
    assert "y.etapa==='P4C'" in text
