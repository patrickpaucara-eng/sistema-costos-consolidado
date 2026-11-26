# OT-C32 · Punto 5 — Procesar o vender

## Alcance

El panel Decidir incluye una calculadora por unidad con el precio de venta actual, el precio después del procesamiento y el costo incremental posterior al punto de separación. Python calcula el ingreso incremental, resta el costo adicional y recomienda **PROCESAR** solo si el beneficio es mayor que cero; en otro caso recomienda vender en el punto actual.

## Pruebas y resultado

Comando focalizado:

```sh
PYTHONPATH=src /tmp/reyna-c32-2-venv/bin/python -m pytest -q tests/test_c32_5_procesar_vender.py
```

Resultado: **3 pruebas aprobadas**: caso numérico directo, API y recorrido del panel en Chromium.

Compuerta completa (`python tools/verificar.py`): **489 pruebas aprobadas, 1 advertencia, 26 subpruebas aprobadas; contrato de resultados conforme; COMPUERTA: VERDE**.

| Venta actual | Venta tras procesar | Costo adicional | Beneficio neto por unidad | Resultado |
|---:|---:|---:|---:|---|
| S/ 10 | S/ 14 | S/ 3 | S/ 1 | PROCESAR |

## Límite

La recomendación considera el efecto incremental indicado por el usuario. No distribuye costos conjuntos anteriores al punto de separación ni añade capacidad, calidad, demanda u otros costos que no se ingresaron.
