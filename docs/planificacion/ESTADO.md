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
| MVP Ola 3 | Guardia de una empresa por espacio, cierre transaccional y caso controlado T18/T23.3/T23.5. 22 pruebas combinadas aprobadas; recorrido real previo de Chromium. Ver [evidencia](../entrega/evidencias/MVP_OLA3.md). Empaquetado y smoke local completados; el workflow Windows falló dos veces antes de asignar runner. No hay EXE ni prueba nativa; ver [registro](../entrega/evidencias/WINDOWS_ACTIONS_2026-11-20.md). |
| D9 · cuentas CTA | Semántica MCD decidida; mutaciones `CTA_*` limitadas a empresa del evento. T15/T17/T19/T20 y un caso base sintético T18/T23.3/T23.5 contrastan saldos seleccionados con aritmética independiente. D9 integral pendiente: ruta externa T25.4/huella, `RESULTADO_METODO` conciliable, claves/dimensiones, deducibilidad faltante en pérdidas/ocio y revisión independiente. Ver [decisión](../entrega/evidencias/D9_DECISION_SEMANTICA.md), [contrato](../entrega/evidencias/D9_CONTRATO_DE_DATOS.md), [caso T15](../entrega/evidencias/D9_CUADRE_T15.md), [casos T17/T19/T20](../entrega/evidencias/D9_CUADRE_EVENTOS.md), [caso T18/T23.3/T23.5](../entrega/evidencias/D9_CUADRE_T23_3_T23_5.md), [matriz O-1](../entrega/evidencias/D9_MATRIZ_Y_CASO.md) y [CSV](../entrega/evidencias/D9_CONTROL_O1.csv). |
| Plan activo | Visión en seis olas preservada como referencia; el [plan maestro](PLAN_MAESTRO.md) establece fases y correspondencia, y el [plan MVP](../entrega/PLAN_MVP_Y_PENDIENTES.md) gobierna las próximas puertas. |

## Siguiente tarea reanudable

1. Resolver `CGA_DED` para pérdida anormal y ocio, las claves empresariales y las demás brechas del [contrato D9](../entrega/evidencias/D9_CONTRATO_DE_DATOS.md).
2. Extender el caso base T18/T23.3/T23.5 al puerto T25.4, fijar selección por huella, persistir `RESULTADO_METODO` y conciliar por clave y total.
3. Probar repetición del cierre, reversa, recuperación, reapertura y fallos intermedios con las cuentas presentes.
4. Reforzar trazabilidad entre evento/línea, método DBD y cambio de cuenta; detectar claves duplicadas dentro de la empresa.
5. Continuar con flete/T14.2 y D14 enlazando cada regla con MCD/DBD y casos ORIA/Frenosa.

Antes de afirmar aceptación offline en Windows, resolver por qué GitHub Actions no asignó runner al job `windows-2022`; la evidencia disponible no atribuye el fallo al código de compilación.

## Coordinación multiagente de Ola 3

El coordinador concentra decisiones de metodología, arquitectura, dependencias y aceptación. Para este lote se usaron: un revisor D9 de solo lectura que encontró y delimitó los problemas de unidades y clave de `SALIDA`; un auditor de empaquetado de solo lectura; y un implementador Windows con modelo Sol en razonamiento medio, limitado a launcher, build, smoke y workflow. El coordinador integró el caso, ajustó la evidencia, ejecutó pruebas y conserva la aceptación independiente.

Para optimizar contexto, los especialistas reciben únicamente fuentes y rutas de su tarea; el inventario con SHA y este estado evitan volver a leer las 292 ramas o el repositorio completo. En la siguiente ola, reservar esfuerzo alto para decisiones MCD/DBD, cálculo y seguridad de datos; nivel medio para cambios acotados con aceptación definida; nivel bajo para búsqueda, formato y actualización rutinaria de documentos. Mantener como máximo tres especialistas concurrentes y asignar revisión independiente a cambios que afecten cálculo o persistencia.

## Guardas y límites pendientes

- La regla de empresa detecta operadores activos para las transacciones habilitadas del piloto y rechaza espacios ambiguos. No reemplaza la prueba integral de claves y filtros en todas las tablas/métodos.
- La cadena de cierre ejecuta pasos `OFICIAL` o `CIERRE` de `CIERRE_PASO`. La atomicidad de persistencia está probada; D9 y la exactitud del resultado contable no.
- La aceptación usa fixture didáctica. No hay aún datos reales, cotejo completo de costo integral con ORIA, volumen de producción, Excel/Windows nativo, corte físico, autenticación o uso multioperador.
- No se han implementado flete/T14.2, D14, la instancia histórica completa ni la Analítica autónoma. No hay código SQLite paralelo.
- Los espacios importados con la versión anterior deben reimportarse para recibir los metadatos de empresa y cierre agregados en Ola 3.

El inventario remoto del 20-nov confirmó 292 ramas y 290 puntas únicas; los nombres y SHA están en [INVENTARIO_BRANCHES_2026-11-20.csv](../auditoria/INVENTARIO_BRANCHES_2026-11-20.csv), con recomendación de integración selectiva en [ESTRATEGIA_INTEGRACION_BRANCHES.md](../auditoria/ESTRATEGIA_INTEGRACION_BRANCHES.md). Las seis olas siguen como mapa estratégico; el trabajo operativo lo gobiernan fases 0–8 y M0–M8. La monografía se analiza en [ANALISIS_MONOGRAFIA.md](ANALISIS_MONOGRAFIA.md). Al retomar, confirmar rama/remoto y hashes, ejecutar la suite y no fusionar ramas en bloque.
