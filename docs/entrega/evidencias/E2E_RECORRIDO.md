# Prueba de punta a punta (25-nov, Claude) — sin parches

Recorrido por la API local sobre copias: Frenosa 2010-12 y SERVITEC 2025-07. Navegación de pantallas: `tests/test_esqueleto_navegacion.py`; registro T14–T20, T14.1 y T16: `tests/test_formulario_guiado.py` y `tests/test_devoluciones.py`.

**Resultado: 28 de 30 pasos correctos.**

| Paso | Esperado | Resultado | Obtenido |
|---|---|---|---|
| frenosa: calcular REAL | 200 | OK | 200 |
| frenosa: resultados | 200 con objetos y trazas | OK | 200 |
| frenosa: sello | VIGENTE | OK | {'estado': 'VIGENTE'} |
| frenosa: exportar resultados | 201 | OK | 201 |
| frenosa: exportar analitica | 201 | OK | 201 |
| frenosa: exportar proyeccion | 201 | OK | 201 |
| frenosa: exportar html | 201 | OK | 201 |
| frenosa: exportar informe | 201 | OK | 201 |
| frenosa: exportar presentacion | 201 | OK | 201 |
| frenosa: periodos bimestre | 200 | OK | 200 |
| frenosa: proyección granular 6 meses | 200 con 6 meses | OK | 200 |
| frenosa: calibrar aprendizaje | 200 | OK | 200 |
| frenosa: ver aprendizaje | 200 | OK | 200 |
| frenosa: cotizar pedido especial | 200 | ERROR | {'error': 'No hay un periodo cerrado para cotizar.'} |
| segundo: calcular REAL | 200 | OK | 200 |
| segundo: resultados | 200 con objetos y trazas | OK | 200 |
| SERVITEC julio REAL | REB 22,975 / MPR 5,165 | OK | {'MPR': 5165.0, 'REB': 22975.0} |
| segundo: sello | VIGENTE | OK | {'estado': 'VIGENTE'} |
| segundo: exportar resultados | 201 | OK | 201 |
| segundo: exportar analitica | 201 | OK | 201 |
| segundo: exportar proyeccion | 201 | OK | 201 |
| segundo: exportar html | 201 | OK | 201 |
| segundo: exportar informe | 201 | OK | 201 |
| segundo: exportar presentacion | 201 | OK | 201 |
| segundo: periodos bimestre | 200 | OK | 200 |
| segundo: proyección granular 6 meses | 200 con 6 meses | OK | 200 |
| segundo: calibrar aprendizaje | 200 | OK | 200 |
| segundo: ver aprendizaje | 200 | OK | 200 |
| segundo: cotizar pedido especial | 200 | ERROR | {'error': 'No hay un periodo cerrado para cotizar.'} |
| frenosa: ver cierres | 200 | OK | 200 |
