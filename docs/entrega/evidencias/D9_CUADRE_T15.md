# D9 · caso independiente T15

**Caso:** `D9-T15-2026-04-B-OS01`.

**Estado:** prueba parcial de tres saldos CTA; no es aceptación contable ni conciliación del cierre integral.

## Entradas congeladas

El caso reutiliza, solo en copias temporales, `tests/fixtures/ola1/Sistema_Costos.xlsx`, SHA-256 `43c9170c04b23e678de7abf7bab39f43c4251ea14695b351d884639ea972be40`. El insumo completo y el resultado esperado están versionados en [caso_t15_eventos.json](../../../tests/fixtures/d9/caso_t15_eventos.json). La prueba confirma el SHA del libro y que cantidades, mermas, moneda funcional, impuesto y tipos de cambio coinciden con los registros fuente.

1. Empresa B usa PEN como moneda funcional. `CAJA4KG` se compra en USD, sin impuesto unitario. El IGV del libro se recupera y no entra al costo.
2. El 10 de marzo se reciben 2.000 unidades a USD 0,80 con tipo de cambio 3,75: PEN 6.000,00.
3. El 5 de abril se reciben 1.000 unidades a USD 0,85 con tipo de cambio 3,72: PEN 3.162,00.
4. La orden `OS-01` produce 10 unidades. El componente establece 250 cajas por unidad y merma normal de 2 %. El 10 de abril registra consumo real de 2.600 cajas.

Los datos anteriores se leen de `EMPRESA`, `RECURSO`, `TIPO_CAMBIO`, `IMPUESTO`, `OBJETO` y `COMPONENTE`; las fechas y valores también se cotejan con las fórmulas `M-F-ING`, `M-F-CPU` y `M-F-EXCESO` de la fixture.

## Esperado independiente

El esperado se deriva con aritmética decimal separada del motor:

| Cálculo | Resultado |
|---|---:|
| Valor de entradas | 2.000 × 0,80 × 3,75 + 1.000 × 0,85 × 3,72 = PEN 9.162,00 |
| Costo promedio móvil | PEN 9.162,00 ÷ 3.000 = PEN 3,0540 por caja |
| Cantidad permitida | 10 × 250 × (1 + 2/100) = 2.550 cajas |
| Exceso anormal | 2.600 − 2.550 = 50 cajas |
| Valor real consumido | 2.600 × 3,0540 = PEN 7.940,40 |
| Material asignado al objeto | 2.550 × 3,0540 = PEN 7.787,70 |
| Pérdida anormal | 50 × 3,0540 = PEN 152,70 |
| Saldo en almacén | 3.000 − 2.600 = 400 cajas × PEN 3,0540 = PEN 1.221,60 |

Controles de conservación: `PEN 7.787,70 + PEN 152,70 = PEN 7.940,40`; `PEN 7.940,40 + PEN 1.221,60 = PEN 9.162,00`.

## Resultado leído del libro persistido

La prueba ejecuta dos T14 y un T15 a través de `Store.execute`, que guarda cada transacción en un XLSX temporal. Después vuelve a cargar ese archivo y compara estas filas con el JSON esperado:

| Cuenta y clave de B | Valores esperados y observados |
|---|---|
| `CTA_OBJ_PER` · objeto `OS-01`, periodo `2026-04`, empresa B | `COP_MAT=7.787,70`; `COP_PERD=152,70` |
| `CTA_OBJ_REC` · `OS-01 × CAJA4KG`, periodo `2026-04`, empresa B | `COR_CAN_PERM=2.550`; `COR_CAN_REAL=2.600`; `COR_MTO=7.940,40` |
| `CTA_GASTO` · periodo `2026-04`, centro `LINEA1`, concepto pérdida anormal, empresa B | `CGA_MTO=152,70`; `CGA_DED` queda vacío |

El mismo libro contiene filas de empresa A con claves operativas iguales. La prueba confirma que las filas A permanecen sin cambio, y que la repetición del mismo T15 retorna el recibo sin modificar ninguna de las siete hojas CTA.

## Límite del resultado

El caso valida el importe y las cantidades de tres cuentas en el recorrido T15 y demuestra que la transacción persiste el saldo. **No incluye una fila `RESULTADO_METODO`, no cubre las otras cuatro cuentas y no valida el cierre mensual completo.** `M-ACU-CGA-PERD` no define `CGA_DED`; por eso la casilla vacía no se considera una resolución tributaria ni una fila de gasto completamente contratada.

La ejecución de referencia y las pruebas de aislamiento, actualización y rollback están en [MVP_OLA3.md](MVP_OLA3.md) y [test_d9_event_accounts.py](../../../tests/test_d9_event_accounts.py). Los casos parciales T17/T19/T20 se documentan en [D9_CUADRE_EVENTOS.md](D9_CUADRE_EVENTOS.md). El contrato de las siete cuentas está en [D9_CONTRATO_DE_DATOS.md](D9_CONTRATO_DE_DATOS.md); siguen pendientes `CGA_DED` para pérdida anormal/ocio, fuentes y claves por cuenta y una conciliación integral con esperado independiente y `RESULTADO_METODO` persistido.
