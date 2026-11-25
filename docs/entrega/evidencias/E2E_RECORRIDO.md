# Prueba de punta a punta (25-nov) · OT-C25

Recorrido de `python tools/e2e_recorrido.py` por la API local sobre datos temporales: Frenosa 2010-12 y SERVITEC 2025-07.

**Resultado observado: 29 de 30 pasos correctos.**

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
| frenosa: cotizar pedido especial | 200 | ERROR | {'error': 'La actividad A-CC no tiene un inductor único'} |
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
| segundo: cotizar pedido especial | 200 | OK | 200 |
| frenosa: ver cierres | 200 | OK | 200 |

La ejecución devolvió código cero aun con un paso ERROR; revisar el contenido, no solo el código de salida. La navegación y los registros tienen pruebas separadas.
