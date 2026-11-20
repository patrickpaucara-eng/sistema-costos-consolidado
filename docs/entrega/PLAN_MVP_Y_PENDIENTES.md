# Plan de ejecución · MVP y fortalecimiento pendiente

**Actualizado:** 20 de noviembre de 2026 (hora de Lima).

**Rama:** `desarrollo/mvp-ola3`, basada en `desarrollo/capacidad-inicial@16c419f`.

**Referencia histórica, solo lectura:** `patrickpaucara-eng/sistema-costos-reyna@cac2501d9f712655dda466d216dc5bff2dd446a5` (`desarrollo/ola1`).

**Decisiones vigentes:** Python es el motor operativo; Excel es el libro de trabajo e intercambio; HTML local es la interfaz; VBA queda congelado; SQLite se aplaza hasta que Excel/Python alcance estabilidad demostrada. No se desarrolla SQLite en paralelo.

## Resultado que cubre este MVP

El MVP deja reproducibles la importación, la compra T14, el consumo T15, la reapertura del libro y la ejecución de la cadena de cierre configurada. El espacio admite una sola empresa operativa; las combinaciones ambiguas se rechazan. La cadena se calcula sobre una copia en memoria y se aplica al libro con una sustitución única del XLSX. Si falla, no se escriben cambios de negocio y queda un recibo de rechazo para hacer idempotente el reintento.

Esto acredita un recorrido técnico con la fixture histórica indicada; **no** certifica los asientos de D9, el costo integral por orden contra ORIA, el flete, D14, la exactitud metodológica universal ni la aptitud comercial. Las pruebas, la base y sus límites están en [REGISTRO_CAPACIDADES.md](REGISTRO_CAPACIDADES.md) y [evidencias/MVP_OLA3.md](evidencias/MVP_OLA3.md).

## Decisiones y límites de ejecución

- `desarrollo/ola1` se consulta como fuente histórica. El repositorio original no recibe cambios; el trabajo se integra en este consolidado.
- No se fusionan ramas históricas, no se elimina historia y no se implementa SQLite en paralelo.
- Los documentos recientes de Claude se preservan por contenido y SHA en [fuentes/claude/ola3](../fuentes/claude/ola3/README.md). Sus descripciones orientan requisitos, pero no sustituyen la revisión del código, MCD/DBD y casos numéricos.
- Cada cambio de cálculo debe tener un caso independiente antes de tocar el motor. Las diferencias de Claude, Frenosa y ORIA se conservan con fuente, página o línea, resultado esperado y resultado observado.
- La fixture es didáctica. Ningún porcentaje histórico de avance se toma como porcentaje auditado del producto.

## Plan ejecutado y puertas

