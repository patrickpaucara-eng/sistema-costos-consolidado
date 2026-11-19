"""Mide una ejecución del caso de compra y consumo del piloto.

Desde la raíz del repositorio: PYTHONPATH=src python tools/medir_piloto.py
"""

from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import platform
import sys
from tempfile import TemporaryDirectory
from time import perf_counter

from reyna_local.store import Store


FIXTURE = (
    Path(__file__).resolve().parents[1] / "tests/fixtures/ola1/Sistema_Costos.xlsx"
)


def peak_rss_bytes():
    try:
        import resource
    except ImportError:
        return None
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform == "darwin":
        return peak
    if sys.platform.startswith("linux"):
        return peak * 1024
    return None


def main():
    seconds = {}

    def measure(name, operation, *args):
        start = perf_counter()
        result = operation(*args)
        seconds[name] = round(perf_counter() - start, 6)
        return result

    purchases = [
        ("compra-1", 20260310, "2026-03", 2000, 0.80),
        ("compra-2", 20260405, "2026-04", 1000, 0.85),
    ]
    consumption = {
        "transaction": "T15", "user": "SUPERV1", "request_id": "consumo",
        "header": {
            "FECHA": 20260410, "PER": "2026-04", "EMP": "B", "OBJ": "OS-01",
            "CEN": "LINEA1", "REC": "CAJA4KG", "ALM": "ALM1", "CANT": 2600,
        },
        "lines": [],
    }

    fixture_bytes = FIXTURE.read_bytes()
    with TemporaryDirectory() as directory:
        store = Store(directory)
        workspace = measure("importacion", store.create, {
            "name": "Medición del piloto", "workbook_path": str(FIXTURE),
        })
        identifier = workspace["id"]
        for name, date, period, quantity, cost in purchases:
            status, response = measure(name, store.execute, identifier, {
                "transaction": "T14", "user": "ALMACEN1", "request_id": name,
                "header": {
                    "FECHA": date, "PER": period, "EMP": "B", "REC": "CAJA4KG",
                    "ALM": "ALM1", "CANT": quantity, "CU_DOC": cost,
                    "MON": "USD", "IMP": "IGV",
                },
                "lines": [],
            })
            if status != 200:
                raise RuntimeError(f"{name} falló: {response}")
        applied = measure("consumo", store.execute, identifier, consumption)
        if applied[0] != 200:
            raise RuntimeError(f"El consumo falló: {applied[1]}")

        reopened = measure("reapertura", Store, directory)
        table = measure("consulta", reopened.table, identifier, "EXISTENCIA")
        replay = measure("reintento", reopened.execute, identifier, consumption)
        if replay != applied or reopened.table(identifier, "EXISTENCIA") != table:
            raise RuntimeError("El reintento cambió el recibo o el saldo.")
        rows = [dict(zip(table["columns"], row)) for row in table["rows"]]
        [stock] = [
            row for row in rows
            if (row["EXI_EMP"], row["EXI_REC"], row["EXI_ALM"]) == ("B", "CAJA4KG", "ALM1")
        ]
        amount = Decimal(str(stock["EXI_VAL"])).quantize(Decimal("0.01"))
        if (
            stock["EXI_CAN"] != 400 or amount != Decimal("1221.60")
            or stock["EXI_CPU"] != 3.054 or table["version"] != 3
        ):
            raise RuntimeError(f"Saldo o versión inesperados: {stock}, {table['version']}")

        result = {
            "plataforma": platform.platform(),
            "python": platform.python_version(),
            "fixture": {"bytes": len(fixture_bytes), "sha256": sha256(fixture_bytes).hexdigest()},
            "libro_gestionado_bytes": Path(workspace["workbook_path"]).stat().st_size,
            "motor_sha256": workspace["engine_sha256"],
            "segundos": seconds,
            "rss_maximo_bytes": peak_rss_bytes(),
            "saldo": {"unidades": stock["EXI_CAN"], "valor_pen": float(amount),
                      "costo_unitario_pen": stock["EXI_CPU"], "version": table["version"]},
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
