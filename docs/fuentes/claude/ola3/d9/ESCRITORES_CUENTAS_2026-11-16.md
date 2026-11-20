# Escritores de las 7 cuentas (deuda grupo B, D-I0b-1)

Generado por `python3 -I informes/DEUDA/escritores.py` (no editar a mano; la prueba `pruebas/deuda/test_cuadre_cuentas.py` comprueba que este informe coincide con DBD_4c).

**Regla D-I0b-1** (`informes/I0b/TABLA_FINAL.md`): cada cuenta tiene **un solo escritor**, el paso del cierre que publica RESULTADO_METODO (`kit/v41/correr_caso.py`, K1→K9), y una prueba de cuadre entre ambos.

## Resumen

| Cuenta | Servicios que escriben (DBD_4c) | Transacciones raíz | Escritura Python/VBA por nombre en kit/ | ¿Escribe el cierre que publica RESULTADO_METODO? | ¿Hoja en ENV.xlsx (O-1)? |
|---|---|---|---|---|---|
| CTA_ACTOR | 2 | T21, T23.8 | 0 | No | No |
| CTA_CENTRO | 7 | T15, T17, T23.1, T23.2 | 0 | No | No |
| CTA_GASTO | 6 | T15, T16, T19, T23.0, T23.2, T23.5, T29.1 | 0 | No | No |
| CTA_OBJ_PER | 5 | T15, T16, T23.0, T23.2, T23.3 | 1 | No | No |
| CTA_OBJ_REC | 6 | T15, T16, T23.0 | 0 | No | No |
| CTA_FUNCION | 1 | T17 | 0 | No | No |
| CTA_VTA_PER | 3 | T20, T23.0, T23.3 | 0 | No | No |

**Conclusión [VERIFICADO 2026-11-16]:** ninguna cuenta cumple D-I0b-1 hoy. Todas se escriben desde varias transacciones del motor (en línea T15–T29 y lotes T23.x) y **ninguna** desde el cierre V4.1 que publica RESULTADO_METODO: `correr_caso.py` publica RESULTADO_METODO e INV_PROCESO (K9, por CARGA) pero no toca ninguna CTA_*. El caso O-1 (`casos/V41/ENV.xlsx`) ni siquiera trae las hojas, así que el cuadre no puede hacerse. Las pruebas quedan en `xfail(strict=True)` con esta razón.

## CTA_ACTOR

### Servicios de DBD_4c que escriben

| Servicio | Operación | Qué hace | Transacción raíz (modalidad) · cadena de SN |
|---|---|---|---|
| M-ACU-CAC | ACUMULAR | Acumular el hecho en la cuenta del actor | T21 «Hecho de comportamiento del proveedor» (ONLINE) · OP-HEC |
| M-ACT-CAC | ACTUALIZAR | Guardar indicador y tipología | T23.8 «calificar el comportamiento» (BATCH) · OP-CALIF>OP-CALIF-UNO |

### Escritura Python/VBA por nombre en kit/

- ninguna

### Correspondencia de cuadre con RESULTADO_METODO [PROPUESTA]

- **ninguna**: ningún método de la cadena V4.1 publica en RESULTADO_METODO un concepto que alimente esta cuenta.

## CTA_CENTRO

### Servicios de DBD_4c que escriben

| Servicio | Operación | Qué hace | Transacción raíz (modalidad) · cadena de SN |
|---|---|---|---|
| M-ACU-CCE-H | ACUMULAR | Horas efectivas del centro | T15 «Consumo de recursos en el objeto» (ONLINE) · OP-VIA>OP-VIA-CAP |
| M-ACU-CCE-SUM | ACUMULAR | El centro recibe el costo suministrado | T17 «Costo de un centro» (ONLINE) · OP-CEN-SUM |
| M-ACT-CCE-CIE | ACTUALIZAR | Guardar tasa, asignado y ocio | T23.2 «Cierre: costear la capacidad» (BATCH) · OP-CAP>OP-CAP-UNCEN |
| M-ACU-CCE-REC | ACUMULAR | El centro de producción recibe el servicio | T23.1 «Cierre: distribuir centros de servicio» (BATCH) · OP-REP-SEL>OP-REP-INT>OP-SRV-PASADA>OP-SRV-UNO>OP-SRV-DIST>OP-USO-DIST>OP-ENVIA>OP-A-PRD |
| M-ACU-CCE-DIST | ACUMULAR | Total distribuido por el centro de servicio | T23.1 «Cierre: distribuir centros de servicio» (BATCH) · OP-REP-SEL>OP-REP-INT>OP-SRV-PASADA>OP-SRV-UNO>OP-SRV-DIST |
| M-ACT-CCE-RCA | ACTUALIZAR | Guardar la separación fijo/variable usada | **ninguna** (servicio huérfano: no lo llama ningún SN) |
| M-ACT-CCE-EXT | ACTUALIZAR | Escribir en la cuenta del centro lo que entrega el resultado (mismos destinos que el reparto interno) | T23.1 «Cierre: distribuir centros de servicio» (BATCH) · OP-REP-SEL>OP-REP-EXT>OP-REP-UNO |

