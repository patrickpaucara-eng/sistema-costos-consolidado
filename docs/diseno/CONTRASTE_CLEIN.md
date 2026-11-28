# Contraste crítico: nuestro sistema vs. el SIC-ABCDIEP de W. Oria (CLEIN 2026, sesiones 1–3)
*Claude, 28-nov. Fuente: material del CLEIN (`cleinOria.zip` del proyecto): «Análisis funcional y técnico SIC-ABCDIEP» (25 capítulos), guía de usuario, informe Monte Carlo, caso ALPROSA. Solo conceptos citados; nada de su código.*

## Veredicto en una línea
En el **núcleo de costeo** (ABC en dos etapas, recíproco por sistema lineal, conservación, cierre con aprobación independiente, «dato faltante ≠ 0», pronosticar inductores antes de recomponer el costo) estamos **a la par o por encima**. Nos quedamos **chicos en lo que hace a su sistema «estocástico, predictivo e inteligente»**: cómo se mide el riesgo, cómo se mide la precisión, el margen por capas y el gobierno de la inteligencia. Y su alcance es la **cadena de suministro completa** (costo de servir), no la orden.

## Dónde coincidimos (decirlo en la presentación, con su vocabulario)
| Oria pide | Nosotros |
|---|---|
| Recurso → actividad → objeto; tasa = costo / Σ consumo; denominador cero bloquea | Reparto P1–P7; I8 «criterio suma cero» (C38 lo adelanta a la carga) |
| Capacidad práctica y costo no utilizado visible | Ocio por naturaleza, que viaja hasta la orden; CONTABLE lo manda a gasto |
| Recíproco resolviendo el sistema lineal | `reparto_etapas` (probado a mano en `test_modelo3_oria`) |
| Conservación exacta, reparto de céntimos por mayor residuo | I1 + ALG-09 (residuo al mayor monto) + oráculo SERVITEC 0.00 |
| Cierre con aprobación de otra persona, bloqueo, huella | `cierre.py` (sello; C38-7 refuerza la huella) |
| «La ausencia de datos es distinta de cero» | Principio del dueño; C37/C38 lo hacen cumplir |
| Pronosticar inductores y recursos, luego recomponer costos | `proyectar_granular` (mismo motor) |
| Ecuación de tiempo t = β0 + Σ βi·xi calibrada con observaciones | Receta de familia por mínimos cuadrados (C34) |
| Evaluación por origen móvil (sin mirar el futuro) | `proyeccion.precision` |

## Dónde nos quedamos chicos (ordenado por lo que más pesa con Oria)
| # | Oria exige | Nosotros hoy | ¿Antes del 9-dic? |
|---|---|---|---|
| K1 | Precisión con **MAE, WAPE y sesgo**, y **comparar contra un modelo ingenuo** (último valor, promedio de 3) — «un modelo que no le gana al ingenuo no sirve» | Solo error % medio absoluto; sin comparación con ingenuo | **Sí** (chico) |
| K2 | Monte Carlo **sobre la red ABC** (recalcular actividades por réplica), **probabilidad de superar el presupuesto**, **costo medio de la cola**, convergencia, semilla | Monte Carlo sobre el **margen final** con rangos triangulares **fijos en el código** (0.95–1.08…) | **Sí** la parte honesta: rangos desde los errores medidos (o marcados SUPUESTO), prob. de superar presupuesto y cola P90; declarar que no simula la red |
| K3 | **Margen por capas**: ingreso → costo directo → costo de actividades → costo de servir → contribución; estructura corporativa aparte | Costeo variable y margen de contribución, no en capas | **Sí** (presentación de datos que ya existen) |
| K4 | **Inteligencia gobernada**: la alerta explica regla, dato, magnitud y alternativa; el usuario acepta, rechaza o **pospone con motivo**; **el modelo no cambia precios, compras ni personal automáticamente** | Propuestas con aprobación; la **visión del dueño** es autonomía creciente hasta ejecutar sin aprobar | **Decisión del dueño** (ver abajo) |
| K5 | Distribución por variable con metadatos (fuente, muestra, método de ajuste, vigencia) y **dependencia** entre variables | P05–P95 asumiendo independencia (límite declarado) | No: declarar como límite |
| K6 | **Costo de servir** por SKU, pedido, cliente, canal, ruta, contrato (cadena completa, post venta) | Costo por orden y producto | No: límite y trabajo futuro |
| K7 | Ingesta con **cuarentena**, duplicado idéntico/distinto, **conciliación con el mayor contable** | Validación del libro (C38 la endurece); sin conciliación con contabilidad | Parcial (C38); conciliación = límite |
| K8 | Contexto peruano (IGV, detracciones, tipo de cambio contable vs. BCRP, calendario) | Moneda extranjera básica | No: límite |
| K9 | Roles, doble control, MFA, auditoría de accesos | Un usuario; registra ≠ aprueba | No: límite declarado |

## Decisión del dueño (K4) — importante para la nota
Oria, que califica, escribe que **ningún modelo debe cambiar precios, compras o dotación automáticamente** y que toda recomendación se acepta, rechaza o pospone **con motivo**. La visión del dueño (el sistema aprende del gerente hasta ejecutar sin aprobación) choca con eso. Propuesta: **mantener la visión como «autonomía por niveles medida»**, pero el nivel máximo que el sistema alcanza **sin una regla escrita del dueño es «proponer»**; ejecutar sin aprobar exige que el dueño habilite ese tipo de decisión con un umbral de precisión medido. En la presentación se muestra así: inteligencia gobernada hoy, autonomía como camino medido.

## Orden para Codex: OT-C41 (después de C38, antes de C40)
1. **K1:** en `proyeccion.precision` agregar MAE, WAPE (indefinido si Σ real = 0) y sesgo, y la misma evaluación para dos modelos ingenuos (último valor y promedio de 3); la pantalla dice cuál gana y por cuánto. Prueba a mano con 6 meses inventados.
2. **K2:** en `analisis.py` reemplazar los rangos triangulares fijos por rangos sacados de los errores fuera de muestra medidos; si no hay historia suficiente, usar los actuales marcados «SUPUESTO» en pantalla. Agregar probabilidad de superar un presupuesto dado y el costo medio por encima del P90. Texto fijo en pantalla: «simula el margen, no recalcula toda la red ABC».
3. **K3:** vista «Margen por capas» por producto con datos ya publicados (ingreso, directo MD+MOD+SD, actividades CIF, gastos de venta y administración, contribución). Sin tocar el motor.
4. **K4:** (solo si el dueño aprueba) cada propuesta se puede aceptar, rechazar o **posponer** con motivo obligatorio; texto en «Lo que aprendió»: «el sistema propone; ejecutar sin aprobación requiere habilitación del dueño».
5. Límites K5–K9 en el manual y la monografía, con la frase de Oria correspondiente parafraseada.
