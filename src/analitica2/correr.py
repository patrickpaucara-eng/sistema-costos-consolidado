# -*- coding: utf-8 -*-
"""Runner de la capa 2.0: `python -m analitica2.correr <CASO>` desde kit/. Lee salidas/<CASO>/resultado_metodo.json
y los hechos del caso (solo lectura); publica en salidas_a2/<CASO>/ (G-3). Nunca escribe en salidas/."""
import json
import os
import sys
import warnings

warnings.filterwarnings("ignore")
KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAIZ = os.path.dirname(KIT)
if KIT not in sys.path:
    sys.path.insert(0, KIT)

CASOS = {"ENV": ("ENV", "2021-01"), "P10": ("P10", "2026-01"), "P05": ("P05", "2026-01")}


def _json(x):
    return json.dumps(x, ensure_ascii=False, indent=1, default=str, sort_keys=False)


def cargar(caso):
    import puerto_lectura as P
    emp, per = CASOS[caso]
    with open(os.path.join(RAIZ, "salidas", caso, "resultado_metodo.json"), encoding="utf-8") as f:
        rm = json.load(f)["resultado_metodo"]
    libro = os.path.join(RAIZ, "casos", "V41", f"{caso}.xlsx")
    h = P.leer_conceptos(libro, {"(sin MCD) OBJETO": ["NUMERO", "EMPRESA", "COMPONENTE", "CANTIDAD", "ESTADO", "TIPO"],
                                 "(sin MCD) PARAMETRO": ["CODIGO", "VALOR", "MINUTOS", "MAXIMO", "DUENO", "PROTEGIDO", "DESDE"]})
    hechos = {"(sin MCD) OBJETO": [o for o in h["(sin MCD) OBJETO"] if o["EMPRESA"] == emp],
              "(sin MCD) PARAMETRO": [dict(p, DESDE=str(p["DESDE"])) for p in h["(sin MCD) PARAMETRO"]]}
    return hechos, rm, per, emp


def ejecutar_carga(filas):
    """Ejecuta las filas CARGA con canal_carga.ejecutar (espejo del motor, copia en memoria de la base: no escribe la base)
    y devuelve {filas, resultado}. Sin base generada, deja las filas listas y el motivo (las ejecuta el motor en Excel)."""
    from analitica import canal_carga
    if not filas:
        return {"filas": [], "resultado": []}
    try:
        return {"filas": filas, "resultado": canal_carga.ejecutar(filas)}
    except FileNotFoundError as e:
        return {"filas": filas, "resultado": [], "motivo": str(e)}


def correr(caso):
    from analitica2 import elemento, dispersion, seguimiento
    hechos, rm, per, emp = cargar(caso)
    sal = os.path.join(RAIZ, "salidas_a2", caso)
    os.makedirs(sal, exist_ok=True)
    filas = elemento.evaluar(hechos, rm, per, emp, con_mejor=True)
    with open(os.path.join(sal, "ALG13.json"), "w", encoding="utf-8") as f:
        f.write(_json(filas))
    f14 = dispersion.evaluar(hechos, rm, per, emp)
    with open(os.path.join(sal, "ALG14.json"), "w", encoding="utf-8") as f:
        f.write(_json(f14))
    seg = seguimiento.seguir(hechos, {per: rm}, emp)
    with open(os.path.join(sal, "est_decision.json"), "w", encoding="utf-8") as f:
        f.write(_json(seg["est_decision"]))
    with open(os.path.join(sal, "tramas_seg01.json"), "w", encoding="utf-8") as f:
        f.write(_json(seg["tramas"]))
    carga = ejecutar_carga(seg["carga_seguim"] + seg["tramas"])      # I-2 (OT-098 I2-c n.º 2): por el canal (espejo)
    with open(os.path.join(sal, "carga_seguim.json"), "w", encoding="utf-8") as f:
        f.write(_json(carga))
    msgs = elemento.mensajes(filas, rm, per, emp, os.path.join(sal, "mensajes"))
    return {"ALG13": filas, "ALG14": f14, "SEG01": seg, "carga_seguim": carga, "mensajes": msgs}


if __name__ == "__main__":
    caso = sys.argv[1] if len(sys.argv) > 1 else "ENV"
    out = correr(caso)
    print("ALG-13:", [(f["TIPO"], f["REFERENCIA"], f["REFERENCIA_2"], f["DOMINANTE"]) for f in out["ALG13"]])
    print("ALG-14:", sorted({f["TIPO"] for f in out["ALG14"]}), len(out["ALG14"]), "filas")
    print("Mensajes:", len(out["mensajes"]))