| ID | Trabajo y aceptación | Estado | Evidencia / riesgo que queda |
|---|---|---|---|
| M0 | Preservar alcance, SHA, revisión de referencia y decisiones vigentes. | **Completo** | Transferencia de sesión, cuatro Markdown finales, diagnóstico D9 y pruebas históricas con manifiestos; copias duplicadas identificadas. Ver índice de fuentes. |
| M1 | Restringir cada espacio a una empresa con usuarios autorizados para T14/T15 y rechazar operaciones de otra empresa. | **Guardia activa; aislamiento completo pendiente** | Pruebas de rechazo al importar usuarios con permisos en dos empresas y al enviar `EMP` distinta. No se probó igualdad de costos conjunta frente a libros separados; por ello el libro queda limitado a una empresa. |
| M2 | Ejecutar los pasos configurados en memoria, probar fallo en T23.3, guardar con una sola sustitución y reintentar sin duplicar. | **Completo en alcance técnico** | HTML y API recorren T23.1, T23.2, T23.3, T23.5 y T23.9 de la fixture. T23.0 se clasifica `ESTADISTICA`, así que esta evidencia no dice que la cadena sea el cierre contable completo. La inyección de `RuntimeError` en T23.3 deja tablas de negocio y versión intactas; el recibo de rechazo es reproducible. |
| M3 | Enumerar escritores, contrastar las cuentas con MCD/DBD y cerrar un caso independiente por clave. Aplicar saldos de cuenta según eventos, con aislamiento por empresa. | **Semántica y guardia CTA implementadas; conciliación pendiente; salida oficial bloqueada** | El propietario resolvió la semántica por MCD: los eventos afectan el saldo y el cierre lo valida/conciliará. El motor genérico limita mutaciones `CTA_*` a la empresa del evento aunque la clave DBD omita empresa. Tres regresiones cubren cruce A/B, `m_ACTUALIZAR`, reintento y rollback. La fixture no trae O-1 con CTA ni `RESULTADO_METODO` persistido; no hay cuadre independiente. `CTA_GASTO`, `CTA_FUNCION` y `CTA_OBJ_REC` conservan diferencias de grano en el mapeo de O-1. Ver [decisión semántica D9](evidencias/D9_DECISION_SEMANTICA.md), [matriz y caso](evidencias/D9_MATRIZ_Y_CASO.md), [CSV](evidencias/D9_CONTROL_O1.csv) y [fuentes históricas](../fuentes/claude/ola3/d9/README.md). No publicar cifras de estas cuentas como resultado oficial hasta conciliar. |
| M4 | Incorporar el flete a la compra T14 prorrateado por valor; agregar T14.2 para flete tardío sin reescribir la compra. | **Pendiente** | Caso de dos materiales de distinto valor, saldo parcialmente consumido, valor total conservado y variación del periodo documentada. T14.1 ya es devolución a proveedor. |
| M5 | Reexpresar en D14 la venta provisional con la liquidación real, registrando la diferencia en el periodo de ajuste. | **Pendiente** | Conservar la venta y costo originales, enlazar el ajuste y conciliar venta, producto terminado y proceso. Depende de M3 y M4. |
| M6 | Verificar EVE_ORI, hacer visibles merma/pérdida/ineficiencia y añadir los métodos aprobados para coproductos y costo financiero REAL/CONTABLE. | **Investigación/casos pendientes** | No alterar reglas hasta fijar casos ORIA y controles por objetivo. CONTABLE usa VVR para coproductos; el financiero no toca inventario. |
| M7 | Cerrar el paquete de demostración: guía, HTML, instalación reproducible, copia de respaldo y aceptación del dueño en su equipo. | **Parcial** | Wheel instalada en un prefijo temporal y Linux/Chromium y pruebas automatizadas aprobadas; dependencias estaban presentes. Excel nativo/Windows, Office abierto, corte físico y datos reales faltan. |
| M8 | Publicar costos históricos reproducibles y después agregar analítica con medición y políticas de autorización. | **Posterior** | Las instancias requieren insumos, reglas, fecha efectiva, revisión y salida conservada. La analítica autónoma necesita medición y límites; no se simula con reglas ocultas. |

## Secuencia restante de inicio a cierre

