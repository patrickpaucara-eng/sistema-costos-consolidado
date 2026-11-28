# COLA ÚNICA DE CODEX (28-nov) — ejecutar en serie, sin esperar nueva instrucción entre órdenes
Regla: termina una orden (PRs abiertos con compuerta VERDE) y pasa a la siguiente. Si una pieza se bloquea por una prueba existente que solo depende de navegación o selectores, aplica las autorizaciones de DECISIONES_DUENO.md y sigue; cualquier otra duda va a `ordenes/RESPUESTAS_CODEX_24NOV.md` y continúas con la pieza siguiente. Nunca fusionar ni ir a main.

## MONOGRAFÍA 1 (entrega 9-dic; congelar código 6-dic)
1. **OT-C37** C37-2 → C37-7 (en curso).
1b. **OT-C38** C38-1 → C38-10 (correcciones de cálculo de la auditoría; autorizado tocar el cálculo solo en esta orden). Prioridad: si se acerca el 4-dic sin terminar C37, haz C38 antes que lo que quede de C37.
2. **Documentos MN 1** (piezas que la otra IA no alcanzó; insumos en `docs/entrega/otra_ia/` y `docs/entrega/evidencias/`):
   - 26 `docs/entrega/INFORME_PRUEBAS_MN1.docx`: objetivo, tipos de prueba (unitarias, punta a punta, entorno hostil, conservación, oráculo SERVITEC, auditoría), tabla caso/esperado/obtenido/estado con cifras de la corrida final (`tools/verificar.py`, `tools/e2e_recorrido.py`, `tests/auditoria_mn1`, `tests/datos/oraculo_servitec`), cómo reproducir.
   - 27 `docs/entrega/PRESENTACION_MN1.pptx`: 12 diapositivas (problema, MCD/DBD, arquitectura, recorrido de un pedido, reparto P1–P7 con las dos matrices de Oria, decidir, aprendizaje, pruebas y oráculo, auditoría, límites, demo, cierre). Usar `docs/entrega/otra_ia/pieza25/MONOGRAFIA_1_textos.docx` como texto base.
   - 28 `docs/entrega/PREGUNTAS_JURADO_MN1.md`: 25 preguntas difíciles con respuesta corta basada en el sistema.
   - 32 `docs/entrega/GUION_PRUEBA_DUENO.md`: prueba de 15 min del EXE sin internet con SERVITEC (REB 22,975 / MPR 5,165), casilla OK/FALLA por paso, 4 pasos con `tests/datos/libros_hostiles/`.
3. **Manual de usuario (entregable 10)** `docs/entrega/MANUAL_USUARIO.docx`: pantalla por pantalla con capturas del EXE final; se hace DESPUÉS de que Claude una C37 y C38.

## MONOGRAFÍA 2 (después del 9-dic, salvo que la cola de MN 1 termine antes)
4. **Retomar B** desde `docs/entrega/otra_ia/B/BITACORA_B.md`: piezas 5–18 y 19–23 tal como están escritas ahí (spec: `tools/mapa_b/spec.py`; B vive solo en `src/planeamiento/`, `tests/planeamiento/`, `docs/planeamiento/`; piezas 1, 2 y 4 ya hechas y verificadas en `docs/entrega/otra_ia/B/`, moverlas en la pieza 19). Reemplaza a OT-B01.
