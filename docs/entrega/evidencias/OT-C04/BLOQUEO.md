# OT-C04 · Bloqueo de cálculo reproducible

Base: `desarrollo/mono@d21459659e40ccb0e2f1059f9b325bff3b4fcc66`.

El generador `casos/frenosa/generar.py` requiere `datos/frenosa_supuestos/Gastos_Operativos_SUPUESTOS.csv`. El archivo no aparece en la revisión ni en los worktrees accesibles. Los 36 JSON publicados están presentes, pero no sustituyen los insumos que requiere generar el libro.

`PYTHONPATH=src /workspace/reyna-env/bin/python tools/verificar.py` devuelve `COMPUERTA: ROJA → pruebas`. La prueba existente `tests/test_analitica.py::test_tres_sintesis_cumplen_el_contrato[REAL]` falla al generar el caso con `FileNotFoundError` en ese CSV. También se reprodujo en `tests/test_frenosa_anual.py`.

Se necesita que Claude aporte y versione el CSV exacto usado para producir los JSON, con su procedencia. No se deben deducir los supuestos desde resultados agregados. Después se debe ejecutar la compuerta y continuar C04. C07 depende de C04; C05 y C06 también requieren la compuerta verde antes de abrir sus PR.

**Resuelto:** `desarrollo/mono@b05e6cd` incorporó el CSV y su procedencia. La rama fue rebasada sobre esa revisión.
