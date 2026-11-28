"""Corre calcular() del motor real para julio de SERVITEC y guarda lo que el oráculo compara (por orden, por etapa, controles).
Uso: python -I motor_julio.py <repo>/src <SERVITEC_sintetico.xlsx> <salida.json>"""
import json
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, sys.argv[1])
import reyna_local.calculo_local as CL  # noqa: E402

LIBRO, SALIDA, PER = Path(sys.argv[2]), Path(sys.argv[3]), "2025-07"


def correr(libro=LIBRO):
    c = Path(tempfile.mkdtemp(prefix="oraculo_"))
    ficha, err = CL.registrar(c, libro.read_bytes(), libro.name)
    if err:
        raise SystemExit(f"El libro no pasa validar(): {err[:3]}")
    r = CL.calcular(c, PER, "REAL", ficha["id"])
    flujos = defaultdict(float)
    for t in r["trazas"]:
        flujos[f"{t['etapa']}|{t['origen']}|{t['destino']}"] += t["monto"]
    ctrl = {x["control"]: x for x in r["control"]}
    kdx = next(x for k, x in ctrl.items() if k.startswith("Kardex") and "saldo final" in k)
    cons = next(x for k, x in ctrl.items() if k.startswith("Conservación del reparto"))
    return {
        "calculado": r["sello"]["calculado"], "huella_libro": r["sello"]["huella_libro"],
        "objetos": {o["codigo"]: o for o in r["objetos"]},
        "flujos": {k: round(v, 6) for k, v in flujos.items()},
        "ocio_total": sum(x["importe"] for x in r["capacidad_ociosa"]),
        "kardex_saldo_final": kdx["obtenido"], "conservacion": cons["obtenido"],
    }


if __name__ == "__main__":
    SALIDA.write_text(json.dumps(correr(), ensure_ascii=False, indent=1), encoding="utf-8")
    print("ok", SALIDA)
