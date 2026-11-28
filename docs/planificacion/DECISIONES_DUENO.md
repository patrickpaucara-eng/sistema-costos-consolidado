# Decisiones del dueño (vigentes) — leer antes de tocar cálculo o analítica

| Fecha | Decisión | Dónde se aplica |
|---|---|---|
| 22-nov | Pérdida (merma en exceso) y ocio viajan por la misma cadena hasta la orden con etiqueta propia; cada síntesis decide (REAL columnas, CONTABLE gasto NIC 2) | `reparto_etapas` (naturaleza), `resultados.POLITICA_NATURALEZA` — HECHO |
| 22-nov | Directo, escalonado y recíproco salen de los datos; recíproco entre pares del mismo nivel, escalonado entre niveles; el ocio solo baja | `reparto_etapas._reciproco` — HECHO |
| 22-nov | El modelo ABC de referencia es el Modelo 3 de W. Oria; modelos 1 y 2 son casos particulares. La vista se llama «Modelo de costeo» (metodología de W. Oria), no «Modelo de Oria» | motor — HECHO; vista: tarea 2.8 |
| 23-nov | «¿Y si…?» no edita datos pasados: costeo proyectado granular (hechos proyectados → mismo motor) + sensibilidad | tarea 2.4 |
| 23-nov | Aprendizaje: ciclo automático con guardas (mide error, recalibra, aplica si mejora fuera de muestra); las decisiones humanas son una fuente más | tarea 2.5 |
| 23-nov | Periodos por fecha libre (día, quincena, mes, bimestre, trimestre, semestre, año) sin código nuevo por periodo | tarea 2.6 |
| 23-nov | Propuestas según causa: precio → negociar con el proveedor (Compras); cantidad → mejorar eficiencia (Producción) | tarea 2.7 |
| 23-nov | Comportamiento del costo (fijo / variable / mixto, fijo dentro del periodo relevante) y controlabilidad (controlable / no controlable por centro) como atributos del RECURSO; costeo variable (directo), margen de contribución y punto de equilibrio | tarea 2.9 |
| 23-nov | **Los costos no controlables (compartidos, según Oria) no reciben propuestas de reducción**: las propuestas solo se dirigen a costos controlables por el responsable | tarea 2.9 + filtro en propuestas |
| 23-nov | Presupuestos operativo, financiero y de inversión pertenecen al futuro «sistema de planeamiento financiero», que leerá este sistema por el puerto de lectura | fuera de alcance |
| 23-nov | SQLite después; no se omite funcionalidad para la monografía, solo lo no funcional (rendimiento, seguridad avanzada) | plan |
| 23-nov | Codex y otras IAs: solo tareas de bajo contexto con orden escrita y prueba de aceptación, o revisión independiente | `ordenes/` |
| 24-nov | Un inductor único por actividad, definido una vez por causa-efecto; se reparte el saldo REAL sobre lo realmente entregado (la tasa predeterminada es solo para costeo normal y cotizaciones) | ya vigente (una regla por etapa y origen) |
| 24-nov | La regresión NO define el inductor: sirve para separar fijo y variable (decisiones); R² solo valida una vez la causa-efecto | tareas 2.5 y 2.9 |
| 24-nov | Retrabajo y rechazos internos = pérdida (costo de no calidad), aparte del costo normal | extender naturaleza PERDIDA a T18.4–T18.7 (tarea 2.9b) |
| 24-nov | Actividad conjunta (coproductos/residuo): valor neto realizable; el residuo no se costea como producto | coproductos D-9 (VVR); ajustar a VNR con costos posteriores (2.9b) |
| 24-nov | Pedidos especiales: costo = Σ consumo estimado de cada actividad × costo unitario de su capacidad (TDABC); consumo sugerido por plantilla/OT parecida/checklist | tarea 2.4b (cotizador por actividades) |
| 24-nov | Costos escalonados: el bloque se define una vez en el RECURSO que crece por escalones (operario, máquina, turno): capacidad por bloque y costo por bloque | tarea 2.4 (proyección y sensibilidad) |
| 24-nov | Costeo por componentes con estado de cada transformación (BOM multinivel, rutas, costo por estado intermedio) | después de la entrega (R2); en la monografía: estándares por componente generados de la historia (2.5) |
| 24-nov | Envoltorio estratégico (crítica de DeepSeek, validada): **costo objetivo** = precio de mercado − margen objetivo, en el cotizador (2.4b) y en las propuestas (cu_objetivo ya existe); **kaizen** = propuestas + seguimiento medido (ya existe); **costo de la calidad** en 4 categorías (prevención, evaluación, falla interna, falla externa) como atributo del recurso/evento (2.9b); **gobierno del dato**: responsable y evidencia por inductor + indicador de calidad del dato en el panel (2.9b); MES/IoT, MFCA (ISO 14051), ciclo de vida, flujo de valor y benchmarking: se declaran en el informe como arquitectura objetivo (R3/R4) | 2.4b, 2.9b, C19 |
| 25-nov | Prueba de punta a punta sin parches: cada error se documenta (paso, esperado, obtenido, causa probable) en docs/entrega/evidencias/ERRORES_E2E.md y se corrige en lote con Codex; documentación 80/20: solo lo mínimo que exige MN_01, breve | aplica a la prueba E2E y a C24 |
| 25-nov | T14.1 y T16 habilitadas en el formulario (plan 2.2); la prueba de capacidad inicial pasa a esperar las 8 transacciones ; la prueba de T16 «no habilitada» pasa a exigir que el motor la rechace sin orden (422) | tests/test_capacidad_inicial.py:209,220 |
| 25-nov | Manual descriptivo completado: la prueba de documentos deja de esperar los 6 marcadores [CLAUDE] y exige que no queden | tests/test_documentos_generados.py:24 |
| 25-nov | Niveles de suficiencia de información (0 a 4) por capacidad: el sistema publica el catálogo de datos (desde el DBD), importa con emparejamiento de columnas y validación, detecta el nivel y aplica una plantilla de reglas por nivel; cada dato se etiqueta medido/estimado/supuesto. Más datos = más granularidad; pocos datos = saldos sin detalle, declarado en pantalla | Claude (cálculo) + Codex (pantallas); antes del 9-dic |
| 25-nov | Un solo mecanismo para ESTIMADO y PROYECTADO: se pronostica cada recurso granular (precio, cantidad, inductor) con la historia y se pasa por el mismo motor ABC para formar centros, actividades, OT y cualquier síntesis compuesta. ESTIMADO = ese cálculo para el mes que se compara con el real; PROYECTADO = los meses futuros. Nunca se estima sobre el resultado final | Claude, antes del desglose (E12) |
| 25-nov | (propuesta, pendiente de visto bueno) Síntesis: REAL, CONTABLE y PROYECTADO; ESTIMADO pasa a «precisión de la proyección» (Aprender). Costo estimado de la OT (nombre del MCD: T09/T13) = cantidades previstas × tasas proyectadas a los meses de ejecución; base del análisis de variaciones (tasa, cantidad, ocio) | — |
| 25-nov | APROBADO: síntesis REAL, CONTABLE y PROYECTADO; ESTIMADO se retira como síntesis y pasa a «precisión de la proyección» (Aprender). Sin la palabra «estimado» en pantallas | autoriza actualizar pruebas que esperan ESTIMADO |
| 25-nov | APROBADO: costo proyectado de la OT (cotizador, T09/T13) = cantidades previstas repartidas por intervalo × tasas proyectadas por grupo de recursos al punto medio del intervalo; bloques por intervalo; rango P05–P95; base de variaciones (tasa, cantidad, ocio) | — |
| 25-nov | APROBADO: intervalo = parámetro de la empresa por grupo de recursos, sugerido por el sistema desde la volatilidad de precios (tolerancia 2 %), aprobado por el dueño; el cotizador solo puede acortarlo, con motivo; la OT elige contrato con reajuste o precio cerrado | — |
| 25-nov | APROBADO: cotizar por familias de componentes (lógica de bloques DBCA): receta aprendida, pertenencia por intervalo de predicción 95 %, fusionar por ANOVA, separar por normalidad; parámetros obligatorios por familia | C27 bloque G |
| 25-nov | APROBADO en OT-C27: E2; controles Desde/Hasta/Agrupar solo en Periodos y actualización de su prueba de navegación | `ordenes/OT-C27_OLA2_COMPLETA.md`, bloque F |
| 25-nov | E6: criterio MIN_STD → MIN_REAL en dos pruebas de capacidad (mismo dato, nuevo inductor de minuto real) | tests/test_naturaleza_costo.py, tests/test_capacidad_y_merma.py |
| 25-nov | Panel Decidir (sección H): ER gerencial, PE preciso por ABC (ponderado solo como respaldo, Oria), relevancia por regla del 10 %, producir/tercerizar, eliminar línea, pedido especial con y sin capacidad ociosa; atributo CF evitable | Claude |
| 25-nov | A3: se retira ESTIMADO de la API, la publicación y las pantallas; pruebas de API/exportación ajustadas citando la decisión. resultados.construir conserva el camino interno solo por compatibilidad (no expuesto) | tests/test_c04, c07, costeo_variable, estrategico, entrega_armar, api_resultados |
| 26-nov | Poka-yoke: el código de la OT lo asigna el sistema (OT-<EMP>-<PRODUCTO>-<NNNN>); nadie lo teclea; el motor rechaza claves repetidas. Autoriza actualizar tests/test_aceptar_cotizacion.py | C32 |
| 26-nov | PENDIENTE AL FINAL: mapa con drill-down: cada módulo abre otro mapa del mismo diseño con sus subcomponentes (no una lista de pasos), para validar posición y orden lógico; se hace cuando todo esté construido, como imagen fiel para corrección masiva | Claude |
| 26-nov | PENDIENTE (a validar con Oria): monografía 2 (presupuestos) se mantiene como LIBRO APARTE, como ya decidió el dueño en el diseño PRES del 2-nov, que lee el costo por un puerto de solo lectura. Corrige la anotación previa de este día («variante sobre la misma Base»). Lo que se comparte son los parámetros de tiempo, capacidad y calendario (E29). Sílabo de Oria: sem. 13 presupuesto maestro, sem. 14 presupuesto basado en actividades y simulación, sem. 15 presupuesto financiero (CPPC, VAN, TIR, CAPEX, estados proyectados). No se inicia antes del 9-dic | Claude |
| 27-nov | MN 02 (presupuestos), respuestas del dueño: (a) enunciado no disponible; el ciclo pasado fue «de presupuestos». (b) Autonomía: al inicio el gerente sigue la recomendación o hace lo suyo; el sistema aprende en silencio de cada acción hasta que sus recomendaciones pasen directo a ejecución. (c) Tiempo real. (d) Al operario no se le dice qué hacer; se mide su desempeño. (e) Caso: SERVITEC, desplazando a Frenosa. (f) Calendario: MN 01 se entrega 9-dic (máx. 15); MN 02 se presenta a Oria el 16-dic para recoger recomendaciones. (g) Codex hace el trabajo pesado | Dueño |
| 27-nov | E29 se ejecuta como OT-C34 (6 piezas chicas en serie) | `ordenes/OT-C34_E29_PEDIDO.md` |
| 27-nov | ACLARADO: no hay datawarehouse compartido entre costos y presupuesto. Presupuesto es libro aparte con su propia base (partidas, caja, financiamiento); lee de costos solo el contrato publicado (`contrato.py`), nunca la base interna. Misma regla que ya usan pantallas y dashboard. C (analítica/decidir/familias) no es tercer sistema: vive dentro de costos porque necesita la traza completa, no un resumen | Claude |
| 27-nov | Validado: Kendo / Finanzas Corporativas I (FIEECS, prof. Heber Baldeón) es OTRO curso del dueño, no de Oria. Se usa como referencia metodológica para rellenar PF (deuda con bonos/leasing NIIF16, impuesto corriente/diferido, VAN/TIR, valorización FCD) sin copiar sus hojas ni su código; la práctica de Kendo (rondas R1-R6) es entrega propia de ese curso, no se integra al sistema | Claude |

