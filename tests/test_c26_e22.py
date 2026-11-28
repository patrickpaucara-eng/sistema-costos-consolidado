from pathlib import Path

def test_grupos_desplegables():
    text = (Path(__file__).resolve().parents[1]/'src/reyna_local/web/index.html').read_text()
    nav = text.split('<nav aria-label="Secciones del sistema" id="nav-destinos">', 1)[1].split('</nav>', 1)[0]
    for name in ('Pedido','Operación','Costos','Futuro','Aprendizaje','Configuración'):
        assert f'>{name}</summary>' in nav
    assert nav.count('<details class="nav-menu"') == 6
    assert nav.count('class="nav-menu" data-destino="costos" open') == 1
    assert 'data-destino="configuracion"><summary>Configuración</summary>' in nav
