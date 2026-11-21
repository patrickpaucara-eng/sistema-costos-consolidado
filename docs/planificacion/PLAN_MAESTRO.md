# Plan maestro de consolidación

Versión 5 · actualizado el 20 de noviembre de 2026 · ejecución MVP Python + Excel.

## Decisión vigente al retomar

El dueño confirmó conservar Excel como almacén y retirar VBA de la operación. SQLite se aplaza hasta demostrar estabilidad y no se desarrolla en paralelo. Se conservaron los módulos VBA de main y Ola 1 como ZIP de referencia inalterada. El primer lote usa adaptador Excel y motor Python con un contrato de lectura, ejecución y consulta independiente de la interfaz. La sustitución futura del adaptador requerirá equivalencia y pruebas, con alcance propio.

## Resultado esperado

Un sistema universal de costos e inteligencia de decisiones con funcionamiento offline, cálculos reproducibles, trazabilidad de cada resultado, operación práctica y recuperación comprobable. El alcance comercial se demostrará mediante casos representativos y pruebas de instalación, operación, respaldo y restauración.

El trabajo se organiza en los tres niveles elegidos por el dueño. La Base conserva los datos necesarios y su procedencia. Síntesis, asociada a la macrofunción Entrega, determina los costos solicitados. Analítica usa hechos y resultados para explicar, anticipar, proponer y medir decisiones. La correspondencia formal de estos niveles con MCD y DBD se valida en la fase 1.

## Autoridad y estado

| Asunto | Estado |
|---|---|
| Auditoría y pruebas seguras sobre copias | Autorizadas |
| Conservación de fuentes y documentación en el repositorio consolidado | Autorizada |
| Mapa HTML del funcionamiento actual | Actualizado con el MVP Ola 3; distingue el piloto de la referencia histórica |
| Tres niveles Base / Síntesis / Analítica | Dirección conceptual indicada por el dueño |
| Modelo conceptual detallado y contratos entre niveles | Borrador conservado; cotejo metodológico y pruebas de aceptación pendientes |
| Uso individual o varias personas simultáneas | Pendiente de decisión |
| Semántica de cuentas D9 | Decisión posterior del dueño conforme a MCD: los eventos actualizan saldos afectados y el cierre valida/conciliará; una proyección derivada debe mantenerse aparte. |
| Stack y ejecución del plan | Instrucción posterior: Python único + Excel como almacenamiento e intercambio + HTML. SQLite aplazado. |
| Repositorio histórico sistema-costos-reyna | Consulta y pruebas sobre copias |
| 93 % de avance heredado | Declaración pendiente de validación |

El dueño aprobó el stack y dio la instrucción «Procede con tu plan» el 18-nov. Se ejecutan las tareas dependientes al cerrar sus contratos y pruebas. Las decisiones materiales pendientes siguen registradas y se consultan cuando impiden avanzar.

## Punto de partida reproducible

- Histórico integrado — main a96ba794a6171a325836a5a56bf1c9392dbd8482.
- Candidata técnica — desarrollo/ola1 cac2501d9f712655dda466d216dc5bff2dd446a5.
- Demo de referencia — prototipo/v41-congelado 3a2850060c96b2f7eaeae613c8a402aa9486c079.
- OT-001 inventarió 292 ramas, 290 puntas, 289 árboles y 819 commits alcanzables.
- En las tres revisiones, la historia Python dio 392/392 y ENVASE 66/66. Ola 1 corrigió 16 errores de coherencia y elevó automatización a 5/5.
- Continúan abiertos el aislamiento integral de la cadena, P20 en la construcción estricta, corrección contable D9, flete/T14.2, D14, integridad de las huellas y conciliación metodológica.
- Los libros completos MCD y DBD llegaron después de OT-001 y están en el índice de fuentes. Su recepción habilita el cotejo metodológico pendiente.
- El consolidado contiene fuentes, HTML y el MVP técnico Ola 3. Su motor Python parte del espejo de Ola 1 y añade una guarda de empresa para las mutaciones `CTA_*`; el adaptador permite T14/T15/T17/T18/T19/T20 y, cuando el libro lo declara, recibe T25.4 y selecciona la corrida en T23.5 en una copia Excel. El caso base y el puerto VNR externo tienen pruebas sintéticas y límites separados; la conciliación integral D9, el cálculo ORIA y las cuentas oficiales siguen sin habilitarse. Ver el registro de capacidades y sus límites.

