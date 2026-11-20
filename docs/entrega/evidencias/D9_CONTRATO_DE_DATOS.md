# D9 · contrato de datos de las cuentas

**Fecha:** 20 de noviembre de 2026 (hora de Lima).

**Estado:** borrador por servicio y campo; resuelto para un caso T15 parcial, no aprobado como contrato universal.

## Alcance y fuentes

Este inventario combina la semántica elegida por el propietario conforme al MCD con las tablas y servicios declarados en `DBD_4c_Servicios_Datos` y `DBD_4d_Transacciones` de `DBD_Fuente.xlsx` (SHA-256 `479186097f106f845c51da794cdf4e43fd3a4376c6617e1ca6ee281e87980456`), más la configuración `MET`, `MCA`, `FRM`, `TIPO_CAMBIO` y `TABLAS_LOGICAS` de la fixture `Sistema_Costos.xlsx` (SHA-256 `43c9170c04b23e678de7abf7bab39f43c4251ea14695b351d884639ea972be40`).

El MCD §6.2.1 describe el saldo de cuenta como resultado neto de eventos (p. 194 del PDF); el DBD dice que las tablas maestras mantienen saldos y reciben actualizaciones transaccionales para los eventos que las afectan (p. 75). Esta guía deja constancia de qué especifica el modelo actual y qué falta acordar. No equipara un nombre de columna con una política contable aprobada.

## Reglas transversales

| Propiedad | Contrato observado / regla de trabajo | Límite que falta cerrar |
|---|---|---|
| Semántica | Cada movimiento aceptado actualiza los saldos de cuenta que afectan. El cierre verifica y concilia. `CTA_ACTOR` describe comportamiento, no costo. | La conciliación integral de todos los servicios y de todos los cierres todavía no se probó. |
| Empresa e identidad | El saldo pertenece a una empresa; su columna termina en `_EMP`. Para el grano lógico se incorpora empresa a la clave aunque algunas claves MCA/`CLAVE_COMPUESTA` la omitan. El motor Python filtra la empresa del evento. | `CLAVE_COMPUESTA` de la fixture omite EMP para `CTA_OBJ_REC` y `CTA_GASTO`. El libro no impone unicidad física; duplicados de la misma clave dentro de una empresa requieren detección y política de reparación. |
| Periodo | Las columnas `*_PER` identifican el periodo del saldo. Operaciones en línea reciben `PER`; los servicios de cierre usan el periodo seleccionado por la cadena. | Validar cada servicio de ajuste tardío, devolución y reapertura para que el periodo de efecto y el periodo de origen no se confundan. |
| Moneda | Los importes de cuenta deben estar en la moneda funcional de la empresa (`EMPRESA.EMP_MON_FUN`); las tablas CTA no guardan columna de moneda. T14 convierte desde la moneda del documento usando `TIPO_CAMBIO`; el caso T15 usa PEN para la empresa B. | La moneda de salida y el tipo de cambio efectivo deben quedar verificados por cada fuente de importe, incluidos gasto declarado, función, centro y venta. |
| Agregación y signo | `MCA` define `SUMA`, `RESTA` o `ASIGNA`. SUMA acumula impactos positivos; RESTA modela las devoluciones configuradas; ASIGNA guarda una medida o clasificación del periodo. `DIF_VEN` debe conservar su signo en el ajuste de costo de ventas. | No hay política universal para correcciones, reversas, repetición de lotes o reapertura que cubra los siete dominios. |
| Precisión | La precisión proviene de cada fórmula DBD: en la fixture `M-F-ING` redondea costo unitario convertido a 4 decimales y monto de línea a 2; `M-F-CPU` calcula valor/cantidad; `M-F-EXCESO` redondea cantidad permitida a 4 y pérdida a 2. | No hay precisión global definida por cuenta. Las demás fórmulas requieren un inventario campo por campo antes de fijar conciliaciones generales. |
| Trazabilidad | `BITACORA` registra tabla, fila, columna, valor anterior/nuevo y número de log. El log identifica la transacción. | No conserva un vínculo estable directo entre cada cambio de CTA, `EVE_NUM`/`LIN_NUM` y `MET_COD`; el contrato causal y su consulta quedan pendientes. |

## Contrato observado por cuenta

### `CTA_ACTOR` · comportamiento del actor

