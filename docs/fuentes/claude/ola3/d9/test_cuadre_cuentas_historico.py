# -*- coding: utf-8 -*-
"""Deuda grupo B · D-I0b-1 (informes/I0b/TABLA_FINAL.md): las 7 cuentas tienen UN SOLO escritor, el paso del cierre que
publica RESULTADO_METODO, y su total cuadra con RESULTADO_METODO para el mismo periodo y elemento (tolerancia 0.01).

Caso: O-1 (ENVASE, casos/V41/ENV.xlsx, 2021-01), cadena K1→K7 como informes/V41/integra_env.py.
Lo que hoy no se cumple queda en xfail(strict=True) con la razón exacta, calculada de DBD_4c, kit/ y del caso:
cuando se arregle, el xfail desaparece solo (la marca se pone únicamente si la condición sigue fallando) y, si
alguien lo arregla sin quitar la marca, strict=True lo hace saltar. Solo pruebas: no cambia motor, base ni servicios."""
import os
import sys

import pytest

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "informes", "DEUDA"))
import escritores as E  # noqa: E402

TOL = 0.01
_DBD = E.escritores_dbd()
_KIT = E.escritores_kit()
_HOJAS = E.hojas_libro()
_RM = E.correr_o1()


def escritores(cuenta):
    """Todos los escritores de la cuenta: servicios de DBD_4c (con su transacción raíz) y escritura por nombre en kit/."""
    out = [f"DBD_4c {s['sad']} ({s['op']}; {', '.join(sorted({r[0] for r in s['rutas']})) or 'sin transacción'})" for s in _DBD[cuenta]]
    out += [f"kit {a}:{i}" for a, i, _ in _KIT[cuenta]]
    return out


def falla_escritor(cuenta):
    w = escritores(cuenta)
    if len(w) == 1 and E.CIERRE_PUBLICA in w[0]:
        return None
    return (f"{cuenta}: {len(w)} escritores y ninguno es el cierre que publica RESULTADO_METODO ({E.CIERRE_PUBLICA}, "
            f"que no escribe ninguna CTA_*): " + "; ".join(w))


def leer_cuenta(cuenta, libro=E.CASO_O1):
    import puerto_lectura as P
    filas = P.leer(libro, [cuenta])[cuenta]
    pre = {r for r in (filas[0].keys() if filas else []) if r.endswith(("_PER", "_EMP"))}
    return [r for r in filas if all(str(r[k]) == E.PAR_O1["PER" if k.endswith("_PER") else "EMP"] for k in pre)]


def falla_cuadre(cuenta):
    """None si cuadra; si no, la razón exacta."""
    if cuenta not in _HOJAS:
        return (f"{cuenta}: el caso O-1 (casos/V41/ENV.xlsx) no tiene la hoja {cuenta}; el cierre V4.1 "
                f"({E.CIERRE_PUBLICA}) publica RESULTADO_METODO pero no escribe la cuenta, así que no hay total que cuadrar")
    if not E.CUADRE[cuenta]:
        return f"{cuenta}: ningún método de la cadena V4.1 publica en RESULTADO_METODO un concepto para esta cuenta"
    filas = leer_cuenta(cuenta); difs = []
    for col in sorted({c for c, *_ in E.CUADRE[cuenta]}):
        rm = sum(E.total_resultado(_RM, m, t, k) for c, m, t, k in E.CUADRE[cuenta] if c == col)
        cta = sum(float(r.get(col) or 0) for r in filas)
        if abs(cta - rm) > TOL:
            difs.append(f"{col} cuenta {cta:.2f} ≠ RESULTADO_METODO {rm:.2f}")
    return f"{cuenta} {E.PAR_O1['PER']}: " + "; ".join(difs) if difs else None


def _params(fn):
    out = []
    for c in E.CUENTAS:
        r = fn(c)
        out.append(pytest.param(c, id=c, marks=[pytest.mark.xfail(strict=True, reason=r)] if r else []))
    return out


# ------------------------------------------------------------------------------------------- pruebas que pasan hoy
def test_o1_publica_los_conceptos_del_cuadre():
    """La cadena O-1 corre y publica cada concepto que el cuadre usa (sin esto el cuadre no significaría nada)."""
    faltan = [(m, t, k) for cs in E.CUADRE.values() for _, m, t, k in cs
              if not any(x[0] == t and x[2] == k for x in _RM.get(m, []))]
    assert not faltan, f"RESULTADO_METODO de O-1 sin: {faltan}"


def test_informe_escritores_al_dia():
    """informes/DEUDA/escritores_cuentas.md es exactamente lo que da DBD_4c + kit/ hoy (regenerar con escritores.py)."""
    ruta = os.path.join(RAIZ, "informes", "DEUDA", "escritores_cuentas.md")
    assert open(ruta, encoding="utf-8").read() == E.informe(), "informe desactualizado: python3 -I informes/DEUDA/escritores.py"


def test_cada_cuenta_tiene_escritor_en_dbd():
    """Ninguna cuenta queda sin escritor (si quedara, el inventario estaría mal leído)."""
    assert all(_DBD[c] for c in E.CUENTAS)


# ------------------------------------------------------------------------------------------- D-I0b-1
@pytest.mark.parametrize("cuenta", _params(falla_escritor))
def test_un_solo_escritor(cuenta):
    assert falla_escritor(cuenta) is None, falla_escritor(cuenta)


@pytest.mark.parametrize("cuenta", _params(falla_cuadre))
def test_cuadre_con_resultado_metodo(cuenta):
    assert falla_cuadre(cuenta) is None, falla_cuadre(cuenta)