Los resultados de pruebas expresan su versión y su caso. Para repetir una prueba se fijan también los datos y el entorno. La observación de mezcla entre empresas se reprodujo en el método con hechos mezclados y requiere verificar toda la ruta de operación.

## Cómo se ejecutará

Cada tarea tendrá un identificador, dependencia, responsable por función, entrada, salida y evidencia de aceptación. Los estados serán pendiente, en curso, bloqueada, en revisión y aceptada. El cierre requiere evidencia y revisión. Las fechas y estimaciones se asignan por lote una vez fijado su alcance.

La secuencia principal será recuperación → método → modelo conceptual → pruebas de aceptación → validación del stack aprobado → diseño → implementación por recorridos completos → validación de entrega.

Se podrá adelantar la reproducción de un fallo confirmado mientras se cotejan las fuentes. Una discrepancia se registra y se continúa con tareas independientes. Las decisiones materiales sobre finalidad de costos, autoridad de una regla, alcance de producto, stack y publicaciones requieren al dueño. Las elecciones operativas reversibles las resuelve el orquestador.

## Fase 0 · Asegurar continuidad

| Tarea | Dependencia | Acción y salida | Criterio de cierre |
|---|---|---|---|
| P00 | Ninguna | Verificar fuentes, hashes, permisos y revisiones iniciales. | Se pueden localizar originales y repetir la captura Git. |
| P01 | P00 | Preservar el expediente OT-001, comandos, inventario y logs fuera del repositorio histórico. Registrar límites y fecha de corte. | Copia remota verificable y manifiesto de integridad. |
| P02 | P01 | Abrir registro de requisitos, decisiones, dudas y tareas. Vincular los hallazgos a fuente y SHA. | Cada afirmación decisiva tiene procedencia y estado. |
| P03 | P02 | Fijar protocolo de actualización del HTML y de reanudación. | La siguiente sesión identifica versión, último lote y tarea pendiente desde Git. |

P00 tiene evidencia previa y se reconfirmará al iniciar el lote. P01 requiere trasladar y verificar la evidencia local de OT-001 antes de depender de su persistencia en Cloud.

## Fase 1 · Validar metodología y alcance

| Tarea | Dependencia | Acción y salida | Criterio de cierre |
|---|---|---|---|
| M01 | P00 | Leer MCD y DBD con índice por páginas. Extraer definiciones y macrofunciones pertinentes. | Matriz de reglas con cita de edición y página PDF. |
| M02 | M01 | Contrastar MCD v3, la ficha v3.1, enmiendas y borrador v3.2. | Cada diferencia queda como confirmada, pendiente o propuesta, con impacto. |
| M03 | M01 | Recuperar decisiones del dueño en Git y contrastar notas finales con fuentes. | Cronología sin equiparar fecha reciente con autoridad metodológica. |
| M04 | M01 | Comparar casos de ORIA, CLEIN y Frenosa. Reconstruir el incidente de robustez hasta donde lo permitan los originales. | Caso reproducible o faltantes concretos identificados. |
| M05 | M01–M04 | Definir primer entorno empresarial, usuarios simultáneos, industrias y volumen. Identificar restricciones de equipos e instalación. | Escenario inicial y extensiones posteriores aprobados por el dueño. |
| M06 | M02, M05 | Definir qué significa real, contable, proyectado, calidad, estándar y otras solicitudes. Revisar combinaciones válidas. | Glosario con ejemplos, contraejemplos y preguntas de costo acordados. |

**Puerta de fase.** Aprobación del vocabulario, alcance inicial y reglas con interpretación material. Las preguntas pendientes que no afecten al lote se conservan con su efecto.

## Fase 2 · Cerrar el modelo conceptual

