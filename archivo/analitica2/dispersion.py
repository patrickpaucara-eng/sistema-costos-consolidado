# -*- coding: utf-8 -*-
"""ALG-14 · Umbral por dispersión y contracción (ESPEC_ANALITICA2 §4, OT-088). Pura, Decimal, orden por código."""
from decimal import Decimal as D

from .comun import ELEMENTOS, d, q6, parametros, objetos, indice_objetos, can, poblacion


def _ventana(per, n):
    a, m = int(per[:4]), int(per[5:7])
    out = []
    for _ in range(n):
        out.append(f"{a:04d}-{m:02d}")
        m -= 1
        if m == 0:
            a, m = a - 1, 12
    return out


def _confianza(m):
    return "baja" if m < 5 else ("media" if m < 30 else "alta")


def _sigma(xs):
    """σ muestral (n − 1) de una lista de Decimal; (media, σ)."""
    n = len(xs)
    media = sum(xs) / n
    var = sum((x - media) ** 2 for x in xs) / (n - 1)
    return media, var.sqrt()


def evaluar(hechos, resultado_metodo, per, emp, familias=None):
    """Filas H-14, H-14-SIN_Z (OT de `per`, D-7 n.º 7) y H-14H (familias), ordenadas por (TIPO, REFERENCIA, REFERENCIA_2)."""
    par = parametros(hechos, per)
    ventana = int(par["A2.VENTANA"])
    k = par["A2.K_CONTRAE"]
    idx = {}
    for p in sorted(_ventana(per, ventana)):            # ascendente: el periodo más reciente prevalece
        idx.update(indice_objetos(resultado_metodo, p, emp))
    ots_per = set(o for (o, c) in indice_objetos(resultado_metodo, per, emp))
    pob = poblacion(hechos, idx, emp, familias)
    grupos = {}
    for ot, f in pob.items():
        grupos.setdefault(f, []).append(ot)
    grupos = {f: sorted(v) for f, v in grupos.items() if len(v) >= 2}      # F-2 / D-7 n.º 11
    todas = sorted(pob)
    filas = []
    for fam in sorted(grupos, key=str):
        ots = grupos[fam]
        for e in ELEMENTOS:
            x = {p: idx.get((p, "C_" + e), D(0)) / can(idx, p) for p in ots}
            # heterogeneidad: todas las OT de la familia en la ventana (n ≥ 3)
            if len(ots) >= 3:
                media, sig = _sigma(list(x.values()))
                if media != 0 and sig / media > par["A2.CV_MAX"]:
                    filas.append({"PERIODO": per, "EMPRESA": emp, "TIPO": "H-14H", "REFERENCIA": fam, "REFERENCIA_2": e,
                                  "VALOR": q6(sig / media), "UMBRAL": q6(par["A2.CV_MAX"]), "N_FAMILIA": len(ots)})
            for o in ots:
                if o not in ots_per:
                    continue
                resto = [p for p in ots if p != o]
                m = len(resto)
                den = sum(can(idx, p) for p in resto)
                mu = sum(idx.get((p, "C_" + e), D(0)) for p in resto) / den
                if mu == 0:
                    continue                                                   # D-7 n.º 10
                gen = [p for p in todas if p != o]
                dg = sum(can(idx, p) for p in gen)
                mu_g = sum(idx.get((p, "C_" + e), D(0)) for p in gen) / dg
                w = D(m) / (D(m) + k) if (m + k) else D(1)
                mu_c = w * mu + (1 - w) * mu_g
                base = {"PERIODO": per, "EMPRESA": emp, "REFERENCIA": o, "REFERENCIA_2": e, "UMBRAL": q6(par["A2.Z_MAX"]),
                        "MU": q6(mu), "MU_GLOBAL": q6(mu_g), "MU_CONTRAIDO": q6(mu_c), "N": m, "CONFIANZA": _confianza(m)}
                sigma = None
                if m >= 3:
                    sigma = _sigma([x[p] for p in resto])[1]
                if sigma is None or sigma == 0:
                    base.update({"TIPO": "H-14-SIN_Z", "VALOR": None, "SIGMA": None if sigma is None else q6(sigma),
                                 "MOTIVO": "m < 3" if sigma is None else "sigma = 0"})
                    filas.append(base)
                    continue
                z = (x[o] - mu_c) / sigma
                if z > par["A2.Z_MAX"]:
                    base.update({"TIPO": "H-14", "VALOR": q6(z), "SIGMA": q6(sigma)})
                    filas.append(base)
    return sorted(filas, key=lambda f: (f["TIPO"], str(f["REFERENCIA"]), str(f["REFERENCIA_2"])))
