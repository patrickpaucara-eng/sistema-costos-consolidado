"""C35-3: roles de parámetros y flujo de pedido de tres pasos."""
from __future__ import annotations

import json
import shutil
import threading
from pathlib import Path
from urllib.request import Request, urlopen

from openpyxl import load_workbook
import pytest

from reyna_local.__main__ import ReynaServer
from reyna_local.recetas_pedido import (
    aprender_familia,
    guardar_familias_en_libro,
    leer_familias_de_libro,
    resolver_parametros,
)
from nav_helpers import ir_a_pestana


ROOT = Path(__file__).resolve().parents[1]


def _modelo_roles():
    definiciones = [
        {"codigo": "kg", "nombre": "Peso", "unidad": "kg", "minimo": 1, "maximo": 100,
         "quien_sabe": "cliente"},
        {"codigo": "m2", "nombre": "Área", "unidad": "m²", "minimo": 1, "maximo": 200,
         "quien_sabe": "derivado"},
        {"codigo": "densidad", "nombre": "Densidad", "unidad": "kg/m³", "minimo": 1, "maximo": 200,
         "quien_sabe": "tecnico"},
    ]
    receta = lambda base, coef: {"base": base, "coeficientes": {"kg": coef}, "n": 8}
    return {"familia": "TOLVA", "parametros": {p["codigo"]: p for p in definiciones},
            "inductores": {"HORAS": {"base": 1, "coeficientes": {"kg": .1, "m2": .2, "densidad": .01}, "n": 8}},
            "derivaciones": {"m2": receta(2, 2), "densidad": receta(4, 1.5)}}


def _historia():
    filas = []
    for kg, m2, densidad, horas in (
        (1000, 50, 10, 61), (1200, 62, 8, 69), (1400, 48, 12, 86),
        (1600, 75, 9, 99), (1800, 55, 14, 104), (2000, 80, 11, 117),
    ):
        filas.append({"sintesis": "REAL", "familia": "TOLVA",
                      "parametros": {"kg": kg, "m2": m2, "densidad": densidad},
                      "inductores": {"FO-1": horas}})
    return filas


