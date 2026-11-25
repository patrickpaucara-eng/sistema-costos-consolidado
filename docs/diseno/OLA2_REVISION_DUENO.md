# Ola 2 de la revisión del dueño (25-nov) — especificación con casos a mano
Fuente: `docs/entrega/evidencias/ERRORES_E2E.md` y `docs/planificacion/DECISIONES_DUENO.md` (filas 25-nov). No se toca `src/metodos/reparto_etapas.py`.

## A. Un solo mecanismo de pronóstico (E25, E12, E8)
- Pronóstico por recurso granular (precio unitario, cantidad, medida de inductor) con `analisis.pronostico_puntual`; se arma el mes con `proyeccion.proyectar_hechos` y se pasa por el motor.
- PROYECTADO = meses futuros, con desglose por **recurso, centro, actividad y OT** (usar las aristas/trazas del motor del mes proyectado).
- ESTIMADO se retira como síntesis: lo que hacía pasa a «Precisión de la proyección» = para cada mes pasado t, el proyectado hecho con la historia hasta t−1 contra el real de t (error % por OT y total).
- Futuro (E8): primero la proyección por hechos con desglose y tornado; la banda estadística del margen solo si MASE < 1; si no, aviso «historia insuficiente para pronosticar con confianza».
- Prueba: con factores 1 el mes proyectado = mes base por recurso, centro, actividad y OT (±0.01).

## B. Cotizador por intervalos = costo proyectado de la OT (decisiones 25-nov)
- Entrada: cantidades totales de la OT (actividades e insumos), duración en meses, curva (pareja / al inicio / al final), contrato (REAJUSTE / CERRADO).
- Intervalo por grupo de recursos (MD, MOD, CIF-energía, CIF-servicios…): parámetro de empresa `INTERVALO_GRUPO`, sugerido por el sistema y aprobado.
  Regla de sugerencia: mayor L ∈ {1,2,3,6,12} tal que la mediana del rango % (máx/mín − 1) de las ventanas móviles de L meses de su precio ≤ 2 %.
- Tasa de cada intervalo = tasa proyectada del grupo en el **mes medio** del intervalo. Bloques recalculados por intervalo.
- Salida: costo por intervalo y total, P05–P95, brecha contra el costo objetivo. Al aceptar → T13 abre la OT con su costo proyectado; al cerrar → variaciones tasa / cantidad / ocio.
- **Caso a mano 1:** OT de 6 meses, intervalo trimestral, curva pareja; material 1,000 kg y MOD 600 h. Tasas al mes medio: T1 MAT 10, MOD 20; T2 MAT 11, MOD 21.
  T1 = 500×10 + 300×20 = **11,000**; T2 = 500×11 + 300×21 = **11,800**; total **22,800**.
- **Caso a mano 2 (sugerencia de intervalo):** precios [10, 10.1, 10.15, 10.5, 10.6, 10.62], tolerancia 2 % →
  L=2: rangos 1.00 %, 0.50 %, 3.45 %, 0.95 %, 0.19 % → mediana 0.95 % ✓; L=3: 1.50 %, 3.96 %, 4.43 %, 1.14 % → mediana 2.73 % ✗ → **bimestral**.
- **Caso a mano 3 (variaciones):** proyectado 10 h × 60 = 600; real 12 h, tasa real 65 → real 780.
  Tasa = (65 − 60) × 12 = **60**; cantidad = (12 − 10) × 60 = **120**; total 180 ✓.