- 27-nov: el dueño pide corregir E30–E33 en una sola orden (OT-C35) antes de continuar la revisión; la agrupación del menú por ciclo del pedido es propuesta de Claude, pendiente de contraste con Tino.

- 27-nov (AUTORIZACIÓN): el dueño autoriza a Codex a actualizar `tests/test_c26_e22.py` para que refleje el menú nuevo de OT-C35-1 (seis destinos, un solo menú abierto). Solo ese cambio de la prueba; el resto de pruebas existentes sigue sin tocarse. Codex lo declara en el PR.

- 27-nov (AUTORIZACIÓN C35-1): Codex puede actualizar las pruebas que solo dependen del menú (`test_c26_e23.py`, `test_c26_interaccion.py`, `test_esqueleto_navegacion.py` y otras de navegación) para recorrer destino → pestaña. Solo cambian selectores y pasos de navegación; ninguna aserción de cálculo, monto o dato. Lista de archivos tocados en el PR.
- 27-nov: el mapa a detalle se construye mejorando `docs/diagramas/sistema-actual-reyna.html` (drill-down por módulo), no desde cero.

- 27-nov: `mapa-presupuesto-B.html` mejorado con «Vista simple» en lenguaje cotidiano (hechos → plan → salidas → lazo de corrección); B1/B2 quedan como detalle técnico. Punteado = sin aprobar (misión, horizonte, herramienta de solución, parámetros reales, enunciado de Oria).