| Tarea | Dependencia | Acción y salida | Criterio de cierre |
|---|---|---|---|
| C01 | M06 | Definir Base con hechos, maestros, reglas, planes, resultados y decisiones, todos con procedencia. | Cada dato tiene identidad, significado, unidad y responsable. |
| C02 | C01 | Definir Síntesis como solicitud → selección de hechos/reglas → cálculo → validación → entrega. | El recorrido se explica para una compra, una orden y un periodo. |
| C03 | C02 | Definir dimensiones de solicitud y selección de método. | Empresa, objeto, periodo, finalidad, base de datos y versión quedan explícitos. |
| C04 | C03 | Resolver identidad y ámbito de empresa, periodo, recurso, almacén y orden. Considerar historial requerido para promedio y saldos de apertura. | Códigos iguales en empresas distintas conservan significado y saldo propios. |
| C05 | C02–C04 | Definir fórmulas, unidades, precisión y política de redondeo por publicación. | Un mismo caso tiene respuesta manual, tolerancia y explicación del residuo. |
| C06 | C04, C05 | Definir resultados oficiales, escenarios, cierre, ajustes y reapertura autorizada. | Se puede reproducir un periodo cerrado y explicar una corrección posterior. |
| C07 | C01, C06 | Definir Analítica y ciclo de propuesta, aplicación, medición y aprendizaje. | Cada acción indica dato, propósito, límite, autorización y forma de reversión. |
| C08 | C01–C07 | Dibujar grafo objetivo y mapa MCD → DBD → contrato → caso. | Ningún resultado esencial depende de un concepto sin definición. Revisión del dueño. |

Un proceso común puede invocar distintos métodos y fórmulas. Contable puede expresar finalidad, real/proyectado la base de información y calidad una dimensión de análisis. M06 y C03 deben verificar esa interpretación y sus combinaciones antes de convertirla en diseño definitivo.

La autonomía podrá crecer con evidencia de desempeño y una política aprobada. Se definirán acciones permitidas, límites, vigencia, registro, suspensión y revisión. La IA generativa, si se incorpora, tendrá contrato y funcionamiento opcional acordados.

## Fase 3 · Diseñar casos y pruebas de aceptación

| Tarea | Dependencia | Acción y salida | Criterio de cierre |
|---|---|---|---|
| A01 | C03–C05 | Dos empresas con mismos códigos, precios distintos y una orden cada una. | Operarlas juntas produce lo mismo que operarlas separadas. Se verifica desde entrada hasta reapertura. |
| A02 | C05 | Casos manuales de compra, moneda/impuesto, consumo, devolución, merma, pérdida y reparto. | Conservación de cantidades y valores, tolerancias explicadas y traza completa. |
| A03 | C06 | Dos periodos, órdenes abiertas y saldo inicial/final. | El cierre de un mes alimenta exactamente la apertura del siguiente. |
| A04 | C06 | Interrumpir cada punto crítico de cierre y repetir cargas. | Restauración consistente, reintento sin duplicar y un único resultado confirmado. |
| A05 | C05, C06 | Reconciliar cuentas suplementarias y resultados publicados. | Responsable de escritura identificado y cuadre del mismo alcance y versión. |
| A06 | C03, C06 | Variar un insumo, regla, cotización o dependencia de cálculo. | La identidad de corrida y su evidencia reflejan el cambio. El periodo anterior sigue reproducible. |
| A07 | C07 | Evaluar propuesta válida, fuera de límites, degradada y suspendida. | Se cumplen permisos, vigencia, registro y reversión definidos. |
| A08 | M04, M05 | Instalar, operar offline, respaldar, restaurar y medir con volumen representativo. | Umbrales acordados y resultados con equipo, filas, tiempo y memoria documentados. |
| A09 | A01–A08, A10 | Vincular requisitos a casos y revisar cobertura del diseño. | Cada caso define entradas, oráculo, tolerancia y prueba de aceptación. |
| A10 | C01–C05 | Definir costo por proyectos mediante configuración y conservar el caso de órdenes. | Caso y oráculo para probar estabilidad de esquema, contratos y resultados históricos. |

En esta fase se diseñan casos y oráculos. La implementación y la aceptación dinámica corresponden a fases 6–7. T01 puede usar los contratos de prueba sin exigir un producto terminado.

A01 puede empezar como diagnóstico en copias sobre la implementación actual antes de cerrar C08. Sus resultados alimentarán el modelo. Los oráculos manuales se revisan de forma independiente del código que produce el resultado.

## Fase 4 · Validar la tecnología aprobada y la transición

| Tarea | Dependencia | Acción y salida | Criterio de cierre |
|---|---|---|---|
| T01 | M05, C08, A09 | Contrastar el stack aprobado con los requisitos del entorno. | Evidencia de offline, concurrencia, instalación, auditoría, recuperación, rendimiento y mantenimiento. |
| T02 | T01 | Medir riesgos técnicos con prototipos acotados autorizados. | Evidencia sobre importación fiel, precisión, cierre recuperable y distribución. |
| T03 | T01, T02 | Fijar versiones, dependencias, distribución e intercambio del stack aprobado. | Documento técnico con pruebas y costo de transición. |
| T04 | T03 | Comprobar la aprobación registrada y las condiciones para el primer lote. | Stack aprobado el 18-nov. Versiones y contratos listos para implementar. |

