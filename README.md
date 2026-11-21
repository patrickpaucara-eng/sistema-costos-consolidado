# Sistema de Costos Consolidado

Repositorio privado de trabajo para consolidar el Sistema de Costos Reyna. El punto histórico de referencia de la auditoría OT-001 es `main@a96ba794a6171a325836a5a56bf1c9392dbd8482` del [repositorio original](https://github.com/patrickpaucara-eng/sistema-costos-reyna/commit/a96ba794a6171a325836a5a56bf1c9392dbd8482), que se mantiene en solo lectura.

## Decisiones vigentes

Python es el único motor operativo; Excel es el libro de trabajo e intercambio; la interfaz es HTML local. VBA se conserva congelado y SQLite se aplaza hasta demostrar estabilidad. Los libros completos MCD y DBD de Tino son la base metodológica. Los adjuntos y fuentes de Claude, ORIA y Frenosa se conservan con índices y hashes en [docs/fuentes](docs/fuentes/INDICE_FUENTES.md). El 93 % histórico no está validado como avance global.

## Estado de la entrega

La rama activa `desarrollo/mvp-ola3` prepara el candidato 0.2.0: permite en Linux importar libros, registrar T14/T15/T17/T18/T19/T20 desde el formulario JSON, cerrar los pasos configurados y consultar en HTML. Si el libro declara el puerto T25.4 y sus tablas de resultados, permite recibir una corrida sintética y seleccionar su huella al ejecutar T23.5. Los casos D9 de eventos T15/T17/T19/T20 y los recorridos base y externos de T23.5 comparan saldos seleccionados con cálculos independientes; los datos sintéticos no habilitan cifras oficiales. El libro se modifica en una sola sustitución por cadena de cierre; el reintento usa recibos. Cada espacio se limita a una empresa operativa.

La suite `python -m unittest discover -s tests -v` pasó 55/55 en Linux con Python 3.12 y dependencias fijadas. El recorrido real en Chromium validó compras, consumo y cierre en la fixture. El caso T23.3/T23.5 base usa insumos sintéticos y deja `RESULTADO_METODO` vacío; el recorrido externo T25.4/T23.5 guarda y lee una corrida VNR de prueba por método, versión y huella. Es evidencia parcial: no concilia D9 integral ni valida el costo de la orden contra ORIA, flete/T14.2 o D14.

## Plan y continuidad

- [Plan de ejecución MVP y deuda restante](docs/entrega/PLAN_MVP_Y_PENDIENTES.md): puertas, dependencias, incertidumbres y trabajo desde D9 hasta la estabilidad.
- [Plan maestro y correspondencia con las seis olas](docs/planificacion/PLAN_MAESTRO.md): visión estratégica y orden operativo vigente.
- [Análisis frente a la Monografía 01](docs/planificacion/ANALISIS_MONOGRAFIA.md): requisitos, entregables, rúbrica y prioridades hasta el 9 de diciembre.
- [Inventario y estrategia de integración de las ramas](docs/auditoria/ESTRATEGIA_INTEGRACION_BRANCHES.md): censo remoto de solo lectura y criterio de selección; no propone fusionarlas en bloque.
- [Registro de capacidades](docs/entrega/REGISTRO_CAPACIDADES.md) y [evidencia Ola 3](docs/entrega/evidencias/MVP_OLA3.md): qué está probado y sus límites.
- [Guía para repetir el recorrido](docs/entrega/GUIA_PILOTO_EXCEL.md).
- [Mapa HTML del sistema histórico y del MVP actual](docs/diagramas/sistema-actual-reyna.html).
- [Estado de reanudación](docs/planificacion/ESTADO.md) y [contratos de los tres niveles](docs/modelo/CONTRATOS_DE_LOS_NIVELES.md).
- [Lectura de MCD](docs/metodologia/LECTURA_MCD.md), [lectura de DBD](docs/metodologia/LECTURA_DBD.md) e [índice de fuentes](docs/fuentes/INDICE_FUENTES.md).

La ruta sintética T25.4/T23.5 ya tiene pruebas focalizadas y revisión independiente de la selección por método, versión y huella. La siguiente tarea crítica es cerrar las brechas D9 restantes: resolver las claves y deducibilidad por fuente, ampliar la conciliación a las cuentas requeridas por O-1 y probar reversa y recuperación. El caso base T18/T23.3/T23.5 está documentado en [evidencia D9](docs/entrega/evidencias/D9_CUADRE_T23_3_T23_5.md), y el puerto externo tiene evidencia separada con sus límites. Windows/Excel nativo, aceptación del EXE, autenticación empresarial, rendimiento con datos reales, conciliación D9 integral, flete/T14.2, D14, aislamiento integral, publicación histórica y analítica autónoma siguen pendientes.
