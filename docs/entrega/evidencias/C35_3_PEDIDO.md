# C35-3 · Pedido en lenguaje del cliente

## Estado de verificación

La rama `codex/C35-3` parte de `4363065`. La compuerta previa a la autorización del 28-nov quedó **ROJA: 65 pasaron, 1 falló, 1 advertencia; el contrato de resultados cumple**. El fallo reveló que el recorrido C26 no podía entrar al precio compartido desde Avanzado cuando el libro no trae familias. También estaba pendiente adaptar el E2E C34-5 a los tres pasos y al panel Definir. El dueño autorizó únicamente preparación, selectores y pasos de esos dos recorridos, sin alterar aserciones ni datos que cambian el costo.

Con esa autorización, C26 ahora abre Avanzado, avanza al paso Resultado y conserva el precio de mercado S/ 5 000. C34-5 espera a que carguen las familias antes de editar las políticas en Definir; reusa los mismos valores de margen, días, capacidad, compromiso, lote, preparación, adicionales y precio, y añade solo los datos requeridos por el nuevo formulario y el umbral de firma. Las aserciones de costo/rango/plazo/fundamento/lote/OT conservan sus literales; el importe calculado no se usa como nueva expectativa. El servicio existente calcula la comparación: la interfaz ahora le pasa el tamaño alternativo y presenta sus resultados. No cambiaron `pedido.py`, los módulos de costo ni el motor.

## Qué quedó implementado

- `#cotizador` presenta tres pasos: datos del cliente, resultado y aceptación.
- Los seis campos lógicos de pedido son familia/producto, cantidad, cliente, fecha, contrato y condición de pago; las medidas de familia conocidas por el cliente aparecen aparte.
- `FAMILIA_ROL` agrega `quien_sabe` (`cliente`, `derivado`, `tecnico`) y la derivación opcional, sin cambiar las columnas de las hojas heredadas. Si falta una derivación o queda fuera del rango declarado, se pide el dato técnico y el resultado sigue preliminar hasta recalcular.
- La pantalla muestra costo esperado y rango P05–P95, precio sugerido frente al mercado, plazo, suficiencia y fórmula, supuesto, dato y límite. La aceptación vuelve a mostrar el fundamento y usa el flujo atómico T09→T13 existente.
- Las políticas del paso Definir incluyen plazo, margen, proyección, intervalo/curva, lote/preparación, adicionales y umbrales de firma. La cotización no se marca firme cuando faltan umbrales, el rango no se estima, excede el umbral o falta información de capacidad.
- No cambiaron `src/reyna_local/pedido.py`, el motor de costos, `src/metodos/`, `store.py` ni pruebas existentes.

## Pruebas propias

| Caso | Resultado |
|---|---|
| Derivación aprendida sin pedir el parámetro técnico; falta de receta solicita confirmación | Pasa |
| Derivación fuera del rango declarado se detiene | Pasa |
| Roles y derivaciones sobreviven al guardado y lectura del XLSX | Pasa |
| La derivación se aprende solo con historia REAL suficiente | Pasa |
| Chromium: seis campos, derivación de área, confirmación de densidad pendiente y aceptación de OT | Pasa; crea `OT-FRE-SW50-0001` en libro temporal |
| Cuatro casos manuales de C34-6 | 4/4 pasan; importes esperados intactos |
| C26 sin familias: entrar a Avanzado, ir al precio y cotizar con S/ 5 000 | Pasa; conserva la aserción «Costo:» |
| C34-5: configurar políticas en Definir, cotizar, revisar el fundamento y comparar lote antes de aceptar | Pasa; conserva los datos de costo, aserciones y OT `OT-FRE-SW50-0001` |

Comando focalizado posterior a la autorización: `PYTHONPATH=src /tmp/reyna-c35-venv/bin/python -m pytest -q tests/test_c26_interaccion.py tests/test_c34_5_pedido.py tests/test_c35_3_pedido.py tests/test_c34_6_cuatro_rubros.py` → **13 passed**. La compuerta final ejecutada una vez en C35-3 dio **VERDE: 569 passed en 919.17 s; contrato de resultados válido**.

## Límites pendientes

- Las políticas, los borradores preliminares y los últimos valores se guardan en `localStorage`, por navegador y equipo; aún no se comparten entre puestos ni se guardan en el libro.
- La condición de pago queda en la solicitud y en el valor local predeterminado, pero el esquema/flujo T09→T13 no tiene un campo persistente para ella. `store.py` está excluido por instrucciones vigentes; requiere decidir el contrato de almacenamiento antes de ofrecer persistencia.
- El cálculo de plazo continúa en días de capacidad, sin calendario laboral ni carga automática de OTs abiertas. El rango combinado sigue suponiendo errores independientes, límite preexistente.
- La ejecución focalizada posterior a la autorización queda registrada al cerrar este lote; debe seguirse con una sola compuerta completa C35-3 antes del PR. La última revisión de las pruebas afectadas debe conservar la recepción de la comparación, el fundamento, la aceptación T09→T13 y el libro temporal original.