- 27-nov (MN 02, propuesta del dueño, pendiente de aprobación formal): **misión del sistema B** = «entregar la programación de realización de los recursos comprometidos para el cumplimiento de los objetivos». **Horizonte** = n unidades de tiempo hacia adelante (n es parámetro); **frecuencia de actualización** = tiempo real, disparada por eventos (no por calendario); son dos cosas distintas. **Calculadora** = investigación de operaciones. **Parámetros** = arrancan como supuestos declarados (SUPUESTO) y se ajustan con la experiencia; los valores obsoletos se cierran con fin de vigencia, no se borran.

- 27-nov (REGLA DE ALCANCE): el mapa detallado modela todo lo existente y cada módulo/método declara su **justificación** (decisión del dueño, requisito de la MN 01, o «sin decisión»). Lo «sin decisión» que no aporte valor al sistema se **archiva o relega** (desactivado, no activo en el sistema; código conservado en `archivo/`), porque el dueño debe conocer a detalle todo lo que corre. Candidato inicial a revisar: costeo normal con sobre/subaplicación, variaciones de material, moneda extranjera y devoluciones (commit ea58a63, 21-nov), sin decisión explícita registrada. Nada se archiva sin decisión del dueño sobre cada pieza.
- 27-nov: el dueño valida pasar la sesión a Opus con esfuerzo alto para el mapa detallado.

