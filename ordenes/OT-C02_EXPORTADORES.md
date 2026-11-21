# OT-C02 · Exportadores y documentos generados (Codex · esfuerzo medio)
Rama: `codex/ot-c02` desde `desarrollo/mono`. PR contra `desarrollo/mono`. No unir. No toca `web/` (eso es OT-C01).
**Objetivo:** que los entregables de la mono salgan del sistema con un clic, desde el contrato de resultados.
**Hacer (módulo `src/reyna_local/exportar.py`, sin calcular costos):**
1. Excel de resultados (entregable 6): objetos, actividades, estado de resultados NIIF 18.
2. Excel de analítica (7): relevancia, hallazgos.
3. Excel de proyección y propuestas (8): serie proyectada (determinística y P05/P50/P95), escenarios, propuestas con impacto.
4. **HTML sin conexión (12):** un solo archivo con el dashboard y los datos embebidos (mismo diseño que OT-C01 cuando esté; mientras, uno simple).
5. Word con todo el código fuente (3): script `tools/codigo_a_word.py` que recorre `src/` y `tools/` con índice. Usar `python-docx` con versión fija en `pyproject.toml`.
6. Endpoint `POST /api/exportar?tipo=...` que deja el archivo en la carpeta de datos y devuelve su ruta.
**Aceptación:** `python tools/verificar.py` en VERDE; pruebas que abren cada archivo generado y comparan 3 cifras con el contrato de ejemplo; el HTML abre sin internet (ninguna URL externa). Registrar tiempos.
