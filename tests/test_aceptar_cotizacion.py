# -*- coding: utf-8 -*-
"""OT-C31 punto 3: aceptar una cotización abre la OT con su costo proyectado congelado (T09 + T13) en UNA escritura.
Si la segunda transacción falla, el libro no cambia (atómico)."""
import hashlib, json, threading
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from openpyxl import load_workbook
from reyna_local.__main__ import ReynaServer

ROOT = Path(__file__).resolve().parents[1]


def _q(base, m, u, b=None):
    try:
        with urlopen(Request(base + u, data=None if b is None else json.dumps(b).encode(), method=m, headers={"Content-Type": "application/json"}), timeout=60) as r:
            return r.status, json.load(r)
    except HTTPError as e:
        return e.code, json.load(e)


def _filas(libro, hoja):
    wb = load_workbook(libro, read_only=True); r = list(wb[hoja].values); wb.close()
    return [dict(zip(r[0], x)) for x in r[1:]]


def test_aceptar_abre_ot_con_costo_proyectado_y_es_atomico(tmp_path, monkeypatch):
    srv = ReynaServer(tmp_path / "e", 0); t = threading.Thread(target=srv.serve_forever, daemon=True); t.start(); B = f"http://127.0.0.1:{srv.server_port}"
    try:
        _, sp = _q(B, "POST", "/api/workspaces", {"name": "c", "workbook_path": str(ROOT / "casos/libros/frenosa.xlsx")}); w = sp["id"]
        libro = tmp_path / "e" / w / "libro.xlsx"
        base = dict(user="JCOSTOS", periodo="2010-12", fecha="20101228", producto="SW50", cantidad=100, cliente="MERCADO", monto=1234.5, huella="abc")
        # Decisión del dueño 26-nov: el código lo asigna el sistema, ignorando objeto.
        from reyna_local import motor_espejo as M
        original = M.Motor.ejecutar
        monkeypatch.setattr(M.Motor, "ejecutar", lambda self, trx, *a, **k: "ERROR: simulado" if trx == "T13" else original(self, trx, *a, **k))
        s, r = _q(B, "POST", f"/api/workspaces/{w}/aceptar-cotizacion", {**base, "request_id": "a1", "objeto": "OT-NUEVA-000"})
        assert s == 422 and "T13" in r["error"]                          # T09 pasó, T13 falló → nada se escribe
        assert not _filas(libro, "ESTIMACION") and not [x for x in _filas(libro, "TARIFA") if x["TAR_TIPO"] == "EST"]
        monkeypatch.setattr(M.Motor, "ejecutar", original)
        s, r = _q(B, "POST", f"/api/workspaces/{w}/aceptar-cotizacion", {**base, "request_id": "a2", "objeto": "IGNORAR"})
        assert s == 200, r
        assert r["objeto"] == "OT-FRE-SW50-0001"
        est = _filas(libro, "ESTIMACION"); ot = [o for o in _filas(libro, "OBJETO") if o["OBJ_NUM"] == "OT-FRE-SW50-0001"]
        assert len(est) == 1 and est[0]["EST_ESTADO"] == "ACEPTADA" and est[0]["EST_OBJ"] == "OT-FRE-SW50-0001"
        assert len(ot) == 1 and ot[0]["OBJ_PRO"] == "SW50" and float(ot[0]["OBJ_CST_PLAN"]) == 1234.5 and ot[0]["OBJ_EST"] == "A"
        assert [x["TAR_REC"] for x in _filas(libro, "TARIFA") if x["TAR_TIPO"] == "EST"] == ["MAT_SW50"]
        s2, r2 = _q(B, "POST", f"/api/workspaces/{w}/aceptar-cotizacion", {**base, "request_id": "a2", "objeto": "OT-FRE-SW50-0001"})
        assert s2 == 200 and r2 == r                                     # idempotente por identificador
        s3, r3 = _q(B, "POST", f"/api/workspaces/{w}/aceptar-cotizacion", {**base, "request_id": "a3"})
        assert s3 == 200 and r3["objeto"] == "OT-FRE-SW50-0002"
    finally:
        srv.shutdown(); t.join(); srv.server_close()