- 27-nov (ajuste): en el mapa no se etiqueta lo que el dueño ya decidió (queda implícito). Solo se marca lo que **no tiene justificación** (sin requisito ni valor para el sistema), como candidato a archivar.

- 27-nov: mapa a detalle de B (MN 02) generado desde una especificación en datos (`tools/mapa_b/spec.py`) y validado con `tools/mapa_b/validar.py` (10 pruebas: entradas resueltas, sin ciclos, restricciones con datos, eventos con ticket, parámetros con vigencia y 3 casos calculados). Todos los valores de parámetros son SUPUESTO. La validación detectó un hueco (los tickets no llegaban a la recomendación) y un ciclo entre inversión y plan, ambos corregidos. No prueba realismo de los supuestos, rapidez del solucionador ni coincidencia con el enunciado de Oria.

- 27-nov (AUTORIZACIÓN C35-2): Codex puede cambiar solo los pasos de navegación de `test_pantalla_modelo_costeo.py::test_modelo_y_avisos_en_chromium` (ir a Inicio, consultar, volver a Modelo), sin tocar aserciones, y correr una segunda compuerta completa. La misma regla vale para cualquier otra prueba de C35 que solo dependa de navegación.

- 27-nov: OT-C37 (funcionalidad MN 01: practicidad, valor, entorno hostil) reemplaza a OT-C36; el mapa a detalle ya lo hizo Claude. Archivar código que no corre (E43) sigue pendiente de decisión del dueño.

- 28-nov (AUTORIZACIÓN C35-3/4): Codex puede adaptar preparación, selectores y pasos de `test_c26_interaccion.py` y `test_c34_5_pedido.py` al Pedido de 3 pasos. Prohibido cambiar aserciones, cifras esperadas o datos de entrada que alteren el resultado; el PR lista cada línea cambiada.

- 28-nov: los defectos E44 (fechas al revés, clave duplicada, criterio suma 0, número como texto, montos de LINEA) se corrigen antes del 9-dic en C37-7. La validación de lo que entregue la otra IA la hacen Codex (por pruebas) o la propia IA con validaciones automáticas, no Claude.

- 28-nov: entregas de la otra IA (piezas 24, 25, 30) incorporadas sin revisión de Claude: libros hostiles y oráculo SERVITEC en `tests/datos/`, textos de monografía en `docs/entrega/otra_ia/`. Codex debe convertir `verificar_pieza24.py` y `verificar_pieza30.py` en pruebas de la compuerta (C37-7).
- 28-nov (pendiente A→B): el contrato de resultados (`contrato.py`) no publica capacidad práctica, receta por producto ni fecha de entrega de las órdenes, que B necesita. Ampliar el contrato es tarea de A después de C37 (orden futura), no de B.

