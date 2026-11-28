"""C34-5: pedido guiado y aceptación completa en Chromium."""
from __future__ import annotations

import json
import shutil
import threading
from pathlib import Path
from urllib.request import Request, urlopen

from openpyxl import load_workbook
import pytest

from reyna_local.__main__ import ReynaServer
from reyna_local.recetas_pedido import aprender_familia, guardar_familias_en_libro, intervalo_prediccion
from nav_helpers import ir_a_pestana


ROOT = Path(__file__).resolve().parents[1]


def _historicas():
    observaciones = []
    for kg, horas in ((1000, 61), (1200, 69), (1500, 86), (1800, 99)):
        observaciones.append({"sintesis": "REAL", "familia": "TOLVA", "parametros": {"kg": kg},
                              "inductores": {"FO-1": horas}})
    return observaciones


def _crear_espacio(base, libro):
    request = Request(base + "/api/workspaces", data=json.dumps({
        "name": "E2E Pedido C34-5", "workbook_path": str(libro)
    }).encode(), headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def test_intervalo_pedido_real_y_parametro_requerido():
    definiciones = [{"codigo": "kg", "nombre": "Peso", "unidad": "kg", "minimo": 500, "maximo": 2000}]
    modelo = aprender_familia("TOLVA", definiciones, _historicas())
    intervalo = intervalo_prediccion(modelo, "FO-1", {"kg": 1300})
    assert intervalo["estimable"]
    assert intervalo["p05"] < intervalo["media"] < intervalo["p95"]
    with pytest.raises(ValueError, match="Falta parámetro obligatorio: Peso"):
        intervalo_prediccion(modelo, "FO-1", {})


def test_reemplazar_receta_sin_historia_borra_intervalos_antiguos():
    from openpyxl import Workbook
    from reyna_local.recetas_pedido import leer_familias_de_libro

    workbook = Workbook()
    familia_con_estadistica = aprender_familia(
        "TOLVA",
        [{"codigo": "kg", "nombre": "Peso", "unidad": "kg", "minimo": 500, "maximo": 2000}],
        _historicas(),
    )
    guardar_familias_en_libro(workbook, {"TOLVA": familia_con_estadistica})
    sin_historia = {"familia": "TOLVA", "parametros": familia_con_estadistica["parametros"],
                    "inductores": {"FO-1": {"base": 10, "coeficientes": {"kg": 0.05}, "n": 2}}}
    guardar_familias_en_libro(workbook, {"TOLVA": sin_historia})
    releida = leer_familias_de_libro(workbook)
    assert "estadistica" not in releida["TOLVA"]["inductores"]["FO-1"]
    workbook.close()


def test_pedido_guiado_en_chromium_hasta_abrir_ot(tmp_path):
    sync = pytest.importorskip("playwright.sync_api")
    libro_dir = tmp_path / "libros"
    libro_dir.mkdir()
    libro_path = libro_dir / "frenosa.xlsx"
    shutil.copyfile(ROOT / "casos/libros/frenosa.xlsx", libro_path)
    workbook = load_workbook(libro_path)
    modelos = {"TOLVA": aprender_familia(
        "TOLVA",
        [{"codigo": "kg", "nombre": "Peso", "unidad": "kg", "minimo": 500, "maximo": 2000}],
        _historicas(),
    )}
    guardar_familias_en_libro(workbook, modelos)
    measure = workbook["MEDIDA"]
    # La tarifa de FO-1 del periodo usa una capacidad práctica demostrativa.
    measure.append(("2010-12", "FRE", "AC_PROD", "CAP", "FO-1", 1000))
    workbook.save(libro_path)
    workbook.close()

    server = ReynaServer(tmp_path, 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    browser = None
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        workspace = _crear_espacio(base, libro_path)
        with sync.sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch(args=["--no-sandbox"])
            except Exception:
                browser = playwright.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
            page = browser.new_page()
            page.goto(base + "/")
            ir_a_pestana(page, '#modelo')
            page.locator('#pedido-definir summary').click()
            page.locator('[data-def-capacidad="FO-1"]').wait_for(state="attached")
            page.locator('#pedido-config-dias').fill('12')
            page.locator('#pedido-config-margen').fill('30')
            page.locator('#pedido-config-meses').fill('0')
            page.locator('#pedido-config-intervalo').select_option('3')
            page.locator('#pedido-config-curva').select_option('s')
            page.locator('#pedido-config-lote').fill('1')
            page.locator('#pedido-config-preparacion').fill('100')
            page.locator('#pedido-config-contingencia').fill('5')
            page.locator('#pedido-config-subcontrato').fill('20')
            page.locator('#pedido-config-transporte').fill('10')
            page.locator('#pedido-config-generales').fill('15')
            page.locator('#pedido-config-umbral-monto').fill('1000000')
            page.locator('#pedido-config-umbral-ancho').fill('100000')
            page.locator('[data-def-capacidad="FO-1"]').fill('8')
            page.locator('[data-def-comprometida="FO-1"]').fill('2')
            page.locator('#pedido-config-form button[type=submit]').click()
            ir_a_pestana(page, '#cotizador')
            page.locator("#pedido-familia option[value='TOLVA']").wait_for(state="attached")
            page.locator("#pedido-producto").fill("SW50")
            page.locator("#pedido-cantidad").fill("1")
            page.locator("#pedido-cliente").fill("CLIENTE PRUEBA")
            page.locator("#pedido-condicion-pago").fill("contado")
            page.locator("#pedido-fecha").fill("2010-12-28")
            page.locator("#pedido-contrato").select_option("CERRADO")
            page.locator("#pedido-familia").select_option("TOLVA")
            page.locator('[data-parametro="kg"]').fill("1300")
            page.locator("#pedido-continuar").click()
            page.locator("#pedido-lote-comparar").fill("0.5")
            page.locator("#pedido-precio").fill("10000")
            page.locator("#pedido-calcular").click()
            page.locator("#pedido-paso-aceptar").wait_for(state="visible", timeout=60000)
            texto = page.locator("#pedido-resumen-confirmacion").inner_text()
            assert "Rango P05–P95:" in texto
            assert "Entrega más temprana:" in texto and "días tarde" in texto
            assert "Precio sugerido:" in texto and "mercado:" in texto
            assert "Comparación de tamaños de lote" in page.locator("#pedido-resumen-confirmacion").inner_text()
            page.locator("#pedido-resumen-confirmacion details").first.click()
            texto = page.locator("#pedido-resumen-confirmacion").inner_text()
            for campo in ("Fórmula:", "Supuesto:", "Dato usado:", "Límite:"):
                assert campo in texto
            page.locator("#pedido-resumen-confirmacion summary").filter(has_text="Comparación de tamaños de lote").click()
            assert "diferencia máxima entre alternativas" in page.locator("#pedido-resumen-confirmacion").inner_text().lower()
            assert page.locator("#cot-aceptar-box").evaluate("x => x.open")
            page.locator(f"#ac-espacio option[value='{workspace['id']}']").wait_for(state="attached")
            page.locator("#cot-aceptar button[type=submit]").click()
            page.locator("#ac-estado").get_by_text("OT-FRE-SW50-").wait_for(timeout=60000)
            estado = page.locator("#ac-estado").inner_text()
            assert "OT-FRE-SW50-0001" in estado

            # Comprueba que la ruta atómica dejó una estimación aceptada y su OT.
            response = urlopen(f"http://127.0.0.1:{server.server_port}/api/workspaces", timeout=30)
            spaces = json.load(response)["workspaces"]
            workspace_id = spaces[0]["id"]
            operational_book = tmp_path / workspace_id / "libro.xlsx"
            saved = load_workbook(operational_book, read_only=True, data_only=True)
            estimates = list(saved["ESTIMACION"].values)
            objects = list(saved["OBJETO"].values)
            saved.close()
            assert any(row[7] == "ACEPTADA" and row[8] == "OT-FRE-SW50-0001" for row in estimates[1:])
            assert any(row[0] == "OT-FRE-SW50-0001" and row[2] == "SW50" for row in objects[1:])
            browser.close()
    finally:
        if browser:
            try:
                browser.close()
            except Exception:
                pass
        server.shutdown()
        thread.join()
        server.server_close()
