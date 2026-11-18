"""Sonda OT-001: identidad de empresa al valorar un mismo recurso y almacén."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(sys.argv[1]) / "kit"))
from metodos.valuacion import calcular

rows = [
    dict(EMPRESA="A", RECURSO="K", ALMACEN="L", KDX_EVE=1, KDX_LIN=1, KDX_CAN=10, KDX_VAL=100),
    dict(EMPRESA="B", RECURSO="K", ALMACEN="L", KDX_EVE=2, KDX_LIN=1, KDX_CAN=10, KDX_VAL=900),
    dict(EMPRESA="A", RECURSO="K", ALMACEN="L", KDX_EVE=3, KDX_LIN=1, KDX_CAN=-1, KDX_VAL=0),
]
for scope, events in (("A", [r for r in rows if r["EMPRESA"] == "A"]), ("A+B", rows)):
    result, _ = calcular({"(sin MCD) KARDEX": events}, {"EMP": "A"}, {})
    outgoing = [r for r in result if r[:3] == ("SALIDA", "3-1-L", "MONTO")]
    print(scope, outgoing)
