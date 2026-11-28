# OT-C37 — Funcionalidad pendiente MN 01 (practicidad, valor, entorno hostil)

Base: `desarrollo/mono` con C35 unida. Origen: `docs/entrega/evidencias/ERRORES_E2E.md` E35, E37–E43 y `docs/diagramas/mapa-detalle-mn01.html` (mapa leído del código). **Reemplaza a OT-C36**: el mapa ya está hecho; de C36 solo se conserva la plantilla UIX (C37-0).
Reglas: rama `codex/C37-N`, un PR por punto contra `desarrollo/mono`, nunca fusionar ni ir a main; no tocar `reparto_etapas.py` ni `motor_espejo.py`; pruebas existentes: solo se cambian pasos de navegación (autorizado), nunca aserciones de cálculo; compuerta completa una vez al final de cada rama. Lo ambiguo a `ordenes/RESPUESTAS_CODEX_24NOV.md` y sigues.

## Tres principios (criterio de aceptación de TODO punto)
1. **Práctico:** el caso típico en ≤ 3 pasos y ≤ 6 campos; el sistema nunca pide un dato que ya tiene (lo precarga y deja editarlo).
2. **Aporta valor:** cada pantalla termina en un número accionable o una recomendación; lo que no aporta se oculta o se archiva.
3. **Entorno hostil:** sin internet, libro incompleto, celdas vacías, texto donde va número, archivo dañado, dos pestañas abiertas. Nunca un 0 silencioso, nunca un error técnico en pantalla: mensaje «Falta X en la hoja Y» y la pantalla sigue usable con lo que sí hay.

## C37-0 Plantilla UIX única
Toda pantalla: pestañas arriba → entradas → resultado → fundamento (fórmula, dato, supuesto, límite) → siguiente acción. Tab/Enter recorren la pantalla. Aplicar a las pantallas que se toquen en C37-1…7. Documentar en `docs/diseno/PLANTILLA_UIX.md` (≤ 1 página).

## C37-1 Registrar movimiento sin JSON (E38)
Cabecera y líneas como formulario con campos tipados generados desde `/api/trx-campos` (lista de recursos, OT y centros como desplegables con búsqueda). «Espacios de trabajo» deja de tener su propio formulario (solo lista de espacios). «Importar libro» se une a «Cargar empresa». Prueba Chromium: registrar T15 sin escribir JSON; texto en campo numérico → mensaje, no envío.

## C37-2 Ruta de la orden reproducible y matrices de Oria (E37)
Cada fila de tramo muestra la cadena completa: monto del tramo → medida de la orden / total → parte de la orden; con esas columnas la cifra se reproduce con calculadora. Por etapa, botón «Ver matrices»: matriz de configuración (orígenes × destinos, medida, total) y matriz de cálculo (monto × medida ÷ total) con fila «Σ = origen ✔/diferencia». Prueba: para una OT de SERVITEC, cada parte = monto × medida ÷ total con tolerancia 0.01.

## C37-3 Decidir con datos propios (E35, E41)
Capacidad ociosa y unidades desplazadas se precargan de `resultado["capacidad_ociosa"]` y de las medidas CAP; se eliminan el Sí/No y el 0 por defecto. Se elimina la demanda máxima = ventas × 1.5: usar ventas del periodo y, si no hay, pedir el dato marcado «falta dato». «Pedido especial» de Decidir se retira y enlaza al Pedido (una sola forma de evaluar un pedido). Prueba: con capacidad ociosa calculada > 0 la decisión no pregunta; sin medidas CAP muestra «falta capacidad» y no decide.

## C37-4 Tramos de cantidad conectados al Pedido (E39)
`tramos_cantidad.calcular_costo_recurso` entra en el cálculo del pedido cuando el libro trae `COSTO_TRAMO`; el fundamento muestra el tramo usado. Sin tabla, resultado idéntico al actual (regresión). Caso: 200 h de soldadura, 0–160 a 30 y >160 a 45 → 6,600 visible en el Pedido.

## C37-5 Una sola familia (E40)
Regla: `recetas_pedido` (mínimos cuadrados) es el mecanismo de cotización; `familias.py` (bloques) queda solo como diagnóstico de la historia y su botón «Usar receta en cotizador» usa la receta de `recetas_pedido`. Si ambas existen para la misma familia, la pantalla muestra una sola. Prueba: misma familia, un solo número en Pedido y en Familias.

## C37-6 Pantallas sin valor y huérfanas (E42 y mapa)
Simulación: si aporta, entra al menú en Futuro; si duplica Laboratorio/Futuro, se oculta (decidir con evidencia en el PR). Inicio: se reduce a 3 accesos (Cotizar pedido, Registrar, Planta del costo). «Word código» pasa a Configuración (es de la monografía).

## C37-7 Prueba de entorno hostil
`tests/test_entorno_hostil.py` con copias del libro SERVITEC: (a) hoja obligatoria borrada, (b) celdas vacías en MEDIDA, (c) texto en un monto, (d) archivo truncado, (e) dos cálculos simultáneos, (f) sin red (EXE offline). Esperado: mensaje en español con hoja y columna, sin traza de Python en pantalla, sin 0 silenciosos, libro original intacto. Evidencia con capturas.

## Fuera de esta orden (decisión del dueño pendiente)
Archivar código que no corre (E43: analitica/, analitica2/, métodos cáscara, sueltos). No tocar hasta que el dueño decida pieza por pieza.

## Cierre
Evidencia por punto en `docs/entrega/evidencias/C37_N_*.md`, tiempos en tu CSV, actualizar manual descriptivo (≤ 150 palabras más). Reporte: PRs, compuerta, campos y clics por caso típico antes/después.