### Escritura Python/VBA por nombre en kit/

- ninguna

### Correspondencia de cuadre con RESULTADO_METODO [PROPUESTA]

- `CCE_SUM` ↔ `REPARTO_ETAPAS` · CENTRO · COSTO_PROPIO
- `CCE_RECIB` ↔ `REPARTO_ETAPAS` · CENTRO · RECIBIDO
- `CCE_DIST` ↔ `REPARTO_ETAPAS` · CENTRO · DISTRIBUIDO
- `CCE_OCIO` ↔ `REPARTO_ETAPAS` · CENTRO · OCIO

## CTA_GASTO

### Servicios de DBD_4c que escriben

| Servicio | Operación | Qué hace | Transacción raíz (modalidad) · cadena de SN |
|---|---|---|---|
| M-ACU-CGA-PERD | ACUMULAR | Gasto del periodo: pérdida anormal | T15 «Consumo de recursos en el objeto» (ONLINE) · OP-VAL-LINEA-T15>OP-VALOR-T15>OP-GASTO-PERD<br>T23.0 «Cierre: aplicar valuación (resultado del método externo a las salidas pendientes)» (BATCH) · OP-APL-VAL>OP-APL-EVE>OP-APL-LIN>OP-APL-PEND>OP-APL-EXT>OP-APL-T15>OP-VALOR-T15>OP-GASTO-PERD |
| M-ACU-CGA-OCIO | ACUMULAR | El ocio va al gasto del periodo | T23.2 «Cierre: costear la capacidad» (BATCH) · OP-CIE-CAP>OP-CIE-UNCEN |
| M-ACT-CGA-DEV | ACTUALIZAR | Reducir la pérdida anormal del periodo | T16 «Devolución de recursos del objeto» (ONLINE) · OP-VAL-LINEA-T16>OP-VALOR-T16>OP-GASTO-DEV<br>T23.0 «Cierre: aplicar valuación (resultado del método externo a las salidas pendientes)» (BATCH) · OP-APL-VAL>OP-APL-EVE>OP-APL-LIN>OP-APL-PEND>OP-APL-EXT>OP-APL-T16>OP-VALOR-T16>OP-GASTO-DEV |
| M-ACU-CGA-PER | ACUMULAR | Gasto del periodo por concepto y deducibilidad | T19 «Pérdida declarada (desmedro, siniestro)» (ONLINE) · OP-VAL-LINEA-T19>OP-VALOR-T19<br>T23.0 «Cierre: aplicar valuación (resultado del método externo a las salidas pendientes)» (BATCH) · OP-APL-VAL>OP-APL-EVE>OP-APL-LIN>OP-APL-PEND>OP-APL-EXT>OP-APL-T19>OP-VALOR-T19 |
| M-ACU-CGA-VNR | ACUMULAR | La rebaja es gasto del periodo (no deducible mientras no se realice) | T23.5 «Cierre: valor neto realizable (NIC 2)» (BATCH) · OP-VNR-SEL>OP-VNR-EXT>OP-VNR-FILA>OP-VNR-CLV>OP-VNR-APL>OP-VNR-REB<br>T23.5 «Cierre: valor neto realizable (NIC 2)» (BATCH) · OP-VNR-SEL>OP-VNR>OP-VNR-REC>OP-VNR-EXI>OP-VNR-REB |
| M-ACU-CGA-TFI | ACUMULAR | Faltante (o sobrante) del inventario físico al gasto del periodo | T29.1 «Toma de inventario físico» (ONLINE) · OP-TFI-LIN |

### Escritura Python/VBA por nombre en kit/

- ninguna

### Correspondencia de cuadre con RESULTADO_METODO [PROPUESTA]

- `CGA_MTO` ↔ `LIQUIDACION_OT` · PERIODO · GAD
- `CGA_MTO` ↔ `LIQUIDACION_OT` · PERIODO · GVT

## CTA_OBJ_PER

### Servicios de DBD_4c que escriben

