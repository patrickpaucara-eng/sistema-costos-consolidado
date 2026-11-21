"""Compuerta única (Karpathy/SpaceX: revisión automática). Uso: python tools/verificar.py [--rapido]
Falla (código ≠ 0) si algo se rompe. Nadie entrega un cambio sin pasarla: ni Claude, ni Codex."""
import subprocess, sys, json, pathlib
RAIZ = pathlib.Path(__file__).resolve().parents[1]
pasos = [("pruebas", [sys.executable, "-m", "pytest", "tests", "-q", "-x"] + (["-m", "not lento"] if "--rapido" in sys.argv else []))]
fallos = []
for nombre, cmd in pasos:
    r = subprocess.run(cmd, cwd=RAIZ, env={**__import__("os").environ, "PYTHONPATH": str(RAIZ / "src")}, capture_output=True, text=True)
    print(f"[{'OK' if r.returncode == 0 else 'FALLA'}] {nombre}: {r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr.strip()[-300:]}")
    if r.returncode: fallos.append(nombre)
# contrato de resultados: el ejemplo debe cumplir el esquema
from importlib import util
spec = util.spec_from_file_location("contrato", RAIZ / "src" / "reyna_local" / "contrato.py"); c = util.module_from_spec(spec); spec.loader.exec_module(c)
errs = c.validar(json.loads((RAIZ / "tests/fixtures/contrato/resultados_ejemplo.json").read_text(encoding="utf-8")))
print(f"[{'OK' if not errs else 'FALLA'}] contrato de resultados: {errs or 'cumple'}")
if errs: fallos.append("contrato")
print("COMPUERTA:", "VERDE" if not fallos else "ROJA → " + ", ".join(fallos))
sys.exit(1 if fallos else 0)
