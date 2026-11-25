from pathlib import Path

def test_rechazos_se_muestran_segun_contrato():
    text=(Path(__file__).resolve().parents[1]/'src/reyna_local/web/index.html').read_text()
    assert "table('inv-rechazos',r.rechazos||[]" in text
    assert "['importe','Pérdida S/']" in text
