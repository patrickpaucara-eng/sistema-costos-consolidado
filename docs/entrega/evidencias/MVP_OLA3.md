# Evidencia de aceptación técnica · MVP Ola 3

**Fecha:** 20 de noviembre de 2026 (hora de Lima).

**Rama:** `desarrollo/mvp-ola3`; base `desarrollo/capacidad-inicial@16c419f`.

**Fuente del motor y fixture:** revisión histórica `desarrollo/ola1@cac2501d9f712655dda466d216dc5bff2dd446a5`, ejecutada solo en copias.


## Resultado

La ruta terminó desde la interfaz HTML: se importó una copia de `tests/fixtures/ola1/Sistema_Costos.xlsx`, se registraron dos compras T14 y un consumo T15, y se cerró el periodo B/2026-04. La página mostró T23.1, T23.2, T23.3, T23.5 y T23.9 como correctas, sin errores de JavaScript. Se generó automáticamente el identificador de cierre.

El resultado observado en la misma fixture fue 400 unidades restantes de CAJA4KG en ALM1, empresa B, con costo unitario S/ 3,054 y saldo S/ 1.221,60. El libro marcó 2026-04 como cerrado. Este valor de existencia corresponde al caso aritmético de compras y consumo; **no** es un oráculo de costo integral de la orden ni de sus asientos.

## Atomicidad técnica del cierre

La cadena configurada se procesa sobre tablas copiadas en memoria. La fixture clasifica T23.1, T23.2, T23.3, T23.5 como `OFICIAL` y T23.9 como `CIERRE`; T23.0 está clasificada como `ESTADISTICA`. Al completar, el servicio escribe un XLSX temporal, guarda un respaldo de la versión anterior y sustituye el libro una sola vez; la versión del espacio avanza por los pasos confirmados. Al fallar, se conserva el estado de negocio y la versión previos. El rechazo sí agrega un recibo `RECEIPTS`, por lo que el mismo identificador y contenido devuelve el mismo resultado.

Se inyectó una excepción `RuntimeError` durante T23.3. La respuesta fue 422, el intento quedó registrado y el reintento devolvió el mismo 422. Se compararon todas las tablas del libro salvo `META` y `RECEIPTS`; ninguna tabla de negocio cambió. La versión quedó igual.

Esto demuestra persistencia de la cadena de pasos como unidad técnica; **no** demuestra que todos los pasos produzcan cuentas correctas. La validación del contrato de escritura por evento y la conciliación contable D9, el costo integral ORIA, el flete/T14.2 y la reexpresión D14 siguen pendientes.

El diagnóstico recuperado de `desarrollo/deuda@0b8f63c` precisa D9: enumera siete `CTA_*`, detecta de uno a siete servicios escritores por tabla y constata que el cierre que publica `RESULTADO_METODO` no escribe esas cuentas. Sus 14 pruebas estrictas documentan escritor único y cuadre por cada tabla. La función histórica `correr_o1()` se ejecutó en una copia temporal de solo lectura para exportar 119 valores calculados en memoria; no se escribieron cuentas en el XLSX ni se comparó una tabla `RESULTADO_METODO` persistida, porque O-1 no trae las hojas CTA. La evidencia, claves, sumas, diferencias de grano y límites están en [matriz y caso D9](D9_MATRIZ_Y_CASO.md) y [CSV de referencia](D9_CONTROL_O1.csv). El código de escritores y las pruebas recuperadas se conservaron, pero no se integraron; las 14 pruebas no se ejecutaron en este incremento.

### D9 · semántica MCD y regresión de ámbito

El propietario resolvió seguir el MCD: los eventos actualizan transaccionalmente los saldos de cuenta que afectan; el cierre los valida y concilia, sin regenerar las mismas cuentas a partir de un agregado. Se conserva la diferencia histórica: D-I0b-1 había clasificado esas tablas como suplementarias de cierre. La decisión, su fundamento y sus límites están en [D9_DECISION_SEMANTICA.md](D9_DECISION_SEMANTICA.md).

En el motor Python, los métodos DBD ya se ejecutan por operaciones genéricas. Se hizo que las mutaciones `CTA_*` identifiquen la columna `*_EMP` desde el esquema y solo reutilicen/actualicen filas de la empresa del evento; las filas nuevas reciben esa empresa aunque la MCA omita la empresa de la clave. La prueba carga filas A y B con claves de negocio iguales y confirma que A no se altera. El mismo caso T15 compara las filas persistidas de tres cuentas contra un esperado decimal independiente en [caso_t15_eventos.json](../../../tests/fixtures/d9/caso_t15_eventos.json), repite el `request_id` y compara las siete cuentas. Otra prueba inyecta un fallo tras la escritura de `CTA_OBJ_REC` y confirma que las cuentas y el inventario/evento se revierten. Una prueba directa de `m_ACTUALIZAR` verifica que solo cambia B aunque la clave DBD omita empresa. El reintento del cierre también compara las siete hojas CTA antes y después.

