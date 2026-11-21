# OT-C08 · Paquete de los 13 entregables con un comando (Codex · medio)
Rama `codex/ot-c08` desde `desarrollo/mono` (≥ `4837244`). PR contra `desarrollo/mono`. No unir.
**Objetivo:** `python tools/entrega/armar.py --periodo 2010-12` deja en `entrega_MN01/` todo lo que pide Oria, listo para comprimir.
1. **Excel faltantes** (nuevos tipos en `exportar.py`, sin recalcular nada):
   - `entrada`: datos de entrada del caso tal como los lee el cálculo (`datos/frenosa/*.csv` + `datos/frenosa_supuestos/*.csv`), una hoja por archivo, hoja `FUENTES` con FUENTES.md y LEEME.md.
   - `propuestas`: hoja Propuestas (`propuestas`), hoja Escenarios (`escenarios`, con p05/p50/p95 y prob. de pérdida), hoja Relevancia, total de impacto anual.
2. **Excel existentes** (resultados, analítica, proyección) generados para REAL, CONTABLE y ESTIMADO del periodo.
3. **HTML sin conexión** con el mismo diseño del dashboard (cierra el pendiente de C07 «diseño simplificado»): KPI, serie con banda p05–p95, relevancia, diagnóstico, escenarios, propuestas, ESTIMADO. Sin URL externas (prueba que busca `http` en el archivo).
4. **Word**: los que produce `tools/documentos/generar.py` + `codigo` (código fuente).
5. **Registro de tiempos**: correr `tools/consolidar_tiempos.py` y copiar el .xlsx.
6. `entrega_MN01/LEEME.txt`: índice numerado 1–13 con el nombre de cada archivo (el EXE figura como «se agrega al compilar en Windows»).
**Aceptación:** prueba que arma la carpeta en un directorio temporal y verifica que existan los 13 ítems (menos el EXE) y que los 3 Excel de resultados repiten `kpi.costo_total` del JSON; compuerta VERDE; tiempos en `codex.csv`. No tocar cálculo ni pruebas existentes.
