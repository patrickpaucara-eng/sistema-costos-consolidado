# Continuidad del Sistema de Costos Consolidado

Al iniciar una sesión, leer `README.md`, `docs/fuentes/INDICE_FUENTES.md`, `docs/planificacion/ESTADO.md` y `docs/entrega/PLAN_MVP_Y_PENDIENTES.md`. Consultar Git y verificar los hashes y la rama antes de tomar la descripción HTML como estado actual.

## Decisiones vigentes del dueño

- Python es el único motor operativo; Excel es libro de trabajo e intercambio; la interfaz es HTML local.
- VBA queda congelado. SQLite se aplaza hasta que el sistema Python/Excel demuestre estabilidad. No se crea ni mantiene una implementación SQLite paralela.
- El repositorio histórico `patrickpaucara-eng/sistema-costos-reyna` es solo lectura. Trabajar únicamente en el consolidado y en la rama autorizada.
- Los libros completos de MCD y DBD de Tino son las fuentes metodológicas primarias. Los documentos de Claude, ORIA y Frenosa se contrastan con el código, las fuentes y las decisiones más recientes del dueño.
- No tratar el 93 % declarado como progreso verificado.

## Método de trabajo

El dueño definió Base, Síntesis/Entrega y Analítica como niveles conceptuales. Mantener estable la Base; añadir variantes de costo mediante contratos y datos configurables; dar a Analítica permisos limitados por capacidad y medir su calidad. No prometer universalidad sin casos.

Cada cambio de cálculo necesita un caso esperado independiente, fuentes y SHA, revisión del método y evidencia de ejecución. No editar pruebas para acomodar la salida del motor. Distinguir estado operativo de resultado metodológicamente aceptado.

Entregar por capacidades activas. Antes de declarar una capacidad lista, registrar operación, datos de prueba, resultado, revisión, limitaciones y siguiente acción en `docs/entrega/REGISTRO_CAPACIDADES.md` y `docs/entrega/evidencias/`. Si cambia el flujo, actualizar `docs/diagramas/sistema-actual-reyna.html` en el mismo lote.

Las ramas históricas se consultan sin modificarlas. Guardar el trabajo autorizado en el repositorio consolidado, verificar el remoto y mantener cambios acotados. Los ensayos se ejecutan sobre copias temporales del XLSX, no sobre el archivo original del repositorio histórico.

## Reanudación actual

La rama de trabajo es `desarrollo/mvp-ola3`. El MVP valida importación, T14/T15, reapertura, una guardia de empresa y el guardado de la cadena configurada. No valida D9, costo integral ORIA, flete/T14.2, D14, Windows/Excel nativo ni analítica. El inventario D9 y una línea base numérica O-1 están en `docs/entrega/evidencias/D9_MATRIZ_Y_CASO.md`; no equivalen a un cuadre independiente. La siguiente puerta es decidir si `CTA_*` son cuentas MCD impactadas por eventos o proyecciones derivadas de cierre, resolver el grano faltante y construir el oráculo independiente antes de implementar cuentas. Consultar `docs/entrega/PLAN_MVP_Y_PENDIENTES.md` para la secuencia y las condiciones de aceptación.
