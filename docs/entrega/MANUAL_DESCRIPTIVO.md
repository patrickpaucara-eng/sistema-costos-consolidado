# Manual descriptivo del sistema de costos

## 1. Arquitectura
| Capa | Qué es | Dónde |
|---|---|---|
| Datos | Libro Excel con el modelo DBD: catálogos (recursos, centros, actividades, criterios, órdenes) y movimientos (eventos, líneas, kardex, medidas, ventas) | `casos/plantilla_dbd.xlsx`, `casos/libros/` |
| Operación | Transacciones T14–T20 validadas por reglas del propio libro (TRX, TRX_CAMPO, TOP); cada una deja evento, recibo y respaldo | `src/reyna_local/store.py` |
| Cálculo | Motor ABC por etapas; valuación de kardex; síntesis | `src/metodos/reparto_etapas.py`, `src/reyna_local/resultados.py` |
| Contrato | Estructura única de resultados, validada; sello SHA-256 | `src/reyna_local/contrato.py`, `calculo_local.py` |
| Analítica | Descriptivo, diagnóstico, relevancia, proyección, escenarios, propuestas, aprendizaje | `analisis.py`, `proyeccion.py`, `aprendizaje.py`, `variable.py`, `estrategico.py`, `cotizador.py` |
| Presentación | Servidor local + HTML; exportadores Excel/Word/HTML | `__main__.py`, `web/index.html`, `exportar.py` |

Regla de diseño: las pantallas y documentos **solo leen el contrato**; nunca recalculan costos.

## 2. Modelo de costeo (MCD/DBD de Tino Reyna; ABC escalonado de W. Oria)
| Etapa | Origen → destino | Base |
|---|---|---|
| P1 | Material → orden | Kardex promedio ponderado; merma en exceso aparte |
| P2/P3 | Mano de obra y servicios directos → actividad u orden | Horas u otro inductor |
| P4A | Indirectos → centros | m², kWh, % |
| P4B | Centros de apoyo ↔ entre sí → centros productivos | Recíproco exacto (N = (I − P)⁻¹) |
| P4D/P4E | Centros → actividades; estratégicas → apoyo → operativas | Inductor único por actividad |
| P4C | Actividades operativas → órdenes | Inductor de la actividad; capacidad (CAP) separa el ocio |
| P5–P7 | Administración, ventas, financieros → órdenes | Inductor del gasto |

**Naturaleza del costo:** NORMAL, PÉRDIDA (merma en exceso, rechazo sin reproceso) y OCIO (capacidad no usada) viajan hasta la orden con su etiqueta.

## 3. Síntesis
| Síntesis | Costo de la orden | Uso |
|---|---|---|
| REAL | MD + MOD + CIF + administración + ventas + financieros + pérdida + ocio | Gerencial, precio objetivo |
| CONTABLE | MD + MOD + CIF normales (NIC 2); pérdida, ocio y gastos al estado de resultados (NIIF 18) | Inventario y estados financieros |
| ESTIMADO | Costo más fiel según la historia (pronóstico validado fuera de muestra, con banda) | Presupuestar y comparar |
El resultado operativo es el mismo en REAL y CONTABLE; solo cambia qué se carga al objeto.

## 4. Analítica y gestión
| Función | Método |
|---|---|
| Diagnóstico | Elemento que más explica la variación del costo unitario; umbral aprendido max(5 %, 2·MAD) |
| Relevancia | Pareto 80 % |
| Proyección | 6 meses: pronóstico elegido fuera de muestra + banda conformal 90 % por horizonte |
| Proyección por hechos | Clona el último mes, escala volumen/precios, corre el mismo motor; bloques escalonados; sensibilidad ±10 % |
| Propuestas | Por causa (precio → compras; cantidad → producción); sin propuestas sobre costos no controlables; prioridad = impacto × probabilidad (Beta-Binomial) |
| Costeo variable | Fijo/variable por recurso (atributo o regresión con R² ≥ 0.7); margen de contribución; punto de equilibrio |
| Aprendizaje | Recalibra estándares y umbrales solo si mejora fuera de muestra y cambia ≤ 20 %; si no, pide aprobación; nunca toca el costo real |
| Cotizador | TDABC: tasa = costo de actividad / capacidad práctica; costo objetivo = precio × (1 − margen) |
| Calidad y gobierno | Costo de calidad en 4 categorías; % de inductores con responsable y evidencia |

## 5. Controles y seguridad
- Conservación: Σ recursos = Σ costo de las órdenes (por naturaleza) en cada cálculo.
- Sello SHA-256 del libro y del resultado; estados VIGENTE / RESULTADO_ALTERADO.
- Usuario, perfil y empresa validados por transacción; recibos idempotentes; respaldo antes de escribir.
- Servidor solo local; política de contenido sin evaluación de código.

## 6. Límites declarados y arquitectura objetivo
No incluido en esta versión (no funcional): base de datos SQLite, integración ERP/MES/IoT, rendimiento a gran escala.
Arquitectura objetivo: captura por adaptadores (MES/IoT), MFCA ISO 14051, flujo de valor y benchmarking.
