# OT-C37-1 · Registro tipado sin JSON

Base de trabajo: `ff09bec` (`desarrollo/mono`, con C35-1 integrada). La capacidad queda en `codex/C37-1`; C37-0 continúa en su PR separado.

## Cambio

- `/api/trx-campos` expone `tipo` junto a cada campo. Las listas salen directamente de `TCA_LISTA`; «fecha», «número» y «texto» se derivan de `TCA_ETQ` porque la estructura `TRX_CAMPO` del libro no declara un tipo escalar.
- El formulario genera cabecera y líneas desde ese contrato. Cada lista conserva un `<select>` nativo y agrega un filtro de búsqueda; los códigos de OT, recursos y centros siguen seleccionándose desde las opciones disponibles.
- Los campos de cantidad aceptan números. Si Chromium bloquea texto no numérico, la pantalla muestra un mensaje en español antes del envío.
- Se retiró el formulario independiente que pedía una ruta local. La carga XLSX y la creación del espacio de operación quedan bajo «Cargar empresa»; «Espacios de trabajo» solo lista espacios. El hash antiguo `#importar` redirige a la pantalla unificada.
- Se retiró el editor JSON de la interfaz; la API de ejecución conserva el contrato JSON que consume el formulario.

## Prueba

`tests/test_c37_1_registro_tipado.py` abre Chromium y registra T15 sobre una copia temporal del libro Frenosa. Comprueba búsqueda en listas, captura con campos tipados, rechazo de texto en `Cantidad` sin evento ni aumento de versión y posterior registro correcto de T15. También verifica que no exista formulario en «Espacios de trabajo» y que `#importar` llegue a «Cargar empresa».

La adaptación de `tests/test_c35_1_navegacion_tabs.py` y `tests/nav_helpers.py` solo retira la antigua pestaña «Importar libro» y ajusta el recorrido de 26 a 25 pantallas; no cambia datos ni aserciones de cálculo.

Pruebas focalizadas relacionadas: **7 pasaron** (C37-1, formulario guiado, correlativo de OBJETO y navegación C35/C26). `python tools/verificar.py`: **COMPUERTA VERDE**, 564 pruebas pasaron en 915,48 s; contrato de resultados válido.

## Límite pendiente

`TRX_CAMPO` no conserva un tipo escalar; la clasificación actual usa la etiqueta del libro y puede requerir un atributo explícito para campos nuevos o ambiguos. Esta inferencia solo define controles de captura: la validación final de la transacción sigue en el servidor.
