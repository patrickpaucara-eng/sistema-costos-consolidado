# Integración del piloto 0.1.0

Verificado el 18 de noviembre de 2026, hora de Lima, en Linux/Python 3.12.14. Rama de entrega: `desarrollo/capacidad-inicial`.

- El coordinador ejecutó las nueve pruebas de `tests/test_capacidad_inicial.py`: nueve aprobadas, ninguna omitida. Se conserva la salida en `pruebas-excel.log`. La revisión independiente conserva otra ejecución y sus límites.
- Se construyó `reyna_local-0.1.0-py3-none-any.whl` con `pip wheel --no-deps --no-build-isolation .`, se instaló en un directorio separado con `pip install --no-deps --target ...` y se ejecutó `python -m reyna_local --help` desde fuera del repositorio. Las dependencias ya estaban instaladas en ese entorno. Esto no acredita instalación sin Internet desde cero ni Windows.
- Los dos ZIP congelados se cotejaron archivo a archivo con `git show` de sus revisiones: cinco archivos para main y seis para Ola 1, idénticos. También aprobaron sus manifiestos SHA-256.
- La fixture aprobó su manifiesto y el motor coincide byte a byte con el original Ola 1. Las revisiones y hashes están en `referencia/ORIGEN_MOTOR.md`.
- Se comprobó que `src`, `tests` y `pyproject.toml` no contienen implementación SQLite. No se modificó ni ejecutó VBA.
- El recorrido Chromium y la navegación del HTML actualizado se registran en `RECORRIDO_HTML.md`. El catálogo y JavaScript del mapa histórico permanecen intactos.

`rendimiento-excel.json` conserva la medición directa del coordinador: importación, tres operaciones, lectura con nueva instancia y reintento. Es una sola corrida con un libro pequeño. La herramienta `tools/medir_piloto.py` permite repetir ese caso, genera JSON y elimina sus copias temporales. Puede devolver tiempos y tamaños diferentes. La nueva instancia no equivale a un reinicio del sistema operativo; la reapertura entre procesos se comprueba en las pruebas HTTP.

Desde la raíz, después de instalar:

```sh
python -m unittest discover -s tests -v
PYTHONPATH=src python tools/medir_piloto.py
sha256sum -c tests/fixtures/ola1/SHA256SUMS
sha256sum -c referencia/vba-congelado/SHA256SUMS
```

El hito conserva código, datos de prueba, evidencia y guía en Git. Las carpetas operativas y los libros gestionados se excluyen del control de versiones. La aceptación se limita a CAP-01–CAP-05; los límites abiertos del registro de capacidades siguen vigentes.
