# C34-5 — Pedido guiado

## Alcance implementado

La sección de cotización presenta el flujo **Pedido**: cliente, producto/servicio, cantidad, fecha solicitada y contrato; familia técnica y parámetros obligatorios; capacidad y carga diaria declaradas; preparación por lote y conceptos adicionales; precio de mercado, margen y horizonte opcional. El modo manual previo queda bajo «Avanzado».

El servidor consulta la receta opcional `FAMILIA_PARAM` del libro activo, calcula cantidades por actividad/material y obtiene el costo con el último REAL publicado. Si existe historia residual suficiente, muestra P05–P95 de predicción. El resultado incluye plazo expresado en días de capacidad, precio sugerido y brecha contra mercado, decisión, preparación, adicionales y comparación de dos tamaños de lote. El desplegable de fundamento expone fórmula, supuesto, datos usados y límite.

Al aceptar, el formulario toma los datos calculados y emplea el escritor atómico ya existente de T09→T13. No se duplicó el registro operativo.

## Evidencia

- `tests/test_c34_5_pedido.py`: 3 pruebas propias, todas verdes.
- Chromium: formulario, receta Tolva de prueba dentro de un libro Frenosa temporal, cálculo del costo/rango, revisión del plazo/precio/fundamento, comparación de lotes y aceptación hasta generar `ESTIMACION` aceptada y `OBJETO` `OT-FRE-SW50-0001`.
- Persistencia: una receta reemplazada sin estadística borra la banda residual vieja, para evitar mostrar intervalos que ya no corresponden al modelo.
- La regresión de la API conserva el formulario manual avanzado cuando el libro no contiene familias configuradas.

## Límites y pendientes

- El rango suma intervalos t por inductor y declara independencia entre errores; no modela covarianza entre recursos.
- La pantalla solicita capacidad práctica y compromiso diario al usuario. No deduce automáticamente una agenda de OTs abiertas ni el calendario laboral de la empresa.
- El plazo compara días de capacidad con los días que el usuario declara disponibles hasta la fecha; no convierte feriados, turnos o calendario real en una fecha de entrega calculada.
- Los datos del piloto Frenosa avisan cuando las tasas del periodo son provisionales. La receta y la cotización requieren revisar que el REAL y las medidas correspondan al libro y periodo seleccionados.
- `COSTO_TRAMO` aún no modifica este pedido. Falta una decisión de contrato sobre si una fila se identifica por código de recurso, material, actividad o inductor y cómo se valora a través de tasas proyectadas; el cálculo marginal de C34-3 sigue verificado de manera aislada.
- La compuerta completa se registra por separado en el PR; el test focalizado no sustituye la validación del conjunto.
