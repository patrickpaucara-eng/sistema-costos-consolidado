"""C37-5: Familias lleva al Pedido con la receta configurada y muestra el mismo costo."""
import shutil
import threading
from pathlib import Path

import pytest
from openpyxl import load_workbook
from nav_helpers import ir_a_pestana
from reyna_local.__main__ import ReynaServer
from reyna_local.recetas_pedido import aprender_familia, guardar_familias_en_libro


ROOT = Path(__file__).resolve().parents[1]


def test_pedido_y_familias_muestran_mismo_costo_con_receta_del_libro(tmp_path):
    sync = pytest.importorskip('playwright.sync_api')
    folder = tmp_path / 'libros'
    folder.mkdir()
    path = folder / 'frenosa.xlsx'
    shutil.copyfile(ROOT / 'casos/libros/frenosa.xlsx', path)
    wb = load_workbook(path)
    historia = [{'sintesis': 'REAL', 'familia': 'TOLVA', 'parametros': {'kg': kg},
                 'inductores': {'FO-1': horas}}
                for kg, horas in [(1000, 61), (1200, 69), (1500, 86), (1800, 99)]]
    modelo = aprender_familia('TOLVA', [{'codigo': 'kg', 'nombre': 'Peso', 'unidad': 'kg',
                                         'minimo': 500, 'maximo': 2000}], historia)
    guardar_familias_en_libro(wb, {'TOLVA': modelo})
    wb.save(path)
    wb.close()
    server = ReynaServer(tmp_path, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync.sync_playwright() as p:
            try:
                browser = p.chromium.launch(args=['--no-sandbox'])
            except Exception:
                browser = p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
            try:
                page = browser.new_page()
                page.goto(f'http://127.0.0.1:{server.server_port}/')
                ir_a_pestana(page, '#familias')
                page.locator('#fam-familia option[value="TOLVA"]').wait_for(state='attached', timeout=30000)
                assert page.locator('#fam-familia option[value="TOLVA"]').count() == 1
                page.locator('#fam-familia').select_option('TOLVA')
                page.locator('#fam-historia').fill('{"FO-1": [10, 11, 9, 10, 10]}')
                page.locator('#fam-analizar').click()
                sync.expect(page.locator('#fam-estado')).to_contain_text('diagnóstico')
                page.locator('#fam-usar').click()
                sync.expect(page.locator('#pedido-familia')).to_have_value('TOLVA')
                page.locator('#pedido-producto').fill('SW50')
                page.locator('#pedido-cantidad').fill('1')
                page.locator('#pedido-cliente').fill('CLIENTE')
                page.locator('#pedido-fecha').fill('2010-12-28')
                page.locator('#pedido-condicion-pago').fill('contado')
                page.locator('[data-parametro="kg"]').fill('1300')
                page.locator('#pedido-continuar').click()
                page.locator('#pedido-precio').fill('10000')
                with page.expect_response(lambda response: response.url.endswith('/api/pedido/cotizar') and response.request.method == 'POST', timeout=60000) as response_info:
                    page.locator('#pedido-calcular').click()
                response = response_info.value
                assert response.ok
                costo = response.json()['costo_esperado']
                assert costo > 0
                formatted = page.evaluate('(v) => new Intl.NumberFormat("es-PE", {maximumFractionDigits: 2}).format(v)', costo)
                sync.expect(page.locator('#pedido-resultado')).to_contain_text(f'Costo esperado: S/ {formatted}')
                ir_a_pestana(page, '#familias')
                sync.expect(page.locator('#fam-ultima')).to_contain_text(f'costo esperado S/ {formatted}')
            finally:
                browser.close()
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
