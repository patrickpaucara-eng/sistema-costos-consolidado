from pathlib import Path


def test_grafo_usa_aristas_y_monto_del_contrato():
    s=(Path(__file__).resolve().parents[1]/'src/reyna_local/web/index.html').read_text()
    assert 't.origen===codigo||t.destino===codigo' in s
    assert 'value(t.monto_tramo)' in s
    assert "boton.addEventListener('click'" in s
