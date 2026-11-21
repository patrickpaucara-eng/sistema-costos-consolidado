# Etapa 3 · Analítica (diagnóstico, descriptivo, predictivo, prescriptivo) y síntesis ESTIMADO

Módulo `src/reyna_local/analisis.py`. Lee solo resultados publicados; nunca recalcula costos.

| Análisis | Cómo | Prueba |
|---|---|---|
| Descriptivo | Serie mensual por producto y elemento | contrato |
| Diagnóstico (causa raíz) | Costo unitario del mes vs promedio de 6 meses; causa = elemento con mayor variación por unidad | `test_diagnostico_a_mano` |
| Relevancia | Pareto de elementos; crítico = acumula hasta 80 % | `test_relevancia_pareto` |
| Predictivo determinístico (6 meses) | Ventas y costo con el método que menos se equivoca fuera de muestra (ingenuo, media, SES, Holt; MASE) | `test_tres_sintesis...` |
| Predictivo estocástico | Monte Carlo (semilla 2010, 2 000 rutas) con los errores fuera de muestra del margen, acumulados en el horizonte → P05/P50/P95 | `test_proyeccion_reproducible_y_banda_creciente` |
| ESTIMADO (D-8) | Costo más fiel según la historia, por elemento, con datos solo anteriores al mes (fuera de muestra) y banda; no es estándar | `test_estimado_es_fuera_de_muestra` |
| Escenarios | Base, material +10 %, volumen −10 %, salarios +5 %, precio de venta +3 %; Monte Carlo triangular de margen y probabilidad de pérdida | `test_escenario_base_es_el_resultado_publicado` |
| Prescriptivo | Propuestas con impacto anual = brecha contra el promedio de 6 meses × 12 | contrato |

## Correcciones hechas con ojo crítico (RA-09, RA-10)
- La primera banda estocástica sorteaba errores de ventas y costo **desalineados** (cada serie elige su método y sus errores empiezan en meses distintos) → banda artificialmente ancha. Ahora la banda se calcula sobre el **margen** con sus propios errores.
- Las propuestas comparaban contra el **mejor** mes histórico (puede ser atípico) → impacto inflado. Ahora contra el **promedio de 6 meses**, coherente con el diagnóstico.

## Límite dicho en el informe
El margen de Frenosa 2010 es muy volátil (−111 mil a +296 mil entre meses) y 12 meses no bastan para estimar estacionalidad (requiere ≥ 24): la banda a 6 meses es ancha **por los datos, no por el método**. El pronóstico del margen es apenas mejor que el ingenuo (MASE 0.95), y se informa así.
