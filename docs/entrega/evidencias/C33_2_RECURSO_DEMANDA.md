# OT-C33-2 · tope de demanda en recurso escaso

## Caso a mano

Capacidad disponible: **100 h**. Ambos productos consumen 10 h por unidad. A aporta MC de S/ 100 por unidad (S/ 10/h) y su demanda máxima es 4 unidades. B aporta MC de S/ 60 por unidad (S/ 6/h) y admite hasta 10 unidades.

| Producto | MC por unidad de recurso | Tope | Unidades asignadas | Recurso usado |
|---|---:|---:|---:|---:|
| A | S/ 10/h | 4 | 4 | 40 h |
| B | S/ 6/h | 10 | 6 | 60 h |

Resultado: A recibe primero 40 h hasta su tope; las 60 h restantes pasan a B. La capacidad usada es 100 h y la no usada es 0 h.

Con topes menores (A=2, B=3), el mismo caso asigna 20 h y 30 h, respectivamente, y muestra **50 h de capacidad no usada**. El algoritmo existente ya limitaba unidades por demanda máxima; C33-2 hace visible ese sobrante con un rótulo directo y conserva la asignación secuencial por MC/recurso.

## Pruebas

Prueba propia: `tests/test_c33_2_tope_demanda.py`.

- Caso manual por función: límites, orden de prioridad, recurso usado y sobrante exactos.
- API: límites de demanda y sobrante expuestos en la respuesta.
- Chromium: comprueba A=4/B=6 y el mensaje visible `capacidad no usada: 0`; luego limita A=2/B=3 y comprueba `capacidad no usada: 50`.

Comando focalizado:

```sh
PYTHONPATH=src python -m pytest -q tests/test_c33_2_tope_demanda.py
```

Resultado focalizado: **3 pruebas aprobadas**.

Compuerta completa (`python tools/verificar.py`): **507 pruebas aprobadas, 1 advertencia, 26 subpruebas aprobadas; contrato de resultados conforme; COMPUERTA: VERDE**.
