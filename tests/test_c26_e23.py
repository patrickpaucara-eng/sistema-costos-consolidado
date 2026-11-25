from pathlib import Path

def test_no_hay_menu_de_simulacion():
    text = (Path(__file__).resolve().parents[1]/'src/reyna_local/web/index.html').read_text()
    nav = text.split('<nav aria-label="Secciones del sistema">',1)[1].split('</nav>',1)[0]
    assert 'href="#simulacion"' not in nav
    assert 'href="#proyeccion"' in nav
