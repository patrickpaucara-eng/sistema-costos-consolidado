# OT-C05 · Paquete de ejecución

El empaquetado incorpora módulos, fuentes, datos, caso Frenosa y dependencias de Word; el humo verifica importación, reapertura, cálculo REAL de julio y exportación HTML. El ensayo Linux usó una copia temporal con C04, porque las órdenes aún están en PR separados.

## Cómo probar

Tras integrar C04 y C05 en una rama de entrega, ejecutar en Windows x64 `python tools/windows/build.py` con CPython 3.12.10, o ejecutar el workflow manual de GitHub Actions. Los pasos de entrega y prueba sin conexión están en `tools/windows/LEEME.md`.

## Pendiente

Falta producir y probar el EXE real en Windows y con Excel nativo; la disponibilidad del runner depende de GitHub. La validación de Linux usa proxies inutilizables y un directorio aislado, no una desconexión física. Ver `DIAGNOSTICO.md` para el SHA del binario y los límites.
