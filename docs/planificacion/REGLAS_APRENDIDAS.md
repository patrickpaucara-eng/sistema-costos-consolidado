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
