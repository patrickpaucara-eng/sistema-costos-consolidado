# Ola 2 · D2 · Traza de compra T14

La prueba de aceptación ejecuta T14 y T15 por HTTP y lee las hojas de traza y recibos del XLSX administrado. Usa copias temporales de `tests/fixtures/ola1/Sistema_Costos.xlsx` en la base `desarrollo/mvp-ola3@86aaa4f`. SHA-256 de la fixture `43c9170c04b23e678de7abf7bab39f43c4251ea14695b351d884639ea972be40`. [Correspondencia de la Ola 2 en el plan maestro](../../planificacion/PLAN_MAESTRO.md).

| Operación | Resultado verificado |
| --- | --- |
| Compra T14 de 2.000 unidades de `CAJA4KG` por `ALMACEN1`, empresa B, periodo `2026-03` | HTTP 200 y un incremento de versión. Al reiniciar el servidor queda una fila T14 en `LOG_TRX` con `LOG_EST = A`. Cada fila de `BITACORA` tiene `BIT_LOG` igual a `LOG_NUM`, y el total de filas enlazadas coincide con `LOG_NCAMB`. |
| Reintento de la misma compra tras reiniciar el servidor | Misma respuesta HTTP 200, mismos valores en ambas hojas y un único recibo para `d2-compra`. |
| Consumo T15 de 2.600 unidades por `SUPERV1`, periodo `2026-04` | HTTP 422. Conserva ambas hojas y la versión de la compra. Tras otro reinicio, el reintento devuelve la misma respuesta HTTP 422 y el XLSX conserva un único recibo para `d2-rechazo` con esa respuesta. |

```sh
python -m unittest discover -s tests -p test_wave2_log_trace.py -v
```

Una prueba aprobada con las dependencias declaradas instaladas, tanto en el directorio de trabajo como en una copia de `86aaa4f` que contenía únicamente la prueba nueva. La evidencia cubre la persistencia y el reintento de este recorrido D2. Quedan fuera de este caso la reversión de transacciones confirmadas, la recuperación tras un corte y la aceptación de D3/D4. [Prueba reproducible](../../../tests/test_wave2_log_trace.py).
