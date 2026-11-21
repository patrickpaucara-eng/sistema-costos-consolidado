# OT-C04 · Calcular y exportar con un clic desde la interfaz (Codex · medio)
Rama `codex/ot-c04` desde `desarrollo/mono`. PR contra `desarrollo/mono`. No unir.
**Objetivo:** el usuario nunca toca archivos: elige periodo y síntesis, pulsa **Calcular** y luego **Exportar**.
1. Endpoint `POST /api/calcular?sintesis=REAL|CONTABLE&periodo=AAAA-MM` que llama a `reyna_local.resultados.construir(...)` sobre el libro del caso (generado con `casos/frenosa/generar.py` si no existe en la carpeta de datos), valida con `contrato.validar` y guarda `resultados/frenosa_<periodo>_<sintesis>.json` en la carpeta de datos. **No modificar** `resultados.py`, `src/metodos`, `src/analitica*` ni `casos/` (cálculo de Claude). Si falta algo, pídelo.
2. En la interfaz: botón **Calcular** junto al selector de periodo/síntesis (con indicador «calculando…»), y en **Reportes** un botón por exportador (Excel resultados, Excel analítica, Excel proyección, HTML sin conexión, Word código) que descarga o abre el archivo.
3. Armonizar el **HTML sin conexión** con el diseño del dashboard (mismos colores, KPI y gráficos; sin URL externas).
**Aceptación:** prueba que hace calcular → resultados → exportar para julio 2010 REAL y CONTABLE y compara 3 cifras con el JSON; `python tools/verificar.py` en VERDE; capturas en `docs/entrega/evidencias/OT-C04/`; tiempos en `docs/entrega/tiempos/codex.csv`.
