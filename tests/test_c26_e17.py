from pathlib import Path

def test_variable_muestra_campos_del_contrato():
    text=(Path(__file__).resolve().parents[1]/'src/reyna_local/web/index.html').read_text()
    assert 'r.costeo_variable||{}' in text
    assert all(x in text for x in ('punto_equilibrio_ventas','margen_contribucion','variable-no-controlables'))
