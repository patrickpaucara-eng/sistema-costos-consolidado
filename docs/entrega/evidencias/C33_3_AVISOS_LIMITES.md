# OT-C33-3 · avisos de límites del modelo

Se añadieron avisos fijos, breves y no modales en las vistas correspondientes:

| Vista | Aviso mostrado |
|---|---|
| Futuro | El costo variable se proyecta lineal dentro del rango observado de cantidades. |
| Cotizador | El costo variable se proyecta lineal dentro del rango observado de cantidades. |
| Familias | Supone que el proceso no cambió; si cambió máquina, proveedor o método, reinicie la historia de la familia. |
| Decidir / recurso escaso | Una sola restricción. Con varias, use Exportar a Excel para Solver. |
| Registrar / sistema | Uso de un solo usuario a la vez. |

Prueba propia: `tests/test_c33_3_avisos_limites.py`. En Chromium navega por las cinco secciones y confirma que cada aviso aparece visible con el texto esperado. No hay modal ni aviso condicional.

Comando focalizado:

```sh
PYTHONPATH=src python -m pytest -q tests/test_c33_3_avisos_limites.py
```

Resultado focalizado: **1 prueba aprobada** en Chromium.

Compuerta completa (`python tools/verificar.py`): **505 pruebas aprobadas, 1 advertencia, 26 subpruebas aprobadas; contrato de resultados conforme; COMPUERTA: VERDE**.
