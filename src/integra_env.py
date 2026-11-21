# -*- coding: utf-8 -*-
"""Integración del arquitecto: corre REPARTO_ETAPAS sobre el estado de hechos de ENVASE (casos/V41/ENV.xlsx) y lo compara
con el oráculo independiente O-1 (informes/ARQ_V4/oraculo_envase.py) en valores internos. Uso (desde la raíz): python -I informes/V41/integra_env.py"""
import io, os, sys, contextlib, warnings
from decimal import Decimal as D
warnings.filterwarnings("ignore")
RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(RAIZ, "kit"))
import puerto_lectura as P
from metodos import reparto_etapas as R


def valuacion_alg01(libro):
    """Valuación con el método del eje VALUACION (OT-079, VALUACION_PROMEDIO); valores internos."""
    from metodos import valuacion as V
    res, _ = V.calcular(P.leer_conceptos(libro, V.CONSUME), {}, {})
    return [r for r in res if r[0] == "SALIDA"]


def _valuacion_alg01_referencia(libro):
    """ALG-01 en Decimal escrito por el arquitecto: referencia independiente de OT-079."""
    k = P.leer(libro, ["KARDEX"])["KARDEX"]
    k.sort(key=lambda r: (int(r["KDX_FEC"]), int(r["KDX_EVE"])))
    sal, st = [], {}
    for r in k:
        key = (r["KDX_REC"], r["KDX_ALM"]); c, v = st.get(key, (D(0), D(0))); q = R._d(r["KDX_CAN"])
        if q > 0: st[key] = (c + q, v + R._d(r["KDX_VAL"]))
        else:
            cpu = v / c; m = -q * cpu; st[key] = (c + q, v - m)
            sal.append(("SALIDA", f"{r['KDX_EVE']}-{r['KDX_LIN']}-{r['KDX_ALM']}", "MONTO", m))
    return sal


def main():
    libro = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, "casos", "V41", "ENV.xlsx")   # I-1: también sobre la base sembrada
    h = P.leer_conceptos(libro, R.CONSUME)
    prev = {"VALUACION_PROMEDIO": valuacion_alg01(libro)}
    fin = R.interno(h, dict(PER="2021-01", EMP="ENV"), prev)
    g = {}
    sys.argv = ["x", os.path.join(RAIZ, "informes", "ARQ_V4", "insumos", "ENVASE_SAC_plantilla_Oria.xlsx")]
    with contextlib.redirect_stdout(io.StringIO()): exec(open(os.path.join(RAIZ, "informes", "ARQ_V4", "oraculo_envase.py")).read(), g)
    peor = D(0); n = 0
    for o in g["ots"]:
        for e, src in (("MD", "md"), ("PD", "pd"), ("SD", "sd"), ("CIF", "cif"), ("GAD", "gad"), ("GVT", "gvt")):
            ora = R._d(g[src][o]); sis = fin.get(o, {}).get(e, D(0)); dif = abs(ora - sis); n += 1
            if dif > peor: peor = dif
            if dif > D("1e-6"): print(f"DIFERENCIA {o} {e}: sistema {sis:.6f} oráculo {ora:.6f}")
    inef = fin.get("INEF", {})
    print(f"{n} valores comparados; diferencia máxima {peor:.2E}; INEF {inef}")
    t = R.trazar(h, dict(PER="2021-01", EMP="ENV"), prev, "OBJETO", "OT1520", "CIF")
    print("P-45: traza CIF OT1520 =", round(sum(l["monto_atribuido"] for l in t if l["raiz"]), 6), "líneas", len(t))


if __name__ == "__main__":
    main()


def cadena():
    """K1 → K7 completo en memoria sobre ENVASE, contra O-1."""
    from metodos import liquidacion as L, costo_ventas_gastos as CV
    libro = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, "casos", "V41", "ENV.xlsx")   # I-1: también sobre la base sembrada; par = dict(PER="2021-01", EMP="ENV")
    prev = {"VALUACION_PROMEDIO": valuacion_alg01(libro)}
    prev["REPARTO_ETAPAS"] = R.calcular(P.leer_conceptos(libro, R.CONSUME), par, prev)[0]
    prev["LIQUIDACION_OT"] = L.calcular(P.leer_conceptos(libro, L.CONSUME), par, prev)[0]
    out, tot = CV.interno(P.leer_conceptos(libro, CV.CONSUME), par, prev)
    print("CPT %.2f IFPP %.2f | ventas %.2f CV %.2f MB %.2f PT %.2f" % (tot["CPT"], tot["IFPP"], tot["VENTAS"], tot["CV"], tot["MB"], tot["PT_FINAL"]))
    for o, x in out.items(): print(f"  {o} CV {x['CV']:.2f} MB {x['MB']:.2f} MB% {x['MB_PCT']*100:.2f}")
    print("Familias:", [(k, round(c, 6)) for t, k, c2, c in prev["LIQUIDACION_OT"] if t == "FAMILIA" for _ in [0] if c2 == "CU"])


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "cadena":
    pass


def cotizacion():
    """O-4 sobre la cadena real: PROYECCION_OT propone tarifas; DIFERENCIAS_OT contra lo real de OT1541."""
    from metodos import liquidacion as L, proyeccion as PR, diferencias as DF
    sys.path.insert(0, os.path.join(RAIZ, "kit"))
    from casos import cotizacion_ot1541 as C
    libro = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, "casos", "V41", "ENV.xlsx")   # I-1: también sobre la base sembrada; par = dict(PER="2021-01", EMP="ENV")
    prev = {"VALUACION_PROMEDIO": valuacion_alg01(libro)}
    prev["REPARTO_ETAPAS"] = R.calcular(P.leer_conceptos(libro, R.CONSUME), par, prev)[0]
    prev["LIQUIDACION_OT"] = L.calcular(P.leer_conceptos(libro, L.CONSUME), par, prev)[0]
    c = C.cargar()
    objs = P.leer_conceptos(libro, {"(sin MCD) OBJETO": PR.CONSUME["(sin MCD) OBJETO"]})["(sin MCD) OBJETO"]
    h = {"(sin MCD) ESTIMACION": [dict(c["cabecera"], EST_CST=None, CLIENTE=None)], "(sin MCD) LIN_ESTIM": c["lineas_estim"], "(sin MCD) OBJETO": objs}
    pi = dict(par, PRECISION="INTERNA")
    rp, _ = PR.calcular(h, pi, prev)
    print("Tarifas propuestas:", {k.split("|")[1]: round(v, 6) for t, k, c_, v in rp if t == "LIN_ESTIM"})
    print("Cotización:", {c_: v for t, k, c_, v in rp if t == "ESTIMACION"})
    h["(sin MCD) ESTIMACION"][0]["EST_CST"] = [v for t, k, c_, v in rp if c_ == "EST_CST"][0]
    rd, _ = DF.calcular(h, pi, prev)
    print("Variaciones:", {c_: round(v, 6) for t, k, c_, v in rd if t == "OBJETO" and isinstance(v, float)})
