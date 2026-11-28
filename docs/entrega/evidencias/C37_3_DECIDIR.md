# OT-C37-3 · Decidir con datos propios

**Base:** `desarrollo/mono@f440f78`. **Alcance:** presentación de resultados y pruebas; el cálculo no se modificó.

En Decidir, la capacidad práctica viene de `datos_libro.medidas` (nivel CAP) y la no usada, si está publicada, de `capacidad_ociosa`. La demanda inicial de cada producto es su venta del periodo, editable; una venta ausente se presenta como «falta dato». Sin capacidad CAP utilizable la asignación permanece deshabilitada; si falta demanda, no se envía. La cantidad para producir/tercerizar también se precarga de ventas; el usuario indica los costos de la decisión, incluso cuando correspondan a cero. El formulario duplicado de pedido especial se reemplaza por un enlace a Pedido.

**Verificación:** `tests/test_c37_3_decidir.py` comprueba en Chromium SERVITEC abril 2025 REAL: capacidad no usada 40 y demanda inicial MPR = 10 y REB = 10; en copias del contrato comprueba la demanda ausente y la ausencia de CAP. `tests/test_c32_4_recurso_escaso.py` y `tests/test_c33_2_tope_demanda.py` mantienen los casos manuales de asignación: 7 pruebas focalizadas verdes en total. La compuerta completa quedó VERDE con 572 pruebas y contrato válido. No se editaron pruebas existentes.

**Antes y después:** en la asignación, antes se elegía el recurso y se corregían tantos máximos como productos desde 1,5 veces la venta; ahora se elige el recurso y se comprueba la venta precargada (sin campos nuevos), con una acción para asignar. Si falta una venta, se pide solo ese dato. La cantidad de campos depende de los productos.

**Pendiente:** `decidir.asignar_recurso` conserva la alternativa `venta × 1,5` si otro cliente llama a la API sin máximos; la pantalla siempre envía máximos explícitos. Las unidades que desplazaría un pedido no pueden deducirse solo de una capacidad ociosa agregada: faltan consumo del pedido y asignación por producto. El enlace a Pedido no acredita ese cálculo. Un valor de cero se admite únicamente si fue informado.
