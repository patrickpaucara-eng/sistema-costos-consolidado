"""Aceptación del formulario con Frenosa; PT y saldo son datos sintéticos de prueba."""
import json
import threading
from pathlib import Path
from urllib.request import Request, urlopen

import pytest
from openpyxl import load_workbook
from reyna_local.__main__ import ReynaServer

ROOT = Path(__file__).resolve().parents[1]


def request(url, body=None):
    data = None if body is None else json.dumps(body).encode()
    with urlopen(Request(url, data=data, headers={"Content-Type": "application/json"}), timeout=60) as response:
        return response.status, json.load(response)


def test_seis_transacciones_desde_campos_frenosa(tmp_path):
    # Frenosa no trae producto terminado ni asignación INV para PRODUCTO.
    # Se agregan exclusivamente en esta copia; el saldo inicial también es sintético.
    book = load_workbook(ROOT / "casos/libros/frenosa.xlsx")
    assert list(book["PRODUCTO_PT"].values)[1:] == []  # brecha del libro de origen
    assert not any(row[1] == "PRODUCTO" and row[2] == "INV" for row in list(book["ASIGNACION"].values)[1:])
    book["RECURSO"].append(["SW50", "Producto SW50 de prueba", "PRODUCTO", "kg", None, "S", "FRE"])
    book["PRODUCTO_PT"].append(["SW50", "SW50", 1, None, "FRE"])
    book["ASIGNACION"].append(["TRE", "PRODUCTO", "INV", "ALG-PROM", 19000101, "FRE"])
    book["EXISTENCIA"].append(["SW50", "ALM_FRE", 10, 50, 5, "FRE"])
    path = tmp_path / "copia_frenosa.xlsx"
    book.save(path)
    book.close()
    server = ReynaServer(tmp_path / "espacios", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        _, space = request(base + "/api/workspaces", {"name": "Copia de prueba", "workbook_path": str(path)})
        wid = space["id"]
        common = {"FECHA": "20101228", "PER": "2010-12", "EMP": "FRE"}
        cases = [
            ("T14", "ALMACEN1", {"ALM": "ALM_FRE", "MON": "PEN", "IMP": "IGV"}, {"REC": "MAT_SW50", "CANT": "10", "CU_DOC": "2"}),
            ("T15", "SUPERV1", {"OBJ": "OT-FRENOSA-SW50-2010-12", "CEN": "PLANTA_FRE", "ALM": "ALM_FRE"}, {"REC": "MAT_SW50", "CANT": "1"}),
            ("T17", "CONTAB1", {"CEN": "PLANTA_FRE", "MON": "PEN"}, {"REC": "REC001", "MTO_DOC": "10"}),
            ("T18", "SUPERV1", {"OBJ": "OT-FRENOSA-SW50-2010-12", "ALM": "ALM_FRE", "AVA": "100"}, {"REC": "SW50", "CANT": "1"}),
            ("T19", "ALMACEN1", {"ALM": "ALM_FRE", "CEN": "PLANTA_FRE", "MOT": "DESMEDRO_SIN_ACTA"}, {"REC": "MAT_SW50", "CANT": "1"}),
            ("T20", "COMERC1", {"ALM": "ALM_FRE", "CLI": "MERCADO", "MON": "PEN"}, {"REC": "SW50", "CANT": "1", "PVU": "5"}),
        ]
        saved = tmp_path / "espacios" / wid / "libro.xlsx"
        for number, (code, user, head, line) in enumerate(cases, 1):
            _, config = request(base + f"/api/trx-campos?id={wid}&trx={code}")
            fields = {(f["nivel"], f["variable"]): f for f in config["campos"]}
            header = {**common, **head}
            for level, values in (("C", header), ("L", line)):
                for name, value in values.items():
                    field = fields[level, name]
                    if field["lista"]:
                        assert value in field["valores"], (code, name, value)
            status, result = request(base + f"/api/workspaces/{wid}/execute", {
                "transaction": code, "user": user, "request_id": f"guiado-{code}",
                "header": header, "lines": [line],
            })
            assert status == 200 and result["result"] == "OK", result
            assert result["version"] == number
            wb = load_workbook(saved, read_only=True, data_only=True)
            events = list(wb["EVENTO"].values)
            wb.close()
            columns = events[0]
            assert events[-1][columns.index("EVE_TRX")] == code
            assert events[-1][columns.index("EVE_USR")] == user
    finally:
        server.shutdown()
        thread.join()
        server.server_close()



def test_frenosa_periodos_tienen_fechas_finales_validas():
    """La fuente debería contener fechas reales; no se normalizan sin autorización."""
    from datetime import datetime
    book = load_workbook(ROOT / "casos/libros/frenosa.xlsx", read_only=True, data_only=True)
    rows = list(book["PERIODO"].values)
    book.close()
    columns = rows[0]
    invalid = []
    for row in rows[1:]:
        try:
            datetime.strptime(str(row[columns.index("PER_FIN")]), "%Y%m%d")
        except ValueError:
            invalid.append(row[columns.index("PER_COD")])
    assert not invalid, f"Fechas finales inválidas: {invalid}"
