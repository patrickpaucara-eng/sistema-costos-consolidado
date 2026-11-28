# C35-1 / E34 · Navegación y pestañas

## Cambio

La navegación se organiza en seis destinos: Pedido, Operación, Costos, Futuro, Aprendizaje y Configuración. Configuración aparece plegada al abrir el sistema; los demás grupos funcionan como acordeón y conservan los 26 destinos actuales. Al seleccionar una sección, las opciones de su grupo también se muestran como pestañas horizontales pegadas debajo de la barra global. La URL conserva el destino activo y permite recuperarlo al actualizar la página.

## Evidencia disponible

- `tests/test_c26_e22.py`: actualizado con autorización del dueño para comprobar los seis destinos y un grupo abierto al inicio.
- `tests/test_c35_1_navegacion_tabs.py`: recorre las 26 pantallas en Chromium; valida el acordeón, los enlaces de pestaña y la restauración de la pestaña activa al recargar.
- Prueba focalizada, tras conservar el `aria-label` previo: `PYTHONPATH=src /tmp/reyna-costos-test/bin/python -m pytest -q tests/test_c26_e22.py tests/test_c35_1_navegacion_tabs.py` → **2 pasaron** (25,51 s; incluye Chromium).

## Límites y siguiente verificación

La primera compuerta completa, ejecutada en `e3e1bdc`, terminó **ROJA: 63 pasaron, 1 falló**; `tests/test_c26_e23.py::test_no_hay_menu_de_simulacion` buscaba el `aria-label` anterior. Se restauró el atributo y su prueba focalizada quedó verde, pero no se repitió la compuerta. Antes de poder cerrar la rama, falta decidir cómo tratar los recorridos históricos: `tests/test_c26_interaccion.py` exige cinco grupos y enlaces directos, mientras el nuevo menú tiene seis grupos plegables; `tests/test_esqueleto_navegacion.py` también intenta pulsar todos los enlaces de grupos cerrados. No se modificaron porque el permiso de pruebas solo cubre `tests/test_c26_e22.py`. El menú y las pestañas no cambian cálculos ni endpoints.
