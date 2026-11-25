# Ciclo de aprendizaje autónomo (tarea 2.5) — diseño

Reemplaza el catálogo fijo (no escalable, decisión 23-nov). El sistema aprende de su propia historia, pero **nunca toca el costo
real**: solo calibra estimaciones, umbrales, prioridades, la proyección (2.4) y la cotización (2.4b).

## Calibradores (cada uno: valor del libro → valor aprendido + evidencia)
| Calibrador | Dato | Regla |
|---|---|---|
| Consumo estándar por componente | cantidad real / unidad buena por mes (DIFERENCIA.DIF_QREAL / OBJ_CAN) vs COMPONENTE.CMP_CAN_EST | mediana; atípicos marcados si \|x − mediana\| > 3 × 1.4826 × MAD (se informan, la mediana ya los resiste) |
| Merma normal | merma % por mes (DIF_QMER / DIF_QREAL) vs CMP_MERMA | igual |
| Umbral del diagnóstico | variación % mensual del costo unitario por producto | umbral = max(5 %, 2 × MAD) |
| Probabilidad de éxito de propuestas | propuestas pasadas y su cumplimiento (≥ 0.8 = éxito) por tipo/causa | Beta-Binomial, previa Beta(1,1): p = (1 + éxitos) / (2 + intentos); prioridad = impacto × p |
| Modelo de pronóstico por serie | lo que ya elige PRONÓSTICO | se guarda modelo y MASE para auditoría |
| Fuerza del inductor | costo mensual de la actividad vs su inductor | R² < 0.5 con ≥ 6 meses → **alerta** «inductor débil»; nunca cambia el inductor (decisión 24-nov) |

## Guardas (quién decide)
- **APLICADO automático** si mejora fuera de muestra (origen móvil: predecir el mes t con la historia hasta t−1; error absoluto medio menor que el del valor del libro) **y** \|cambio\| ≤ 20 %.
- Si no: **PENDIENTE** → el dueño aprueba o rechaza (API). RECHAZADO no se vuelve a proponer con la misma evidencia.
- Vigencia: desde el periodo siguiente al cálculo; nunca retroactivo. El libro no se modifica: la capa vive en `datos/aprendizaje/<empresa>.json`
  (id, calibrador, objeto, valor_libro, valor_aprendido, cambio_pct, mae_libro, mae_aprendido, estado, vigente_desde, decidido_por, fecha).

## Guarda por calibrador (aclaración 25-nov a pedido de Codex)
| Calibrador | Referencia | Error fuera de muestra | Estado |
|---|---|---|---|
| Consumo estándar | COMPONENTE.CMP_CAN_EST | MAE de un paso (mes t con la historia hasta t−1, desde t = 3) del aprendido vs. el del libro | APLICADO si mejora y \|cambio\| ≤ 20 %; si no, PENDIENTE |
| Merma normal | COMPONENTE.CMP_MERMA | igual | igual |
| Umbral del diagnóstico | 5 % (valor actual del sistema) | no aplica (regla estadística, no toca costos) | APLICADO automático con ≥ 6 meses |
| Probabilidad de éxito | previa Beta(1,1) | no aplica | APLICADO automático (solo ordena propuestas) |
| Modelo de pronóstico / R² del inductor | — | ya validado por PRONÓSTICO / no aplica | INFORMATIVO (solo se registra o alerta) |
Solo los estándares pueden quedar PENDIENTES, porque son los únicos que cambian cifras de proyección y cotización.
Interfaz para otros módulos: `aprendizaje.estandar_vigente(empresa, producto, recurso, periodo) → (valor, merma) | None` (solo APLICADO y vigente).
C23 la llama si existe; sin capa, usa el libro.

## Casos a mano (pruebas obligatorias)
1. Consumo [10, 10.2, 9.9, 10.1, 15, 10] contra libro 12 → mediana **10.05**, 15 marcado atípico, cambio −16.25 %, mejora fuera de muestra → **APLICADO**.
2. Misma historia contra libro 20 → cambio −49.75 % → **PENDIENTE**.
3. Propuestas del mismo tipo: 2 éxitos de 3 → p = 3/5 = **0.6** → impacto 1,000 → prioridad **600**.
4. Variaciones con MAD 4 % → umbral **8 %**; con MAD 1 % → **5 %**.
5. Costos REAL y CONTABLE publicados idénticos con y sin la capa de aprendizaje.
