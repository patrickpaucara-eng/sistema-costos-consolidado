# -*- coding: utf-8 -*-
"""Tarea 1.1 y 1.2 del plan (23-nov): naturaleza del costo (NORMAL, PERDIDA, OCIO) y conservación generalizada.
- Propiedad: con modelos ABC aleatorios (centros, actividades E/A/O, capacidad, criterio propio del ocio), Σ recursos = Σ llegado
  a los objetos, en total y por naturaleza; el ocio generado es exactamente el ocio que llega con su etiqueta.
- Casos a mano: ocio con el mismo inductor y con criterio propio; merma en exceso a la orden que la causó.
- Síntesis: REAL lleva pérdida y ocio en columnas propias del costo de la orden; CONTABLE los deja fuera (NIC 2) y el resultado
  operativo es el mismo en ambas."""
import json, os, random, shutil, sys
from decimal import Decimal as D
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from metodos import reparto_etapas as R  # noqa: E402

TOL = D("1e-9")


def _med(crit, nivel, pares):
    return [dict(PERIODO="X", EMPRESA="E", CRITERIO=crit, NIVEL=nivel, DESTINO=d, CANTIDAD=q) for d, q in pares]


def _base(reglas, medidas, lineas, recursos, centros=(), actividades=(), objetos=("OT1", "OT2")):
    return {"(sin MCD) REGLA_REPARTO": [dict(ETAPA=e, ORIGEN=o, CRITERIO=c, DESDE=19000101) for e, o, c in reglas],
            "(sin MCD) MEDIDA": medidas,
            "(sin MCD) LINEA": [dict(EVENTO=1, NUMERO=i + 1, RECURSO=r, CANTIDAD=q, COSTO_UNITARIO_DOCUMENTO=cu) for i, (r, q, cu) in enumerate(lineas)],
            "EVENTO": [dict(NUMERO=1, PERIODO="X", EMPRESA="E", OBJETO=None, CENTRO=None)],
            "RECURSO": [dict(CODIGO=r, TIPO_RECURSO=t) for r, t in recursos],
            "(sin MCD) TIPO_RECURSO": [dict(CODIGO=t, ELEMENTO_COSTO=t[:-2]) for t in ("IND_T", "PD_T", "SD_T", "MD_T")],
            "CENTRO": [dict(CODIGO=c, EMPRESA="E", TIPO=t) for c, t in centros],
            "(sin MCD) OBJETO": [dict(NUMERO=o, EMPRESA="E", TIPO="OT") for o in objetos],
            "ACTIVIDAD": [dict(CODIGO=a, NIVEL=n) for a, n in actividades],
            "PERIODO": [dict(CODIGO="X", EMPRESA="E", INICIO=20260101)]}


PAR = dict(PER="X", EMP="E")


def _aleatorio(seed):
    rnd = random.Random(seed)
    objs = [f"OT{i}" for i in range(1, rnd.randint(1, 4) + 1)]
    E = [f"E{i}" for i in range(rnd.randint(0, 1))]; A = [f"A{i}" for i in range(rnd.randint(0, 2))]; O = [f"O{i}" for i in range(rnd.randint(1, 3))]
    PRO = [f"PRO{i}" for i in range(rnd.randint(1, 2))]; APR = [f"APR{i}" for i in range(rnd.randint(0, 1))]
    reglas, med, lineas, recursos = [], [], [], []
    w = lambda: rnd.randint(1, 50)
    def regla(et, org, nivel, dests):
        c = f"C_{et}_{org}"; reglas.append((et, org, c)); med.extend(_med(c, nivel, [(d, w()) for d in dests]))
        if rnd.random() < 0.5:                                                    # capacidad mayor que el uso → ocio
            tot = sum(x["CANTIDAD"] for x in med if x["CRITERIO"] == c)
            med.extend(_med(c, "CAP", [(org, tot * rnd.uniform(1.01, 1.6))]))
            if nivel == "OBJ" and rnd.random() < 0.5:                             # criterio propio del ocio
                co = f"OC_{org}"; reglas.append(("OCIO", org, co)); med.extend(_med(co, "OBJ", [(rnd.choice(objs), w())]))
    for i in range(rnd.randint(2, 5)):
        r = f"IND{i}"; recursos.append((r, "IND_T")); lineas.append((r, 1, rnd.randint(100, 5000)))
        if rnd.random() < 0.5: regla("P4A", r, "CEN", rnd.sample(PRO + APR, rnd.randint(1, len(PRO + APR))))
        else: regla("P4A", r, "ACT", rnd.sample(E + A + O, rnd.randint(1, len(E + A + O))))
    recursos += [("MOD", "PD_T"), ("SERV", "SD_T")]; lineas += [("MOD", 1, rnd.randint(500, 3000)), ("SERV", 1, rnd.randint(50, 800))]
    regla("P2", "MOD", "ACT", O); regla("P3", "SERV", "OBJ", objs)
    for c in APR: regla("P4B", c, "CEN", PRO)
    for c in PRO: regla("P4C", c, "OBJ", objs)
    for a in E: regla("P4E", a, "ACT", A + O)
    for a in A: regla("P4E", a, "ACT", O)
    for a in O: regla("P4C", a, "OBJ", objs)
    act = [(a, "E") for a in E] + [(a, "A") for a in A] + [(a, "O") for a in O]
    return _base(reglas, med, lineas, recursos, [(c, "PRO") for c in PRO] + [(c, "APR") for c in APR], act, objs), sum(D(c) for _, _, c in lineas)


