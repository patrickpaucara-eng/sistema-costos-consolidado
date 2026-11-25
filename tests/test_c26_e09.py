from pathlib import Path

def test_cada_propuesta_explica_sus_datos():
    text=(Path(__file__).resolve().parents[1]/'src/reyna_local/web/index.html').read_text()
    assert 'Cómo se calculó' in text
    assert all(x in text for x in ('x.cu_base','x.cu_objetivo','x.cantidad_mes'))
    assert 'El contrato no aporta el desglose' in text
