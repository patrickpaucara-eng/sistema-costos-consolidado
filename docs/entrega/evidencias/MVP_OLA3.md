# Evidencia de aceptación técnica · MVP Ola 3

**Fecha:** 19 de noviembre de 2026 (hora de Lima).

**Rama:** `desarrollo/mvp-ola3`; base `desarrollo/capacidad-inicial@16c419f`.

**Fuente del motor y fixture:** revisión histórica `desarrollo/ola1@cac2501d9f712655dda466d216dc5bff2dd446a5`, ejecutada solo en copias.


## Resultado

La ruta terminó desde la interfaz HTML: se importó una copia de `tests/fixtures/ola1/Sistema_Costos.xlsx`, se registraron dos compras T14 y un consumo T15, y se cerró el periodo B/2026-04. La página mostró T23.1, T23.2, T23.3, T23.5 y T23.9 como correctas, sin errores de JavaScript. Se generó automáticamente el identificador de cierre.

El resultado observado en la misma fixture fue 400 unidades restantes de CAJA4KG en ALM1, empresa B, con costo unitario S/ 3,054 y saldo S/ 1.221,60. El libro marcó 2026-04 como cerrado. Este valor de existencia corresponde al caso aritmético de compras y consumo; **no** es un oráculo de costo integral de la orden ni de sus asientos.

## Atomicidad técnica del cierre

La cadena configurada se procesa sobre tablas copiadas en memoria. La fixture clasifica T23.1, T23.2, T23.3, T23.5 como `OFICIAL` y T23.9 como `CIERRE`; T23.0 está clasificada como `ESTADISTICA`. Al completar, el servicio escribe un XLSX temporal, guarda un respaldo de la versión anterior y sustituye el libro una sola vez; la versión del espacio avanza por los pasos confirmados. Al fallar, se conserva el estado de negocio y la versión previos. El rechazo sí agrega un recibo `RECEIPTS`, por lo que el mismo identificador y contenido devuelve el mismo resultado.

Se inyectó una excepción `RuntimeError` durante T23.3. La respuesta fue 422, el intento quedó registrado y el reintento devolvió el mismo 422. Se compararon todas las tablas del libro salvo `META` y `RECEIPTS`; ninguna tabla de negocio cambió. La versión quedó igual.

Esto demuestra persistencia de la cadena de pasos como unidad técnica; **no** demuestra que todos los pasos produzcan cuentas correctas. D9 (un solo escritor por cuenta), conciliación contable, costo integral ORIA, flete/T14.2 y reexpresión D14 están pendientes.

El diagnóstico recuperado de `desarrollo/deuda@0b8f63c` precisa D9: enumera siete `CTA_*`, detecta de uno a siete servicios escritores por tabla y constata que el cierre que publica `RESULTADO_METODO` no escribe esas cuentas. Sus 14 pruebas estrictas documentan escritor único y cuadre por cada tabla. La función histórica `correr_o1()` se ejecutó en una copia temporal de solo lectura para exportar 119 valores calculados en memoria; no se escribieron cuentas en el XLSX ni se comparó una tabla `RESULTADO_METODO` persistida, porque O-1 no trae las hojas CTA. La evidencia, claves, sumas, diferencias de grano y límites están en [matriz y caso D9](D9_MATRIZ_Y_CASO.md) y [CSV de referencia](D9_CONTROL_O1.csv). El código de escritores y las pruebas recuperadas se conservaron, pero no se integraron; las 14 pruebas no se ejecutaron en este incremento.

## Aislamiento empresarial del piloto

La importación rechaza un libro cuando detecta usuarios con permisos T14/T15 en más de una empresa. Una operación que declare `EMP` distinta de la empresa del espacio se rechaza antes de modificar el negocio. Son controles preventivos de alcance; no equivalen a una prueba completa de aislamiento interno para todas las tablas y métodos.

## Verificaciones ejecutadas

| Verificación | Resultado |
|---|---|
| `python -m unittest discover -s tests -v` con Python 3.12 | 13 pruebas aprobadas en 36,799 s; incluye cierre exitoso, reintento, fallo inyectado, guardia empresarial, concurrencia y preservación del XLSX. |
| Ejecución real desde Chromium usando el wheel instalado | Importación, T14 × 2, T15, aviso de uso exclusivo con copia de prueba, cierre con cinco pasos correctos y cero errores de página. El servidor se ejecutó fuera del checkout. |
| `node --check` sobre el script de `src/reyna_local/web/index.html` | Sintaxis JavaScript aprobada. |
| Empaquetado e instalación aislada | Candidato `reyna_local-0.2.0-py3-none-any.whl` construido; SHA-256 `2c01a1f447d54d6631c9920c279b496db22a36d68cba106851449fd5d9b46054`. Instalado fuera del checkout y `python -m reyna_local --help` respondió; el HTML vino dentro del wheel y el recorrido completo pasó desde ese paquete. Las dependencias ya estaban disponibles. |
| Manifiesto de fuentes de Ola 3 | Los cuatro Markdown conservados verifican con `sha256sum -c`. |

Las pruebas usan copias temporales de la fixture; no escriben en el repositorio original ni requieren Excel/VBA. Los 13 tests cubren más que la cadena de cierre; no deben leerse como 13 pruebas metodológicas independientes.

## Reproducción automatizada

Desde la raíz del repositorio, con dependencias instaladas:

```sh
python -m unittest discover -s tests -v
```

El test `test_cierre_oficial_guarda_una_vez_y_reintenta` ejercita el cierre por API y `test_cierre_fallido_no_persiste_pasos_parciales` inyecta la excepción en T23.3. La ruta HTML fue recorrida con Chromium en un directorio temporal, usando la misma fixture. El [manifiesto de los documentos de Claude](../../fuentes/claude/ola3/SHA256SUMS) se verifica desde la raíz mediante:

```sh
sha256sum -c docs/fuentes/claude/ola3/SHA256SUMS
```

## Fuera de esta aceptación

- Excel nativo en Windows, Excel abierto durante el servicio, corte físico y restauración tras pérdida del disco.
- Cuadre de `CTA_*`, D9, costo integral de orden por un oráculo ORIA, flete/T14.2, D14, productos conjuntos y costo financiero.
- Aislamiento demostrable para todas las empresas, autenticación empresarial, concurrencia de operadores y volumen real.
- Publicación inmutable por fecha, rendimiento de varios periodos y aprendizaje autónomo.

No se ha aceptado el producto para uso empresarial oficial. El alcance activo y sus siguientes puertas constan en [REGISTRO_CAPACIDADES.md](../REGISTRO_CAPACIDADES.md) y [PLAN_MVP_Y_PENDIENTES.md](../PLAN_MVP_Y_PENDIENTES.md).
