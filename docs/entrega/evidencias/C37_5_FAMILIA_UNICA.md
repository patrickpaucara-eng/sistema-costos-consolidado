# OT-C37-5 · Una receta en la interfaz

**Alcance parcial:** la pantalla de Familias selecciona una familia del libro y abre Pedido con ella. La cotización usa el mecanismo ya existente de `recetas_pedido`; Familias muestra el mismo importe de la última cotización de la familia en esta sesión. Las medias e intervalos de bloques se presentan como diagnóstico histórico y ya no se envían desde esta pantalla para cotizar. No se cambió el motor de cálculo.

**Prueba:** `tests/test_c37_5_familia_unica.py` usa una copia temporal del libro Frenosa con la familia parametrizada TOLVA; ejecuta el análisis de bloques, selecciona la familia, cotiza en Pedido y compara el costo devuelto con lo mostrado en ambas pantallas. Las tres pruebas existentes de Familias conservan sus aserciones. Cuatro pruebas focalizadas verdes; compuerta completa VERDE con 572 pruebas y contrato válido.

**Uso:** Familias → seleccionar familia → Usar receta en cotizador; completar los datos de Pedido y calcular. Al volver a Familias aparece el último costo de la familia en la sesión, sin guardar una cotización nueva.

**Pendiente:** la API `/api/cotizar` todavía permite que un cliente envíe una receta de bloques, porque una prueba existente exige ese comportamiento y la orden prohíbe cambiar aserciones. La compatibilidad pendiente está registrada en `ordenes/RESPUESTAS_CODEX_24NOV.md`. La funcionalidad completa requiere resolverla; la evidencia no declara retirado el contrato antiguo.
