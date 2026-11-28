# -*- coding: utf-8 -*-
"""B7b · Nivel 1 de autonomía (ARQUITECTURA_V4_1 §9.2 R-71/R-72/R-73, §9.3 H-05, §9.7 #8). OT-084.
H-05 vigila las reglas de nivel 1: si una marca más del 50 % de los objetos que evalúa, propone subir su umbral al
percentil 80 de la desviación observada. Si el valor cumple R-71, SISTEMA deja PROPONER y APRUEBA-PARM en CARGA
(vigencia = periodo siguiente, R-72); si no, deja una propuesta de nivel 2 en estado P con el diagnóstico.
Memoria: no se repite una propuesta P o R del mismo parámetro y valor. Python no escribe en la base: todo va por CARGA."""
from decimal import Decimal as D, ROUND_HALF_UP

from analitica import canal_carga, hallazgos

_E6 = D("0.000001")
LIMITE = D("0.5")                 # R-71 (3): mejora = el % marcado baja y queda en 50 % o menos
USR = "SISTEMA"
# reglas de nivel 1 vigiladas por H-05: regla → parámetro
VIGILADAS = {"H-02": "ENV.DIF_MAX", "H-03": "ENV.FAM_DESV"}


def _d(v):
    return D(str(v))


def percentil_80(valores):
    """Interpolación lineal: x[⌊h⌋] + (h − ⌊h⌋)·(x[⌊h⌋+1] − x[⌊h⌋]), h = (n − 1)·0.8 (adenda 2 de OT-084)."""
    x = sorted(valores)
    h = (len(x) - 1) * D("0.8")
    i = int(h)
    p = x[i] if i + 1 >= len(x) else x[i] + (h - i) * (x[i + 1] - x[i])
    return p.quantize(_E6, rounding=ROUND_HALF_UP)


def _siguiente(per):
    a, m = int(per[:4]), int(per[5:7])
    a, m = (a + 1, 1) if m == 12 else (a, m + 1)
    return f"{a:04d}{m:02d}01"


def _desviaciones(regla, hechos, rm, per, emp):
    """Desviación de cada objeto que la regla evalúa (misma base que hallazgos.evaluar)."""
    idx = hallazgos._indice(rm, per, emp)
    out = {}
    if regla == "H-03":
        cu, fam = hallazgos._por(idx, "OBJETO", "CU"), hallazgos._por(idx, "FAMILIA", "CU")
        term = {}
        for o in hallazgos._objetos(hechos):
            if o.get("ESTADO") == "T" and o.get("TIPO", "OT") == "OT" and o.get("EMPRESA") in (None, emp):
                term.setdefault(o["COMPONENTE"], []).append(str(o["NUMERO"]))
        for f, ots in term.items():
            if len(ots) >= 2 and fam.get(f, D(0)) > 0:
                out.update({ot: cu[ot] / fam[f] - 1 for ot in ots if ot in cu})
    elif regla == "H-02":
        dif, flex = hallazgos._por(idx, "OBJETO", "DIFERENCIA"), hallazgos._por(idx, "OBJETO", "ESTIMADO_FLEXIBLE")
        out = {ot: dif[ot] / flex[ot] for ot in dif if flex.get(ot, D(0)) > 0}
    return out


def _fila_param(motor, cod):
    t = motor.T["PARAMETRO"]
    f = [dict(zip(t["h"], r)) for r in t["r"] if r[0] == cod]
    return f[0] if f else None


def _ya_propuesto(motor, cod, valor):
    t = motor.T["PARAM_CAMBIO"]
    for r in t["r"]:
        c = dict(zip(t["h"], r))
        if c["PCA_TABLA"] == "PARAMETRO" and c["PCA_CLAVE"] == cod and c["PCA_ESTADO"] in ("P", "R"):
            try:
                if abs(_d(c["PCA_NUE"]) - valor) <= _E6:
                    return True
            except Exception:   # noqa: BLE001
                continue
    return False


def _es_nivel1(p):
    return p is not None and p.get("PAR_DUENO") == "SISTEMA" and p.get("PAR_PROT") == "N"


