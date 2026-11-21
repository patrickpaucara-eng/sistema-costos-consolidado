# -*- coding: utf-8 -*-
"""CAT-01 · Evaluadores registrados (ESPEC_ANALITICA2 §7, D-5). Uno por regla; puros; devuelven filas de hallazgo.
Firma: evaluador(hechos, resultado_metodo, per, emp, parametros) -> list[dict]."""
from analitica import hallazgos


def _prototipo(tipo):
    def ev(hechos, resultado_metodo, per, emp, parametros):
        return [dict(f) for f in hallazgos.evaluar(hechos, resultado_metodo, per, emp) if f["TIPO"] == tipo]
    ev.__name__ = "ev_" + tipo.replace("-", "")
    return ev


def h13(hechos, resultado_metodo, per, emp, parametros):
    from analitica2 import elemento
    return elemento.evaluar(hechos, resultado_metodo, per, emp, con_mejor=False)


def _dispersion(tipo):
    def ev(hechos, resultado_metodo, per, emp, parametros):
        from analitica2 import dispersion
        return [f for f in dispersion.evaluar(hechos, resultado_metodo, per, emp) if f["TIPO"] == tipo]
    ev.__name__ = "ev_" + tipo.replace("-", "")
    return ev


REGISTRO_EVALUADORES = {f"H0{i}": _prototipo(f"H-0{i}") for i in range(1, 8)}
REGISTRO_EVALUADORES.update({"H13": h13, "H14": _dispersion("H-14"), "H14H": _dispersion("H-14H")})
