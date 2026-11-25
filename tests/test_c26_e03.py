from pathlib import Path

def test_no_se_desaturan_graficos():
    text = (Path(__file__).resolve().parents[1]/'src/reyna_local/web/index.html').read_text()
    assert 'filter:grayscale(1)' not in text
    for color in ('#116b61','#47988b','#82bdb1','#d0a35c','#dc7650','#845a78'):
        assert color in text
