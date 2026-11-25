# -*- coding: utf-8 -*-
"""T14.1 (devolución a proveedor) y T16 (devolución del objeto al almacén) desde el formulario guiado, en copia de Frenosa."""
import json, threading
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from openpyxl import load_workbook
from reyna_local.__main__ import ReynaServer

ROOT = Path(__file__).resolve().parents[1]


def _req(url, body=None):
    data = None if body is None else json.dumps(body).encode()
    try:
        with urlopen(Request(url, data=data, headers={"Content-Type": "application/json"}), timeout=60) as r: return r.status, json.load(r)
    except HTTPError as e: return e.code, json.load(e)


def _kardex(path, mat):
    wb = load_workbook(path, read_only=True, data_only=True); rows = list(wb["KARDEX"].values); wb.close()
    h = rows[0]; return [dict(zip(h, r)) for r in rows[1:] if r[h.index("KDX_REC")] == mat]


def test_compra_devolucion_consumo_devolucion(tmp_path):
    srv = ReynaServer(tmp_path / "e", 0); t = threading.Thread(target=srv.serve_forever, daemon=True); t.start()
    base = f"http://127.0.0.1:{srv.server_port}"
    try:
        _, sp = _req(base + "/api/workspaces", {"name": "dev", "workbook_path": str(ROOT / "casos/libros/frenosa.xlsx")}); wid = sp["id"]
        libro = tmp_path / "e" / wid / "libro.xlsx"
        c = {"FECHA": "20101228", "PER": "2010-12", "EMP": "FRE"}
        for trx in ("T14.1", "T16"):
            s, cfg = _req(base + f"/api/trx-campos?id={wid}&trx={trx}"); assert s == 200 and cfg["campos"]
        pasos = [("T14", "ALMACEN1", {**c, "ALM": "ALM_FRE", "MON": "PEN", "IMP": "IGV"}, {"REC": "MAT_SW50", "CANT": "10", "CU_DOC": "2"}),
                 ("T14.1", "ALMACEN1", {**c, "ALM": "ALM_FRE", "CPB": "NC-001", "RUC": "20100000001"}, {"REC": "MAT_SW50", "CANT": "4"}),
                 ("T15", "SUPERV1", {**c, "OBJ": "OT-FRENOSA-SW50-2010-12", "CEN": "PLANTA_FRE", "ALM": "ALM_FRE"}, {"REC": "MAT_SW50", "CANT": "3"})]
        evs = []
        for i, (trx, u, h, l) in enumerate(pasos):
            s, r = _req(base + f"/api/workspaces/{wid}/execute", {"transaction": trx, "user": u, "request_id": f"d{i}", "header": h, "lines": [l]})
            assert s == 200, r
            wb = load_workbook(libro, read_only=True); evs.append(list(wb["EVENTO"].values)[-1][0]); wb.close()
        h16 = {**c, "OBJ": "OT-FRENOSA-SW50-2010-12", "CEN": "PLANTA_FRE", "ALM": "ALM_FRE", "EVE_ORI": evs[2]}
        s, r = _req(base + f"/api/workspaces/{wid}/execute", {"transaction": "T16", "user": "SUPERV1", "request_id": "d3", "header": h16, "lines": [{"REC": "MAT_SW50", "CANT": "1"}]})
        assert s == 200, r
        s, r = _req(base + f"/api/workspaces/{wid}/execute", {"transaction": "T16", "user": "SUPERV1", "request_id": "d4", "header": h16, "lines": [{"REC": "MAT_SW50", "CANT": "5"}]})
        assert s == 422                                     # no se devuelve más de lo consumido
        wb = load_workbook(libro, read_only=True); ev = list(wb["EVENTO"].values); wb.close()
        h = ev[0]; trx = [r[h.index("EVE_TRX")] for r in ev[-4:]]
        assert trx == ["T14", "T14.1", "T15", "T16"]           # el exceso de T16 no dejó evento (el kardex se valúa al cierre)
    finally:
        srv.shutdown(); t.join(); srv.server_close()
