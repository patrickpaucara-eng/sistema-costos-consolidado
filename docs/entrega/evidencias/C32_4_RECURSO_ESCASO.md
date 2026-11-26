# OT-C32 · Punto 4 — Asignación de un recurso escaso

## Alcance

El panel Decidir permite elegir una capacidad de nivel `CAP` del resultado REAL, revisar o editar la demanda máxima por producto y asignar la disponibilidad en orden descendente de MC por unidad del recurso. El cálculo usa el margen gerencial publicado, el consumo `OBJ` por orden, la capacidad `CAP` y una traza que vincula el inductor con el recurso o actividad. No vuelve a calcular costos. Los máximos iniciales son 1,5 veces la venta REAL del periodo; la pantalla los marca como supuestos editables.

## Pruebas y resultado

Comando focalizado:

```sh
PYTHONPATH=src /tmp/reyna-c32-2-venv/bin/python -m pytest -q tests/test_c32_4_recurso_escaso.py
```

Resultado: **3 pruebas aprobadas**: caso numérico directo, API y recorrido del panel en Chromium.

Compuerta final `python tools/verificar.py`: **COMPUERTA: VERDE**, 489 pruebas aprobadas, 1 advertencia y 26 subpruebas aprobadas; el contrato de resultados cumple.

| Producto | MC unitario | Consumo de máquina | MC por hora | Demanda máxima |
|---|---:|---:|---:|---:|
| A | S/ 30 | 2 h/u | S/ 15/h | 40 u |
| B | S/ 20 | 1 h/u | S/ 20/h | 70 u |

Con 100 horas, la asignación observada fue **B = 70 u, A = 15 u**, con capacidad utilizada de 100 h y MC total de **S/ 1,850**.

## Límites

La recomendación maximiza la contribución para una sola capacidad elegida. No incluye una segunda restricción, costo de oportunidad de otros recursos, calidad, tiempos de preparación ni una validación metodológica empresarial. Si no hay trazas y medidas `OBJ` completas, el panel no ofrece la capacidad para evitar presentar consumos incompletos como cero.
