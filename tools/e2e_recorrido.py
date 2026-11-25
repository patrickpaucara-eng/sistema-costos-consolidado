"""Recorrido de punta a punta por la API local (Frenosa y SERVITEC). Uso: python tools/e2e_recorrido.py"""
import json, sys, threading, tempfile, shutil
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from reyna_local.__main__ import ReynaServer
ROOT = Path(__file__).resolve().parents[1]; tmp = Path(tempfile.mkdtemp())
srv = ReynaServer(tmp, 0); threading.Thread(target=srv.serve_forever, daemon=True).start()
B = f"http://127.0.0.1:{srv.server_port}"; LOG = []
def q(m, url, body=None):
    d = None if body is None else json.dumps(body).encode()
    try:
        with urlopen(Request(B + url, data=d, method=m, headers={"Content-Type": "application/json"}), timeout=300) as r: return r.status, json.load(r)
    except HTTPError as e:
        try: return e.code, json.load(e)
        except Exception: return e.code, {}
def paso(n, esperado, ok, obtenido): LOG.append((n, esperado, "OK" if ok else "ERROR", str(obtenido)[:220]))
for emp in ("frenosa", "segundo"):
    s, r = q("POST", f"/api/calcular?sintesis=REAL&periodo={'2010-12' if emp=='frenosa' else '2025-07'}&empresa={emp}", {})
    paso(f"{emp}: calcular REAL", "200", s == 200, s if s == 200 else r)
    s, r = q("GET", f"/api/resultados?sintesis=REAL&periodo={'2010-12' if emp=='frenosa' else '2025-07'}&empresa={emp}")
    res = r if s == 200 else {}
    paso(f"{emp}: resultados", "200 con objetos y trazas", s == 200 and res.get("objetos") and res.get("trazas"), s)
    if emp == "segundo" and res:
        c = {o["codigo"][-11:-8]: o["costo_total"] for o in res["objetos"]}
        paso("SERVITEC julio REAL", "REB 22,975 / MPR 5,165", c.get("REB") == 22975 and c.get("MPR") == 5165, c)
    if res:
        s, r = q("POST", "/api/sello", {"resultados": res}); paso(f"{emp}: sello", "VIGENTE", s == 200 and "VIGENTE" in json.dumps(r), r)
        for t in ("resultados", "analitica", "proyeccion", "html", "informe", "presentacion"):
            s, r = q("POST", f"/api/exportar?tipo={t}", {"resultados": res}); paso(f"{emp}: exportar {t}", "201", s == 201, s if s == 201 else r)
    s, r = q("GET", f"/api/periodos?empresa={emp}&sintesis=REAL&desde={'2010-07-01' if emp=='frenosa' else '2025-06-01'}&hasta={'2010-08-31' if emp=='frenosa' else '2025-07-31'}&grano=bimestre")
    paso(f"{emp}: periodos bimestre", "200", s == 200, s if s == 200 else r)
    s, r = q("GET", f"/api/proyeccion?empresa={emp}&meses=6"); paso(f"{emp}: proyección granular 6 meses", "200 con 6 meses", s == 200 and len(r.get("meses", [])) == 6, s if s == 200 else r)
    s, r = q("POST", "/api/aprendizaje/calibrar", {"empresa": emp}); paso(f"{emp}: calibrar aprendizaje", "200", s == 200, s if s == 200 else r)
    s, r = q("GET", f"/api/aprendizaje?empresa={emp}"); paso(f"{emp}: ver aprendizaje", "200", s == 200, s if s == 200 else r)
    acts = [a["codigo"] for a in res.get("actividades", [])][:2]
    s, r = q("POST", "/api/cotizar", {"empresa": emp, "actividades": {a: 1 for a in acts}, "materiales": {}, "precio_mercado": 5000, "margen_objetivo": 0.3})
    paso(f"{emp}: cotizar pedido especial", "200", s == 200, s if s == 200 else r)
s, r = q("GET", "/api/cierres?empresa=frenosa&usuario=COSTOS1"); paso("frenosa: ver cierres", "200", s == 200, s if s == 200 else r)
print(json.dumps(LOG, ensure_ascii=False, indent=0))
srv.shutdown(); shutil.rmtree(tmp, ignore_errors=True)
