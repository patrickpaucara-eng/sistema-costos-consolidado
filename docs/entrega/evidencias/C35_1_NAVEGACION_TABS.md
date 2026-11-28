# C35-1 / E34 · Navegación y pestañas

## Cambio

La navegación se organiza en seis destinos: Pedido, Operación, Costos, Futuro, Aprendizaje y Configuración. Configuración aparece plegada al abrir el sistema; los demás grupos funcionan como acordeón y conservan los 26 destinos actuales. Al seleccionar una sección, las opciones de su grupo también se muestran como pestañas horizontales pegadas debajo de la barra global. La URL conserva el destino activo y permite recuperarlo al actualizar la página.

## Evidencia disponible

- `tests/test_c26_e22.py`: actualizado con autorización del dueño para comprobar los seis destinos y un grupo abierto al inicio.
- `tests/test_c35_1_navegacion_tabs.py`: recorre las 26 pantallas en Chromium; valida el acordeón, los enlaces de pestaña y la restauración de la pestaña activa al recargar.
- Prueba focalizada: `PYTHONPATH=src /tmp/reyna-costos-test/bin/python -m pytest -q tests/test_c26_e22.py tests/test_c35_1_navegacion_tabs.py` → **2 pasaron** (25,87 s; incluye Chromium).

## Límites y siguiente verificación

La compuerta completa debe ejecutarse una vez al cerrar la rama. Varias pruebas históricas recorren directamente enlaces de grupos cerrados o esperan cinco grupos; no se modificaron porque la autorización del dueño se limitó a `tests/test_c26_e22.py`. Si esas pruebas chocan con el nuevo acordeón, se requiere decisión para actualizar sus recorridos. El menú y las pestañas no cambian ningún cálculo ni endpoint.
