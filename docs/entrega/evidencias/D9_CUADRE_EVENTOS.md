# D9 · casos parciales T17, T19 y T20

**Fecha:** 20 de noviembre de 2026 (hora de Lima).

**Estado:** tres casos de evento comparan cuentas persistidas con cálculos independientes; no constituyen la conciliación integral D9.

## Fuente y ejecución

Los eventos T17, T19 y T20 usan los escenarios 9, 10, 18 y 24 del libro `tests/fixtures/ola1/Sistema_Costos.xlsx`, SHA-256 `43c9170c04b23e678de7abf7bab39f43c4251ea14695b351d884639ea972be40`. Las pruebas verifican el SHA y el texto fuente de cada escenario antes de construir la solicitud. DBD declara T17/T19/T20 como transacciones en línea y configura sus operaciones en `TOP`, `OME`, `MET`, `MCA` y `FRM` del mismo libro. MCD §6.2.1 y DBD p.75 fundamentan verificar las cuentas como saldos afectados por eventos.

El servicio del consolidado habilita explícitamente T14, T15, T17, T19 y T20. El motor aún aplica el perfil por transacción del libro; T16 y las operaciones por lotes no se habilitan desde el formulario de eventos. Las pruebas usan espacios temporales y vuelven a leer el XLSX guardado.

## T17 · costo suministrado por centro y función

El escenario fuente 9 registra PEN 30.000 de depreciación en `LINEA1`. El escenario 10 registra USD 4.000 de energía a PEN 3,72 por dólar, es decir PEN 14.880. El resultado independiente es:

`30.000 + (4.000 × 3,72) = PEN 44.880`.

La prueba lee de las cuentas persistidas `CTA_CENTRO.CCE_SUM=44.880` para `LINEA1/2026-04/B`, con función `PRD`, y `CTA_FUNCION.CFU_MTO=44.880` para `PRD/2026-04/B`. Hay filas A con las mismas claves de negocio; permanecen iguales. Se verifica, además, que el tipo de cambio USD cotejado con la fixture sea 3,72.

## T19 · pérdida declarada y clasificación de la regla

La prueba reutiliza las dos compras y el consumo del caso independiente T15 para fijar un costo medio de PEN 3,054 por unidad. El escenario fuente 18 declara diez cajas dañadas sin acta notarial. La regla `DESMEDRO_SIN_ACTA` del libro clasifica el concepto como `DESMEDRO` y `REG_DED=N`.

El cálculo separado da `10 × 3,054 = PEN 30,54`. La fila persistida de `CTA_GASTO` tiene periodo `2026-04`, centro responsable `ALM1`, concepto `DESMEDRO`, importe PEN 30,54 y `CGA_DED=N`. El inventario termina en 390 cajas por PEN 1.191,06. Una fila de empresa A con la misma clave queda sin cambios.

Este caso confirma el camino T19, donde DBD asigna `DED` desde la regla. No define `CGA_DED` para la pérdida anormal T15 ni para el ocio T23.2: sus métodos `M-ACU-CGA-PERD` y `M-ACU-CGA-OCIO` no asignan ese campo.

## T20 · venta por dos líneas

El escenario fuente 24 registra 1.500 cajas a USD 12 y 500 a USD 12,50. Para aislar T20, la prueba prepara en su copia temporal un saldo de apertura sintético de 2.500 cajas de producto terminado, PEN 12.500, a PEN 5 por caja. Ese saldo no existe en la fixture original ni se presenta como salida de una orden real.

Con el tipo de cambio del caso, el esperado independiente es:

| Medida | Cálculo | PEN |
|---|---|---:|
| Ingreso | `1.500 × 12 × 3,72 + 500 × 12,50 × 3,72` | 90.210,00 |
| Costo de venta | `(1.500 + 500) × 5` | 10.000,00 |
| Margen de la venta | `90.210 − 10.000` | 80.210,00 |
| Existencia final | `500 cajas × 5` | 2.500,00 |

La prueba compara las dos filas `VENTA`, la existencia final y `CTA_VTA_PER` (`VPE_ING=90.210`, `VPE_CST=10.000`) contra esos valores. Una fila de empresa A con el mismo periodo se conserva, y repetir el `request_id` no vuelve a modificar cuentas.

## Límites y siguiente puerta

- El saldo sintético hace que T20 pruebe el registro de la venta y su cuenta; **no** demuestra la producción de producto terminado desde una orden.
- T17/T19/T20 comparan eventos con esperados independientes, pero no con una fila `RESULTADO_METODO` persistida en la misma corrida.
- La fixture clasifica T23.0 como `ESTADISTICA`, por lo que el cierre del servicio no la ejecuta. No se cambia esa clasificación ni se interpreta su salida como reporte oficial.
- Faltan casos independientes de T23.5 y T23.3, junto con producto terminado generado, vínculo causal evento/línea/método y pruebas de reversa y reapertura.
- La clave física de `CTA_GASTO` omite `CGA_DED`. Los casos no aprueban una política contable ni corrigen esa clave.

El insumo y esperado están versionados en [caso_t17_t19_t20_eventos.json](../../../tests/fixtures/d9/caso_t17_t19_t20_eventos.json); el caso T15 y las siete cuentas están en [D9_CUADRE_T15.md](D9_CUADRE_T15.md) y [D9_CONTRATO_DE_DATOS.md](D9_CONTRATO_DE_DATOS.md).