1. **Cerrar el contrato de datos D9.** Definir fuente, signo, clave, periodo, agregación, moneda, redondeo y reversión por campo. Resolver con hechos fuente las dimensiones faltantes de `CTA_GASTO`, `CTA_FUNCION` y `CTA_OBJ_REC`; si faltan, mantener esos campos fuera de la salida oficial.
2. **Construir el cuadre independiente D9.** Persistir hechos, cuentas y resultados del mismo caso, comparar por clave y total con un esperado independiente, y probar repetición del cierre, fallo, reintento y reversión. La línea base O-1 actual es salida del motor histórico y no satisface este criterio.
3. **Fortalecer D9 tras el cuadre.** Completar la vinculación causal entre evento/línea, servicio DBD y cambio de cuenta; detectar duplicados de clave dentro de la empresa; probar recuperación y reapertura del ciclo. Mantener la semántica decidida: eventos actualizan cuentas, el cierre valida y concilia.
4. **Resolver flete en T14/T14.2.** Definir campos y claves de evento desde el DBD. Probar asignación por valor, redondeo, saldo restante y material ya consumido. Una corrección tardía agrega ajuste al mes actual y referencia EVE_ORI; no reabre ni reescribe el evento original.
5. **Resolver D14.** Acordar el punto exacto de la secuencia T23.3/T23.5 que dispone costo real, calcular diferencia de unidades vendidas y guardar un ajuste trazable. Probar una orden con venta antes de liquidar, otra posterior, saldo terminado y saldo en proceso.
6. **Completar validación de método.** Revisar devoluciones EVE_ORI y distinguir merma absorbida, pérdida a resultado e ineficiencia de tiempo. Añadir coproductos/gastos financieros solo con oráculo y `objetivo` explícito; preservar la prohibición de afectar inventario CONTABLE con costo financiero.
7. **Dar forma al flujo de operación.** Sustituir JSON técnico por formularios guiados basados en TRX_CAMPO y DBD, sin codificar las reglas de costeo en HTML. Mantener mensajes simples, detalle de rechazos, identificador de reintento y consulta de trazas.
8. **Asegurar instalación y operación.** Empaquetar para Windows, probar con Excel cerrado y con el equipo del dueño, comprobar respaldo/restauración, permisos, dos periodos consecutivos y volumen esperado. El servicio debe ser el único editor del XLSX gestionado.
9. **Abrir la puerta de estabilidad.** Un revisor distinto reproduce instalación, compra/consumo, cierre, reportes y recuperación. Aceptar el MVP solo si casos MCD/DBD/ORIA cuadran, no hay duplicados y las evidencias están enlazadas por SHA y revisión.
10. **Evaluar SQLite después de esa puerta.** Medir la estabilidad del contrato motor/adaptador y recién entonces plantear migración. El código y los ensayos SQLite permanecen fuera del alcance actual.
11. **Construir publicación histórica y Analítica.** Versionar cada instancia de costo por fecha y datos, y después validar la analítica en modo sugerencia. El aprendizaje autónomo requiere medición y límites, no se simula con reglas ocultas.

## Incertidumbres registradas

- El conteo de escritores D9 ya fue cotejado contra DBD_4c en la revisión histórica. La línea base O-1 es una salida calculada en memoria, no un cuadre contra cuenta persistida ni un oráculo independiente.
- Hay valores CTA en escenarios distintos conservados por OT-001; no corresponden a O-1 y no se mezclan como si fueran un mismo caso.
- Semántica resuelta: las cuentas operativas se actualizan por los eventos que las afectan y el cierre las valida/conciliará; una proyección derivada, si se requiere, debe ser distinta y reconstruible. La decisión no cubre aún cada campo o cifra.
- `CTA_GASTO`, `CTA_FUNCION` y `CTA_OBJ_REC` requieren dimensiones ausentes de las salidas propuestas; no rellenarlas con repartos o claves supuestas.
- Claude marca errores de OPERAR MES como resueltos en VBA. El propietario decidió congelar VBA, así que no se reabre ese código; la ruta nueva necesita errores equivalentes en HTML/Python.
- T14.2 es el nombre candidato para ajuste tardío; T14.1 tiene semántica existente de devolución a proveedor.
- La corrección de costo provisional debe preservar el hecho original de venta y declarar el periodo contable del ajuste.
- El diagnóstico de costo y robustez de Frenosa se recibió como exportación JSONL; fórmulas, macros o archivos representados como texto no son ejecutables desde esa exportación.
- Autenticación empresarial, simultaneidad multiusuario, volumen de producción, reversión tras corte eléctrico, múltiples periodos y entorno Windows siguen sin evidencia.
- El 93 % mencionado por Claude se conserva como declaración histórica no auditada; no se usa para estimar el porcentaje actual.

## Reanudación

La matriz de escritores y el cálculo de referencia O-1 están preservados en [D9_MATRIZ_Y_CASO.md](evidencias/D9_MATRIZ_Y_CASO.md); la decisión metodológica y la prueba de ámbito están en [D9_DECISION_SEMANTICA.md](evidencias/D9_DECISION_SEMANTICA.md). La siguiente puerta es completar el contrato de datos, conseguir dimensiones fuente y construir un cuadre independiente. Hasta completar esas condiciones, D9 queda bloqueado como resultado oficial. Después se retoma el flete/T14.2. Revisar [ESTADO.md](../planificacion/ESTADO.md), [REGISTRO_CAPACIDADES.md](REGISTRO_CAPACIDADES.md), [MVP_OLA3.md](evidencias/MVP_OLA3.md) y [sistema-actual-reyna.html](../diagramas/sistema-actual-reyna.html).
