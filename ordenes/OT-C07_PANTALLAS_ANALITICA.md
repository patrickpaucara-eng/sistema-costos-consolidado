# OT-C07 · Pantallas de analítica y dashboard histórico/actual/proyectado (Codex · medio)
Rama `codex/ot-c07` **desde `codex/ot-c04`** (las dos tocan `web/`; así no chocan). PR contra `desarrollo/mono`. No unir.
**Fuente única:** los JSON publicados `datos/resultados/frenosa_<AAAA-MM>_<REAL|CONTABLE|ESTIMADO>.json` (36 archivos, 2010-01..12) vía `/api/resultados`. La interfaz **solo lee** el contrato; no calcula nada. Si falta un dato, pídelo.

## Qué mostrar (campos del contrato)
1. **Dashboard temporal** (`serie`): una línea por `ventas`, `costo_total` y `margen`. Tramos con estilo distinto: `HISTORICO` (sólido), `ACTUAL` (marcado), `PROYECTADO_DET` (punteado) y `PROYECTADO_EST` como **banda sombreada p05–p95 con línea p50**. Leyenda «determinístico» vs «estocástico». Pie con `proyeccion_info` (modelo, MASE, semilla, simulaciones). Si `serie` no trae proyectadas (enero–junio, historia corta), mostrar el aviso «Se necesitan más de 6 meses para proyectar».
2. **Relevancia** (`relevancia`): Pareto (barras + % acumulado), críticos (`critico=true`) resaltados.
3. **Diagnóstico** (`hallazgos`): tarjetas con `mensaje`, `impacto` (S/), `causa`, `variacion` (%).
4. **Escenarios** (`escenarios`): tabla y gráfico de rango (p05–p50–p95 del margen) por escenario; columna `prob_perdida` en %, en rojo si > 10 %.
5. **Propuestas** (`propuestas`): tabla código, descripción, impacto anual, plazo, responsable; total del impacto.
6. **Síntesis ESTIMADO** (`estimacion`, solo cuando existe): por producto `cu_total` con banda p05–p95, método y MASE; texto fijo: «Estimación estadística fuera de muestra (no es un estándar)».
7. Selector de síntesis con las tres: REAL, CONTABLE, ESTIMADO. En CONTABLE, nota: «Financieros fuera del inventario (NIC 2 / NIIF 18)».
8. El **HTML sin conexión** (exportador) incluye las mismas secciones 1–6.

## Aceptación
- Prueba que carga 2010-12 en las tres síntesis y comprueba que cada sección tiene el número de filas del JSON y que la banda usa p05/p95.
- Prueba con 2010-03: aparece el aviso de historia corta y no se rompe.
- `python tools/verificar.py` VERDE; capturas por sección en `docs/entrega/evidencias/OT-C07/`; tiempos en `docs/entrega/tiempos/codex.csv`.
- Lenguaje para usuario no técnico; errores en español.
