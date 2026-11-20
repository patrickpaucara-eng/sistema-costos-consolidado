# D9 · matriz de cuentas y caso O-1

- **Fecha:** 20 de noviembre de 2026 (hora de Lima).
- **Rama de trabajo:** `desarrollo/mvp-ola3`, candidato `0.2.0`.
- **Resultado:** semántica de cuentas resuelta por el propietario conforme al MCD; aislamiento empresarial de escrituras CTA probado en el piloto. La línea base O-1 sigue siendo parcial y no es aceptación contable.

## Conclusión ejecutiva

La deuda D9 es real: en el DBD de la rama histórica, las siete tablas `CTA_*` reciben escrituras desde entre uno y siete servicios y el cierre que publica `RESULTADO_METODO` no las escribe. La hoja O-1 tampoco contiene estas siete cuentas. Las 14 pruebas históricas `xfail(strict=True)` describen ese incumplimiento, pero las siete pruebas de cuadre se detienen al detectar la hoja faltante; no comparan valores guardados en las cuentas.

La semántica ya no está pendiente: por instrucción del propietario y conforme al MCD, las cuentas operativas conservan los impactos de los eventos; el cierre las valida y concilia. No corresponde reemplazarlas por una reconstrucción agregada al cierre. La decisión y el límite de la evidencia están desarrollados en [D9_DECISION_SEMANTICA.md](D9_DECISION_SEMANTICA.md). El piloto también corrige el cruce entre empresas cuando la clave configurada en DBD omite `*_EMP`, y prueba aislamiento, reintento y reversión. Se añadió el [caso T15 con esperado decimal independiente](D9_CUADRE_T15.md), que concilia parcialmente tres cuentas por evento. Esto no concilia O-1, las otras cuentas o el cierre integral; no habilita resultados oficiales.

| Tabla | Servicios escritores DBD_4c | Transacciones raíz reportadas |
|---|---:|---|
| `CTA_ACTOR` | 2 | T21, T23.8 |
| `CTA_CENTRO` | 7 | T15, T17, T23.1, T23.2 |
| `CTA_GASTO` | 6 | T15, T16, T19, T23.0, T23.2, T23.5, T29.1 |
| `CTA_OBJ_PER` | 5 | T15, T16, T23.0, T23.2, T23.3 |
| `CTA_OBJ_REC` | 6 | T15, T16, T23.0 |
| `CTA_FUNCION` | 1 | T17 |
| `CTA_VTA_PER` | 3 | T20, T23.0, T23.3 |

El conteo corresponde a servicios DBD, ejecutados por el motor genérico; un mismo servicio puede aparecer bajo más de una transacción raíz. El inventario histórico no encuentra escritores Python/VBA productivos directos por nombre de tabla; hay una escritura de `CTA_OBJ_PER` sólo en un ayudante de prueba.

Se calculó una línea base de **119 filas y 15 agregaciones propuestas** sobre O-1, periodo `2021-01`, empresa `ENV`. Los totales coinciden con las salidas calculadas en memoria por el motor histórico. Eso no prueba que las cuentas estén conciliadas: O-1 no tiene las hojas CTA y `correr_o1()` no persiste una tabla `RESULTADO_METODO`. El detalle está en [D9_CONTROL_O1.csv](D9_CONTROL_O1.csv).

Tres propuestas de mapeo no tienen grano suficiente en la salida calculada: `CTA_GASTO` requiere centro, concepto y deducibilidad; `CTA_FUNCION` requiere función; `CTA_OBJ_REC` requiere recurso y cantidad además del objeto. No se deben completar esas dimensiones con valores inventados ni publicar esas cuentas como oficiales.

## Evidencia y procedencia

