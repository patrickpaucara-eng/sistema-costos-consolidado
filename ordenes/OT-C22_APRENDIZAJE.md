# OT-C22 · Ciclo de aprendizaje con guardas (tarea 2.5) — Codex nivel ALTO
Rama `codex/C22` desde `desarrollo/mono`; PR contra `desarrollo/mono`. Diseño: `docs/diseno/APRENDIZAJE.md` (léelo entero).
No toques el motor ni `resultados.py` salvo la llamada indicada. Módulo nuevo `src/reyna_local/aprendizaje.py`.

## Pasos
1. `calibrar(libro, emp, resultados_publicados)` → lista de calibraciones del diseño (solo lee libro y resultados publicados).
2. Guardas: APLICADO / PENDIENTE según el diseño; persistir en `datos/aprendizaje/<empresa>.json` (JSON ordenado, sin fechas de reloj en las pruebas: parámetro `hoy`).
3. Uso (solo valores APLICADOS y vigentes para el periodo): `analisis.diagnostico(..., umbral=...)` recibe el umbral aprendido; `propuestas` agrega
   `probabilidad` y `prioridad` (impacto × p) y ordena por prioridad; `proyeccion` (C21) y el cotizador (C23) leen el consumo estándar aprendido si existe.
   La llamada desde `resultados.construir` es una línea que aplica la capa a hallazgos y propuestas; los costos no se tocan.
4. API: `GET /api/aprendizaje?empresa` y `POST /api/aprendizaje/decidir {id, decision: APROBAR|RECHAZAR}`.
5. Registrar en `docs/entrega/REGISTRO_CAPACIDADES.md`.

## Pruebas obligatorias `tests/test_aprendizaje.py`
Los 5 casos a mano del diseño, más: RECHAZADO no reaparece; un valor calculado en 2010-06 rige desde 2010-07 y no cambia 2010-06.
Aceptación: COMPUERTA VERDE; publicación de costos idéntica (solo cambian hallazgos/propuestas si hay capa aplicada; Frenosa sin capa = igual).
