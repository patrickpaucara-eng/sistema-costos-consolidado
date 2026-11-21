# OT-C01 · Pantallas y dashboard (Codex · esfuerzo medio)
Rama: `codex/ot-c01` desde `desarrollo/mono`. PR contra `desarrollo/mono`. No unir.
**Objetivo:** el sistema se ve y se navega como un producto profesional (20 % de la nota: «flexible, fácil, agradable»).
**Entrada:** el contrato `src/reyna_local/contrato.py` y su ejemplo `tests/fixtures/contrato/resultados_ejemplo.json`. Las pantallas SOLO leen el contrato; no calculan costos.
**Hacer:**
1. Endpoint `GET /api/resultados?sintesis=REAL|CONTABLE|ESTIMADO&periodo=AAAA-MM` en `__main__.py`. Por ahora devuelve el ejemplo (marcado «EJEMPLO»); Claude conectará el cálculo real después sin cambiar la forma.
2. Navegación en `web/index.html` (o varios archivos en `web/`): Inicio · Cargar (lo existente) · Cerrar mes · **Dashboard** · Costos por objeto · Análisis (hallazgos y relevancia) · Proyección · Simulación (escenarios) · Propuestas · Reportes. Selector de síntesis y periodo visible siempre.
3. **Dashboard:** 5 KPI del contrato; gráfico de línea con histórico + actual + proyectado determinístico y banda estocástica P05–P95; barras apiladas por objeto (md, mod, cif, admin, gasto_venta, financiero); Pareto de relevancia con los críticos marcados; tabla de hallazgos con impacto en S/.
4. Gráficos con JavaScript **embebido** (sin CDN: debe funcionar sin internet). Diseño limpio, consistente, legible, números con separador de miles.
5. Errores siempre en español y sin texto técnico.
**Aceptación:** `python tools/verificar.py` en VERDE; las 55 pruebas previas siguen pasando; una prueba nueva que arranca el servidor, pide `/api/resultados` y valida con `contrato.validar`; capturas de cada pantalla en `docs/entrega/evidencias/OT-C01/`. Registrar la sesión en `docs/entrega/REGISTRO_TIEMPOS.xlsx`.
