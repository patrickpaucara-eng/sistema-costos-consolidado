# OT-C34 — E29: el cotizador pasa a ser «pedido»

Base: `desarrollo/mono` con C33 unida. Especificación de origen: `docs/entrega/evidencias/ERRORES_E2E.md` § E29.
Reglas: una rama `codex/C34-N` y un PR contra `desarrollo/mono` por punto; nunca fusionar ni ir a main; no tocar `reparto_etapas.py` ni `motor_espejo.py`; no editar pruebas existentes sin decisión en `DECISIONES_DUENO.md`; durante el trabajo corre solo tus pruebas; compuerta completa UNA vez al final de cada rama, nunca dos en paralelo. Si una pieza depende de otra aún no unida, rebasa sobre la rama anterior y dilo en el PR. Lo ambiguo va a `ordenes/RESPUESTAS_CODEX_24NOV.md` y sigues.

Cada pieza es chica a propósito (una sesión de Codex). Orden obligatorio: C34-1 → C34-6.

## C34-1 Plantilla de parámetros por familia (datos, sin pantalla)
Columna/hoja opcional en el libro: por familia, lista de parámetros obligatorios (nombre, unidad, rango válido) y la fórmula de receta: cantidad de cada inductor = base + Σ coeficiente × parámetro (lineal; los coeficientes se aprenden de las OT reales por mínimos cuadrados en Python puro, sin scipy).
- Caso a mano: familia «Tolva»; OT históricas con kg = 1000, 1200, 1500 y horas de soldadura 60, 70, 85 → coeficiente 0.05 h/kg, base 10 h. Nueva tolva de 1300 kg → 75 h.
- Si falta un parámetro obligatorio, el pedido no se calcula y dice cuál falta.

## C34-2 Conceptos adicionales y preparación por lote
El pedido admite líneas fuera del ABC: subcontrato, transporte, gastos generales, contingencia (% sobre costo). Y separa: costo de preparación fijo por lote + costo variable por unidad.
- Caso: 50,000 cajas; preparación 1,200 por lote; variable 0.354 por caja → un lote 18,900; dos lotes de 25,000 → 20,100. La pantalla muestra la diferencia.

## C34-3 Tramos de cantidad (costo variable no lineal)
Por recurso, tabla opcional de tramos: hasta Q1 tasa t1, de Q1 a Q2 tasa t2... (horas extra, descuento por volumen). Mismo patrón que `costo_por_intervalos`, pero por cantidad.
- Caso: soldadura 0–160 h a 30/h, más de 160 h a 45/h; pedido de 200 h → 160×30 + 40×45 = 6,600.
- Sin tabla de tramos, el resultado es idéntico al actual (prueba de regresión).

## C34-4 Curva S y capacidad contra fecha
- Cuarta curva «s» en `costo_por_intervalos` (pesos 1-2-3-3-2-1 normalizados, repartidos según el número de intervalos). Caso a mano en la prueba.
- Capacidad: con la capacidad práctica de cada actividad y la carga ya comprometida (OT abiertas), calcular la fecha más temprana. Responde «llega» o «N días tarde». Caso: 85 h de soldadura, capacidad libre 6 h/día, pide 12 días → 15 días, 3 tarde.

## C34-5 Pantalla «Pedido» y fundamento
Reemplaza el formulario del cotizador por: (1) datos del cliente: qué, cuánto, para cuándo, contrato; (2) datos del técnico: familia y sus parámetros obligatorios (C34-1); (3) conceptos adicionales (C34-2). El sistema muestra: costo esperado con rango P05–P95, plazo (C34-4), precio sugerido frente a mercado y decisión relevante.
Cada resultado lleva su **fundamento** en 4 líneas: fórmula, supuesto, dato usado, límite. El modo antiguo (actividades e inductores a mano) queda como «Avanzado», plegado. «Aceptar» abre la OT con el flujo atómico ya existente.
Prueba Chromium: un pedido completo de punta a punta hasta la OT.

## C34-6 Prueba de los 4 rubros
Libros sintéticos mínimos (o familias dentro de SERVITEC) para metalmecánica, construcción, imprenta y servicios. Por rubro, una prueba que recorre el pedido y verifica el número esperado escrito a mano en la prueba. Evidencia en `docs/entrega/evidencias/C34_6_CUATRO_RUBROS.md`.

## Cierre
Evidencia por punto en `docs/entrega/evidencias/C34_N_*.md`, tiempos en tu CSV. Reporte final: PRs, compuerta y pendientes.