@pytest.mark.parametrize("seed", range(200))
def test_conservacion_por_naturaleza_en_modelos_aleatorios(seed):
    h, entra = _aleatorio(seed)
    final, aristas, res = R.correr(h, PAR, {"VALUACION_PROMEDIO": []})
    llega = {n: D(0) for n in R.NATURALEZAS}
    for v in final.values():
        for k, x in v.items():
            assert x >= -TOL
            llega[R.separar(k)[1]] += x
    assert abs(sum(llega.values()) - entra) < TOL                                 # nada se crea ni se pierde
    assert abs(llega["OCIO"] - sum((g["monto"] for g in res["ocio"]), D(0))) < TOL  # el ocio generado llega íntegro
    assert llega["PERDIDA"] == 0


def test_ocio_con_el_mismo_inductor_y_con_criterio_propio():
    """LUZ 1000 → PLANTA. PLANTA reparte por horas OT1 1, OT2 3 (uso 4) con capacidad 5: ocio = 1/5 = 200.
    Normal 800 → 200 / 600; ocio 200 con el mismo inductor → 50 / 150; con criterio propio (todo a OT1) → 200 / 0."""
    reglas = [("P4A", "LUZ", "KWH"), ("P4C", "PLANTA", "HM")]
    med = _med("KWH", "CEN", [("PLANTA", 1)]) + _med("HM", "OBJ", [("OT1", 1), ("OT2", 3)]) + _med("HM", "CAP", [("PLANTA", 5)])
    h = _base(reglas, med, [("LUZ", 1, 1000)], [("LUZ", "IND_T")], [("PLANTA", "PRO")])
    f = R.interno(h, PAR, {"VALUACION_PROMEDIO": []})
    assert f["OT1"]["CIF"] == D(200) and f["OT2"]["CIF"] == D(600)
    assert f["OT1"]["CIF|OCIO"] == D(50) and f["OT2"]["CIF|OCIO"] == D(150)
    h2 = _base(reglas + [("OCIO", "PLANTA", "SOLO_OT1")], med + _med("SOLO_OT1", "OBJ", [("OT1", 1)]), [("LUZ", 1, 1000)], [("LUZ", "IND_T")], [("PLANTA", "PRO")])
    f2 = R.interno(h2, PAR, {"VALUACION_PROMEDIO": []})
    assert f2["OT1"]["CIF|OCIO"] == D(200) and "CIF|OCIO" not in f2["OT2"]
    _, _, res = R.correr(h2, PAR, {"VALUACION_PROMEDIO": []})
    assert res["ocio"][0]["origen"] == "PLANTA" and res["ocio"][0]["monto"] == D(200) and res["ocio"][0]["criterio"] == "SOLO_OT1"


