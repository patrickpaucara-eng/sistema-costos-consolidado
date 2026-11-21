# Origen de los módulos de costeo y analítica trasladados (Etapa 1, 21-nov-2026)
Repositorio histórico `sistema-costos-reyna`, rama `desarrollo/ola1`, commit `cac2501d9f712655dda466d216dc5bff2dd446a5` (incluye D12, D1 y la corrección de referencias de I-5).
Trasladados sin cambios de lógica, con los mismos nombres de módulo (los imports no se reescriben):
- `kit/metodos` → `src/metodos` (métodos de costeo: reparto por etapas/ABC, valuación, liquidación, simulación de cierre…)
- `kit/analitica`, `kit/analitica2` → `src/` (hallazgos, pronóstico, Monte Carlo, riesgo, catálogo, seguimiento)
- `kit/casos/comun.py`, `kit/puerto_lectura.py`, `kit/rutas.py`, `informes/V41/integra_env.py` → `src/`
- `fuente/DBD_Fuente.xlsx`, `fuente/Datos_Iniciales.xlsx` → `fuente/`
Verificación en origen: pytest 521, historia 392/392, O-1 66/66.