| Elemento | Revisión / SHA-256 |
|---|---|
| Fuente histórica de escritores y pruebas | `desarrollo/deuda@0b8f63cef1a94ab7602d880a814ce068b4d7a814`; copias conservadas en [`docs/fuentes/claude/ola3/d9`](../../fuentes/claude/ola3/d9/README.md). |
| Libro DBD del modelo | `fuente/DBD_Fuente.xlsx`, blob `ac172ef403886ad50e15ddb2f7b95e55a0bc22ac`; copia conservada en [insumos/DBD_Fuente.xlsx](../../fuentes/claude/ola3/d9/insumos/DBD_Fuente.xlsx); SHA-256 `479186097f106f845c51da794cdf4e43fd3a4376c6617e1ca6ee281e87980456`. |
| Fixture O-1 | `casos/V41/ENV.xlsx`, blob `dc0db68c56993556141b96467975e3b1e37e960c`; copia conservada en [insumos/ENV_O1.xlsx](../../fuentes/claude/ola3/d9/insumos/ENV_O1.xlsx); SHA-256 `d87eeb7f049efb0a48c7e920def4397ed5860633c85b622f9ee40bf1820f156e`. La copia se mantuvo sin cambios. |
| Libros completos MCD/DBD | ZIP original `docs/fuentes/originales/drive-download-20261118T142451Z-1-001.zip`, SHA-256 `c45f7670436f99792c3bb017066ce414cc2b2aa4f2914dec4ade4a983f08f7fc`. PDF MCD SHA-256 `1597195b8a94978a2d7b9c2115421fa9fd4a2aee0cf0f7ef633406fc230aa52d`; PDF DBD SHA-256 `d5dfe7e8bf564dd780148fa08fce47269b89433b67fe9d1c22b406465035568e`. |
| CSV de controles calculados | SHA-256 `fae12b5ebb57b7a472d7f875b7a21cef5529a0fb2c68718573acf7314f85e1da`; 119 filas de datos. |

El cálculo de referencia llamó `informes/DEUDA/escritores.py` y su `correr_o1()` en una copia temporal de solo lectura. Esa función calcula los métodos en memoria. No se integró ni se ejecutó código en el repositorio original, no se cambió la fixture ni se escribió `RESULTADO_METODO` en ella. La regeneración de esta línea base desde un checkout limpio todavía no está automatizada; el CSV conserva los resultados observados y la huella de la fixture.

El manifiesto [D9_SHA256SUMS](D9_SHA256SUMS) verifica esta matriz, la decisión semántica, el contrato, el caso T15, el JSON de esperado y el CSV. El manifiesto de [insumos D9](../../fuentes/claude/ola3/d9/insumos/SHA256SUMS) verifica las copias del DBD y la fixture.

## Esquema, grano y mapeo candidato

Los nombres de clave y las columnas se cotejaron con `DBD_Fuente.xlsx`. Los mapeos son hipótesis de conciliación tomadas de la deuda histórica; no son una aprobación de semántica o de asientos.

