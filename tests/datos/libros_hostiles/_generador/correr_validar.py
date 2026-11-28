"""Arnés: ejecuta libro_dbd.validar() del repo del usuario sobre libros dados (no modifica el repo)."""
import sys, json
REPO_SRC, PLANTILLA = sys.argv[1], sys.argv[2]
sys.path.insert(0, REPO_SRC)
from pathlib import Path
import reyna_local.libro_dbd as B
B.PLANTILLA = Path(PLANTILLA)      # el repo ligero no trae casos/plantilla_dbd.xlsx
out = {}
for p in sys.argv[3:]:
    try:
        out[Path(p).name] = B.validar(p)
    except Exception as e:
        out[Path(p).name] = [f"EXCEPCIÓN {type(e).__name__}: {e}"]
print(json.dumps(out, ensure_ascii=False, indent=1))