### Estado del stack

La decisión posterior [PYTHON_EXCEL.md](PYTHON_EXCEL.md) sustituye SQLite por Excel para el primer paquete. Las referencias SQLite siguientes describen el plan de migración aplazado. La validación de guardado, recuperación e idempotencia se aplica ahora a archivos Excel.

El stack vigente del histórico usa Excel para almacenamiento, VBA para la operación e intérprete Python de apoyo, métodos y analítica. La versión auditada registra duplicación del intérprete y rutas con persistencia distinta.

**Decisión histórica del 18-nov, revisada después por el dueño** — SQLite local fue aprobado inicialmente. La decisión vigente aplaza SQLite y mantiene Python como motor único, Excel como libro de trabajo/intercambio y HTML como interfaz. El modelo externo del DBD de Tino guía captura, validación, consulta y presentación.

Se verificarán versiones, instalación y operación sin Internet. El servicio de la interfaz HTML funcionará localmente; la forma de empaquetarlo se decide mediante T02. La ruta actual escribe Excel con reemplazo atómico y limita cada libro a una empresa operativa. La cantidad de personas concurrentes y sus equipos sigue por precisar. El trabajo activo se rige por [el plan MVP](../entrega/PLAN_MVP_Y_PENDIENTES.md); no implementar la fase de persistencia SQLite hasta alcanzar su puerta de estabilidad.

El prototipo SQL del histórico se compara con el modelo conceptual antes de reutilizarlo. Su existencia no acredita una migración completa.

## Fase 5 · Diseño e importación de la base técnica

La fase se conserva como historial de planificación. La decisión vigente aplaza la implementación SQLite; cualquier futuro trabajo de esa fase depende de la puerta de estabilidad del plan MVP.

| Tarea | Dependencia | Acción y salida | Criterio de cierre |
|---|---|---|---|
| D01 | T04 | Clasificar componentes por conservar, corregir, rediseñar o archivar. Seleccionar cambios de Ola 1 por alcance. | Manifiesto de origen por SHA y justificación por componente. |
| D02 | D01 | Importar la revisión aprobada al consolidado en rama de trabajo. | Procedencia verificable y revisión de los archivos incluidos. |
| D03 | D01, C08, D06 | Diseñar modelo lógico/físico, claves, restricciones y evolución de esquema. | Cubre identidades, integridad por empresa, historial y resultados versionados. |
| D04 | D03 | Diseñar límites de motor, almacenamiento, síntesis, analítica e interfaz. | Cada llamada declara entrada, salida, error y responsable de escritura. |
| D05 | D03, D04 | Diseñar transacción de cierre, recuperación, reintentos y respaldo. | Puntos de fallo e invariantes trazados a A03–A06. |
| D06 | C08, A09 | Diseñar el modelo externo y prototipo HTML con datos de ejemplo antes de fijar el esquema físico. | El operador puede cargar, corregir, cerrar, consultar y restaurar. |
| D07 | D02–D06 | Diseñar migración y comparación con la referencia. | Ensayo reversible, inventario de excepciones y plan de retorno. |

## Fase 6 · Construcción incremental

Cada recorrido termina con datos guardados, consulta y prueba de reapertura. El constructor recibe las pruebas y contratos del lote.

| Lote | Dependencia | Entrega funcional | Aceptación |
|---|---|---|---|
| I01 | D07 | Instalación local, empresas, usuarios y catálogos mínimos. | Aislamiento y restauración de maestros en un entorno limpio. |
| I02 | I01 | Compra → ingreso → consumo → kardex → existencia. | A01 y casos de A02, incluida repetición de documento según identidad definida. |
| I03 | I02 | Orden → horas/servicios → medidas → reparto. | Importe trazable y unidades conservadas en casos manuales. |
| I04 | I03 | Liquidación → terminado/en proceso → costo de venta. | Casos de referencia y A03–A06. |
| I05 | I04 | Solicitudes adicionales aprobadas de costo y conciliaciones. | A10 y aceptación independiente por combinación de dimensiones y método. |
| I06 | I04, C07 | Hallazgos y escenarios → propuestas con evidencia. | Comparación reproducible y aislamiento del escenario. |
| I07 | I06 | Aplicación supervisada y medición del efecto. | Permisos, vigencia y reversión aprobados en A07. |
| I08 | I07 | Autonomía para acciones expresamente aprobadas. | Cumplimiento de límites, suspensión y desempeño en historia y casos nuevos. |

