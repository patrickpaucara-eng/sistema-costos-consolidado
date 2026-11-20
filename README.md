# Sistema de Costos Consolidado

Repositorio privado de trabajo para consolidar el Sistema de Costos Reyna. El punto histórico de referencia de la auditoría OT-001 es `main@a96ba794a6171a325836a5a56bf1c9392dbd8482` del [repositorio original](https://github.com/patrickpaucara-eng/sistema-costos-reyna/commit/a96ba794a6171a325836a5a56bf1c9392dbd8482), que se mantiene en solo lectura.

## Decisiones vigentes

Python es el único motor operativo; Excel es el libro de trabajo e intercambio; la interfaz es HTML local. VBA se conserva congelado y SQLite se aplaza hasta demostrar estabilidad. Los libros completos MCD y DBD de Tino son la base metodológica. Los adjuntos y fuentes de Claude, ORIA y Frenosa se conservan con índices y hashes en [docs/fuentes](docs/fuentes/INDICE_FUENTES.md). El 93 % histórico no está validado como avance global.

## Estado de la entrega

La rama activa `desarrollo/mvp-ola3` prepara el candidato 0.2.0: completa en Linux el flujo de importación, compras T14, consumo T15, cierre de los pasos configurados y consulta en HTML. El libro se modifica en una sola sustitución por cadena de cierre; el reintento usa recibos. Cada espacio se limita a una empresa operativa.

La suite actual usa `python -m unittest discover -s tests -v`. El recorrido real en Chromium validó compras, consumo y cierre en la fixture. Las regresiones D9 verifican aislamiento por empresa, idempotencia y rollback; un caso T15 contrasta tres saldos persistidos con un esperado decimal independiente. Esto es un cuadre parcial: aún no concilia D9 integral ni valida el costo de la orden contra ORIA, flete/T14.2 o D14.

## Plan y continuidad

- [Plan de ejecución MVP y deuda restante](docs/entrega/PLAN_MVP_Y_PENDIENTES.md): puertas, dependencias, incertidumbres y trabajo desde D9 hasta la estabilidad.
- [Registro de capacidades](docs/entrega/REGISTRO_CAPACIDADES.md) y [evidencia Ola 3](docs/entrega/evidencias/MVP_OLA3.md): qué está probado y sus límites.
- [Guía para repetir el recorrido](docs/entrega/GUIA_PILOTO_EXCEL.md).
- [Mapa HTML del sistema histórico y del MVP actual](docs/diagramas/sistema-actual-reyna.html).
- [Estado de reanudación](docs/planificacion/ESTADO.md) y [contratos de los tres niveles](docs/modelo/CONTRATOS_DE_LOS_NIVELES.md).
- [Lectura de MCD](docs/metodologia/LECTURA_MCD.md), [lectura de DBD](docs/metodologia/LECTURA_DBD.md) e [índice de fuentes](docs/fuentes/INDICE_FUENTES.md).

La siguiente tarea crítica es resolver las brechas del contrato D9 (incluida la deducibilidad de pérdidas), ampliar el caso T15 independiente a los demás dominios CTA y conciliar un `RESULTADO_METODO` persistido. El caso parcial y su contrato están en [evidencia D9](docs/entrega/evidencias/D9_CONTRATO_DE_DATOS.md). Windows/Excel nativo, autenticación empresarial, rendimiento con datos reales, conciliación D9 integral, flete/T14.2, D14, aislamiento integral, publicación histórica y analítica autónoma siguen pendientes.