- 28-nov: auditoría independiente (otra IA) con 9 hallazgos confirmados → OT-C38. Se autoriza a Codex tocar el cálculo solo para C38, con la prueba de auditoría y el oráculo SERVITEC como compuerta. El libro de ejemplo SERVITEC debe poder cerrarse: se agrega la cuenta de merma (C38-10). La otra IA queda en pausa (sin créditos); su cola restante (B piezas 5–23, MN 1 piezas 26–29 y 31–32) se retoma cuando haya créditos o se reasigna.

- 28-nov: cola única de Codex en `ordenes/COLA_CODEX.md` (C37 → documentos MN 1 → manual → B). C38 (correcciones de cálculo) la hace Claude en paralelo, porque el cálculo es responsabilidad de Claude según AGENTS.md y no choca con las pantallas de C37.

- 28-nov (cambio): C38 la hace Codex (no Claude) para ahorrar tokens; va en `COLA_CODEX.md` justo después de C37, con prioridad sobre C37 si se acerca el 4-dic.

- 28-nov (MN 02): misión de B = la del 27-nov (programación de recursos comprometidos). Los presupuestos (operativo, efectivo, inversiones, financiero, control, estados) son síntesis configurables del plan; cada línea de ticket lleva fecha de devengo, fecha de caja, clase y estado. M6 queda cubierta como conjunto de síntesis.

- 28-nov: el dueño aprueba E43 tal como está en `docs/entrega/E43_ARCHIVO_PROPUESTA.md` → OT-C40 en la cola de Codex, después de C38.

- 28-nov (K4 aprobado): autonomía por niveles medida; sin habilitación escrita del dueño el sistema solo PROPONE; cada propuesta se acepta, rechaza o pospone con motivo. C41-4 se ejecuta.

- 28-nov (respuestas a bloqueos de Codex, Claude con aval del dueño):
  - **E45:** se autoriza cambiar en `tests/test_c37_2_matrices_ruta.py` SOLO la aserción que exige «Σ = origen DIFERENCIA» / «Diferencia S/ -9,600» en `PD|OCIO` P2: esa aserción la escribió C37-2 ayer y codifica el defecto E45, no una cifra verificada. Nueva aserción: la matriz de la naturaleza OCIO usa como base la parte OCIO del origen (2,400 → 2,400 a PRU) y muestra «Σ = origen ✔». Ninguna otra aserción cambia.
  - **E46:** correcto, la pantalla no debe recalcular. Se amplía el contrato: pasa a C38-11 (cálculo autorizado).
  - **C37-3:** el valor por defecto `venta × 1.5` de `decidir.asignar_recurso` se elimina: sin demanda explícita la API responde «falta demanda por producto». Pasa a C38-12. «Unidades desplazadas» no se puede deducir del contrato: el campo queda con «falta dato» y se declara como límite.
  - **C37-4 (tramos en el Pedido): SE CORTA** (regla de recorte, nivel 5). Motivo: COSTO_TRAMO es por recurso y el Pedido valora por actividad; integrarlo exige descomponer la tasa de la actividad por recurso y evitar doble cómputo. Se declara como límite: «costo marginal por tramos calculado y probado por recurso (`tramos_cantidad.py`), no integrado a la cotización por actividad».
  - **C37-5:** se acepta como está: la pantalla usa solo la receta de mínimos cuadrados; la API `/api/cotizar` conserva la receta de bloques por compatibilidad (la exige una prueba existente). Se documenta.

- 28-nov (B, decididas por Claude por delegación del dueño):
  - **Campo `sentido`** (entrada/salida) en las líneas de FINANCIAMIENTO y APORTE: **aprobado** como 8.º campo; sin él no se puede devolver un préstamo ni pagar su interés.
  - **Una sola base para el material en B:** igual que el sistema de costos (A): **promedio ponderado** (no PEPS); el costo se **devenga al consumir** y la **caja sale al pagar la compra** (según plazo de pago). El stock inicial entra valorizado (no gratis) y el inventario final se valoriza al mismo promedio. Calculadora, estados y líneas deben converger a esta base (pendiente de B, PR #59).
