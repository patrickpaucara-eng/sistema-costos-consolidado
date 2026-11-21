# Ola 2 · D3 · Caracterización del kardex

**Resultado:** D3 sigue pendiente. Este registro reproduce el estado actual del piloto; no representa aceptación del kardex.

## Contrato de referencia

La fuente preservada [DBD_Fuente.xlsx](../../fuentes/claude/ola3/d9/insumos/DBD_Fuente.xlsx), SHA-256 `479186097f106f845c51da794cdf4e43fd3a4376c6617e1ca6ee281e87980456`, clasifica `EXISTENCIA` como cuenta de referencia. En la hoja `DBD_4f_Alineacion_I0b` (filas 43, 49–50, 84), `KARDEX` es derivada de línea y evento, mediante lista de acceso o reconstrucción. La fuente también propone retirar `KARDEX_SALDO` en favor de `EXISTENCIA`. El modelo interno heredado todavía clasifica las hojas de kardex como parque; R01 no se ejecuta en la ruta Python habilitada del piloto.

## Recorrido observado

Se creó un espacio temporal desde la fixture intacta, SHA-256 `43c9170c04b23e678de7abf7bab39f43c4251ea14695b351d884639ea972be40`, y se aceptaron estas tres operaciones por `Store.execute`:

1. T14, empresa B, marzo de 2026: 2.000 unidades de `CAJA4KG` a USD 0,80, con tipo de cambio 3,75; entrada PEN 6.000,00.
2. T14, empresa B, abril de 2026: 1.000 unidades a USD 0,85, con tipo de cambio 3,72; entrada PEN 3.162,00.
3. T15, empresa B, abril de 2026: consumo de 2.600 unidades a costo promedio PEN 3,054; salida PEN 7.940,40.

Después de reabrir el XLSX, `EVENTO` y `LINEA` tenían tres filas; `EXISTENCIA` mostraba 400 unidades, PEN 1.221,60 y CPU PEN 3,054. `KARDEX` y `KARDEX_SALDO` estaban vacías. La cuenta de existencias cuadra con el cálculo independiente, pero el movimiento detallado no se presenta en el piloto.

## Qué falta para aceptar D3

- Invocar y probar la proyección de R01 desde un corte explícito, sin alterar los hechos ni `EXISTENCIA`.
- Fijar empresa, periodo/corte y orden para movimientos tardíos o con la misma fecha. `KARDEX` no incluye una columna `*_EMP`; `KARDEX_SALDO` tampoco identifica empresa ni periodo.
- Verificar que el saldo corrido por movimiento concilie con `EXISTENCIA`, incluyendo repetición, reinicio y cambio de corte.
- Retirar o dejar de usar `KARDEX_SALDO` solo después de confirmar compatibilidad con el contrato DBD y consultas del usuario.

La operación desde una instancia nueva evita confundir el historial de un corte con otro; no resuelve por sí sola la repetición de un corte anterior en una instancia ya poblada. Por ello, este experimento no habilita D3, no modifica el motor ni convierte `KARDEX_SALDO` en una fuente autorizada.