def test_merma_en_exceso_va_a_la_orden_que_la_causo():
    """Salida de 100 kg valorizada en 500 hacia OT1, con 20 kg sobre el estándar: 400 normal y 100 de pérdida, ambos en OT1."""
    h = _base([("P1", "MAT", "CONSUMO")], [], [("MAT", 100, None)], [("MAT", "MD_T")])
    h["EVENTO"] = [dict(NUMERO=1, PERIODO="X", EMPRESA="E", OBJETO="OT1", CENTRO=None)]
    prev = {"VALUACION_PROMEDIO": [("SALIDA", "1-1-ALM", "MONTO", 500)], "EXCESO": {"1-1": 20}}
    final, aristas, _ = R.correr(h, PAR, prev)
    assert final["OT1"]["MD"] == D(400) and final["OT1"]["MD|PERDIDA"] == D(100)
    a = next(x for x in aristas if x["naturaleza"] == "PERDIDA")
    assert a["criterio"] == "CAUSANTE" and a["destino"] == "OT1" and a["medida"] == D(20)
    traza = R.trazar(h, PAR, prev, "OBJETO", "OT1", "MD|PERDIDA")
    assert abs(sum(l["monto_atribuido"] for l in traza if l["raiz"]) - D(100)) < TOL


def test_real_lleva_el_ocio_en_columna_y_contable_lo_deja_fuera(tmp_path):
    """Frenosa diciembre con capacidad de MOD = 125 % de los minutos usados (copia temporal; el libro del caso no se toca)."""
    from openpyxl import load_workbook
    from reyna_local import resultados, contrato
    raiz = Path(__file__).resolve().parents[1]
    p = tmp_path / "f.xlsx"; shutil.copy(raiz / "casos/libros/frenosa.xlsx", p); wb = load_workbook(p); ws = wb["MEDIDA"]; cab = [c.value for c in ws[1]]
    usados = sum(float(r[cab.index("MED_CAN")]) for r in ws.iter_rows(min_row=2, values_only=True)
                 if r[cab.index("MED_PER")] == "2010-12" and r[cab.index("MED_CRIT")] == "MIN_STD")
    fila = dict(MED_PER="2010-12", MED_EMP="FRE", MED_CRIT="MIN_STD", MED_NIVEL="CAP", MED_DEST="MOD", MED_CAN=usados * 1.25)
    ws.append([fila.get(c) for c in cab]); wb.save(p)
    c = resultados.calcular_periodos(str(p), "FRE")
    real = resultados.construir(str(p), periodo="2010-12", sintesis="REAL", _cache=c)
    cont = resultados.construir(str(p), periodo="2010-12", sintesis="CONTABLE", _cache=c)
    assert contrato.validar(real) == [] and contrato.validar(cont) == []
    ocio = sum(x["importe_produccion"] for x in real["capacidad_ociosa"])
    assert ocio > 0 and abs(sum(o["ocio"] for o in real["objetos"]) - ocio) < 0.05
    assert all(o["ocio"] == 0 for o in cont["objetos"])
    gastos = sum(o["admin"] + o["gasto_venta"] + o["financiero"] for o in real["objetos"])
    assert abs(real["kpi"]["costo_total"] - cont["kpi"]["costo_total"] - gastos - ocio) < 0.05
    assert real["kpi"]["margen_operativo"] == cont["kpi"]["margen_operativo"]
    assert all(x["ok"] for x in real["control"] if "Conservación" in x["control"] or "Ocio" in x["control"] or "Ruta" in x["control"])


# ---------- regresiones de la revisión independiente OT-R01 (Codex, 23-nov) ----------
def test_r01_1_saldo_mixto_que_suma_cero_igual_se_reparte():
    """Una actividad recibe MOD 100 y un indirecto −100 (nota de crédito): suma cero, pero cada elemento debe llegar a la orden."""
    reglas = [("P2", "MOD", "HH"), ("P4A", "NC", "DIR"), ("P4C", "X", "UNI")]
    med = _med("HH", "ACT", [("X", 1)]) + _med("DIR", "ACT", [("X", 1)]) + _med("UNI", "OBJ", [("OT1", 1)])
    h = _base(reglas, med, [("MOD", 1, 100), ("NC", 1, -100)], [("MOD", "PD_T"), ("NC", "IND_T")], actividades=[("X", "O")], objetos=("OT1",))
    f = R.interno(h, PAR, {"VALUACION_PROMEDIO": []})
    assert f["OT1"]["PD"] == D(100) and f["OT1"]["CIF"] == D(-100)