La interfaz acompaña cada lote. El ritmo de evolución depende de los contratos del modelo y de la equivalencia probada con los casos validados. Los cambios tecnológicos se hacen en los límites definidos en D04 para conservar resultados que deban mantenerse.

## Fase 7 · Migración y piloto

| Tarea | Dependencia | Acción y salida | Criterio de cierre |
|---|---|---|---|
| V01 | Lotes requeridos | Migrar copias representativas y validar relaciones, totales y excepciones. | Informe por tabla y por caso, con conteos y saldos reconciliados. |
| V02 | V01 | Ejecutar referencia y candidata sobre los mismos insumos y reglas. | Diferencias explicadas, revisadas y aceptadas por alcance. |
| V03 | V02 | Piloto del operador y del dueño en el equipo de destino. | Operaciones y errores previstos ejecutados con evidencia. |
| V04 | V03 | Ensayo de fallo, recuperación, respaldo y restauración offline. | La operación se retoma y conserva los saldos y la traza. |
| V05 | V02–V04 | Revisar rendimiento, permisos e integridad de archivos importados. | Cumple los umbrales del entorno aprobado y registra límites. |

## Fase 8 · Entrega y mantenimiento

| Tarea | Dependencia | Acción y salida | Criterio de cierre |
|---|---|---|---|
| E01 | V05 | Empaquetar una versión reproducible y la guía de uso. | Instalación desde cero con dependencias y versión identificadas. |
| E02 | E01 | Auditoría independiente del conjunto y discrepancias pendientes. | Cada requisito aceptado tiene prueba. Los límites se entregan explícitos. |
| E03 | E02 | Entregar versión, respaldo, procedimiento de actualización y retorno. | Dueño acepta alcance y autoriza distribución. |
| E04 | E03 | Establecer mantenimiento, cambios de reglas y nuevas industrias. | Cada ampliación tiene caso, evidencia, revisión y actualización del grafo. |

La calidad comercial se evalúa sobre el alcance entregado. Las industrias, normas o usos sin evidencia se mantienen como pendientes identificados.

## Protocolo de cada cambio y del HTML

1. Seleccionar una tarea del plan y verificar sus dependencias.
2. Revisar fuente y revisión de partida. Precisar entrada, salida e invariantes.
3. Definir cómo se aceptará el cambio y preparar una reproducción del problema cuando corresponda.
4. Construir en una rama acotada del consolidado, dentro de la autorización disponible.
5. Ejecutar las pruebas del alcance, revisar la consistencia al reintentar o reabrir y obtener revisión independiente cuando cambien cálculos, persistencia o permisos.
6. Actualizar el registro de estado y el HTML en el mismo lote cuando cambie el funcionamiento, sus fuentes o la evidencia mostrada.
7. Revisar diferencias y guardar el hito remoto autorizado. La fusión o distribución sigue el alcance de autorización correspondiente.

El mapa actual es [sistema-actual-reyna.html](../diagramas/sistema-actual-reyna.html). Sus niveles Base, Síntesis y Analítica organizan el recorrido implementado. El modelo objetivo tendrá identificación propia y estado de aprobación. La referencia a96ba79 seguirá visible mientras sea el funcionamiento representado.

Al importar producto, el HTML deberá identificar la revisión de código que describe. Mostrará qué lee/escribe cada componente, si el estado queda en archivo o memoria, contratos entre niveles y cobertura de las pruebas relevantes. El catálogo de tablas y funciones se regenerará desde esa revisión cuando cambie su estructura. Se comprobarán navegación, enlaces de evidencia, legibilidad móvil y funcionamiento al abrir el archivo localmente.

## Coordinación y recursos

El orquestador mantiene este plan, dependencias y decisiones. Git/documentación recibe tareas de inventario y localización con esfuerzo bajo o medio. Metodología, costos, integridad de datos y revisión independiente usan esfuerzo alto según complejidad. Programación rutinaria usa esfuerzo medio.

