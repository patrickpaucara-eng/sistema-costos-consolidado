"""Tareas 1.4 (banda calibrada por horizonte) y 1.5 (el sello cubre el resultado)."""
import copy, json, pathlib
from reyna_local import analisis as A
from reyna_local.calculo_local import huella_resultado, verificar_sello

RAIZ = pathlib.Path(__file__).resolve().parents[1]
PUB = lambda p: json.loads((RAIZ / f"datos/resultados/frenosa_{p}_REAL.json").read_text(encoding="utf-8"))


def _hist(r): return [(x["periodo"], x["ventas"], x["costo_total"]) for x in r["serie"] if x["tipo"] in ("HISTORICO", "ACTUAL")]


def test_banda_nunca_de_ancho_cero_y_declara_lo_no_estimable():
    filas, info = A.proyectar(_hist(PUB("2010-07")))                  # 7 meses de historia
    est = [x for x in filas if x["tipo"] == "PROYECTADO_EST"]
    assert est and all(x["p95"] - x["p05"] > 0 for x in est)
    assert len(est) + len(info["banda_no_estimable"]) == 6 and info["banda_no_estimable"]


def test_banda_contiene_al_determinístico_y_no_se_angosta():
    filas, info = A.proyectar(_hist(PUB("2010-12")))
    est = [x for x in filas if x["tipo"] == "PROYECTADO_EST"]
    assert not info["banda_no_estimable"] and len(est) == 6
    assert all(x["p05"] < x["p50"] == x["margen"] < x["p95"] for x in est)
    assert all(b["p05"] <= a["p05"] and b["p95"] >= a["p95"] for a, b in zip(est, est[1:]))


def test_banda_cubre_lo_ocurrido_en_la_historia():
    """Prueba hacia atrás a 1 mes: con la historia hasta cada mes, el margen real del mes siguiente cae dentro de la banda
    al menos la mitad de las veces. Con 3 a 5 errores por horizonte el 90 % nominal no es alcanzable; en Frenosa cubre 3 de 5
    (el que falla por poco es setiembre; noviembre es un quiebre: −111 mil tras +217 mil). Antes (errores centrados) cubría 0 de 5."""
    h = _hist(PUB("2010-12")); dentro = total = 0
    for k in range(7, len(h)):
        filas, _ = A.proyectar(h[:k]); est = [x for x in filas if x["tipo"] == "PROYECTADO_EST"]
        if not est: continue
        real = h[k][1] - h[k][2]; total += 1; dentro += est[0]["p05"] <= real <= est[0]["p95"]
    assert total >= 3 and dentro / total >= 0.5


def test_sello_detecta_una_cifra_cambiada():
    r = PUB("2010-07")
    assert r["sello"]["huella_resultado"] == huella_resultado(r)
    malo = copy.deepcopy(r); malo["objetos"][0]["costo_total"] += 0.01
    assert verificar_sello(RAIZ / "datos", malo)["estado"] == "RESULTADO_ALTERADO"


# ---------- regresiones OT-R02 ----------
def test_r02_serie_constante_no_estimable():
    h = [(f"2010-{m:02d}", 1000.0, 600.0) for m in range(1, 13)]
    filas, info = A.proyectar(h)
    assert not [x for x in filas if x["tipo"] == "PROYECTADO_EST"] and len(info["banda_no_estimable"]) == 6


def test_r02_sello_cubre_metadatos_y_no_se_evade():
    r = PUB("2010-07")
    m = copy.deepcopy(r); m["sello"]["semilla"] = 1
    assert verificar_sello(RAIZ / "datos", m)["estado"] == "RESULTADO_ALTERADO"
    m = copy.deepcopy(r); del m["sello"]["huella_resultado"]; m["kpi"]["ventas"] = 1
    assert verificar_sello(RAIZ / "datos", m)["estado"] == "SIN_HUELLA_RESULTADO"


def test_pronostico_puntual_ingenuo_con_poca_historia_y_modelo_con_suficiente():
    from reyna_local import analisis as A
    assert A.pronostico_puntual([5, 7, 9], 3) == ([9.0, 9.0, 9.0], "INGENUO")
    v, m = A.pronostico_puntual([float(10 + i) for i in range(12)], 2)
    assert len(v) == 2 and m and v[0] > 15
