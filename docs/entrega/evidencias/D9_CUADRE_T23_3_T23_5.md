# D9 · liquidación de orden y rebaja VNR

**Fecha:** 20 de noviembre de 2026 (hora de Lima).

**Estado:** caso de control independiente aprobado para la ruta base; no cierra D9 ni valida un costo comercial ORIA.

## Fuente y configuración

La prueba verifica el SHA-256 de `tests/fixtures/ola1/Sistema_Costos.xlsx` (`43c9170c04b23e678de7abf7bab39f43c4251ea14695b351d884639ea972be40`) y coteja en ese libro la orden `OS-01` de B (10 t), el catálogo `PRODUCTO_PT` (250 cajas por t), el componente `CAJA4KG` (250 cajas de cartón por t y 2 % de merma normal), la tarifa VNR de `CAJA_SINT` para abril (PEN 8 menos gasto de venta PEN 1) y los métodos base `BASE_LIQUIDACION` y `BASE_AJUSTES_NIC2` en estado APROBADO. Las tramas se ejecutan en una copia temporal del libro.

Las entradas de compra, consumo y producto terminado son tramas sintéticas creadas solo para el control; no provienen de un escenario comercial de la fixture. La prueba las ejecuta en una copia temporal del XLSX y vuelve a leer las hojas persistidas.

La clave de `SALIDA` incluye almacén (`SAL_ALM`), junto con objeto, periodo, producto y empresa, como indica la clave declarada en DBD (`DBD_4_Modelo_Interno`, G177). El test exige una sola fila que coincida con cada clave esperada; no acepta la primera fila de una búsqueda ambigua.

## Oráculo manual

| Magnitud | Cálculo independiente | Esperado |
|---|---|---:|
| Producción terminada | `10 t × 250 cajas/t` | 2.500 `CAJA_SINT` |
| Material permitido | `10 t × 250 cajas de cartón/t × (1 + 2/100)` | 2.550 cajas de cartón |
| Material consumido | Trama T15 | 2.550 cajas de cartón |
| Costo unitario del material | Compra sintética | PEN 10,00 |
| Costo material de OS-01 | `2.550 × 10,00` | PEN 25.500,00 |
| Costo por caja terminada | `25.500 / 2.500` | PEN 10,20 |
| VNR unitario | `8,00 − 1,00` | PEN 7,00 |
| VNR total | `2.500 × 7,00` | PEN 17.500,00 |
| Rebaja por VNR | `2.500 × (10,20 − 7,00)` | PEN 8.000,00 |
| Existencia final | 2.500 cajas × PEN 7,00 | PEN 17.500,00 |

La comparación incluye el estado/costo de `OBJETO`, la salida `SALIDA` con su clave `objeto/periodo/producto/almacén/empresa`, las cuentas `CTA_OBJ_PER`, `CTA_OBJ_REC` y `CTA_GASTO`, el registro `AJUSTE_VNR` y el saldo `EXISTENCIA`. La fila A de `CTA_GASTO` con la misma clave de periodo/centro/concepto se siembra con PEN 77 y `CGA_DED=S`; permanece sin cambios mientras la fila B recibe la rebaja PEN 8.000 y `CGA_DED=N`. El test exige una única fila por cada clave completa esperada. El cierre termina B/2026-04 y repetir el mismo identificador no duplica efectos.

También se inyecta un fallo en T23.5, después de que T23.3 haya calculado la transferencia en la copia en memoria. El libro persistido conserva todas las tablas de negocio antes del intento; un identificador nuevo permite repetir el cierre correctamente.

## Límite metodológico y siguiente trabajo

El caso acredita el recorrido técnico de T18 → T23.3 → T23.5 y el cuadre de estos saldos de la ruta base con una aritmética separada y unidades compatibles con `PRODUCTO_PT`. No acredita un método externo T25.4, selección de una corrida externa por huella, costo integral con mano de obra/indirectos, ventas previas a liquidación, D14, flete tardío ni la aceptación tributaria/contable general.

La hoja `RESULTADO_METODO` de la fixture no contiene resultados de esta corrida ni filas de método que puedan compararse con esas cuentas. Por ello no se afirma conciliación integral D9 ni costo oficial. Siguen pendientes la procedencia por evento/línea/método, claves únicas por empresa, `CGA_DED` para pérdida anormal y ocio, reapertura/reversas y el cuadre integral de todas las cuentas del alcance.

Una revisión independiente de solo lectura detectó inicialmente la omisión de `SAL_ALM` y el desajuste entre toneladas de la orden y cajas de producto. Se incorporaron la unidad de rendimiento de `PRODUCTO_PT`, la clave completa y una aserción de unicidad antes de aceptar el caso parcial.

## Reproducir

```sh
python -m unittest tests.test_d9_event_accounts.D9EventAccounts.test_cierre_t23_3_t23_5_cuadra_orden_y_vnr_con_calculo_independiente
python -m unittest tests.test_d9_event_accounts.D9EventAccounts.test_fallo_en_t23_5_revierte_t23_3_y_todo_el_cierre
```

La trama completa y los importes esperados están en [`caso_t23_3_t23_5_cierre.json`](../../../tests/fixtures/d9/caso_t23_3_t23_5_cierre.json). La base metodológica de saldos afectados por eventos consta en MCD §6.2.1 y DBD p. 75; el alcance específico del contrato está en [`D9_CONTRATO_DE_DATOS.md`](D9_CONTRATO_DE_DATOS.md).
