"""OT-C33-2: la demanda limitada deja capacidad al siguiente producto y muestra sobrantes."""
import copy
import json
import threading
from pathlib import Path
from urllib.request import Request, urlopen

import pytest
from nav_helpers import ir_a_pestana

from reyna_local import decidir as D
from reyna_local.__main__ import ReynaServer


ROOT = Path(__file__).resolve().parents[1]


def _caso():
    return {
        "sintesis": "REAL",
        "objetos": [
            {"codigo": "OT-A", "producto": "A", "cantidad": 4},
            {"codigo": "OT-B", "producto": "B", "cantidad": 10},
        ],
        "decidir": {"er_gerencial": {"productos": [
            {"producto": "A", "cantidad": 4, "margen_contribucion": 400},
            {"producto": "B", "cantidad": 10, "margen_contribucion": 600},
        ]}},
        "datos_libro": {
            "ventas": [{"producto": "A", "cantidad": 4}, {"producto": "B", "cantidad": 10}],
            "medidas": [
                {"inductor": "HM", "nivel": "CAP", "destino": "MAQUINA", "destino_nombre": "Máquina", "cantidad": 100},
                {"inductor": "HM", "nivel": "OBJ", "destino": "OT-A", "cantidad": 40},
                {"inductor": "HM", "nivel": "OBJ", "destino": "OT-B", "cantidad": 100},
            ],
        },
        "trazas": [{"criterio": "HM", "origen": "MAQUINA", "destino": "FO-1"}],
    }


def _resultado_para_ui():
    result = json.loads((ROOT / "datos/resultados/frenosa_2010-07_REAL.json").read_text(encoding="utf-8"))
    base = _caso()
    result["periodo_actual"] = "2010-12"
    result["objetos"] = [dict(result["objetos"][0], codigo="OT-A", producto="A", cantidad=4),
                         dict(result["objetos"][1], codigo="OT-B", producto="B", cantidad=10)]
    result["decidir"]["er_gerencial"]["productos"] = base["decidir"]["er_gerencial"]["productos"]
    result["decidir"]["er_gerencial"]["total"] = {"ventas": 1000, "cv": 0, "margen_contribucion": 1000}
    result["datos_libro"]["ventas"] = base["datos_libro"]["ventas"]
    result["datos_libro"]["medidas"] = base["datos_libro"]["medidas"]
    traces = []
    for object_code in ("OT-A", "OT-B"):
        trace = copy.deepcopy(result["trazas"][0])
        trace.update(objeto=object_code, elemento="PD", origen="MAQUINA", destino="FO-1",
                     criterio="HM", raiz=True)
        traces.append(trace)
    result["trazas"] = traces
    return result


@pytest.fixture
def server(tmp_path):
    results = tmp_path / "resultados"
    results.mkdir()
    (results / "frenosa_2010-07_REAL.json").write_text(json.dumps(_caso()), encoding="utf-8")
    (results / "frenosa_2010-12_REAL.json").write_text(json.dumps(_resultado_para_ui()), encoding="utf-8")
    instance = ReynaServer(tmp_path, 0)
    thread = threading.Thread(target=instance.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{instance.server_port}", tmp_path
    instance.shutdown()
    thread.join()
    instance.server_close()


def _post(base, body):
    request = Request(base + "/api/decidir", data=json.dumps(body).encode(),
                      headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def test_caso_manual_tope_de_demanda_pasa_capacidad_al_siguiente_y_muestra_sobrante():
    case = _caso()
    full = D.asignar_recurso(case, "HM", "MAQUINA", {"A": 4, "B": 10})
    assert [(row["producto"], row["unidades_sugeridas"], row["capacidad_usada"])
            for row in full["productos"]] == [("A", 4, 40), ("B", 6, 60)]
    assert (full["capacidad_utilizada"], full["capacidad_restante"]) == (100, 0)

    limited = D.asignar_recurso(case, "HM", "MAQUINA", {"A": 2, "B": 3})
    assert [(row["producto"], row["unidades_sugeridas"], row["capacidad_usada"])
            for row in limited["productos"]] == [("A", 2, 20), ("B", 3, 30)]
    assert (limited["capacidad_utilizada"], limited["capacidad_restante"]) == (50, 50)


def test_api_respeta_tope_y_retorna_capacidad_no_usada(server):
    base, _ = server
    result = _post(base, {"empresa": "frenosa", "periodo": "2010-07", "caso": "recurso_escaso",
                          "criterio": "HM", "destino": "MAQUINA", "demanda_maxima": {"A": 2, "B": 3}})
    assert [(row["producto"], row["unidades_sugeridas"]) for row in result["productos"]] == [("A", 2), ("B", 3)]
    assert (result["capacidad_utilizada"], result["capacidad_restante"]) == (50, 50)


def test_chromium_muestra_capacidad_no_usada_y_caso_a_mano(server):
    sync = pytest.importorskip("playwright.sync_api")
    base, _ = server
    with sync.sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(args=["--no-sandbox"])
        except Exception:
            browser = playwright.chromium.launch(executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        try:
            page = browser.new_page()
            page.goto(base)
            sync.expect(page.locator("#dc-recurso option")).to_have_count(1, timeout=30000)
            ir_a_pestana(page, '#decidir')
            page.locator("#dc-recurso").select_option(value=json.dumps(["HM", "MAQUINA"], separators=(",", ":")))
            page.locator('#dc-demanda-maxima input[data-producto="A"]').fill("4")
            page.locator('#dc-demanda-maxima input[data-producto="B"]').fill("10")
            page.locator("#dc-asignar").click()
            rows = page.locator("#dc-escasez-resultado tbody tr")
            sync.expect(rows).to_have_count(2, timeout=30000)
            sync.expect(page.locator("#dc-escasez-estado")).to_contain_text("capacidad no usada: 0")
            first, second = rows.all_text_contents()
            assert "A" in first and "4" in first and "40" in first
            assert "B" in second and "6" in second and "60" in second

            page.locator('#dc-demanda-maxima input[data-producto="A"]').fill("2")
            page.locator('#dc-demanda-maxima input[data-producto="B"]').fill("3")
            page.locator("#dc-asignar").click()
            sync.expect(page.locator("#dc-escasez-estado")).to_contain_text("capacidad no usada: 50")
        finally:
            browser.close()
