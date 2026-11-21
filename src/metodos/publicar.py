# -*- coding: utf-8 -*-
"""PUBLICAR resultados de un método en la base por el PUERTO DE RESULTADOS (T25.4, E-102).
La base solo acepta métodos registrados como APROBADOS (METODO_REGISTRADO) y guarda cada valor con método, versión y
huella de los hechos usados; repetir la misma entrega no duplica."""
import hashlib, json

def huella(hechos):
    return hashlib.sha256(json.dumps(hechos, sort_keys=True, default=str).encode()).hexdigest()[:16]

def trama(per, emp, metodo, version, hechos, filas):
    """filas = [(tipo, clave, concepto, valor)] → trama de CARGA para T25.4."""
    cab = f"PER={per};EMP={emp};PRS_METODO={metodo};PRS_VER={version};PRS_HUELLA={huella(hechos)}"
    return cab + "".join(f"|PRS_TIPO={t};PRS_CLAVE={c};PRS_CONC={k};PRS_VALOR={v}" for t, c, k, v in filas)

def valuacion_desde_kardex(K, rec, alm, metodo_fn):
    """Corre un método de valuación sobre los hechos de un recurso/almacén y devuelve (hechos, filas de resultado)."""
    rs = [r for r in K if r["KDX_REC"] == rec and r["KDX_ALM"] == alm]
    movs = [dict(tipo="E" if float(r["KDX_CAN"]) > 0 else "S", cantidad=abs(float(r["KDX_CAN"])), monto=float(r["KDX_VAL"]) if float(r["KDX_CAN"]) > 0 else None) for r in rs]
    out = metodo_fn(movs); sal = iter(out["salidas"]); filas = []
    for r, m in zip(rs, movs):
        if m["tipo"] == "S":
            s = next(sal); filas += [("SALIDA", f"{r['KDX_EVE']}-{r['KDX_LIN']}-{alm}", "CU", round(s["cu"], 6)), ("SALIDA", f"{r['KDX_EVE']}-{r['KDX_LIN']}-{alm}", "MONTO", s["monto"])]
    filas += [("EXISTENCIA", f"{rec}-{alm}", "CANTIDAD", out["saldo"]["cantidad"]), ("EXISTENCIA", f"{rec}-{alm}", "VALOR", out["saldo"]["valor"])]
    return [dict(m) for m in movs], filas


def redondear_alg09(filas):
    """V4.1 ALG-09 al publicar: filas [(tipo, clave, concepto, valor interno)] → mismas filas con 2 decimales, de modo que en
    cada grupo (tipo, concepto) la suma publicada sea exactamente el total redondeado; el residuo va al mayor bruto (empate: menor
    clave). Los conceptos de costo unitario o tasa (CU, TASA, PCT) se publican con 6 decimales, sin residuo."""
    from decimal import Decimal as D, ROUND_HALF_UP
    from collections import defaultdict
    seis = ("COSTO_UNITARIO", "CU", "TASA", "PCT")
    grupos, out = defaultdict(list), []
    for i, (t, k, c, v) in enumerate(filas):
        grupos[(t, c)].append(i)
    pub = {}
    for (t, c), idx in grupos.items():
        if any(x in str(c) for x in seis) or not all(isinstance(filas[i][3], (int, float)) for i in idx):
            for i in idx:
                v = filas[i][3]
                pub[i] = float(D(repr(float(v))).quantize(D("0.000001"), ROUND_HALF_UP)) if isinstance(v, (int, float)) else v
            continue
        br = {i: D(repr(float(filas[i][3]))) for i in idx}
        r2 = {i: x.quantize(D("0.01"), ROUND_HALF_UP) for i, x in br.items()}
        res = sum(br.values()).quantize(D("0.01"), ROUND_HALF_UP) - sum(r2.values())
        orden = sorted(idx, key=lambda i: (-br[i], str(filas[i][1]))); j = 0
        while res != 0:
            paso = D("0.01") if res > 0 else D("-0.01"); i = orden[j % len(orden)]
            if paso > 0 or r2[i] + paso >= 0: r2[i] += paso; res -= paso
            j += 1
        for i in idx: pub[i] = float(r2[i])
    return [(t, k, c, pub[i]) for i, (t, k, c, v) in enumerate(filas)]
