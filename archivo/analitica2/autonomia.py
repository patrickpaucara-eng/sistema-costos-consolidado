# -*- coding: utf-8 -*-
"""AUT-01 · Autonomía adaptativa (ESPEC_ANALITICA2 §8, D-13). OT-092. Función pura: no muta entradas ni ejecuta tramas (G-7).
Promoción 2 → 1: en las últimas A2.AUT_N decisiones humanas de una entrada de nivel 2, aprobadas / N > A2.AUT_PROMOVER
  y error medio de EST_DECISION (de las aprobadas) ≤ AUTO_TOL ⇒ SISTEMA PROPONE NIVEL = 1 (cambio de nivel 2; lo aprueba una persona).
Degradación 1 → 2: A2.AUT_REVERSIONES reversiones SEG-01 de decisiones entre las últimas A2.AUT_N automáticas de una
  entrada de nivel 1 ⇒ NIVEL = 2 automático con motivo AUT-01 (bajar autonomía es seguro).
I-2 (OT-098 V7): la degradación se entrega además como filas CARGA @NIVEL (clave `carga_nivel`) para el canal del motor.
Vínculo decisión ↔ entrada: PCA_MOTIVO empieza por la REGLA de la entrada (formato de autonomia_n1) o PCA_PAQ por la regla sin guion."""
import re
from decimal import Decimal as D

from analitica.canal_carga import trama_proponer, trama_nivel

_REV = re.compile(r"REVERSION SEG-01 PCA_NUM=(\d+)")


def _g(f, *k):
    for x in k:
        if x in f and f[x] not in (None, ""):
            return f[x]
    return None


def _de_entrada(c, regla):
    mot = str(_g(c, "MOTIVO", "PCA_MOTIVO") or "")
    paq = str(_g(c, "PAQUETE", "PCA_PAQ") or "")
    return mot.startswith(regla) or paq.startswith(regla.replace("-", ""))


def _num(c):
    return int(D(str(_g(c, "NUMERO", "PCA_NUM") or 0)))


def evaluar_autonomia(catalogo, param_cambio, est_decision, parametros):
    n_max = int(parametros.get("A2.AUT_N", D(10)))
    promover = D(str(parametros.get("A2.AUT_PROMOVER", D("0.90"))))
    rev_max = int(parametros.get("A2.AUT_REVERSIONES", D(2)))
    tol = D(str(parametros.get("AUTO_TOL", D("0.10"))))
    err = {}
    for e in est_decision:
        if _g(e, "EDE_ERR") is not None and str(_g(e, "EDE_ESTADO", "ESTADO") or "MEDIDO") in ("MEDIDO", "MEDIDA"):   # V2 (MEDIDA: histórico)
            err[int(D(str(e["EDE_REF"])))] = D(str(e["EDE_ERR"]))
    revertidas = []
    for c in param_cambio:
        m = _REV.search(str(_g(c, "MOTIVO", "PCA_MOTIVO") or ""))
        if m:
            revertidas.append(int(m.group(1)))
    promociones, degradaciones = [], []
    for ent in sorted(catalogo, key=lambda x: str(x.get("COD"))):
        if str(ent.get("ACTIVO", "S")) != "S":
            continue
        regla, nivel = str(ent.get("REGLA", "")), int(D(str(ent.get("NIVEL", 2))))
        if nivel == 2:
            humanas = sorted((c for c in param_cambio if _de_entrada(c, regla)
                              and str(_g(c, "MOTIVO", "PCA_MOTIVO") or "").startswith(regla + " nivel 2")
                              and str(_g(c, "ESTADO", "PCA_ESTADO")) in ("A", "R")), key=_num)[-n_max:]
            if len(humanas) < n_max:
                continue
            aprobadas = [_num(c) for c in humanas if str(_g(c, "ESTADO", "PCA_ESTADO")) == "A"]
            errores = [err[n] for n in aprobadas if n in err]
            if not errores:
                continue                                           # sin resultado medido no hay promoción (ENM-V41-20)
            if D(len(aprobadas)) / D(len(humanas)) > promover and sum(errores) / D(len(errores)) <= tol:
                promociones += trama_proponer("SISTEMA", [dict(TABLA="PROPUESTA", CLAVE=ent["COD"], COLUMNA="PRO_NIVEL", VALOR_NUEVO=1)],
                                              f"AUT01-{ent['COD']}",
                                              f"AUT-01 promoción: {len(aprobadas)}/{len(humanas)} decisiones humanas aceptadas y error medio "
                                              f"{(sum(errores) / D(len(errores))).quantize(D('0.000001'))}; decide una persona")
        elif nivel == 1:
            auto = sorted((c for c in param_cambio if _de_entrada(c, regla)
                           and str(_g(c, "MOTIVO", "PCA_MOTIVO") or "").startswith(regla + " R-71")), key=_num)[-n_max:]
            ultimas = {_num(c) for c in auto}
            n_rev = sum(1 for n in revertidas if n in ultimas)
            if n_rev >= rev_max:
                degradaciones.append({"COD": ent["COD"], "NIVEL_ANTERIOR": 1, "NIVEL": 2, "USUARIO": "SISTEMA",
                                      "MOTIVO": f"AUT-01 degradación: {n_rev} reversiones SEG-01 en las últimas {len(auto)} decisiones"})
    carga = [t for g in degradaciones for t in trama_nivel("SISTEMA", g["COD"], g["NIVEL"])]   # I-2 V7: @NIVEL (solo baja)
    return {"promociones": promociones, "degradaciones": degradaciones, "carga_nivel": carga}