| Servicio | Operación | Qué hace | Transacción raíz (modalidad) · cadena de SN |
|---|---|---|---|
| M-ACU-COP | ACUMULAR | El objeto recibe el costo por elemento; el exceso, como pérdida | T15 «Consumo de recursos en el objeto» (ONLINE) · OP-VAL-LINEA-T15>OP-VALOR-T15<br>T23.0 «Cierre: aplicar valuación (resultado del método externo a las salidas pendientes)» (BATCH) · OP-APL-VAL>OP-APL-EVE>OP-APL-LIN>OP-APL-PEND>OP-APL-EXT>OP-APL-T15>OP-VALOR-T15 |
| M-ACU-COP-IND | ACUMULAR | El objeto recibe los indirectos | T23.2 «Cierre: costear la capacidad» (BATCH) · OP-CIE-CAP>OP-CIE-UNCEN>OP-CIE-UNOBJ |
| M-ACT-COP-DEV | ACTUALIZAR | Descargar del objeto (costo y pérdida) | T16 «Devolución de recursos del objeto» (ONLINE) · OP-VAL-LINEA-T16>OP-VALOR-T16<br>T23.0 «Cierre: aplicar valuación (resultado del método externo a las salidas pendientes)» (BATCH) · OP-APL-VAL>OP-APL-EVE>OP-APL-LIN>OP-APL-PEND>OP-APL-EXT>OP-APL-T16>OP-VALOR-T16 |
| M-ACT-COP-TRF | ACTUALIZAR | Costo transferido | T23.3 «Cierre: liquidar objetos terminados» (BATCH) · OP-LIQ>OP-LIQ-UNO |
| M-ACU-COP-APL | ACUMULAR | El objeto recibe el CIF aplicado al cierre | T23.2 «Cierre: costear la capacidad» (BATCH) · OP-CIE-APL>OP-CIE-APL-UNO>OP-APL |

### Escritura Python/VBA por nombre en kit/

- `kit/instalador/probar_doble_corrida.py:28` — `wb["CTA_OBJ_PER"].append(["OE-01", "2026-03", 100, 20, 0, 0, 50, 0, "B"]); wb.save(libro)`

### Correspondencia de cuadre con RESULTADO_METODO [PROPUESTA]

- `COP_MAT` ↔ `LIQUIDACION_OT` · OBJETO · PER_MD
- `COP_MOD` ↔ `LIQUIDACION_OT` · OBJETO · PER_PD
- `COP_IND` ↔ `LIQUIDACION_OT` · OBJETO · PER_CIF

## CTA_OBJ_REC

### Servicios de DBD_4c que escriben

| Servicio | Operación | Qué hace | Transacción raíz (modalidad) · cadena de SN |
|---|---|---|---|
| M-ACT-COR-PERM | ACTUALIZAR | Guardar el permitido | T15 «Consumo de recursos en el objeto» (ONLINE) · OP-VAL-LINEA-T15>OP-VALOR-T15>OP-CLAS-INV<br>T23.0 «Cierre: aplicar valuación (resultado del método externo a las salidas pendientes)» (BATCH) · OP-APL-VAL>OP-APL-EVE>OP-APL-LIN>OP-APL-PEND>OP-APL-EXT>OP-APL-T15>OP-VALOR-T15>OP-CLAS-INV |
| M-ACT-COR-DEV | ACTUALIZAR | Reducir el real del objeto | **ninguna** (servicio huérfano: no lo llama ningún SN) |
| M-ACT-COR-DEV-Q | ACTUALIZAR | Reducir la CANTIDAD real del objeto (hecho) | T16 «Devolución de recursos del objeto» (ONLINE) · OP-DEV-Q |
| M-ACT-COR-DEV-V | ACTUALIZAR | Reducir el VALOR real del objeto (valor) | T16 «Devolución de recursos del objeto» (ONLINE) · OP-VAL-LINEA-T16>OP-VALOR-T16<br>T23.0 «Cierre: aplicar valuación (resultado del método externo a las salidas pendientes)» (BATCH) · OP-APL-VAL>OP-APL-EVE>OP-APL-LIN>OP-APL-PEND>OP-APL-EXT>OP-APL-T16>OP-VALOR-T16 |
| M-ACU-COR-Q | ACUMULAR | Cuenta objeto × recurso: acumular la CANTIDAD real (hecho) | T15 «Consumo de recursos en el objeto» (ONLINE) · OP-COR-Q-SEL>OP-COR-Q |
| M-ACU-COR-V | ACUMULAR | Cuenta objeto × recurso: acumular el MONTO (valor) | T15 «Consumo de recursos en el objeto» (ONLINE) · OP-VAL-LINEA-T15>OP-VALOR-T15>OP-CLAS-INV<br>T15 «Consumo de recursos en el objeto» (ONLINE) · OP-VAL-LINEA-T15>OP-VALOR-T15>OP-COR-MOD<br>T23.0 «Cierre: aplicar valuación (resultado del método externo a las salidas pendientes)» (BATCH) · OP-APL-VAL>OP-APL-EVE>OP-APL-LIN>OP-APL-PEND>OP-APL-EXT>OP-APL-T15>OP-VALOR-T15>OP-CLAS-INV<br>T23.0 «Cierre: aplicar valuación (resultado del método externo a las salidas pendientes)» (BATCH) · OP-APL-VAL>OP-APL-EVE>OP-APL-LIN>OP-APL-PEND>OP-APL-EXT>OP-APL-T15>OP-VALOR-T15>OP-COR-MOD |

