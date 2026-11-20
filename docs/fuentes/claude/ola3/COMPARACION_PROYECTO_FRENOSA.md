
## 7. Las fortalezas del pasado tienen debilidades: cómo potenciarlas con nuestra base (no clonarlas)
**Naturaleza [VERIFICADO contra el código actual]:** las 7 fortalezas son **capas de presentación sobre datos que nuestra base ya produce** (RESULTADO_METODO, cuentas, kardex, ALERTA, EST_DECISION, LOG_TRX). Ninguna necesita datos nuevos ni cambia el cálculo, **salvo el flete** (agrega un dato y cambia el costo de compra) y **la simulación** (recalcula, pero en una copia). Por eso son de riesgo bajo: leen lo publicado y lo muestran mejor.

| Fortaleza del pasado | Su debilidad real | Cómo la potencia nuestra base | Naturaleza | Dónde va |
|---|---|---|---|---|
| **Dashboard** | Recalcula desde el Excel cada vez: el número del dashboard puede no ser el auditado; sin traza al origen; sin varias empresas | KPIs leídos **solo de lo publicado** (RESULTADO_METODO con huella); cada número abre su traza N1→N4; filtro por empresa; alertas H-03/H-13 con su impacto en S/ junto al gráfico | Solo lectura | Ola 1b+ |
| **Análisis por periodos** | Suma meses **recalculados** (un mes reimportado cambia la historia); el costo unitario consolidado mezcla OT de meses distintos agrupando por producto | Consolida **periodos cerrados e inmutables**; muestra aparte los hechos tardíos (con su mes de origen); evolución con el puente publicado/recalculado de I-3 | Solo lectura | Ola 1b+ (muchos meses: tras D13) |
| **Simulación con lápiz** | Cambia el dato de origen y **reparte el nuevo total entre meses en proporción** (sin sustento); no registra quién simuló ni para qué decisión | Simula **en una copia** (la base nunca se toca); cada simulación queda como escenario con semilla y, si se adopta, pasa a PROPUESTA → aprobación → seguimiento previsto vs ocurrido (SEG-01). Riesgo con Monte Carlo/CVaR ya construidos | Recalcula en copia | Ola 5 |
| **Agente de consulta** | Coincidencia de palabras; «confianza 109 %»; responde sobre datos recalculados; no distingue empresa | Responde **solo con lo publicado** y su traza; vocabulario y sinónimos como datos (DBD_4e); confianza acotada [0,1] y «no sé» cuando no hay pregunta del catálogo; filtrado por la empresa del usuario | Solo lectura | Ola 5 |
| **Propuestas cuantificadas** | Se quedan en el informe: nadie mide si funcionaron | Ya potenciado: catálogo PROPUESTA + aprobación + **medición de lo previsto frente a lo ocurrido** + autonomía que baja si falla | Ya existe | — |
| **Importar varios meses** | Reimportar **reemplaza** el mes (rompe la auditoría) | Varios meses en orden, cada uno validado, **nunca reemplaza**: un mes cerrado rechaza la carga y lo tardío entra con referencia | Puerto de carga | Tras D13 |
| **Flete en la compra** | Mezcla datos ficticios con reales en la misma hoja | Campo FLETE en T14 prorrateado a las líneas, con caso a mano y paridad Excel↔Python | **Cambia el cálculo** | Ola 3 |
| **Excel maestro autodocumentado** | Documentación escrita a mano: se desactualiza | Hojas Diccionario/Reglas **generadas desde el DBD** (TRX_CAMPO): nunca se desfasan | Solo lectura | Ola 1b (inmediato) |

## 8. Ubicación estratégica (por qué en ese orden)
1. **Ola 1b+ (ya, sin riesgo):** plantilla autodocumentada → dashboard → análisis por periodos. Son lo más visible para el usuario y el profesor y solo leen lo publicado. Dependencia: ninguna (el análisis de muchos meses espera a D13).
2. **D13 rendimiento** antes de importar varios meses: sin índice, 6 meses tardan minutos por mes.
3. **Ola 3 (credibilidad):** flete junto con D9 (un solo escritor de cuentas), porque ambos tocan el costo y se prueban con el mismo caso a mano.
4. **Ola 5 (decisión):** simulación en copia + consulta guiada + capa predictiva: las tres usan el mismo motor de escenarios y el mismo catálogo; construirlas juntas evita tres mecanismos distintos.
