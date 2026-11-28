# C35-1 / E34 · Navegación y pestañas

## Cambio

La navegación se organiza en seis destinos: Pedido, Operación, Costos, Futuro, Aprendizaje y Configuración. Configuración aparece plegada al abrir el sistema; los demás grupos funcionan como acordeón y conservan los 26 destinos actuales. Al seleccionar una sección, las opciones de su grupo también se muestran como pestañas horizontales pegadas debajo de la barra global. La URL conserva el destino activo y permite recuperarlo al actualizar la página.

## Evidencia disponible

- `tests/test_c26_e22.py`: actualizado con autorización del dueño para comprobar los seis destinos y un grupo abierto al inicio.
- `tests/test_c35_1_navegacion_tabs.py`: recorre las 26 pantallas en Chromium; valida el acordeón, los enlaces de pestaña y la restauración de la pestaña activa al recargar.
- Prueba focalizada, tras conservar el `aria-label` previo: `PYTHONPATH=src /tmp/reyna-costos-test/bin/python -m pytest -q tests/test_c26_e22.py tests/test_c35_1_navegacion_tabs.py` → **2 pasaron** (25,51 s; incluye Chromium).

## Pruebas de navegación existentes actualizadas

Se ajustaron solo selectores y pasos para seleccionar destino → pestaña; las aserciones de cálculo, monto, contrato y datos se conservaron:

- `tests/test_c26_e22.py`: comprueba los seis grupos y el grupo abierto al inicio (autorización del dueño).
- `tests/test_c26_e23.py`: localiza el bloque del menú por su id estable.
- `tests/test_c26_interaccion.py`: cuenta seis grupos, valida el único abierto y usa la pestaña correspondiente.
- `tests/test_esqueleto_navegacion.py`: recorre cada enlace bajo su grupo y usa la pestaña superior.
- `tests/test_c29_aprendizaje.py`, `tests/test_c31_1_planta.py`, `tests/test_c31_2_personal.py`, `tests/test_c31_4_familias.py`, `tests/test_c31_p5_laboratorio.py`, `tests/test_c32_4_recurso_escaso.py`, `tests/test_c32_5_procesar_vender.py`, `tests/test_c33_2_tope_demanda.py`, `tests/test_c33_3_avisos_limites.py` y `tests/test_c34_5_pedido.py`: sustituyen clic directo por destino → pestaña.
- `tests/nav_helpers.py`: centraliza el mapa de cada pantalla a su destino y ejecuta ambos pasos.

## Resultado de compuerta

La primera ejecución en `e3e1bdc` quedó roja por una discrepancia de etiqueta; se restauró el `aria-label` existente. Tras la autorización del 27-nov para adaptar pruebas de navegación, la única compuerta final dio **VERDE: 563 pruebas, 1 advertencia y 26 subpruebas; el contrato de resultados cumple**. Ejecución: `PATH=/tmp/reyna-costos-test/bin:$PATH python tools/verificar.py`. El menú y las pestañas no cambian cálculos ni endpoints.
