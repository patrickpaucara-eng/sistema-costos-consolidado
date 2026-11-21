# OT-C06 · Generadores de los documentos Word de la entrega (Codex · medio; formato bajo)
Rama `codex/ot-c06` desde `desarrollo/mono`. PR contra `desarrollo/mono`. No unir.
**Objetivo:** que cada Word de la monografía se genere con un comando, con buen formato (portada, índice, numeración, tablas legibles).
Generadores en `tools/documentos/` (python-docx con versión fija):
1. **Entregable 1 · Cadena de chats:** convierte los `.md` exportados de las conversaciones (Claude y Codex) puestos en `docs/entrega/chats/` a un Word ordenado por fecha, con quién habla (dueño / IA) y los resultados.
2. **Entregable 2 · Etapas del desarrollo:** desde `docs/planificacion/PLAN_MONOGRAFIA_Y_SISTEMA.md`, `ESTADO.md`, `REGLAS_APRENDIDAS.md` y las evidencias de `docs/entrega/evidencias/`.
3. **Entregable 4 · Prueba de funcionamiento:** corre pytest con salida JUnit y arma el Word: cada prueba con su nombre, propósito (docstring) y resultado; más las capturas de OT-C01/OT-C04.
4. **Entregable 10 · Manual de usuario:** pantalla por pantalla con las capturas y los pasos (Cargar → Validar → Importar → Cerrar → Calcular → Dashboard → Reportes).
5. **Entregable 9 · Manual descriptivo:** solo la **plantilla** (capítulos: arquitectura, DBD/MCD, métodos, síntesis REAL/CONTABLE/ESTIMADO, analítica, seguridad) con marcadores `[CLAUDE]` donde Claude escribirá el contenido técnico.
**Aceptación:** los cinco Word se generan sin error y abren; prueba que verifica títulos y cantidad de secciones; `python tools/verificar.py` en VERDE; tiempos en `codex.csv`.
