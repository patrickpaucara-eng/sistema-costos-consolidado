"""Corre las pruebas de la auditoría MN 1 contra el motor real e imprime CONFIRMADO / SOSPECHA por prueba.

Uso:  python3.11 -I correr_auditoria.py <repo> [SERVITEC_sintetico.xlsx]
El repo debe tener fuente/DBD_Fuente.xlsx y casos/plantilla_dbd.xlsx. No modifica nada (todo en carpetas temporales).
Regla: test_S<n>_* afirma el comportamiento correcto → si FALLA, la sospecha queda CONFIRMADA; si pasa, sigue como SOSPECHA.
test_control_* debe pasar; si falla, la prueba de esa sospecha NO ES CONCLUYENTE.
"""
import os
import sys
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
if len(sys.argv) < 2:
    raise SystemExit(__doc__)
os.environ["AUDIT_REPO"] = str(Path(sys.argv[1]).resolve())
if len(sys.argv) > 2:
    os.environ["AUDIT_SERVITEC"] = str(Path(sys.argv[2]).resolve())
sys.path.insert(0, str(AQUI))


class _R(unittest.TextTestResult):
    def __init__(self, *a, **k):
        super().__init__(*a, **k); self.estado = {}

    def addSuccess(self, t): super().addSuccess(t); self.estado[t.id()] = "pasa"
    def addFailure(self, t, e): super().addFailure(t, e); self.estado[t.id()] = "falla"
    def addError(self, t, e): super().addError(t, e); self.estado[t.id()] = "error"


def main():
    suite = unittest.defaultTestLoader.discover(str(AQUI), pattern="test_S*.py")
    r = unittest.TextTestRunner(verbosity=1, resultclass=_R).run(suite)
    print("\nRESUMEN")
    malos_control = set()
    for tid, est in sorted(r.estado.items()):
        mod, nombre = tid.split(".")[0], tid.split(".")[-1]
        if nombre.startswith("test_control"):
            if est != "pasa": malos_control.add(mod)
            print(f"  {nombre:55} control {'OK' if est == 'pasa' else 'FALLA'}")
    for tid, est in sorted(r.estado.items()):
        mod, nombre = tid.split(".")[0], tid.split(".")[-1]
        if nombre.startswith("test_control"): continue
        if mod in malos_control: v = "NO CONCLUYENTE (falló su control)"
        elif est == "falla": v = "CONFIRMADO"
        elif est == "pasa": v = "SOSPECHA (no se reprodujo)"
        else: v = "ERROR DE LA PRUEBA"
        print(f"  {nombre:55} {v}")


if __name__ == "__main__":
    main()
