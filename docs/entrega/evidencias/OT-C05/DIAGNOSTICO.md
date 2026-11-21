# OT-C05 · Diagnóstico inicial

Base `desarrollo/mono@b05e6cd`. El empaquetador actual copia e instala únicamente `src/reyna_local`, mientras los cálculos del caso dependen de `src/metodos`, `src/analitica*`, `src/casos`, módulos superiores de `src`, `fuente`, `casos` y `datos`. Su archivo de requisitos tampoco incluye las dependencias fijadas de Word incorporadas al proyecto. El humo actual valida interfaz, importación y reapertura, pero no llama a `/api/calcular` ni a `/api/exportar`.

C04 está en un PR independiente y no existe en esta base. Para verificar un binario que calcule será necesario preparar una copia temporal de integración con C04, sin fusionar ramas remotas. Debe prestarse especial atención a la ubicación de `calculo_local.py`: el código de C04 obtiene la raíz con `Path(__file__).parents[2]`, mientras PyInstaller puede ubicar el módulo en una estructura distinta. Se debe probar el binario real y corregir esa resolución antes de entregar.

## Ensayo del 21 de noviembre

En una copia temporal se superpusieron los archivos de C04 (`7588676`) al código de C05. PyInstaller 6.13.0 generó en Linux un binario SHA-256 `b6b26cc1d71273bdf5ddd400fcfef7185f98d47a9aaefcae8f43057f4448318f`. El humo con rutas y `PATH` aislados y proxies inservibles verificó interfaz idéntica a la fuente, importación/reapertura, cálculo REAL julio (ventas S/ 888.730) y exportación de HTML. El primer intento detectó que faltaban archivos de `metodos/casos`; se añadió su inclusión. Una compilación con una versión instalada distinta detectó HTML incorrecto; se repitió apuntando al árbol temporal correcto.

La salida fue `Prueba local aprobada. HTML, API, importación, cálculo REAL, exportación y reapertura del libro.` Esto no prueba un EXE de Windows ni una desconexión física. Las ramas no fueron fusionadas; el flujo Windows debe ejecutarse tras integrar C04 y C05.
