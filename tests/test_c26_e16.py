from pathlib import Path

def test_aprendizaje_consulta_y_decide_solo_pendientes():
    text=(Path(__file__).resolve().parents[1]/'src/reyna_local/web/index.html').read_text()
    assert "fetch('/api/aprendizaje?'" in text
    assert "fetch('/api/aprendizaje/decidir'" in text
    assert "x.estado==='PENDIENTE'" in text
