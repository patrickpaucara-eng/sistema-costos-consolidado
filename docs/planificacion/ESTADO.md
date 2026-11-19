# Estado y reanudación

Actualizado el 18 de noviembre de 2026, hora de Lima. Rama `desarrollo/capacidad-inicial`, derivada de `docs/plan-maestro`.

## Mandato vigente

Python como único motor operativo, Excel como almacenamiento/intercambio e interfaz HTML local. SQLite se aplaza hasta demostrar estabilidad, sin desarrollo paralelo. El VBA se conserva congelado. El repositorio histórico se consulta en lectura; la implementación y sus hitos pertenecen al consolidado. El dueño autorizó ejecución autónoma, agentes estratégicos y entrega por capacidades activas. MCD y DBD de Tino son las fuentes primarias para resolver dudas de método y presentación.

Se busca Base estable, cálculo modular por instancias históricas y ampliación por configuración. La autonomía de Analítica exige resultados medidos. Las propuestas conceptuales están en [CONTRATOS_DE_LOS_NIVELES.md](../modelo/CONTRATOS_DE_LOS_NIVELES.md). El 93 % histórico sigue sin validación global.

## Hitos conservados

| Hito | Estado y evidencia |
|---|---|
| Fuentes | Seis originales con manifiesto; libros completos MCD/DBD disponibles en [índice](../fuentes/INDICE_FUENTES.md). |
| Auditoría histórica OT-001 | Expediente de 27 archivos y manifiesto; 292 ramas inventariadas. Referencias y límites en su resumen. |
| Método y conocimiento | Lecturas MCD/DBD con páginas, matriz inicial y recuperación dirigida de Markdown históricos. El cotejo por método continúa. |
| Piloto Python/Excel 0.1.0 | CAP-01–CAP-05 verificadas en su alcance técnico. Compra, consumo, reapertura, reintento y HTML. [Registro y evidencias](../entrega/REGISTRO_CAPACIDADES.md). |
| Conservación de VBA | ZIP exactos de `kit/vba` de main a96ba79 y Ola 1 cac2501, con hashes. |
| Mapa HTML | Conserva mapa histórico a96ba79 y distingue el nuevo recorrido del piloto consolidado. |

El motor Python operativo es copia exacta de `kit/motor_espejo.py` de Ola 1 cac2501. El adaptador preserva las partes ajenas del XLSX, guarda recibo y estado juntos y conserva respaldo de la escritura anterior. Las nueve pruebas cubren disco/HTTP, concurrencia cooperativa, recuperación inyectada y preservación de formato y fórmula. El recorrido real de Chromium confirma la UI. Linux está probado; Windows/Excel nativo sigue pendiente.

## Siguiente tarea reanudable

1. Leer [PYTHON_EXCEL.md](PYTHON_EXCEL.md), el registro de capacidades y su evidencia; comprobar rama, último commit, hashes del motor, fixture y VBA. No reanudar el ensayo SQLite, que permanece fuera de la entrega.
2. Reproducir el caso de mezcla de empresas y seguir sus claves desde compra/consumo hasta valuación y reapertura. Definir el oráculo de igualdad entre operación conjunta y separada antes de modificar reglas.
3. Inventariar las llamadas efectivas del generador/cierre Ola 1 y sus pendientes de Claude; enlazar cada regla con MCD/DBD y los casos ORIA. Conservar las discrepancias por SHA y página.
4. Ampliar el recorrido hasta costo de una orden con conciliación y persistencia recuperable. No habilitar globalmente transacciones sin caso de aceptación.
5. Sustituir captura JSON por campos de negocio al validar contratos; comprobar instalación y recuperación en el equipo de destino. Registrar el alcance entregable de cuatro días por capacidades, sin dar por terminado el conjunto.

## Incertidumbres y límites abiertos

- Dos empresas en el mismo libro: aislamiento de toda la cadena pendiente.
- Excel/Windows nativo, interacción con Office y corte físico: pendientes. El servicio debe ser el único editor del libro gestionado.
- Autenticación personal: pendiente; el piloto supone operador local de confianza.
- Volumen, simultaneidad empresarial e industria inicial: no fijados. Las mediciones de un libro pequeño no representan producción.
- Cierre completo, publicación histórica, equivalencia metodológica, cuentas, BI y aprendizaje autónomo: pendientes.
- El antecedente Frenosa JSONL conserva texto y documentación; fórmulas/macros originales no son reconstruibles por el mero nombre de sus archivos.

La continuidad depende del hito guardado en Git, no de la persistencia del espacio temporal. Revisar el estado remoto antes de iniciar otra sesión. La guía permite repetir el caso en una copia del repositorio.
