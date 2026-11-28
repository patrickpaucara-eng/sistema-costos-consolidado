# B (MN 02): tres decisiones de rumbo (Claude, 28-nov)

## 1. Choque de misiones: hay una misión de B ya aprobada (M6) — DECIDE EL DUEÑO
El proyecto tiene, desde el 1-nov, la misión **M6 aprobada (E-076)** con su diccionario (`claude/PRES_DICCIONARIO_SEMANTICO_ONTOLOGICO.md`) y su parque (`claude/PRES_MCD_PARQUE.md`):
> El sistema de Presupuesto existe para ENTREGAR el presupuesto maestro vigente de su titular —sus inversiones, su operación y su efectivo, con el financiamiento que los sostiene—, proyectado desde su historia y su entorno según su riesgo y reproyectado con los hechos, y su control de ejecución, para que el titular elija las inversiones que más valor crean, las ejecute al menor costo y no exceda su liquidez ni su capacidad de financiamiento.

El 27-nov el dueño propuso otra: «entregar la programación de realización de los recursos comprometidos para el cumplimiento de los objetivos», y `tools/mapa_b/spec.py` se construyó solo con esa. **Contraste con el sílabo de Oria (sem. 13 presupuesto maestro; 14 basado en actividades y simulación; 15 financiero: CPPC, VAN, TIR, recuperación, CAPEX, estados proyectados):**

| Tema del curso | M6 | Misión 27-nov + spec.py |
|---|---|---|
| Presupuesto maestro (operativo + financiero) | Sí (es su producto) | Parcial: no hay presupuesto operativo en base devengado |
| Basado en actividades | Sí (lee costos ABC) | Sí |
| Simulación / riesgo | Sí («según su riesgo») | Solo sensibilidad (pieza 15) |
| CPPC, VAN, TIR, recuperación, CAPEX | Sí | Sí (B6, B8) |
| Estados proyectados | Sí | Sí (B8) |
| Control de ejecución (comprometido, ejecutado, disponible, desviación) | Sí | Solo desviación por ticket |
| Dos relojes: devengado y caja | Sí (diccionario §B) | **No**: mezcla devengado y caja |
| Impuestos, aportes, dividendos | Sí (clases de concepto) | **No** |

**Recomendación:** M6 queda como **misión** (es lo que califica el curso); la misión del 27-nov pasa a ser el **método** con que M6 se cumple (la calculadora programa los recursos comprometidos). Si el dueño aprueba, `spec.py` agrega antes de que Codex siga: (a) base de control DEVENGADO/CAJA en cada monto; (b) partidas con comprometido, ejecutado, disponible; (c) clases INGRESO, EGRESO, INVERSIÓN, APORTE, DIVIDENDO, IMPUESTO; (d) titular. Las piezas 1, 2 y 4 ya hechas siguen sirviendo.

## 2. ¿PuLP entra en el EXE de Windows? — SÍ, con una línea
Verificado en el paquete `pulp==2.9.0`: trae el solucionador CBC para Windows (`pulp/solverdir/cbc/win/64/cbc.exe`) y licencia libre (EPL). Nuestro `tools/windows/build.py` ya usa `--collect-data`; basta agregar `--collect-data pulp` (y `--hidden-import pulp`) al construir el EXE de B. Riesgo residual: antivirus que bloquee `cbc.exe` al extraerse en la carpeta temporal → probar en tu PC; respaldo: exportar a Solver (ya existe en Decidir). **No hace falta cambiar el diseño.**

## 3. Contrato A → B: qué debe publicar costos
B solo lee el contrato publicado (`contrato.py`). Hoy faltan tres cosas, y ya existen en el libro DBD:

| Dato que B necesita | Dónde está hoy en A | Campo nuevo del contrato (opcional, no rompe nada) |
|---|---|---|
| Capacidad práctica por actividad o centro | MEDIDA con MED_NIVEL = CAP | `capacidad`: [{destino, inductor, cantidad, unidad, periodo}] |
| Receta por producto o familia (horas e insumos por unidad) | Trazas por orden + receta de familia (`recetas_pedido`) | `recetas`: [{producto o familia, inductor o recurso, por_unidad, base, n_ordenes}] |
| Fecha comprometida de entrega de la orden | **No existe**: OBJETO solo tiene OBJ_FEC_TER (real) y ESTIMACION no guarda fecha | Agregar `EST_FEC_ENT` a ESTIMACION (la pide el Pedido) y publicar `ordenes_abiertas`: [{codigo, producto, cantidad, avance, fecha_entrega}] |

Orden para Codex: **C39** (ver `ordenes/OT-C39_CONTRATO_A_B.md`), después de C38 y de los documentos de MN 1.
