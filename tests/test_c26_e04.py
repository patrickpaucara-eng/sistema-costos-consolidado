from pathlib import Path

def test_planta_lee_trazas_y_permite_explorarlas():
    text=(Path(__file__).resolve().parents[1]/'src/reyna_local/web/index.html').read_text()
    assert "const trazas=r.trazas||[]" in text
    assert all("['"+n+"'" in text for n in ('Recursos','Centros','Actividades','Órdenes'))
    assert "table('planta-detalle',filas" in text
