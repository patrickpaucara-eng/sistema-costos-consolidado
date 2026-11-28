# libros_hostiles/ — pieza 24 (MN 01)

Son 8 copias de `SERVITEC_sintetico.xlsx` (libro sintético, sin datos reales), cada una con **un** defecto, más una copia de control. Cada archivo trae una hoja **LEEME** al inicio. Esa hoja dice:
- qué defecto tiene y las celdas exactas que se tocaron;
- qué mensaje **debería** dar el sistema;
- qué mensaje dio **de verdad** `libro_dbd.validar()`.

No se modificó ningún archivo del repo ni el libro base: cada defecto se aplicó sobre una copia.

## Resultado

La columna «Mensaje real» es la salida de `validar()` y `calcular()` del repo con el motor completo, ejecutada el 28/11/2026. Las mismas salidas están en `resultados_validar.json`.

| Archivo | Defecto | Mensaje que debería dar | Mensaje real de `validar()` | ¿Detecta? |
|---|---|---|---|---|
| 00_control_sin_defecto | ninguno | sin errores; julio REB 22,975 / MPR 5,165 | (acepta); calcular(): REB 22,975 / MPR 5,165 | ✔ control |
| 01_hoja_obligatoria_borrada | falta la hoja CRITERIO | Falta la hoja CRITERIO. Inductores (unidad de medida). | igual | ✔ |
| 02_celdas_vacias_MEDIDA | MED_CAN vacío, filas 184–186 | Hoja MEDIDA, fila 184: la cantidad debe ser un número ≥ 0. (y filas 185, 186) | igual (3 mensajes) | ✔ |
| 03_texto_en_monto | VTA_ING = «30,000» (texto), fila 14 | Hoja VENTA, fila 14: el ingreso (VTA_ING) debe ser un número. | igual | ✔ |
| 04_fechas_al_reves | PER_INI > PER_FIN en 2025-07 | *Propuesto:* Hoja PERIODO, fila 8: PER_INI (20250731) es posterior a PER_FIN (20250701). | (acepta); calcular() tampoco avisa | ✘ hallazgo |
| 05_codigo_duplicado | OT-SRV-REB-2025-07 dos veces (cantidad 10 y 12) | *Propuesto:* Hoja OBJETO, fila 18: OBJ_NUM «OT-SRV-REB-2025-07» está repetido (ya está en la fila 14). | (acepta); calcular(): REB cantidad 12, unitario **1,914.58** (correcto 2,297.50) | ✘ hallazgo GRAVE |
| 06_criterio_suma_cero | DES_OT de julio = 0 en las dos órdenes | Al cargar: aviso. Al calcular: «I8: P4C DES tiene monto 5700.00 y su criterio DES_OT suma cero» | carga (acepta); calcular(): el mensaje I8 exacto | ½ solo al calcular |
| 07_archivo_truncado | archivo cortado al 50 % de sus bytes | El archivo no es un libro Excel (.xlsx) legible. | igual | ✔ |
| 08_columnas_otro_orden | MEDIDA y OBJETO con columnas invertidas | sin errores y el mismo costo que el control | (acepta); calcular(): REB 22,975 / MPR 5,165 | ✔ |

Como el archivo 07 no se puede abrir, su LEEME también está aparte, en `07_archivo_truncado_LEEME.md`.

## Hallazgos (solo se reportan, no se corrigieron; los corrige otro agente antes del 9-dic)

1. **Código duplicado (05), el más grave.** `validar()` arma OBJETO como diccionario por OBJ_NUM, así que la fila repetida pisa a la primera. `calcular()` acepta el libro y deja REB con cantidad 12: el costo total sigue en 22,975, pero el costo unitario baja a **1,914.58** (lo correcto es 2,297.50, un −16.7 %) y el margen del mes sube de 9,860 a **13,422.33**. Nada avisa.
2. **Fechas al revés (04).** Ni `validar()` ni `calcular()` comparan PER_INI con PER_FIN. Julio da los mismos costos, así que el error pasa sin que nadie lo note. `validar()` tampoco revisa que EVE_FEC caiga dentro de su periodo.
3. **Criterio en cero (06).** La carga lo acepta; recién `calcular()` lo rechaza con la regla I8, que aquí da «I8: P4C DES tiene monto 5700.00…». Lo ideal es avisar al cargar.
4. **Montos con texto.** `_num()` acepta «30000» escrito como texto, porque `float("30000")` funciona. Además, `validar()` no revisa LIN_MTO, LIN_CAN ni LIN_CU_DOC de LINEA.

## Verificación automática

`python -I verificar_pieza24.py <repo>/src` pasa los 9 libros por `validar()` y `calcular()` y los compara con lo esperado. Resultado del 28/11/2026: **PIEZA 24: OK (9 libros)**.

Los casos 04, 05 y 06 están escritos con el comportamiento de **hoy**. Cuando otro agente corrija esos defectos, la verificación fallará a propósito. Ahí hay que reemplazar lo esperado por el mensaje nuevo, y esa falla es la prueba de que la corrección funcionó.

## Cómo se reproduce

```
python -I _generador/hacer_hostiles.py SERVITEC_sintetico.xlsx libros_hostiles <repo>/src <repo>/casos/plantilla_dbd.xlsx
python -I verificar_pieza24.py <repo>/src libros_hostiles
```

Para generar los libros se usó `casos/plantilla_dbd.xlsx` y `fuente/DBD_Fuente.xlsx` de motor_completo.zip, copiados en una copia de trabajo del repo. El código del repo no se tocó.
