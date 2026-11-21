# Reglas aprendidas (cada error se vuelve una regla y una prueba)

| # | Error que ocurrió | Regla | Prueba que lo impide |
|---|---|---|---|
| RA-01 | I-5 declaró referencias a EMPRESA sin columna; la coherencia del DBD «solo avisaba» (16 errores pasaron) | La coherencia del DBD con errores **bloquea** | (repo histórica) coherencia 0 errores en construir |
| RA-02 | VBA usó `emp` en vez de `empA` (Option Explicit) | Toda variable nueva se verifica contra las declaradas | Lint VBA (congelado) |
| RA-03 | El espejo y VBA resolvían distinto la clave del nivel 1 | Un solo motor (Python) | VBA congelado (D-1) |
| RA-04 | `git stash` al cambiar de rama perdió un cambio | Commit antes de cambiar de rama | — (disciplina) |
| RA-05 | Una cifra de la hoja de defensa («1.2 s/mes») no medía lo que decía | Toda cifra pública sale de una medición registrada | Evidencia en `docs/entrega/evidencias/` |
| RA-06 | Mezclar capas (fiscal en real) destruye la trazabilidad | CONTABLE nunca capitaliza financieros ni no atribuibles | `tests/test_contrato.py` |
| RA-07 | Una hoja de entrada vacía no se exportó por generar archivos solo al encontrar filas | Crear un CSV con cabecera para toda hoja declarada, incluso sin filas | `tests/test_frenosa_fuentes.py` |
| RA-07 | Codex y Claude editaron el mismo .xlsx de tiempos → conflicto binario | Cada agente registra en su CSV; un script arma el .xlsx | `tools/consolidar_tiempos.py` |
| RA-08 | Claude puso un archivo de supuestos entre los datos reales del caso (la prueba de Codex lo detectó) | Datos del caso y supuestos van en carpetas separadas | `tests/test_frenosa_fuentes.py` |
| RA-09 | Banda estocástica con errores de dos series desalineados (métodos distintos) → banda inflada | La incertidumbre se mide sobre la variable que se reporta (margen), con sus propios errores | `test_proyeccion_reproducible_y_banda_creciente` |
| RA-10 | Propuesta contra el mejor mes histórico → impacto inflado por un atípico | Brechas contra el promedio de la ventana del diagnóstico | `src/reyna_local/analisis.py` (propuestas) |
| RA-11 | Una prueba usaba un periodo "sin datos" (2010-08) para probar el ejemplo de respaldo; al publicar datos reales dejó de ser ausente | Las pruebas de "dato ausente" usan un periodo fuera del rango del caso (2011-xx) | `tests/test_api_resultados.py` |
| RA-12 | El CSV de supuestos quedó fuera del repo (`datos/` ignorado) y la compuerta pasaba solo en mi copia local | `.gitignore` con excepciones para insumos; antes de cada push correr la compuerta en un clon limpio | `.gitignore`, clon limpio |
| RA-13 | El generador de Frenosa requiere `datos/frenosa_supuestos/Gastos_Operativos_SUPUESTOS.csv`, ausente en la revisión d214596; la compuerta y el cálculo fallan | Las entradas requeridas por el generador deben estar presentes y versionadas antes de publicar resultados o exigir cálculo reproducible | `tests/test_insumos_frenosa_presentes.py` |
