"""C37-2: la ruta de una OT SERVITEC reproduce cada reparto terminal y muestra matrices."""
import json
import threading
from pathlib import Path

import pytest

from nav_helpers import ir_a_pestana
from reyna_local.__main__ import ReynaServer


ROOT = Path(__file__).resolve().parents[1]
RESULTADO = ROOT / "datos" / "resultados" / "segundo_2025-04_REAL.json"
OT = "OT-SRV-MPR-2025-04"


def test_ruta_servitec_reproduce_importe_terminal_y_matrices_en_chromium(tmp_path):
    sync = pytest.importorskip("playwright.sync_api")
    contrato = json.loads(RESULTADO.read_text(encoding="utf-8"))
    finales = [t for t in contrato["trazas"] if t["objeto"] == OT and t["destino"] == OT]
    assert finales
    for tramo in finales:
        base = tramo["tasa"] * tramo["total_criterio"]
        parte = base * tramo["cantidad_destino"] / tramo["total_criterio"]
        assert abs(parte - tramo["monto_tramo"]) <= 0.01
        assert abs(parte - tramo["monto"]) <= 0.01

    server = ReynaServer(tmp_path, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    browser = None
    try:
        with sync.sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch(args=["--no-sandbox"])
            except Exception:
                browser = playwright.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            page.goto(f"http://127.0.0.1:{server.server_port}/")
            page.locator("#result-status").wait_for()
            page.locator("#result-empresa").select_option("segundo")
            page.locator("#result-periodo").fill("2025-04")
            with page.expect_response(lambda response: "/api/resultados?" in response.url and "empresa=segundo" in response.url and "2025-04" in response.url):
                page.locator("#result-cargar").click()
            sync.expect(page.locator("#result-status")).to_contain_text("actualizados", timeout=30000)

            ir_a_pestana(page, "#ruta")
            page.locator("#ruta-objeto").select_option(OT)
            page.locator("#ruta-elemento").select_option("CIF")
            matrices = page.locator("#ruta-matrices")
            etapas = page.locator("#ruta-pasos > div:has(button)")
            assert etapas.count() > 1
            for i in range(etapas.count()):
                etapa = etapas.nth(i)
                etiqueta = etapa.inner_text()
                etapa.get_by_role("button", name="Ver matrices").click()
                sync.expect(matrices).to_be_visible()
                sync.expect(matrices).to_contain_text("Matriz de configuración · orígenes × destinos")
                sync.expect(matrices).to_contain_text("Matriz de cálculo · monto × medida ÷ total")
                filas = matrices.locator("table").nth(1).locator("tbody tr[data-asignado]").evaluate_all(
                    "rows => rows.map(r => ({base:Number(r.dataset.montoBase), medida:Number(r.dataset.medida), "
                    "total:Number(r.dataset.total), asignado:Number(r.dataset.asignado), destino:r.dataset.destino, "
                    "parte:r.dataset.parteOt == null ? null : Number(r.dataset.parteOt), "
                    "factor:r.dataset.factorRuta == null ? null : Number(r.dataset.factorRuta)}))"
                )
                assert filas
                for fila in filas:
                    calculado = fila["base"] * fila["medida"] / fila["total"]
                    assert abs(calculado - fila["asignado"]) <= 0.01
                    if fila["parte"] is not None:
                        assert abs(fila["asignado"] * fila["factor"] - fila["parte"]) <= 0.01
                    if fila["destino"] == OT:
                        assert fila["parte"] is not None
                        assert abs(calculado - fila["parte"]) <= 0.01
                sync.expect(matrices).to_contain_text("Σ = origen")
                if "P4C Actividades → órdenes" in etiqueta:
                    sync.expect(matrices).to_contain_text("Σ = origen ✔")
                    page.locator("#ruta details summary").click()
                    sync.expect(page.locator("#ruta-tabla")).to_contain_text("Base × medida ÷ total")
                    sync.expect(page.locator("#ruta-tabla")).to_contain_text("Parte de esta OT")
                etapa.get_by_role("button").click()

            page.locator("#ruta-elemento").select_option("PD|OCIO")
            p2 = page.locator("#ruta-pasos > div").filter(has_text="P2 Mano de obra")
            p2.get_by_role("button", name="Ver matrices").click()
            sync.expect(matrices).to_be_visible()
            sync.expect(matrices).to_contain_text("Σ = origen DIFERENCIA")
            sync.expect(matrices).to_contain_text("Diferencia S/ -9,600")
            browser.close()
            browser = None
    finally:
        if browser:
            try:
                browser.close()
            except Exception:
                pass
        server.shutdown()
        thread.join()
        server.server_close()