El caso T15 concilia parcialmente `CTA_OBJ_PER`, `CTA_OBJ_REC` y `CTA_GASTO` por evento con aritmética separada. Se añadieron casos independientes para T17 (`CTA_CENTRO`/`CTA_FUNCION`), T19 (`CTA_GASTO`) y T20 (`CTA_VTA_PER`), con esperados y filas persistidas. T20 usa un saldo inicial sintético; ninguno de estos casos concilia una fila `RESULTADO_METODO` de la misma corrida ni es un oráculo ORIA. D9 sigue bloqueado como salida oficial hasta resolver las dimensiones fuente, los casos de cierre T23.5/T23.3 y la conciliación integral.

El servicio y el formulario JSON habilitan explícitamente T14, T15, T17, T19 y T20. T16 y las operaciones por lotes siguen fuera del piloto. La fuente, los cálculos independientes y las limitaciones de los tres nuevos casos constan en [D9_CUADRE_EVENTOS.md](D9_CUADRE_EVENTOS.md).

## Aislamiento empresarial del piloto

La importación rechaza un libro cuando detecta usuarios con permisos para cualquiera de las transacciones habilitadas del piloto (T14/T15/T17/T19/T20) en más de una empresa. Una operación que declare `EMP` distinta de la empresa del espacio se rechaza antes de modificar el negocio. Son controles preventivos de alcance; no equivalen a una prueba completa de aislamiento interno para todas las tablas y métodos.

## Verificaciones ejecutadas

| Verificación | Resultado |
|---|---|
| `/workspace/reyna-env/bin/python -m unittest discover -s tests -v` con Python 3.12 | 20 pruebas aprobadas en 68,423 s; incluye cierre y reintento, fallo inyectado, aislamiento CTA A/B en acumulación y actualización, casos independientes T15/T17/T19/T20, concurrencia y preservación del XLSX. |
| Ejecución real desde Chromium usando el wheel instalado | Importación, T14 × 2, T15, aviso de uso exclusivo con copia de prueba, cierre con cinco pasos correctos y cero errores de página. El servidor se ejecutó fuera del checkout. |
| `node --check` sobre el script de `src/reyna_local/web/index.html` | Sintaxis JavaScript aprobada. |
| Empaquetado e instalación aislada | Candidato `reyna_local-0.2.0-py3-none-any.whl` construido; SHA-256 `2c01a1f447d54d6631c9920c279b496db22a36d68cba106851449fd5d9b46054`. Instalado fuera del checkout y `python -m reyna_local --help` respondió; el HTML vino dentro del wheel y el recorrido completo pasó desde ese paquete. Las dependencias ya estaban disponibles. |
| Manifiesto de fuentes de Ola 3 | Los cuatro Markdown conservados verifican con `sha256sum -c`. |

Las pruebas usan copias temporales de la fixture; no escriben en el repositorio original ni requieren Excel/VBA. Los 20 tests cubren más que la cadena de cierre; no deben leerse como 20 pruebas metodológicas independientes.

## Reproducción automatizada

Desde la raíz del repositorio, con dependencias instaladas:

```sh
python -m unittest discover -s tests -v
```

`test_d9_event_accounts.py` comprueba aislamiento, repetición, reversión y casos T15/T17/T19/T20 con esperados independientes. El test `test_cierre_oficial_guarda_una_vez_y_reintenta` ejercita el cierre por API y `test_cierre_fallido_no_persiste_pasos_parciales` inyecta la excepción en T23.3. La ruta HTML fue recorrida con Chromium en un directorio temporal, usando la misma fixture; esa evidencia visual anterior cubrió T14/T15 y el cierre, mientras la nueva prueba API verifica el límite T17/T19/T20 y el rechazo de T16. El [manifiesto de los documentos de Claude](../../fuentes/claude/ola3/SHA256SUMS) se verifica desde la raíz mediante:

```sh
sha256sum -c docs/fuentes/claude/ola3/SHA256SUMS
```

## Fuera de esta aceptación

- Excel nativo en Windows, Excel abierto durante el servicio, corte físico y restauración tras pérdida del disco.
- Conciliación integral de `CTA_*`/D9 con `RESULTADO_METODO`, costo integral de orden por un oráculo ORIA, flete/T14.2, D14, productos conjuntos y costo financiero. El caso parcial T15 está documentado arriba.
- Aislamiento demostrable para todas las empresas, autenticación empresarial, concurrencia de operadores y volumen real.
- Publicación inmutable por fecha, rendimiento de varios periodos y aprendizaje autónomo.

No se ha aceptado el producto para uso empresarial oficial. El alcance activo y sus siguientes puertas constan en [REGISTRO_CAPACIDADES.md](../REGISTRO_CAPACIDADES.md) y [PLAN_MVP_Y_PENDIENTES.md](../PLAN_MVP_Y_PENDIENTES.md).
