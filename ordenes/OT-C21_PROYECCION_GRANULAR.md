# OT-C21 · Proyección granular, bloques y sensibilidad (tarea 2.4) — Codex nivel ALTO
Rama `codex/C21` desde `desarrollo/mono` (después de unir C18); PR contra `desarrollo/mono`. Diseño: `docs/diseno/PROYECCION_GRANULAR.md` (léelo entero).
No toques `src/metodos/reparto_etapas.py` ni `resultados.py`: solo los llamas. Módulo nuevo `src/reyna_local/proyeccion.py`.

## Pasos
1. Leer hechos y valuación como `resultados.calcular_periodos` (`P.leer_conceptos(libro, R.CONSUME)` y `resultados.previos`). Mes base = último periodo.
2. Construir cada mes h: copia profunda de los hechos; filas nuevas de PERIODO (INICIO = primer día del mes h), OBJETO (`NUMERO@periodo`),
   EVENTO (`NUMERO` → `P<h>-<NUMERO>`, OBJETO renombrado), LINEA y MEDIDA escaladas según el diseño; VALUACION_PROMEDIO de las salidas clonadas con la misma clave nueva.
3. Correr `R.interno(hechos_clon, dict(PER=periodo_h, EMP=emp), previos_clon)`; agrupar por producto (OBJ_PRO de la orden original).
4. Factores: `analisis.pronostico_puntual(serie, H)` (ya existe); parámetro `factores={"vol":{p:x}, "pre":{r:x}, "pv":{p:x}}` los fija por mes 1..H.
5. Tabla opcional BLOQUE (añádela a `libro_dbd` como tabla opcional, a la plantilla y al DBD; vacía en Frenosa).
6. Sensibilidad ±10 % del mes 1, ordenada por |Δ margen|.
7. `GET /api/proyeccion?empresa&meses` en `__main__.py`. Sin pantalla (C17 la pinta).

## Pruebas obligatorias `tests/test_proyeccion_granular.py`
- MINI del diseño con hechos sintéticos: A 1,938.46 · B 861.54; con bloque MOD → 1,500, A 1,038.46 · B 461.54.
- Identidad en Frenosa: factores 1 → costo por producto del mes 1 = costo del mes base (tolerancia 0.01).
- Fijo no se mueve: con vol ×2 y todo fijo salvo MD, el total de no-MD es igual al base.
- Sensibilidad: el factor de mayor |Δ| aparece primero; +10 % y −10 % tienen signos opuestos.
- El libro original no cambia (SHA antes y después).
Aceptación: COMPUERTA VERDE; publicación de resultados idéntica a la de antes.
