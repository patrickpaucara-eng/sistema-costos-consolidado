# Estado y reanudación

Actualizado el 20 de noviembre de 2026 (hora de Lima). Rama `desarrollo/mvp-ola3`, derivada de `desarrollo/capacidad-inicial@16c419f`.

## Mandato del dueño

Python como motor operativo único, Excel como almacenamiento e intercambio e interfaz HTML local. SQLite queda aplazado sin trabajo paralelo; VBA está congelado. El repositorio original se consulta en lectura; la implementación pertenece al consolidado. El dueño autorizó ejecutar el plan y mantener las capacidades y pendientes en el repo.

La Base debe permanecer estable; los cálculos deben ser repetibles por fecha e incorporar variantes de manera modular; la Analítica debe demostrar su aprendizaje con resultados, controles y permisos. MCD y DBD de Tino son referencias metodológicas primarias. Consultar los Markdown recuperados de Claude como evidencia de requisitos, no como órdenes que prevalecen sobre decisiones posteriores del dueño.

## Hitos y evidencia

| Hito | Estado |
|---|---|
| Auditoría histórica OT-001 | Expediente conservado: 27 archivos y 292 ramas inventariadas. La auditoría no certifica el 93 % declarado. |
| Fuentes metodológicas | MCD/DBD completos, CLEIN, casos ORIA y exportación JSONL de Frenosa indexados con hashes. Los cuatro Markdown recientes de Ola 3 también están preservados y con manifiesto SHA. |
| Referencia del motor | Espejo Python de `desarrollo/ola1@cac2501d9f712655dda466d216dc5bff2dd446a5`, con guarda de empresa para mutaciones `CTA_*` en el consolidado; original inalterado. VBA se conserva congelado. |
| CAP-01–CAP-05 | Importar, compra/consumo T14/T15, persistir, reabrir, reintentar, consultar y operar desde HTML, en el alcance documentado. |
| MVP Ola 3 | Guardia de una empresa operativa por espacio y cierre configurado transaccional sobre copia en memoria. 16 pruebas de unidad/API y recorrido real de Chromium; ver [evidencia](../entrega/evidencias/MVP_OLA3.md). |
| D9 · cuentas CTA | El propietario decidió seguir la semántica MCD: eventos actualizan los saldos afectados; el cierre valida y concilia. Se limita la escritura genérica `CTA_*` a la empresa del evento. Pruebas temporales cubren cruce A/B, reintento y rollback. La conciliación sigue pendiente: O-1 no tiene hojas CTA ni `RESULTADO_METODO` persistido, y falta un oráculo independiente. Ver [decisión](../entrega/evidencias/D9_DECISION_SEMANTICA.md), [matriz](../entrega/evidencias/D9_MATRIZ_Y_CASO.md) y [CSV](../entrega/evidencias/D9_CONTROL_O1.csv). |
| Plan activo | [MVP y pendientes](../entrega/PLAN_MVP_Y_PENDIENTES.md), con dependencias desde la guardia y el cierre hasta D9, flete, D14, instalación, publicación y Analítica. |

## Siguiente tarea reanudable

1. Completar el contrato de datos de las cuentas por campo: fuente, signo, clave, periodo, agregación, moneda, redondeo y reversión.
2. Completar con fuentes los atributos que requiere la conciliación de `CTA_GASTO`, `CTA_FUNCION` y `CTA_OBJ_REC`; no inventar dimensiones.
3. Persistir cuentas y resultado de método para un caso con esperado independiente; conciliar por clave y total y probar repetición del cierre, fallo, reversión y recuperación.
4. Reforzar trazabilidad entre evento/línea, método DBD y cambio de cuenta; detectar duplicados de clave dentro de la empresa.
5. Continuar con flete/T14.2 y D14 enlazando cada regla con MCD/DBD y casos ORIA/Frenosa.

## Guardas y límites pendientes

- La regla de empresa detecta operadores activos para T14/T15 y rechaza espacios ambiguos. No reemplaza la prueba integral de claves y filtros en todas las tablas/métodos.
- La cadena de cierre ejecuta pasos `OFICIAL` o `CIERRE` de `CIERRE_PASO`. La atomicidad de persistencia está probada; D9 y la exactitud del resultado contable no.
- La aceptación usa fixture didáctica. No hay aún datos reales, cotejo completo de costo integral con ORIA, volumen de producción, Excel/Windows nativo, corte físico, autenticación o uso multioperador.
- No se han implementado flete/T14.2, D14, la instancia histórica completa ni la Analítica autónoma. No hay código SQLite paralelo.
- Los espacios importados con la versión anterior deben reimportarse para recibir los metadatos de empresa y cierre agregados en Ola 3.

La continuidad depende del hito conservado en Git. Al retomar, confirmar rama/remoto y hashes de los documentos y fixtures, ejecutar la suite, leer el plan y no volver a auditar todas las ramas salvo que aparezca una evidencia que lo requiera.