## C. Niveles de suficiencia (decisión 25-nov)
- Catálogo de datos por nivel (0–4) generado del DBD; plantilla descargable por nivel; importación con emparejamiento de columnas por nombre y reporte de validación (errores no entran).
- Detección por capacidad: 0 totales → absorción tasa única; 1 + consumos y horas por OT; 2 + centros/actividades/inductores medidos → ABC; 3 + capacidad, estándares, merma, rechazos; 4 + ≥ 7 meses → proyección, aprendizaje.
- Bajar de nivel = plantilla de reglas de reparto generada (no código nuevo de motor). Nivel 0: todo IND → un centro → OT por una base.
- Etiqueta por dato: MEDIDO / ESTIMADO / SUPUESTO; cada pantalla muestra su nivel y «qué falta para subir».
- Prueba: libro nivel 0 sintético (costos totales y ventas) calcula y cuadra; Frenosa y SERVITEC detectan su nivel; MOD de Frenosa queda ESTIMADO.

## D. Registro completo y estrés (E26, E27, E6)
- Habilitar en el formulario: T09, T12, T13, T18.2, T18.3, T18.4–T18.7, T20.1, T21, T26, T29, T29.1 (ya definidas en el libro). Una prueba por transacción.
- E6: inductor MOD = minuto real (T18.3) por actividad; Frenosa: minutos reales repartidos según Te × kg, etiqueta ESTIMADO; mismo dinero por OT (prueba).
- E27: OT con costo ×10 → conserva; diagnóstico la marca; aprendizaje la toma como atípica; proyección no se dispara.

## E. Laboratorio (E10)
Copia del libro en un espacio «laboratorio»; editar hechos en pantalla; recalcular; comparar contra el original por OT y elemento; el original no cambia (SHA).

## F. Pantallas pendientes de la ola 1
E2 (fechas solo en Periodos; prueba autorizada), E4 (planta con nodos enlazados), E15 (cotizador con varias actividades y materiales), E21 (`monto_tramo` en el contrato + vista), E7 (detalle por persona con SERVITEC), E13 (tornado completo), prueba en navegador de aprobar/rechazar aprendizaje. E5: sello VIGENTE en un EXE recién instalado.

## G. Familias de componentes con lógica de bloques (DBCA) — decisión 25-nov
Idea del dueño: como en el Diseño de Bloques Completos al Azar, la familia es el «bloque»; dentro de ella las cantidades varían al azar
(distribución normal) pero el efecto es el mismo. El cotizador habla en componentes reconocibles; el sistema explota la receta de la familia.
- **Tabla FAMILIA** (FAM_COD, FAM_DES, FAM_UNI) + **FAMILIA_RECETA** (FAM_COD, ACT o REC, cantidad por unidad) + **FAMILIA_PARAM** (parámetros obligatorios).
- **Receta aprendida:** con las OT reales de la familia, cantidad por unidad de cada inductor → media y desviación. Pasa por las guardas de C22.
- **Pertenencia:** un componente pertenece a la familia si cada inductor cae en su intervalo de predicción al 95 %: media ± t(0.975, n−1) · s · √(1 + 1/n).
  Si no cae en ninguna familia → «componente no reconocido»: el sistema obliga a detallar sus actividades.
- **Mismo efecto (fusionar):** ANOVA de un factor entre dos familias por inductor; p > 0.05 en todos → sugerir fusionar (aprobación del dueño).
- **Separar:** si dentro de una familia falla la normalidad (Shapiro-Wilk p < 0.05) con n ≥ 8 → sugerir dividirla.
- **Cotización:** componentes × receta → cantidades por actividad → tasas por intervalo (bloque B) → costo; el rango P05–P95 usa el intervalo de predicción de la receta.
- **Casos a mano (pruebas obligatorias):**
  1. Familia A, horas por unidad [10, 11, 9, 10, 10] → media 10, s = 0.7071, intervalo **[7.85, 12.15]** (10 ± 2.15). Componente con 11.5 h → pertenece; con 14 h → no reconocido.
  2. Familia B [10.2, 9.8, 10.5, 9.9, 10.1] contra A → ANOVA F = 0.087, p = **0.776** > 0.05 → sugerir fusionar.
- Después del 9-dic (arquitectura objetivo): detección de familia por agrupamiento automático y lectura de familias desde BIM.
