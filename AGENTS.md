# Continuidad del Sistema de Costos Consolidado

> **Coordinador nuevo: lee primero `docs/TRASPASO.md`.**

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

La rama de trabajo es `desarrollo/mvp-ola3`. El MVP valida importación, T14/T15/T17/T18/T19/T20, reapertura, guardia de empresa y guardado de la cadena configurada. Por instrucción del propietario, D9 sigue la semántica MCD: los eventos actualizan los saldos afectados y el cierre los valida/conciliará. El motor limita mutaciones `CTA_*` a la empresa del evento; pruebas cubren cruce A/B, idempotencia y rollback en copias temporales. Casos independientes comparan saldos de T15/T17/T19/T20 y un caso base T18/T23.3/T23.5; este último usa tramas sintéticas y no valida el método externo ni el costo ORIA completo. El contrato de las siete cuentas registra las brechas restantes. D9 integral, flete/T14.2, D14, Windows/Excel nativo y analítica siguen pendientes. Ver `docs/entrega/evidencias/D9_MATRIZ_Y_CASO.md`, decisión/contrato y los tres documentos de cuadre. La siguiente puerta es resolver T25.4/selección por huella, claves/deducibilidad y conciliar `RESULTADO_METODO`. El marco de seis olas y su correspondencia están en `docs/planificacion/PLAN_MAESTRO.md`; la operación se rige por `docs/entrega/PLAN_MVP_Y_PENDIENTES.md`. El inventario actual de 292 ramas es solo lectura; integrar selectivamente, sin fusión masiva.

## MANDATO VIGENTE (21-nov-2026): Monografía MN_01 de Oria — entrega 9-dic 18:00
Plan: `docs/planificacion/PLAN_MONOGRAFIA_Y_SISTEMA.md`. Prioridad absoluta del **mínimo vital** (lo que califica la mono). D9 integral, flete T14.2, D14, SQLite y D3/D4/D13 pasan a **post-estabilidad** salvo que el caso Frenosa los necesite para cuadrar.
Rama de trabajo: `desarrollo/mono` (Claude). Codex trabaja en ramas `codex/<orden>` creadas desde `desarrollo/mono` y abre PR contra `desarrollo/mono`. **Nadie une a main.**

### Roles y niveles
- **Claude (coordinador, esfuerzo alto):** metodología MCD/DBD, cálculo, síntesis REAL/CONTABLE/ESTIMADO, analítica, integración y revisión de todo PR.
- **Codex (ejecución, esfuerzo medio):** pantallas, dashboard, exportadores Excel/Word/HTML, documentos, scripts. Esfuerzo bajo para formato e inventarios.
- **Dueño:** decide y prueba resultados (una página por entrega: qué cambió · qué probar en 15 min · qué decides).

### Barreras (bloquean, no aconsejan)
1. `python tools/verificar.py` debe terminar en **COMPUERTA: VERDE** antes de abrir o aceptar un PR.
2. Pantallas, dashboard y documentos **solo leen el contrato de resultados** (`src/reyna_local/contrato.py`). No recalculan costos. Si necesitan un dato que no está, se pide a Claude ampliar el contrato.
3. No editar pruebas para que pasen. No tocar `motor_espejo.py` ni el cálculo (eso es de Claude).
4. Material por kardex, gastos por reparto. CONTABLE nunca capitaliza financieros ni no atribuibles. ESTIMADO = estimación estadística (no estándar).
5. Cada error encontrado agrega una fila a `docs/planificacion/REGLAS_APRENDIDAS.md` y una prueba.
6. Registrar cada sesión en **tu propio CSV** `docs/entrega/tiempos/<agente>.csv` (fecha,inicio,termino,actividad,etapa,responsable,resultado). **No editar el .xlsx** (es binario y choca); `python tools/consolidar_tiempos.py` lo arma. Es el entregable 13.
