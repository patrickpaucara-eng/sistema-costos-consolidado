from pathlib import Path

def test_tornado_diverge_desde_cero():
    text=(Path(__file__).resolve().parents[1]/'src/reyna_local/web/index.html').read_text()
    assert "v<0?50-ancho:50" in text
    assert "aria-label',(i?'Aumento':'Disminución')" in text