def test_r01_3_criterio_de_ocio_respeta_el_escalonado():
    """El criterio propio del ocio de una actividad estratégica no puede entregar a otra estratégica."""
    reglas = [("P4A", "LUZ", "K"), ("P4E", "E1", "BAJA"), ("OCIO", "E1", "PAR"), ("P4C", "O1", "U")]
    med = (_med("K", "ACT", [("E1", 1)]) + _med("BAJA", "ACT", [("O1", 1)]) + _med("BAJA", "CAP", [("E1", 2)])
           + _med("PAR", "ACT", [("E2", 1)]) + _med("U", "OBJ", [("OT1", 1)]))
    h = _base(reglas, med, [("LUZ", 1, 100)], [("LUZ", "IND_T")], actividades=[("E1", "E"), ("E2", "E"), ("O1", "O")], objetos=("OT1",))
    with pytest.raises(R.Rechazo, match="niveles inferiores"):
        R.correr(h, PAR, {"VALUACION_PROMEDIO": []})


def test_r01_4_ocio_de_administracion_no_se_cuenta_dos_veces(tmp_path):
    """Capacidad de administración 125 % del uso: el ocio de administración sigue siendo gasto de administración; el estado de
    resultados no lo resta otra vez y el resultado operativo es el mismo que sin capacidad."""
    from openpyxl import load_workbook
    from reyna_local import resultados
    raiz = Path(__file__).resolve().parents[1]
    p = tmp_path / "f.xlsx"; shutil.copy(raiz / "casos/libros/frenosa.xlsx", p); wb = load_workbook(p); ws = wb["MEDIDA"]; cab = [c.value for c in ws[1]]
    usados = sum(float(r[cab.index("MED_CAN")]) for r in ws.iter_rows(min_row=2, values_only=True)
                 if r[cab.index("MED_PER")] == "2010-07" and r[cab.index("MED_CRIT")] == "KG_PRODUCIDOS" and r[cab.index("MED_NIVEL")] == "OBJ")
    fila = dict(MED_PER="2010-07", MED_EMP="FRE", MED_CRIT="KG_PRODUCIDOS", MED_NIVEL="CAP", MED_DEST="ADM_FRE", MED_CAN=usados * 1.25)
    ws.append([fila.get(c) for c in cab]); wb.save(p)
    c = resultados.calcular_periodos(str(p), "FRE")
    base = json.loads((raiz / "datos/resultados/frenosa_2010-07_CONTABLE.json").read_text(encoding="utf-8"))
    for s in ("CONTABLE", "REAL"):
        r = resultados.construir(str(p), periodo="2010-07", sintesis=s, _cache=c)
        assert sum(x["importe"] for x in r["capacidad_ociosa"]) > 0 and sum(x["importe_produccion"] for x in r["capacidad_ociosa"]) == 0
        assert r["kpi"]["margen_operativo"] == base["kpi"]["margen_operativo"]
        assert not any("capacidad ociosa" in x["concepto"] for x in r["estado_resultados"])
        assert all(o["ocio"] == 0 for o in r["objetos"])


@pytest.mark.parametrize("seed", range(0, 200, 10))
def test_r01_6_ruta_exacta_de_pérdida_y_ocio_en_varias_etapas(seed):
    h, _ = _aleatorio(seed)
    final, _, _ = R.correr(h, PAR, {"VALUACION_PROMEDIO": []})
    for o, v in final.items():
        for k, x in v.items():
            if "|OCIO" in k:
                raiz = sum((l["monto_atribuido"] for l in R.trazar(h, PAR, {"VALUACION_PROMEDIO": []}, "OBJETO", o, k) if l["raiz"]), D(0))
                assert abs(raiz - x) < D("1e-15")


def test_r01_5_costo_total_es_la_suma_exacta_de_sus_columnas():
    """Por construcción costo_total = round(Σ columnas ya redondeadas): la diferencia es solo error de punto flotante, no céntimos."""
    raiz = Path(__file__).resolve().parents[1]
    for f in sorted((raiz / "datos/resultados").glob("frenosa_*.json")):
        for o in json.loads(f.read_text(encoding="utf-8"))["objetos"]:
            suma = sum(o[k] for k in ("md", "mod", "cif", "admin", "gasto_venta", "financiero", "perdida", "ocio"))
            assert abs(suma - o["costo_total"]) < 1e-6, (f.name, o["codigo"])