Se empieza con el orquestador y hasta tres especialistas cuando existan tareas independientes. Se reutilizan inventarios por SHA y se asignan áreas concretas para evitar releer los mismos archivos. El autor de un cambio crítico y su auditor son agentes distintos. Una revisión multiagente requiere pruebas observables para acreditar el comportamiento.

## Medición y siguiente lote

Se reportarán tareas aceptadas y requisitos verificados con su denominador. Antes de estimar avance global hay que aprobar alcance, prioridades y criterios. Los estados del plan se actualizarán por evidencia y por hito.

El lote documental conservó P00–P03 y la primera extracción de M01–M04. El MVP Ola 3 añade guardias de empresa, cierre técnico de la cadena y casos T18/T23.3/T23.5 base y externo. La suite combinada se registra en [evidencia MVP](../entrega/evidencias/MVP_OLA3.md). D9 incluye un contrato de datos en borrador para siete cuentas y casos que comparan saldos persistidos con esperados independientes; el puerto T25.4/T23.5 selecciona y concilia VNR sintético en una ruta acotada. Esta evidencia es parcial y no valida el costo integral. La siguiente tarea es cerrar las brechas de claves, dimensiones, deducibilidad y recuperación, ampliar la conciliación y obtener revisión independiente; después seguir con flete/T14.2 y D14. El estado detallado y las puertas están en [ESTADO.md](ESTADO.md) y [PLAN_MVP_Y_PENDIENTES.md](../entrega/PLAN_MVP_Y_PENDIENTES.md).

## Relación con las seis olas de Claude

Las seis olas se conservan como la secuencia estratégica histórica, documentada en [SISTEMA_ACTUAL.md](../fuentes/claude/ola3/SISTEMA_ACTUAL.md) y [TRASPASO_AGENTE.md](../fuentes/claude/ola3/TRASPASO_AGENTE.md). La ejecución vigente usa las puertas de este plan y [PLAN_MVP_Y_PENDIENTES.md](../entrega/PLAN_MVP_Y_PENDIENTES.md), porque el dueño modificó después el stack, congeló VBA y aplazó SQLite. El orden puede ajustarse para cumplir dependencias y validar por capacidades; no se infiere avance del 93 % histórico.

| Ola estratégica histórica | Contenido recuperado de Claude | Encaje en la ejecución vigente |
|---|---|---|
| 1 · base inicial | Cerrar Ola 1/1b, operar compras y consumo, soporte de uso | MVP M0–M2 y M7; T18 está habilitada para el caso controlado; prueba del dueño en Windows/Excel nativo sigue pendiente. |
| 2 · estructura | D2 diario/log, D3 kardex y D4 actor | Los artefactos y reglas se preservan como fuente; cualquier incorporación pasa primero por fases 1–3 del plan maestro y su aceptación. No implica implementar SQLite. |
| 3 · credibilidad de costos | D9, flete, pérdidas, D14 y otros métodos | Trabajo activo M3–M6; D9 tiene casos parciales y permanece bloqueado como resultado oficial. |
| 4 · integridad | Huella de resultados y retiro de UMBRAL | Pendiente de diseñar y priorizar tras contratos y aceptación de costos; no se declara cubierto por los recibos técnicos actuales. |
| 5 · analítica y decisión | Predicción, simulación en copia y consulta guiada | M8, después de publicar resultados reproducibles y definir medición, permisos y límites. |
| 6 · prueba global | Seis meses, dos empresas y versión 5.0 | Fases 7–8 del plan maestro, una vez habilitados los recorridos requeridos; el piloto actual es de una empresa por espacio. |

Así, **sí se mantiene la visión de seis olas**, pero el control diario de tareas se hace con fases 0–8 del plan maestro y M0–M8 del plan MVP, con criterios explícitos y evidencia. Las olas antiguas no son el checklist operativo actualizado.

## Prioridad de entrega del 18-nov

El dueño fijó un plazo de cuatro días y pidió reutilizar el trabajo de Claude. Su plan inicial se conserva como [documento histórico](../entrega/PLAN_CUATRO_DIAS.md). La secuencia operativa actual, ya ajustada al stack Python/Excel/HTML y SQLite aplazado, está en [PLAN_MVP_Y_PENDIENTES.md](../entrega/PLAN_MVP_Y_PENDIENTES.md). El cierre del modelo y sus contratos guía los lotes posteriores y los criterios de aceptación se conservan.
