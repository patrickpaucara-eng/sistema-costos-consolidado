# C35-3 · Pedido en lenguaje del cliente

## Estado de verificación

La rama `codex/C35-3` parte de `4363065`. Las cinco pruebas nuevas de `tests/test_c35_3_pedido.py` pasan en local (4 pruebas de receta/persistencia y 1 recorrido Chromium); pytest informa una advertencia de compatibilidad de `anyio`. La compuerta completa no se ha ejecutado todavía: la prueba funcional preexistente `tests/test_c34_5_pedido.py::test_pedido_guiado_en_chromium_hasta_abrir_ot` usa controles y una interacción anterior. No se editó; requiere una decisión sobre actualizar su preparación del flujo conservando sus aserciones.

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

Comando focalizado: `PATH=/tmp/reyna-costos-test/bin:$PATH PYTHONPATH=src python -m pytest -q tests/test_c35_3_pedido.py` → **5 passed, 1 warning**. No se ejecutó la compuerta completa en esta etapa.

## Límites pendientes

- Las políticas, los borradores preliminares y los últimos valores se guardan en `localStorage`, por navegador y equipo; aún no se comparten entre puestos ni se guardan en el libro.
- La condición de pago queda en la solicitud y en el valor local predeterminado, pero el esquema/flujo T09→T13 no tiene un campo persistente para ella. `store.py` está excluido por instrucciones vigentes; requiere decidir el contrato de almacenamiento antes de ofrecer persistencia.
- El cálculo de plazo continúa en días de capacidad, sin calendario laboral ni carga automática de OTs abiertas. El rango combinado sigue suponiendo errores independientes, límite preexistente.
- Pendiente: adaptar con autorización la prueba funcional C34-5 a la interfaz nueva, sin cambiar aserciones de costo, adicionales, plazo, rango ni aceptación. Después ejecutar una vez la compuerta completa.