def ejecutar_nivel1(hechos, resultado_metodo, per, emp, motor):
    """R-73: corre tras hallazgos.evaluar. Devuelve {alertas, tramas, car_res}; las tramas se ejecutan en `motor`."""
    alertas = hallazgos.evaluar(hechos, resultado_metodo, per, emp)
    tramas, car_res = [], []
    for regla, cod in sorted(VIGILADAS.items()):
        p = _fila_param(motor, cod)
        if not _es_nivel1(p):
            continue
        desv = _desviaciones(regla, hechos, resultado_metodo, per, emp)
        if not desv:
            continue
        actual = _d(p["PAR_VAL"])
        marcados = sum(1 for v in desv.values() if v > actual)
        pct = D(marcados) / D(len(desv))
        if pct <= LIMITE:
            continue
        alertas.append({"PERIODO": per, "EMPRESA": emp, "TIPO": "H-05", "REFERENCIA": regla, "REFERENCIA_2": cod,
                        "VALOR": pct.quantize(_E6), "UMBRAL": LIMITE})
        p80 = percentil_80(desv.values())
        lo, hi = _d(p["PAR_MIN"]), _d(p["PAR_MAX"])
        despues = D(sum(1 for v in desv.values() if v > p80)) / D(len(desv))
        paq = f"H05-{per}-{cod}"
        if lo <= p80 <= hi and p80 > actual and despues <= LIMITE:          # R-71 (1)(2)(3); (4)(5): vigencia siguiente, sin CONTABLE
            if _ya_propuesto(motor, cod, p80):
                continue
            motivo = (f"H-05 R-71: {regla} marca {marcados}/{len(desv)} ({pct:.0%}); percentil 80 = {p80}; "
                      f"con el umbral nuevo marcaría {despues:.0%}")
            nuevas = (canal_carga.trama_proponer(USR, [dict(TABLA="PARAMETRO", CLAVE=cod, COLUMNA="PAR_VAL", VALOR_NUEVO=p80)], paq, motivo)
                      + canal_carga.trama_aprueba(USR, paq, "A", _siguiente(per)))
        else:                                                              # sin salida de nivel 1: propuesta de nivel 2 en P
            valor = min(max(p80, lo), hi)
            if _ya_propuesto(motor, cod, valor):
                continue
            motivo = (f"H-05 nivel 2: {regla} marca {marcados}/{len(desv)} ({pct:.0%}); percentil 80 = {p80} fuera de "
                      f"[{lo}, {hi}] o sin mejora; se propone {valor} para decisión humana")
            nuevas = canal_carga.trama_proponer(USR, [dict(TABLA="PARAMETRO", CLAVE=cod, COLUMNA="PAR_VAL", VALOR_NUEVO=valor)], paq, motivo)
        tramas += nuevas
        car_res += canal_carga.ejecutar(nuevas, motor=motor)
    return {"alertas": alertas, "tramas": tramas, "car_res": car_res}


def proponer_nivel1(motor, parametro, valor_nuevo, per, motivo):
    """SISTEMA intenta aplicar un cambio directo: solo procede si R-71 (1) y (2) se cumplen; si no, no deja tramas."""
    p = _fila_param(motor, parametro)
    if not _es_nivel1(p):
        return {"aplicado": False, "car_res": [], "motivo": f"R-71 (1): {parametro} no es de nivel 1 (dueño {p and p.get('PAR_DUENO')}, protegido {p and p.get('PAR_PROT')})"}
    v = _d(valor_nuevo)
    if not (_d(p["PAR_MIN"]) <= v <= _d(p["PAR_MAX"])):
        return {"aplicado": False, "car_res": [], "motivo": f"R-71 (2): {v} fuera de [{p['PAR_MIN']}, {p['PAR_MAX']}]"}
    paq = f"N1-{per}-{parametro}"
    filas = (canal_carga.trama_proponer(USR, [dict(TABLA="PARAMETRO", CLAVE=parametro, COLUMNA="PAR_VAL", VALOR_NUEVO=v)], paq, f"R-71 {motivo}")
             + canal_carga.trama_aprueba(USR, paq, "A", _siguiente(per)))
    res = canal_carga.ejecutar(filas, motor=motor)
    return {"aplicado": all(r["CAR_RES"] == "OK" for r in res), "car_res": res}
