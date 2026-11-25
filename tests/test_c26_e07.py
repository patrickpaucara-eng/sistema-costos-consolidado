from pathlib import Path

def test_ordenes_indica_limite_de_detalle_personal():
    text=(Path(__file__).resolve().parents[1]/'src/reyna_local/web/index.html').read_text()
    assert 'registra cada operario como recurso' in text
    assert 'no hay detalle individual' in text
