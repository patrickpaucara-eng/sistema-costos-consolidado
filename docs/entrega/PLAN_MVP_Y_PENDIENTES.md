# Plan de ejecución · MVP y fortalecimiento pendiente

**Actualizado:** 19 de noviembre de 2026 (hora de Lima).

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
| M3 | Enumerar escritores de cuentas por transacción/cuenta, contrastar con MCD/DBD y construir un caso de cuadre independiente. Después, materializar cada cuenta desde un solo paso del cierre. | **Pendiente; siguiente trabajo crítico** | El informe histórico D9 enumera siete tablas; cada una tiene entre 1 y 7 servicios escritores y ninguna la escribe el cierre que publica `RESULTADO_METODO`. Las 14 pruebas estrictas históricas están marcadas `xfail`. El detalle y sus fuentes están en [d9](../fuentes/claude/ola3/d9/README.md). No habilitar cuentas como resultado oficial sin el cuadre. |
| M4 | Incorporar el flete a la compra T14 prorrateado por valor; agregar T14.2 para flete tardío sin reescribir la compra. | **Pendiente** | Caso de dos materiales de distinto valor, saldo parcialmente consumido, valor total conservado y variación del periodo documentada. T14.1 ya es devolución a proveedor. |
| M5 | Reexpresar en D14 la venta provisional con la liquidación real, registrando la diferencia en el periodo de ajuste. | **Pendiente** | Conservar la venta y costo originales, enlazar el ajuste y conciliar venta, producto terminado y proceso. Depende de M3 y M4. |
| M6 | Verificar EVE_ORI, hacer visibles merma/pérdida/ineficiencia y añadir los métodos aprobados para coproductos y costo financiero REAL/CONTABLE. | **Investigación/casos pendientes** | No alterar reglas hasta fijar casos ORIA y controles por objetivo. CONTABLE usa VVR para coproductos; el financiero no toca inventario. |
| M7 | Cerrar el paquete de demostración: guía, HTML, instalación reproducible, copia de respaldo y aceptación del dueño en su equipo. | **Parcial** | Wheel instalada en un prefijo temporal y Linux/Chromium y pruebas automatizadas aprobadas; dependencias estaban presentes. Excel nativo/Windows, Office abierto, corte físico y datos reales faltan. |
| M8 | Publicar costos históricos reproducibles y después agregar analítica con medición y políticas de autorización. | **Posterior** | Las instancias requieren insumos, reglas, fecha efectiva, revisión y salida conservada. La analítica autónoma necesita medición y límites; no se simula con reglas ocultas. |

## Secuencia restante de inicio a cierre

1. **Cerrar la especificación de D9.** Usar el inventario histórico de las siete cuentas y los escritores genéricos del motor. Por cada cuenta, registrar concepto resultado, transacción, método, sentido, llave, periodo y redondeo. Cotejar DBD pp. 44–45 y 171, y MCD; determinar si `CTA_ACTOR` pertenece al costo. Construir el caso manual antes de editar código.
2. **Aplicar el arreglo mínimo D9.** Reducir cada resultado contable a un solo escritor y conservar el rastro hacia sus hechos. Repetir el caso de éxito, rechazo, cierre interrumpido y reintento. Si no hay oráculo suficiente, entregar el inventario y dejar bloqueado el cálculo oficial.
3. **Resolver flete en T14/T14.2.** Definir campos y claves de evento desde el DBD. Probar asignación por valor, redondeo, saldo restante y material ya consumido. Una corrección tardía agrega ajuste al mes actual y referencia EVE_ORI; no reabre ni reescribe el evento original.
4. **Resolver D14.** Acordar el punto exacto de la secuencia T23.3/T23.5 que dispone costo real, calcular diferencia de unidades vendidas y guardar un ajuste trazable. Probar una orden con venta antes de liquidar, otra posterior, saldo terminado y saldo en proceso.
5. **Completar validación de método.** Revisar devoluciones EVE_ORI y distinguir merma absorbida, pérdida a resultado e ineficiencia de tiempo. Añadir coproductos/gastos financieros solo con oráculo y `objetivo` explícito; preservar la prohibición de afectar inventario CONTABLE con costo financiero.
6. **Dar forma al flujo de operación.** Sustituir JSON técnico por formularios guiados basados en TRX_CAMPO y DBD, sin codificar las reglas de costeo en HTML. Mantener mensajes simples, detalle de rechazos, identificador de reintento y consulta de trazas.
7. **Asegurar instalación y operación.** Empaquetar para Windows, probar con Excel cerrado y con el equipo del dueño, comprobar respaldo/restauración, permisos, dos periodos consecutivos y volumen esperado. El servicio debe ser el único editor del XLSX gestionado.
8. **Abrir la puerta de estabilidad.** Un revisor distinto reproduce instalación, compra/consumo, cierre, reportes y recuperación. Aceptar el MVP solo si casos MCD/DBD/ORIA cuadran, no hay duplicados y las evidencias están enlazadas por SHA y revisión.
9. **Evaluar SQLite después de esa puerta.** Medir la estabilidad del contrato motor/adaptador y recién entonces plantear migración. El código y los ensayos SQLite permanecen fuera del alcance actual.
10. **Construir publicación histórica y Analítica.** Versionar cada instancia de costo por fecha y datos, y después validar la analítica en modo sugerencia. El aprendizaje autónomo requiere resultados confirmados, trazabilidad, reversión y permisos definidos por capacidad.

## Incertidumbres registradas

- Las tablas `CTA_*` aparecen con uno a siete escritores en el informe de Claude; falta cotejar ese conteo contra la revisión histórica y registrar qué tablas se refieren.
- Claude marca errores de OPERAR MES como resueltos en VBA. El propietario decidió congelar VBA, así que no se reabre ese código; la ruta nueva necesita errores equivalentes en HTML/Python.
- T14.2 es el nombre candidato para ajuste tardío; T14.1 tiene semántica existente de devolución a proveedor.
- La corrección de costo provisional debe preservar el hecho original de venta y declarar el periodo contable del ajuste.
- El diagnóstico de costo y robustez de Frenosa se recibió como exportación JSONL; fórmulas, macros o archivos representados como texto no son ejecutables desde esa exportación.
- Autenticación empresarial, simultaneidad multiusuario, volumen de producción, reversión tras corte eléctrico, múltiples periodos y entorno Windows siguen sin evidencia.
- El 93 % mencionado por Claude se conserva como declaración histórica no auditada; no se usa para estimar el porcentaje actual.

## Reanudación

La siguiente tarea es el inventario D9 en el repositorio histórico de solo lectura y el contraste con MCD/DBD; el resultado inicial será una matriz de productores y un caso de cuadre, no un parche a ciegas. Revisar [ESTADO.md](../planificacion/ESTADO.md), [REGISTRO_CAPACIDADES.md](REGISTRO_CAPACIDADES.md), [MVP_OLA3.md](evidencias/MVP_OLA3.md) y [sistema-actual-reyna.html](../diagramas/sistema-actual-reyna.html) antes de retomar.
