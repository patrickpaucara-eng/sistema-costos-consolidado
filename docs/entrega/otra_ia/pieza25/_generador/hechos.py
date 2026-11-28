"""Calcula las cifras que cita MONOGRAFIA_1_textos.docx (para no escribir ninguna a mano)."""
import json, sys, tempfile, pathlib
REPO, LIBRO = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
sys.path.insert(0, str(REPO / "src"))
from openpyxl import load_workbook
wb = load_workbook(LIBRO, read_only=True)
trx = [r for r in wb["TRX"].iter_rows(min_row=2, values_only=True) if r[0]]
tl = [r for r in wb["TABLAS_LOGICAS"].iter_rows(min_row=2, values_only=True) if r[0]]
rr = [r for r in wb["REGLA_REPARTO"].iter_rows(min_row=2, values_only=True) if r[0]]
H = {"trx_total": len(trx), "trx_online": sum(1 for r in trx if r[2] == "ONLINE"), "trx_batch": sum(1 for r in trx if r[2] == "BATCH"),
     "tablas_logicas": len(tl), "hojas_libro": len(wb.sheetnames), "reglas_reparto_servitec": len(rr),
     "etapas_servitec": sorted({r[0] for r in rr})}
def lineas(p): return len((REPO / "src" / p).read_text(encoding="utf-8").splitlines())
H["lineas"] = {p: lineas(p) for p in ["reyna_local/libro_dbd.py", "reyna_local/flujo.py", "metodos/reparto_etapas.py",
               "reyna_local/resultados.py", "reyna_local/contrato.py", "reyna_local/calculo_local.py", "reyna_local/motor_espejo.py",
               "reyna_local/store.py", "reyna_local/__main__.py", "reyna_local/exportar.py", "reyna_local/decidir.py"]}
H["py_reyna_local"] = len(list((REPO / "src/reyna_local").glob("*.py")))
H["py_metodos"] = len(list((REPO / "src/metodos").glob("*.py")))
import reyna_local.calculo_local as CL
c = pathlib.Path(tempfile.mkdtemp())
f, e = CL.registrar(c, LIBRO.read_bytes(), LIBRO.name)
r = CL.calcular(c, "2025-07", "REAL", f["id"])
H["julio"] = {o["producto"]: {k: o[k] for k in ("cantidad", "md", "mod", "cif", "admin", "gasto_venta", "financiero", "perdida", "ocio", "costo_total", "costo_unitario", "ingreso", "margen")} for o in r["objetos"]}
H["julio_kpi"] = r["kpi"]
print(json.dumps(H, ensure_ascii=False, indent=1))
