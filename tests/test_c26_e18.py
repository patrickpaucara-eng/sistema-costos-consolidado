from pathlib import Path

def test_calidad_y_gobierno_usan_contrato():
    text=(Path(__file__).resolve().parents[1]/'src/reyna_local/web/index.html').read_text()
    assert 'r.estrategico||{}' in text
    assert 'estrategico-coq' in text and 'estrategico-faltantes' in text