def _crear_espacio(base, libro):
    request = Request(base + "/api/workspaces", data=json.dumps({
        "name": "E2E Pedido C35-3", "workbook_path": str(libro)
    }).encode(), headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def test_deriva_sin_pedir_confirmacion_y_pide_si_no_hay_receta():
    modelo = _modelo_roles()
    resuelto = resolver_parametros(modelo, {"kg": 10})
    assert resuelto["parametros"] == {"kg": 10.0, "m2": 22.0, "densidad": 19.0}
    assert resuelto["origen"] == {"kg": "cliente", "m2": "derivado", "densidad": "derivado"}
    assert resuelto["faltantes"] == []

    sin_historia = {**modelo, "derivaciones": {"m2": modelo["derivaciones"]["m2"], "densidad": None}}
    pendiente = resolver_parametros(sin_historia, {"kg": 10})
    assert "densidad" not in pendiente["parametros"]
    assert [fila["codigo"] for fila in pendiente["faltantes"]] == ["densidad"]
    assert "confirma el dato técnico" in pendiente["faltantes"][0]["motivo"]


def test_derivacion_fuera_de_rango_se_pide_como_confirmacion():
    modelo = _modelo_roles()
    modelo["derivaciones"]["m2"] = {"base": 250, "coeficientes": {"kg": 1}, "n": 8}
    resultado = resolver_parametros(modelo, {"kg": 10})
    assert "m2" not in resultado["parametros"]
    assert any(x["codigo"] == "m2" for x in resultado["faltantes"])


def test_roles_y_derivaciones_se_conservan_en_libro_excel(tmp_path):
    from openpyxl import Workbook

    modelo = _modelo_roles()
    libro = Workbook()
    guardar_familias_en_libro(libro, {"TOLVA": modelo})
    ruta = tmp_path / "familia.xlsx"
    libro.save(ruta)
    libro.close()
    guardado = load_workbook(ruta, read_only=True, data_only=True)
    try:
        leido = leer_familias_de_libro(guardado)["TOLVA"]
    finally:
        guardado.close()
    assert leido["parametros"]["m2"]["quien_sabe"] == "derivado"
    assert leido["parametros"]["densidad"]["quien_sabe"] == "tecnico"
    assert leido["derivaciones"]["densidad"]["base"] == 4
    assert resolver_parametros(leido, {"kg": 10})["faltantes"] == []


def test_aprende_derivaciones_solo_con_historia_real():
    definiciones = [
        {"codigo": "kg", "nombre": "Peso", "unidad": "kg", "minimo": 1, "maximo": 3000,
         "quien_sabe": "cliente"},
        {"codigo": "m2", "nombre": "Área", "unidad": "m²", "minimo": 1, "maximo": 100,
         "quien_sabe": "derivado"},
        {"codigo": "densidad", "nombre": "Densidad", "unidad": "kg/m³", "minimo": 1, "maximo": 100,
         "quien_sabe": "tecnico"},
    ]
    modelo = aprender_familia("TOLVA", definiciones, _historia())
    assert modelo["derivaciones"]["m2"] is not None
    assert modelo["derivaciones"]["densidad"] is not None
    respuesta = resolver_parametros(modelo, {"kg": 1500})
    assert set(respuesta["parametros"]) == {"kg", "m2", "densidad"}
    assert respuesta["faltantes"] == []


def test_pedido_chromium_hasta_aceptar_ot_con_seis_campos(tmp_path):
    sync = pytest.importorskip("playwright.sync_api")
    libros = tmp_path / "libros"
    libros.mkdir()
    libro_path = libros / "frenosa.xlsx"
    shutil.copyfile(ROOT / "casos/libros/frenosa.xlsx", libro_path)
    workbook = load_workbook(libro_path)
    modelo = aprender_familia(
        "TOLVA",
        [
            {"codigo": "kg", "nombre": "Peso", "unidad": "kg", "minimo": 500, "maximo": 3000,
             "quien_sabe": "cliente"},
            {"codigo": "m2", "nombre": "Área", "unidad": "m²", "minimo": 1, "maximo": 200,
             "quien_sabe": "derivado"},
            {"codigo": "densidad", "nombre": "Densidad", "unidad": "kg/m³", "minimo": 1, "maximo": 200,
             "quien_sabe": "tecnico"},
        ], _historia())
    # El área se deriva de la historia; densidad queda como dato técnico porque
    # no hay receta suficiente y debe pasar por la confirmación de excepción.
    modelo["derivaciones"]["densidad"] = None
    guardar_familias_en_libro(workbook, {"TOLVA": modelo})
    workbook["MEDIDA"].append(("2010-12", "FRE", "AC_PROD", "CAP", "FO-1", 1000))
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
            page.add_init_script("""localStorage.setItem('reyna-pedido:frenosa:config', JSON.stringify({
              dias:12,margen:30,meses:0,intervalo:3,curva:'s',lote:1,preparacion:0,contingencia:0,
              subcontrato:0,transporte:0,generales:0,umbralMonto:1000000,umbralAncho:100000,
              capacidad:{TOLVA:{'FO-1':1000}},comprometida:{TOLVA:{'FO-1':2}}
            }));""")
            page.goto(base + "/")
            page.locator("#result-empresa option[value='frenosa']").wait_for(state="attached")
            page.locator("#pedido-familia option[value='TOLVA']").wait_for(state="attached")
            ir_a_pestana(page, "#cotizador")
            page.locator("#nav-destinos").screenshot(path=str(tmp_path / "menu_c35_3.png"))
            page.locator("#pedido-familia").select_option("TOLVA")
            page.locator("#pedido-producto").fill("SW50")
            page.locator("#pedido-cantidad").fill("1")
            page.locator("#pedido-cliente").fill("CLIENTE PRUEBA")
            page.locator("#pedido-fecha").fill("2010-12-28")
            page.locator("#pedido-contrato").select_option("CERRADO")
            page.locator("#pedido-condicion-pago").fill("30 días")
            page.locator('[data-parametro="kg"]').fill("1300")
            assert page.locator("#pedido-paso-cliente > .fields:not(#pedido-parametros) > fieldset, #pedido-paso-cliente > .fields:not(#pedido-parametros) > label").count() == 6
            assert page.locator("#pedido-falta-confirmar input").count() == 0
            page.locator("#pedido-continuar").click()
            page.locator("#pedido-precio").fill("10000")
            page.locator("#pedido-calcular").click()
            page.get_by_text("Revisa los faltantes o guarda la cotización como preliminar.").wait_for(timeout=60000)
            assert "Cotización preliminar" in page.locator("#pedido-resultado").inner_text()
            campo_tecnico = page.locator('[data-parametro-tecnico="densidad"]')
            assert campo_tecnico.is_visible()
            campo_tecnico.fill("10")
            page.locator("#pedido-calcular").click()
            page.locator("#pedido-paso-aceptar").wait_for(state="visible", timeout=60000)
            resultado = page.locator("#pedido-resumen-confirmacion").inner_text()
            assert "Rango P05–P95:" in resultado
            assert "Precio sugerido:" in resultado and "mercado:" in resultado
            assert "Suficiencia de datos:" in resultado
            assert "Fundamento en 4 líneas" in resultado
            assert page.locator("#pedido-parametros-tecnicos input").count() == 0
            assert page.locator("#pedido-paso-aceptar").is_visible()
            page.screenshot(path=str(tmp_path / "pedido_c35_3.png"), full_page=True)
            page.locator(f"#ac-espacio option[value='{workspace['id']}']").wait_for(state="attached")
            page.locator("#cot-aceptar button[type=submit]").click()
            page.locator("#ac-estado").get_by_text("OT-FRE-SW50-0001").wait_for(timeout=60000)
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