- **Grano lógico:** actor + periodo + empresa (`CAC_ACT`, `CAC_PER`, `CAC_EMP`).
- **Campos:** `CAC_N` cuenta hechos; `CAC_TARDE`, `CAC_RECH` y `CAC_VARPRE` acumulan medidas del evento T21 (`M-ACU-CAC`); `CAC_IND` y `CAC_TIP` se asignan al calificar el actor en T23.8 (`M-ACT-CAC`).
- **Moneda/unidad:** no es una cuenta monetaria de costo. La unidad y escala de `CAC_VARPRE`, el dominio de `CAC_IND`/`CAC_TIP` y su fuente deben definirse con el caso de comportamiento.
- **Reversa:** el inventario DBD no muestra una operación inversa emparejada para todos estos atributos. Definir corrección sin borrar el hecho fuente. Excluida de la conciliación de costos.

### `CTA_CENTRO` · actividad y saldo del centro

- **Grano lógico:** centro + periodo + empresa (`CCE_CEN`, `CCE_PER`, `CCE_EMP`).
- **Campos/fuentes DBD:** `CCE_HORAS` acumula horas efectivas de T15; `CCE_SUM` recibe costos suministrados en T17 y también costos transferidos por `M-ACU-CCE-REC` en T23.1; `CCE_FUN` guarda función. T23.1 acumula `CCE_RECIB` y `CCE_DIST`; T23.2 asigna `CCE_TASA`, `CCE_ASIG`, `CCE_OCIO`, `CCE_VARH`, `CCE_PROP` y `CCE_FIJO` mediante métodos configurados.
- **Moneda/unidad/signo:** horas conservan unidad de tiempo; tasas y medidas conservan su unidad declarada; campos de costo deben usar PEN/base funcional y los signos del servicio. Los campos calculados por T23.2 son asignaciones del proceso de cierre, no nuevos eventos de costo.
- **Reversa:** no se ha probado una reversa general de distribución ni la ejecución de un cierre nuevo sobre el mismo periodo. `M-ACT-CCE-RCA` aparece huérfano en el inventario de escritores y no se trata como escritura activa sin confirmar su llamada.

### `CTA_GASTO` · gasto por periodo, centro y concepto

- **Grano lógico candidato:** periodo + centro + concepto + empresa (`CGA_PER`, `CGA_CEN`, `CGA_CON`, `CGA_EMP`).
- **Campos/fuentes DBD:** `CGA_MTO` suma pérdida anormal T15 (`M-ACU-CGA-PERD`), ocio T23.2, gasto declarado T19, rebaja VNR T23.5 y diferencia de inventario T29.1. T16 resta la pérdida anormal devuelta. `CGA_DED` se asigna desde `DED` para `M-ACU-CGA-PER`; VNR y diferencia de inventario la asignan como `N`.
- **Moneda/signo:** los importes deben estar en moneda funcional; el gasto o rebaja suma según el servicio y una devolución resta el mismo efecto.
- **Bloqueo de contrato:** `M-ACU-CGA-PERD` y `M-ACU-CGA-OCIO` no asignan `CGA_DED`. `CGA_DED` tampoco pertenece a la clave configurada. Una fila de gasto no puede presentarse completa en cuanto a deducibilidad hasta resolver esas omisiones con la fuente metodológica/tributaria autorizada.
- **Reversa:** T16 resta pérdida anormal; no se halló una reversa universal para todos los demás conceptos. Definir cada par de origen/corrección.

### `CTA_OBJ_PER` · costo del objeto por periodo y elemento

- **Grano lógico:** objeto + periodo + empresa (`COP_OBJ`, `COP_PER`, `COP_EMP`).
- **Campos/fuentes DBD:** `COP_MAT`, `COP_MOD`, `COP_IND`, `COP_PERD`, `COP_TRF` y `COP_IND_APL` son elementos de costo. `M-ACU-COP` suma el elemento dinámico `COP_{ELE}` con `MTO_COS` y la pérdida `MTO_GAS` en T15; `M-ACT-COP-DEV` los resta en T16; `M-ACU-COP-IND` y `M-ACU-COP-APL` acumulan indirectos/aplicación en T23.2; `M-ACT-COP-TRF` asigna la transferencia en T23.3.
- **Moneda/signo:** los importes deben estar en moneda funcional. El signo de una devolución es inverso al consumo; los indirectos/transferencias siguen el servicio que los atribuye.
- **Reversa:** existe ruta T16 para consumo/devolución. La repetición o reapertura de T23.2/T23.3 requiere prueba separada.

### `CTA_OBJ_REC` · recurso real y permitido por objeto