| Tabla DBD | Clave/grano registrado | Salida calculada que se propone comparar | Observación del caso O-1 |
|---|---|---|---|
| `CTA_OBJ_PER` | `COP_OBJ + COP_PER + COP_EMP`; columnas de costo incluyen `COP_MAT`, `COP_MOD`, `COP_IND`, `COP_PERD`, `COP_TRF`, `COP_IND_APL` | `LIQUIDACION_OT / OBJETO / PER_MD → COP_MAT`; `PER_PD → COP_MOD`; `PER_CIF → COP_IND`. Hay 11 claves de objeto y periodo/empresa se fijan por parámetros. | El grano propuesto por objeto es compatible para esas tres columnas; no cubre pérdidas, transferencias, indirectos aplicados u otras columnas. No existe hoja CTA que comparar. |
| `CTA_CENTRO` | `CCE_CEN + CCE_PER + CCE_EMP`; incluye suministrado, horas, tasa, asignado, ocio, función, recibido, distribuido y fijo/variable | `REPARTO_ETAPAS / CENTRO / COSTO_PROPIO → CCE_SUM`; `RECIBIDO → CCE_RECIB`; `DISTRIBUIDO → CCE_DIST`; `OCIO → CCE_OCIO`. Hay 17 centros. | La granularidad por centro está disponible. En las salidas calculadas, `CCE_SUM + CCE_RECIB = CCE_DIST` en total. Es un control interno del mismo cálculo, no un oráculo independiente. No hay hoja CTA en O-1. |
| `CTA_GASTO` | `CGA_PER + CGA_CEN + CGA_CON + CGA_EMP`; `CGA_MTO`, `CGA_DED` | Se propone comparar `LIQUIDACION_OT / PERIODO / GAD` y `GVT` con `CGA_MTO`. | **No conciliable por clave:** la salida sólo tiene clave de periodo/empresa (`ENV`), mientras la cuenta requiere centro, concepto y deducibilidad. No se debe repartir ni etiquetar el total sin fuente. |
| `CTA_OBJ_REC` | `COR_OBJ + COR_REC + COR_PER`; también almacena `COR_EMP`; distingue permitido, real cantidad y real monto | Se propone `REPARTO_ETAPAS / OBJETO / MD → COR_MTO`. Hay 11 objetos. | **No conciliable por clave:** resultado no incluye recurso; tampoco publica aquí cantidad real/permitida. El total por objeto no determina filas objeto×recurso. |
| `CTA_FUNCION` | `CFU_PER + CFU_FUN + CFU_EMP`; importe | Se propone `LIQUIDACION_OT / PERIODO / GAD`, `GVT` y `CPT`. | **No conciliable por clave:** la salida contiene `ENV`, no la función. No se puede asignar gasto/costo a función sin el atributo fuente. |
| `CTA_VTA_PER` | `VPE_PER + VPE_EMP`; ingreso y costo | `COSTO_VENTAS_OT / PERIODO / VENTAS → VPE_ING`; `CV → VPE_CST`. | Periodo/empresa es compatible con el resultado agregado. Totales de referencia: ingreso `401730.400000`; costo `242063.138748`. No hay hoja CTA en O-1. |
| `CTA_ACTOR` | `CAC_ACT + CAC_PER + CAC_EMP`; métricas conductuales (cantidad, tardanza, rechazos, variación de precio, indicador/tipo) | Sin correspondencia propuesta con los métodos de costo listados. | Es una cuenta de comportamiento alimentada por hechos del actor, no una salida de costo por orden. Se excluye de esta conciliación D9. |

### Totales del CSV

| Cuenta/campo | Fuente propuesta | Filas | Total calculado |
|---|---|---:|---:|
| `CTA_OBJ_PER.COP_MAT` | `LIQUIDACION_OT/OBJETO/PER_MD` | 11 | 166367.246990 |
| `CTA_OBJ_PER.COP_MOD` | `LIQUIDACION_OT/OBJETO/PER_PD` | 11 | 36520.913264 |
| `CTA_OBJ_PER.COP_IND` | `LIQUIDACION_OT/OBJETO/PER_CIF` | 11 | 80329.619484 |
| `CTA_CENTRO.CCE_SUM` | `REPARTO_ETAPAS/CENTRO/COSTO_PROPIO` | 17 | 136534.110000 |
| `CTA_CENTRO.CCE_RECIB` | `REPARTO_ETAPAS/CENTRO/RECIBIDO` | 17 | 11672.021651 |
| `CTA_CENTRO.CCE_DIST` | `REPARTO_ETAPAS/CENTRO/DISTRIBUIDO` | 17 | 148206.131651 |
| `CTA_CENTRO.CCE_OCIO` | `REPARTO_ETAPAS/CENTRO/OCIO` | 17 | 0.000000 |
| `CTA_GASTO.CGA_MTO` | `LIQUIDACION_OT/PERIODO/GAD`, `GVT` | 2 | 56204.490517* |
| `CTA_FUNCION.CFU_MTO` | `LIQUIDACION_OT/PERIODO/GAD`, `GVT`, `CPT` | 3 | 298276.940750 |
| `CTA_VTA_PER.VPE_ING` | `COSTO_VENTAS_OT/PERIODO/VENTAS` | 1 | 401730.400000 |
| `CTA_VTA_PER.VPE_CST` | `COSTO_VENTAS_OT/PERIODO/CV` | 1 | 242063.138748 |
| `CTA_OBJ_REC.COR_MTO` | `REPARTO_ETAPAS/OBJETO/MD` | 11 | 166367.246990 |

El asterisco en `CTA_GASTO.CGA_MTO` señala la suma aritmética de dos conceptos distintos: GAD `31583.185407` y GVT `24621.305110`. No se deben sumar en una única celda de cuenta sin clasificar los conceptos; la cifra no es un total conciliado. Los 119 renglones CSV se distribuyen así: 33 de `CTA_OBJ_PER`, 68 de `CTA_CENTRO`, 2 de `CTA_GASTO`, 3 de `CTA_FUNCION`, 2 de `CTA_VTA_PER` y 11 de `CTA_OBJ_REC`.