### Escritura Python/VBA por nombre en kit/

- ninguna

### Correspondencia de cuadre con RESULTADO_METODO [PROPUESTA]

- `COR_MTO` ↔ `REPARTO_ETAPAS` · OBJETO · MD

## CTA_FUNCION

### Servicios de DBD_4c que escriben

| Servicio | Operación | Qué hace | Transacción raíz (modalidad) · cadena de SN |
|---|---|---|---|
| M-ACU-CFU | ACUMULAR | Costo por función (NIIF 18) | T17 «Costo de un centro» (ONLINE) · OP-CEN-FUN |

### Escritura Python/VBA por nombre en kit/

- ninguna

### Correspondencia de cuadre con RESULTADO_METODO [PROPUESTA]

- `CFU_MTO` ↔ `LIQUIDACION_OT` · PERIODO · GAD
- `CFU_MTO` ↔ `LIQUIDACION_OT` · PERIODO · GVT
- `CFU_MTO` ↔ `LIQUIDACION_OT` · PERIODO · CPT

## CTA_VTA_PER

### Servicios de DBD_4c que escriben

| Servicio | Operación | Qué hace | Transacción raíz (modalidad) · cadena de SN |
|---|---|---|---|
| M-ACU-VPE-LIQ | ACUMULAR | Costo de ventas del periodo: ajuste de cierre de lo ya vendido | T23.3 «Cierre: liquidar objetos terminados» (BATCH) · OP-LIQ>OP-LIQ-UNO>OP-LIQ-DIST>OP-LIQ-VEN |
| M-ACU-VPE-H | ACUMULAR | Cuenta de ventas del periodo: ingreso (hecho) | T20 «Venta (costo de ventas)» (ONLINE) · OP-VTA-REG |
| M-ACU-VPE-V | ACUMULAR | Cuenta de ventas del periodo: costo (valor) | T20 «Venta (costo de ventas)» (ONLINE) · OP-VAL-LINEA-T20>OP-VALOR-T20<br>T23.0 «Cierre: aplicar valuación (resultado del método externo a las salidas pendientes)» (BATCH) · OP-APL-VAL>OP-APL-EVE>OP-APL-LIN>OP-APL-PEND>OP-APL-EXT>OP-APL-T20>OP-VALOR-T20 |

### Escritura Python/VBA por nombre en kit/

- ninguna

### Correspondencia de cuadre con RESULTADO_METODO [PROPUESTA]

- `VPE_ING` ↔ `COSTO_VENTAS_OT` · PERIODO · VENTAS
- `VPE_CST` ↔ `COSTO_VENTAS_OT` · PERIODO · CV

## Escritores genéricos en kit/ (no nombran la cuenta)

| Archivo | Punto | Nota |
|---|---|---|
| `kit/motor_espejo.py` | Motor.m_ACUMULAR / m_ACTUALIZAR / CREAR | Ejecuta los servicios de DBD_4c: no es un escritor propio, materializa los servicios listados arriba. |
| `kit/vba/motor.bas` | MActualizar (Case "ACUMULAR"/"ACTUALIZAR"/"CREAR") | Motor VBA: igual que el espejo, ejecuta los servicios de DBD_4c. |
| `kit/casos/sembrar_caso.py` | sembrar() | Copia a la base toda hoja del caso que exista en ella (solo excluye RESULTADO_METODO y ALERTA): escribiría la cuenta si el caso trae la hoja. ENV.xlsx (O-1) no trae ninguna CTA_*. |

Las copias `kit/entrega/` y `kit/kit/` repiten los mismos archivos y se excluyen del recuento.

## Método

- Escritor en DBD_4c = servicio cuya operación (MET[1]) es CREAR, ACUMULAR, ACTUALIZAR, ELIMINAR y cuya tabla (MET[2]) es la cuenta. LEER, PARACADA, VALIDA, SI y FORMULA no escriben.
- Transacción raíz: DBD_4b da SN→SAD; un SN «(sub)» se sube por el servicio PARACADA/SI que lo nombra en MET[3].
- Escritura por nombre en kit/: línea con la cuenta y `.append(`, `.cell(`, `setc(`, `]=` o `.Value=`, excluidas las condiciones `If`.
