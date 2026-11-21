"""Etapa 3 · Analítica: reproducible, honesta (fuera de muestra) y coherente con lo publicado."""
import pathlib, sys
import pytest
RAIZ = pathlib.Path(__file__).resolve().parents[1]; sys.path.insert(0, str(RAIZ / "casos/frenosa"))
import generar as G
from reyna_local import analisis as A, contrato, resultados
V = str(RAIZ / "datos/frenosa/Ventas.csv")


@pytest.fixture(scope="module")
def base(tmp_path_factory):
    L, _ = G.generar(str(RAIZ / "casos/plantilla_caso.xlsx"), str(tmp_path_factory.mktemp("a") / "fre.xlsx"))
    return L, resultados.calcular_periodos(L, "FRE")


@pytest.mark.parametrize("s", ["REAL", "CONTABLE", "ESTIMADO"])
def test_tres_sintesis_cumplen_el_contrato(base, s):
    r = resultados.construir(base[0], ventas_csv=V, periodo="2010-12", sintesis=s, _cache=base[1])
    assert contrato.validar(r) == []
    assert sum(1 for x in r["serie"] if x["tipo"] == "PROYECTADO_DET") == 6


def test_proyeccion_reproducible_y_banda_creciente(base):
    a = resultados.construir(base[0], ventas_csv=V, periodo="2010-12", _cache=base[1])
    b = resultados.construir(base[0], ventas_csv=V, periodo="2010-12", _cache=base[1])
    est = [x for x in a["serie"] if x["tipo"] == "PROYECTADO_EST"]
    assert est == [x for x in b["serie"] if x["tipo"] == "PROYECTADO_EST"]          # misma semilla, mismo resultado
    assert all(x["p05"] <= x["p50"] <= x["p95"] for x in est)
    anchos = [x["p95"] - x["p05"] for x in est]
    assert anchos == sorted(anchos)                                                 # la incertidumbre crece con el horizonte


def test_relevancia_pareto(base):
    r = resultados.construir(base[0], ventas_csv=V, periodo="2010-07", _cache=base[1])
    rel = r["relevancia"]
    assert abs(rel[-1]["acumulado"] - 1) < 1e-3 and rel[0]["critico"] and rel[0]["elemento"] == "Material directo"
    assert [x["importe"] for x in rel] == sorted((x["importe"] for x in rel), reverse=True)


def test_escenario_base_es_el_resultado_publicado(base):
    r = resultados.construir(base[0], ventas_csv=V, periodo="2010-07", _cache=base[1])
    esc = {e["nombre"]: e for e in r["escenarios"]}
    assert abs(esc["Base"]["margen"] - r["kpi"]["resultado_antes_impuestos"]) < 0.05
    assert esc["Precio del material +10 %"]["margen"] < esc["Base"]["margen"] < esc["Precio de venta +3 %"]["margen"]


def test_estimado_es_fuera_de_muestra(base):
    """ESTIMADO de un mes usa solo los meses anteriores: alterar el propio mes no cambia la estimación."""
    por, _ = base[1]
    can = {o: 1.0 for p in por for o in por[p]}
    s1 = A.serie_producto(por, can)
    s2 = {k: [(p, ({e: x * 3 for e, x in el.items()} if p == "2010-12" else el), q) for p, el, q in v] for k, v in s1.items()}
    assert A.estimado(s1, "2010-12") == A.estimado(s2, "2010-12")


def test_diagnostico_a_mano(base):
    """Causa raíz: el elemento con mayor variación del costo unitario frente al promedio de 6 meses."""
    por, _ = base[1]
    objs = {o: 1.0 for p in por for o in por[p]}
    import puerto_lectura as P
    can = {r["OBJ_NUM"]: float(r["OBJ_CAN"]) for r in P.leer(base[0], ["OBJETO"])["OBJETO"]}
    s = A.serie_producto(por, can)
    h = {x["referencia"]: x for x in A.diagnostico(s, "2010-12")}
    pts = s["FRE9000"]; dic = pts[-1]; prev = pts[-7:-1]
    cu = sum(dic[1].values()) / dic[2]; ref = sum(sum(x[1].values()) / x[2] for x in prev) / 6
    assert abs(h["FRE9000"]["variacion"] - round((cu - ref) / ref, 4)) < 1e-4


def test_banda_centrada_en_el_deterministico():
    """RA-17: la mediana estocástica acompaña al determinístico (antes se alejaba -132 mil en 6 meses por sesgo de otro modelo)."""
    import json, pathlib
    from reyna_local import analisis as A
    r = json.loads(pathlib.Path("datos/resultados/frenosa_2010-12_REAL.json").read_text(encoding="utf-8"))
    hist = [(x["periodo"], x["ventas"], x["costo_total"]) for x in r["serie"] if x["tipo"] in ("HISTORICO", "ACTUAL")]
    filas, _ = A.proyectar(hist)
    est = [x for x in filas if x["tipo"] == "PROYECTADO_EST"]
    for x in est:
        ancho = x["p95"] - x["p05"]
        assert x["p05"] < x["margen"] < x["p95"] and abs(x["p50"] - x["margen"]) < 0.15 * ancho
