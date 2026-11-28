# Manual descriptivo del sistema de costos

## 1. Arquitectura
| Capa | Qué es | Dónde |
|---|---|---|
| Datos | Libro Excel con el modelo DBD: catálogos (recursos, centros, actividades, criterios, órdenes) y movimientos (eventos, líneas, kardex, medidas, ventas) | `casos/plantilla_dbd.xlsx`, `casos/libros/` |
| Operación | Transacciones T14–T20 validadas por reglas del propio libro (TRX, TRX_CAMPO, TOP); cada una deja evento, recibo y respaldo | `src/reyna_local/store.py` |
| Cálculo | Motor ABC por etapas; valuación de kardex; síntesis | `src/metodos/reparto_etapas.py`, `src/reyna_local/resultados.py` |
| Contrato | Estructura única de resultados, validada; sello SHA-256 | `src/reyna_local/contrato.py`, `calculo_local.py` |
| Analítica | Descriptivo, diagnóstico, relevancia, proyección, escenarios, propuestas, aprendizaje, decisiones, familias, pedido | `analisis.py`, `proyeccion.py`, `aprendizaje.py`, `variable.py`, `estrategico.py`, `decidir.py`, `familias.py`, `cotizador.py` |
| Presentación | Servidor local + HTML; exportadores Excel/Word/HTML | `__main__.py`, `web/index.html`, `exportar.py` |

Reglas de diseño: las pantallas y documentos **solo leen el contrato**; nunca recalculan costos. Ninguna clave la teclea el usuario (el sistema asigna el código de la OT) y el motor rechaza claves repetidas.

## 2. Modelo de costeo (MCD/DBD de Tino Reyna; ABC escalonado de W. Oria)
| Etapa | Origen → destino | Base |
|---|---|---|
| P1 | Material → orden | Kardex promedio ponderado; merma en exceso aparte |
| P2/P3 | Mano de obra y servicios directos → actividad u orden | Horas u otro inductor |
| P4A | Indirectos → centros | m², kWh, % |
| P4B | Centros de apoyo del mismo nivel ↔ entre sí → centros productivos | Recíproco exacto entre pares (N = (I − P)⁻¹) |
| P4D/P4E | Centros → actividades; entre niveles: estratégicas → apoyo → operativas (escalonado, solo hacia abajo); dentro de un mismo nivel: recíproco | Inductor único por actividad |
| P4C | Actividades operativas → órdenes | Inductor de la actividad; capacidad (CAP) separa el ocio |
| P5–P7 | Administración, ventas, financieros → órdenes | Inductor del gasto |

**Naturaleza del costo:** NORMAL, PÉRDIDA (merma en exceso, rechazo sin reproceso) y OCIO (capacidad no usada) viajan hasta la orden con su etiqueta.

En «Ruta del costo», el detalle separa la base de distribución, la medida y el total, el monto que avanza por el tramo y la parte atribuida a la OT tras las etapas posteriores. «Ver matrices» muestra por etapa los orígenes × destinos, sus inductores y la medida/total, además del cálculo y el cuadre por origen. Las diferencias se señalan sin ajustar los importes.

## 3. Síntesis
| Síntesis | Costo de la orden | Uso |
|---|---|---|
| REAL | MD + MOD + CIF + administración + ventas + financieros + pérdida + ocio | Gerencial, precio objetivo |
| CONTABLE | MD + MOD + CIF normales (NIC 2); pérdida, ocio y gastos al estado de resultados (NIIF 18) | Inventario y estados financieros |
El resultado operativo es el mismo en REAL y CONTABLE; solo cambia qué se carga al objeto. El costo **proyectado** no es una síntesis: pronostica cada recurso con su propia historia y pasa por el mismo motor. Su **precisión** compara lo proyectado de un mes pasado con lo que ocurrió.

## 4. Analítica y gestión
| Función | Método |
|---|---|
| Diagnóstico | Elemento que más explica la variación del costo unitario; umbral aprendido max(5 %, 2·MAD) |
| Proyección | 6 meses por recurso (precio, cantidad, inductor), mismo motor; desglose por recurso, centro, actividad y orden; precisión contra lo real |
| Propuestas | Por causa (precio → compras; cantidad → producción); sin propuestas sobre costos no controlables; prioridad = impacto × probabilidad (Beta-Binomial); mensajes por área |
| Costeo variable y relevancia | Fijo/variable por recurso; margen de contribución; punto de equilibrio preciso por producto (el ponderado solo como respaldo); relevancia al 10 % |
| Decidir | Producir o tercerizar, eliminar línea, pedido especial (con y sin capacidad ociosa), un recurso escaso (orden por MC por unidad del recurso, con tope de demanda), procesar o vender; exporta a Excel un modelo para Solver cuando hay varias restricciones |
| Pedido (cotización) | Familia con parámetros obligatorios y receta aprendida; preparación por lote aparte del costo por unidad; tramos de cantidad; conceptos adicionales; costo proyectado por intervalos (curvas pareja, inicio, final, S) con contrato reajustable o cerrado; plazo por capacidad; rango P05–P95; al aceptar abre la OT |
| Familias | Aprende la receta de cada familia con intervalo de predicción 95 %; prueba pertenencia y propone fusionar con ANOVA (siempre aprueba el dueño) |
| Aprendizaje | Recalibra estándares y umbrales solo si mejora fuera de muestra y cambia ≤ 20 %; si no, pide aprobación; nunca toca el costo real |
| Laboratorio | Copia del espacio, transacción de prueba, recálculo y comparación por orden contra el original intacto |
| Suficiencia de datos | Diagnóstico por capacidad (niveles 0–4) y plantilla DBD con guía; cada dato se marca MEDIDO, ESTIMADO o SUPUESTO |
| Calidad y gobierno | Costo de calidad en 4 categorías; % de inductores con responsable y evidencia |

## 5. Controles y seguridad
- Conservación: Σ recursos = Σ costo de las órdenes (por naturaleza) en cada cálculo.
- Sello SHA-256 del libro y del resultado; estados VIGENTE / RESULTADO_ALTERADO.
- Usuario, perfil y empresa validados por transacción; recibos idempotentes; respaldo antes de escribir.
- Servidor solo local; política de contenido sin evaluación de código.

## 6. Límites declarados y arquitectura objetivo
**Del modelo** (también visibles en pantalla):
- El costo variable es lineal dentro de cada tramo de cantidad declarado; fuera de ellos se proyecta lineal.
- El plazo se calcula en días de capacidad; falta un calendario laboral aprobado para dar fechas.
- El rango P05–P95 supone errores independientes entre recursos.
- Las familias suponen que el proceso no cambió; si cambió máquina, proveedor o método se reinicia su historia.
- Decidir resuelve una sola restricción; con varias se exporta a Solver y el resultado solo vale dentro de su rango de sensibilidad.
- Un solo usuario a la vez: el código sugerido no se reserva y la clave única rechaza la colisión.

**Casos de prueba:** Frenosa es un caso real publicado (Cherres Juárez, 2010, PUCP). SERVITEC es un caso sintético creado para probar el sistema; no representa una empresa real.

**No incluido (no funcional):** base SQLite, integración ERP/MES/IoT, rendimiento a gran escala.
**Arquitectura objetivo:** captura por adaptadores (MES/IoT), MFCA ISO 14051, flujo de valor, benchmarking y un sistema de presupuesto/planeamiento aparte que lee el contrato de costos.
