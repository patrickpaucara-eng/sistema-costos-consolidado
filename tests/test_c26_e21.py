from pathlib import Path

def test_tramo_identifica_parte_y_limite_del_contrato():
    text=(Path(__file__).resolve().parents[1]/'src/reyna_local/web/index.html').read_text()
    assert 'Parte de esta orden S/' in text
    assert 'monto total del tramo no está disponible' in text
    assert 'tasa CIF en P4C' in text
