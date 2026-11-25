"""C24: las hojas adicionales transcriben el contrato sin recalcular cifras."""
import json
from pathlib import Path
import pytest
from openpyxl import load_workbook
from reyna_local.exportar import exportar, sistema_html

ROOT = Path(__file__).resolve().parents[1]
BLOQUES = {
    'resultados': [('Rechazos', 'rechazos')],
    'analitica': [('Costeo variable', 'costeo_variable'), ('Estratégico COQ', 'estrategico.coq'),
                  ('Gobierno del dato', 'estrategico.gobierno_dato'), ('Aprendizaje', 'aprendizaje')],
    'proyeccion': [('Proyección granular', 'proyeccion_granular'), ('Sensibilidad', 'sensibilidad'),
                   ('Aprendizaje', 'aprendizaje')],
}

def aplanar(valor, ruta):
    if isinstance(valor, dict):
        return [item for k, v in valor.items() for item in aplanar(v, ruta + '.' + str(k))]
    if isinstance(valor, list):
        return [item for i, v in enumerate(valor) for item in aplanar(v, ruta + '[' + str(i) + ']')]
    return [] if valor is None else [(ruta, valor)]


@pytest.mark.parametrize('archivo', ['frenosa_2010-12_REAL.json', 'segundo_2025-07_REAL.json'])
@pytest.mark.parametrize('tipo', BLOQUES)
def test_bloques_iguales_al_json(tmp_path, archivo, tipo):
    r = json.loads((ROOT/'datos/resultados'/archivo).read_text(encoding='utf-8'))
    wb = load_workbook(exportar(r, tipo, tmp_path), data_only=False)
    for nombre, ruta in BLOQUES[tipo]:
        v = r
        for parte in ruta.split('.'):
            v = v.get(parte) if isinstance(v, dict) else None
        esperado = aplanar(v, ruta)
        observado = list(wb[nombre].values)[1:]
        if not esperado:
            assert observado == [('Sin datos disponibles', None)]
        else:
            # También se comprueba el escape de texto peligroso para Excel.
            esperado = [(k, "'" + x if isinstance(x, str) and x.startswith(('=', '+', '-', '@')) else x)
                        for k, x in esperado]
            for (campo, valor), (campo_e, valor_e) in zip(observado, esperado):
                assert campo == campo_e
                assert float(str(valor).lstrip("'")) == valor_e if isinstance(valor_e, float) else valor == valor_e
            assert len(observado) == len(esperado)
    wb.close()


def test_html_abre_sin_red(tmp_path):
    sync = pytest.importorskip('playwright.sync_api')
    r = json.loads((ROOT/'datos/resultados/frenosa_2010-12_REAL.json').read_text(encoding='utf-8'))
    lib = {'id':'frenosa', 'nombre':'Frenosa', 'periodos':['2010-12']}
    pagina = sistema_html({'frenosa_2010-12_REAL': r}, lib, tmp_path/'offline.html')
    with sync.sync_playwright() as p:
        try: browser = p.chromium.launch(args=['--no-sandbox'])
        except Exception: browser = p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        contexto = browser.new_context(offline=True)
        page = contexto.new_page(); page.set_content(pagina.read_text(encoding="utf-8"), wait_until="load")
        page.locator('#result-periodo').fill('2010-12')
        page.locator('#result-cargar').click()
        sync.expect(page.locator('#result-status')).to_contain_text('actualizados', timeout=15000)
        assert page.locator('#result-kpis').inner_text()
        browser.close()
