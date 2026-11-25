from pathlib import Path

def test_grupos_desplegables():
    text = (Path(__file__).resolve().parents[1]/'src/reyna_local/web/index.html').read_text()
    for name in ('Definir','Estimar','Registrar','Entregar','Aprender'):
        assert name+'</summary>' in text
    assert text.count('<details class="nav-menu" open>') == 5