## Alcance de las pruebas recuperadas

- El archivo histórico `pruebas/deuda/test_cuadre_cuentas.py` deriva 7 `xfail` de escritor único y 7 de cuadre.
- `falla_cuadre()` termina antes de comparar cuando la hoja CTA no existe. Por tanto, esos siete `xfail` confirman falta de hoja, no diferencias monetarias.
- `E.correr_o1()` entrega resultados de cálculo en memoria; el test no lee una tabla persistida `RESULTADO_METODO` para su comparación.
- La auditoría OT-001 conserva otros valores CTA en escenarios históricos distintos (por ejemplo, centros y objetos en 2026). Sirven como regresiones de esos escenarios, pero no son la misma fixture/período ni prueban el cuadre O-1. Referencia: [`PRUEBAS_FROZEN_VERIFIED.log`](../../auditoria/OT-001/evidencias/PRUEBAS_FROZEN_VERIFIED.log).
- El CSV de este expediente es una **línea base reproducida del mismo cálculo histórico**. No es una fuente independiente de costos ni certifica que un importe debe llegar a una cuenta contable.

## Contraste metodológico: MCD y DBD

- *Modelamiento Conceptual de Datos*, edición 2025, p. impresa 13 (página 37 del PDF): las entidades cuenta registran efectos de eventos y expresan `Saldo final = Saldo inicial + Cambio (evento)`.
- El mismo libro, pp. impresas 18–19 (páginas 99–100 del PDF), explica acumuladores por ocurrencia/monto y su uso para describir el comportamiento dinámico de la cuenta.
- *Administración de Bases de Datos*, pp. 44–45, admite tablas suplementarias para consultas críticas sin perder los datos originales y exige controlar la redundancia.
- El mismo libro, p. 171, indica que una vista no tiene datos propios y puede responder más lento.

Esto sustenta separar hechos/cuentas operativas de proyecciones derivadas. La clasificación histórica D-I0b-1 decía que las siete tablas eran suplementarias y debían escribirse en el cierre; esa instrucción se conserva como evidencia, pero el propietario resolvió la semántica posterior a favor de MCD para las cuentas operativas actuales:

1. **Cuenta MCD operativa:** los eventos la afectan transaccionalmente por servicios configurados en DBD, ejecutados por las operaciones genéricas del motor; el cierre la valida y concilia, sin reemplazar los hechos acumulados.
2. **Proyección suplementaria eventual:** puede derivarse de hechos conservados y reglas aprobadas para una consulta concreta, pero debe tener identidad y reconstrucción propias y no confundirse con la cuenta operativa.

No se agrega un escritor de cierre para reconstruir estas mismas cuentas. La implementación genérica conserva la definición de servicios DBD y añade el ámbito de empresa del evento. La conciliación por grano y los tres mapeos incompletos siguen pendientes.

## Criterios para cerrar D9

1. **Resuelto:** aplicar semántica MCD a las cuentas operativas impactadas por eventos; mantener `CTA_ACTOR` fuera del costo. Véase [decisión D9](D9_DECISION_SEMANTICA.md).
2. Para cada campo, especificar fuente, signo, clave completa, periodo efectivo, agregación, moneda, redondeo, reversión y tratamiento de vacíos.
3. Resolver las dimensiones faltantes de `CTA_GASTO`, `CTA_FUNCION` y `CTA_OBJ_REC` con hechos fuente; si no existen, mantener esos campos fuera del resultado oficial.
4. Construir un caso con cuentas y `RESULTADO_METODO` persistidos en el mismo libro, y un esperado independiente del código que se valida.
5. Conciliar por clave y total; probar repetición del cierre, fallo intermedio, reversión/reapertura y que no haya doble acumulación. La regresión piloto ya cubre aislamiento de empresa, reintento de solicitud y reversión de T15.
6. Mantener la escritura de saldo en las transacciones que originan los eventos, con el mecanismo genérico configurado por DBD, y registrar evidencia reproducible. El cierre verifica/conciliará; no regenerará esas mismas cuentas.
