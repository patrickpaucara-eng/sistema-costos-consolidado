"""Publica los resultados de demostración (datos/resultados) con el MISMO camino que usa la aplicación: libro DBD
validado (casos/libros) → calcular → contrato sellado. Uso: python tools/publicar_resultados.py"""
import shutil, sys, tempfile
from pathlib import Path
R = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(R / "src"))
from reyna_local.calculo_local import calcular, catalogo  # noqa: E402

with tempfile.TemporaryDirectory() as d:
    n = 0
    for lib in catalogo(d):
        for per in lib["periodos"]:
            for s in ("REAL", "CONTABLE"):   # ESTIMADO retirado (decisión 25-nov): ver «precisión de la proyección»
                calcular(d, per, s, lib["id"]); n += 1
    for f in (Path(d) / "resultados").glob("*.json"):
        shutil.copy(f, R / "datos" / "resultados" / f.name)
print(n, "resultados publicados")
