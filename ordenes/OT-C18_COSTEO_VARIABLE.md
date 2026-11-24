# OT-C18 · Comportamiento del costo, controlabilidad y costeo variable (tarea 2.9) — Codex nivel ALTO
Rama `codex/C18`; PR contra `desarrollo/mono`. Lee antes `docs/planificacion/DECISIONES_DUENO.md` (filas 23/24-nov).
No toques `src/metodos/reparto_etapas.py`. Trabaja en un módulo nuevo `src/reyna_local/variable.py` + llamada desde `resultados.construir` + contrato.

## Datos (columnas OPCIONALES del libro; agrégalas a `libro_dbd.COLUMNAS_OPCIONALES`, a la plantilla y al DBD como en ACT_NIVEL)
- `RECURSO.REC_COMPORT`: F (fijo en el periodo relevante), V (variable), M (mixto). Vacío = se estima por regresión (abajo) o F.
- `RECURSO.REC_PCT_VAR`: % variable si M (0–100).
- `RECURSO.REC_CTRL`: S/N, ¿lo controla el responsable del centro/actividad? Vacío = S.

## Cálculo (solo lee: trazas raíz por orden = cuánto de cada recurso llegó a cada orden)
1. Variable de la orden = Σ por recurso (monto raíz × fracción variable). Fijo = el resto. Pérdida y ocio: fijos.
2. Regresión (solo si REC_COMPORT vacío): costo mensual del recurso vs. su inductor del mes; con ≥ 6 meses y R² ≥ 0.7 → fracción variable = b·x̄ / ȳ acotada a [0,1]; si no → F. Guardar n, R², a, b. La regresión NUNCA cambia el inductor.
3. Por producto: ventas, costo variable, margen de contribución, fijos del periodo, punto de equilibrio en ventas = fijos / (MC/ventas) (mezcla del mes).
4. Controlabilidad: las propuestas (`r["propuestas"]`) cuyo elemento/recurso sea no controlable se eliminan y se listan en `r["costeo_variable"]["no_controlables"]` con el motivo «costo compartido no controlable (Oria)».
5. Contrato: campo opcional `r["costeo_variable"] = {productos:[...], fijos_periodo, punto_equilibrio_ventas, regresiones:[...], no_controlables:[...]}` en las tres síntesis.

## Caso a mano (prueba obligatoria `tests/test_costeo_variable.py`, con hechos sintéticos)
MAT (V): A 2,000, B 1,000 · MOD (F): A 2,000, B 1,000 · LUZ (M, 40 % variable): A 600, B 400. Ventas A 100 u × 80 = 8,000; B 50 u × 60 = 3,000.
Variable A 2,240 · B 1,160. MC A 5,760 · B 1,840 · total 7,600. Fijos 3,600. Resultado 4,000.
Punto de equilibrio = 3,600 / (7,600/11,000) = **5,210.53**. Costo variable unitario A 22.40 · B 23.20.
Además: una propuesta sobre un recurso con REC_CTRL = N desaparece de `propuestas`.
Aceptación: COMPUERTA VERDE; Frenosa sin columnas nuevas da los mismos costos que hoy.