- **Grano lógico:** objeto + recurso + periodo + empresa (`COR_OBJ`, `COR_REC`, `COR_PER`, `COR_EMP`).
- **Campos/fuentes DBD:** `COR_CAN_PERM` se asigna con `PERM` calculado a partir del estándar del componente, producción del objeto y merma normal; `COR_CAN_REAL` suma cantidades T15 y se resta en T16; `COR_MTO` suma la valuación real del consumo y se resta en T16.
- **Moneda/unidad:** cantidades conservan la unidad del recurso; `COR_MTO` usa la moneda funcional. No comparar cantidad y monto como si tuvieran la misma base.
- **Clave/reversa:** MCA de T15 omite empresa en las claves de acumulación y la asigna como valor. La identidad debe incluirla y la ruta Python la filtra. T16 tiene servicios de resta para cantidad/valor; hay un servicio genérico de devolución histórico que figura sin llamada en el inventario.

### `CTA_FUNCION` · costo por función

- **Grano lógico:** periodo + función + empresa (`CFU_PER`, `CFU_FUN`, `CFU_EMP`).
- **Campos/fuentes DBD:** `CFU_MTO` suma `MTO` por función desde T17 (`M-ACU-CFU`).
- **Moneda/signo:** importe en moneda funcional, sujeto al método de costo que suministra `MTO`.
- **Reversa y prueba:** no se encontró un servicio inverso asociado en el inventario DBD. La salida O-1 no guarda la dimensión función; no se debe asignar GAD/GVT/CPT a una función por suposición.

### `CTA_VTA_PER` · ingreso y costo de ventas

- **Grano lógico:** periodo + empresa (`VPE_PER`, `VPE_EMP`).
- **Campos/fuentes DBD:** `VPE_ING` suma ingreso `ING` de T20; `VPE_CST` suma el costo `MTO` de T20. T23.3 suma `DIF_VEN` para ajustar costo previamente vendido después de la liquidación.
- **Moneda/signo:** importes en moneda funcional. `DIF_VEN` es una variación con signo y debe agregarse sin convertir una reducción en incremento.
- **Reversa:** el inventario declara un ajuste posterior, pero no una reversa equivalente para todo ingreso de T20. Mantener el evento de venta y formalizar devoluciones/anulaciones antes de cerrar el contrato.

## Casos numéricos independientes disponibles

[D9_CUADRE_T15.md](D9_CUADRE_T15.md) conserva el caso `D9-T15-2026-04-B-OS01`: dos compras, un consumo, cálculo decimal por fuera del motor y lectura de las cuentas desde el XLSX persistido en un directorio temporal. El esperado y los insumos están en [caso_t15_eventos.json](../../../tests/fixtures/d9/caso_t15_eventos.json); la prueba confirma importes/cantidades en tres cuentas y conserva una fila de otra empresa con las mismas claves de negocio.

Los casos de [T17, T19 y T20](D9_CUADRE_EVENTOS.md) cotejan, respectivamente, `CTA_CENTRO`/`CTA_FUNCION`, `CTA_GASTO` y `CTA_VTA_PER`. T19 prueba la clasificación que devuelve `REGLA` para el motivo `DESMEDRO_SIN_ACTA`; esto no resuelve `CGA_DED` para la pérdida anormal T15 ni para ocio T23.2. T20 usa un saldo inicial sintético, no producido por una orden.

En conjunto, los cuatro recorridos concilian saldos parciales guardados con aritmética independiente; no incluyen `RESULTADO_METODO`, cobertura integral de las otras cuentas ni la conciliación por clave de O-1. No cierran D9.

## Puertas restantes

1. Resolver `CGA_DED` para pérdida anormal y ocio, y decidir si la deducibilidad forma parte del grano de gasto. El caso T19 solo prueba la clasificación recibida desde su regla fuente.
2. Completar prueba de clave única dentro de empresa y alinear `CLAVE_COMPUESTA` con las identidades empresariales de `CTA_GASTO` y `CTA_OBJ_REC`.
3. Ampliar el caso base T18/T23.3/T23.5 documentado en [D9_CUADRE_T23_3_T23_5.md](D9_CUADRE_T23_3_T23_5.md) al puerto externo T25.4 y a `RESULTADO_METODO`, seleccionando una corrida por huella y conciliando el mismo alcance. Después agregar venta previa a liquidación para probar `CTA_VTA_PER` y D14.
4. Relacionar cada cambio de cuenta con evento, línea y servicio DBD; verificar reversa, fallo, repetición, reapertura y cierre con las siete cuentas presentes.
5. Conciliar un caso integral con `RESULTADO_METODO` y esperado independiente por clave y total. Hasta entonces, no publicar las cuentas como salida contable oficial.
