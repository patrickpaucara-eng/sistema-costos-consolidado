# libros_hostiles/ — pieza 24 (MN 01)

Son 8 copias de `SERVITEC_sintetico.xlsx` (libro sintético, sin datos reales), cada una con **un** defecto, más una copia de control. Cada archivo trae una hoja **LEEME** al inicio. Esa hoja dice:
- qué defecto tiene y las celdas exactas que se tocaron;
- qué mensaje **debería** dar el sistema;
- qué mensaje dio **de verdad** `libro_dbd.validar()`.

No se modificó ningún archivo del repo ni el libro base: cada defecto se aplicó sobre una copia.

## Resultado

La columna «Mensaje real» es la salida de `validar()` del repo ligero, ejecutada el 28/11/2026. Las mismas salidas están en `resultados_validar.json`.

| Archivo | Defecto | Mensaje que debería dar | Mensaje real de `validar()` | ¿Detecta? |
|---|---|---|---|---|
| 00_control_sin_defecto | ninguno | sin errores | (acepta) | ✔ control |
| 01_hoja_obligatoria_borrada | falta la hoja CRITERIO | Falta la hoja CRITERIO. Inductores (unidad de medida). | igual | ✔ |
| 02_celdas_vacias_MEDIDA | MED_CAN vacío, filas 184–186 | Hoja MEDIDA, fila 184: la cantidad debe ser un número ≥ 0. (y filas 185, 186) | igual (3 mensajes) | ✔ |
| 03_texto_en_monto | VTA_ING = «30,000» (texto), fila 14 | Hoja VENTA, fila 14: el ingreso (VTA_ING) debe ser un número. | igual | ✔ |
| 04_fechas_al_reves | PER_INI > PER_FIN en 2025-07 | *Propuesto:* Hoja PERIODO, fila 8: PER_INI (20250731) es posterior a PER_FIN (20250701). | (acepta) | ✘ hallazgo |
| 05_codigo_duplicado | OT-SRV-REB-2025-07 dos veces (cantidad 10 y 12) | *Propuesto:* Hoja OBJETO, fila 18: OBJ_NUM «OT-SRV-REB-2025-07» está repetido (ya está en la fila 14). | (acepta) | ✘ hallazgo |
| 06_criterio_suma_cero | DES_OT de julio = 0 en las dos órdenes | Al calcular: «I8: P4C DES tiene monto [monto] y su criterio DES_OT suma cero» | (acepta; el error saldría al calcular) | ½ POR VERIFICAR |
| 07_archivo_truncado | archivo cortado al 50 % de sus bytes | El archivo no es un libro Excel (.xlsx) legible. | igual | ✔ |
| 08_columnas_otro_orden | MEDIDA y OBJETO con columnas invertidas | sin errores y el mismo costo que el control | (acepta) | ✔ (costo POR VERIFICAR) |

Como el archivo 07 no se puede abrir, su LEEME también está aparte, en `07_archivo_truncado_LEEME.md`.

## Hallazgos (solo se reportan, no se corrigieron)

1. **Fechas al revés (04).** `validar()` no compara PER_INI con PER_FIN. Tampoco revisa que EVE_FEC caiga dentro de su periodo. El efecto en el cálculo está POR VERIFICAR: `motor_espejo.py` ordena los periodos abiertos por PER_INI.
2. **Código duplicado (05).** `validar()` arma OBJETO como un diccionario por OBJ_NUM, así que la fila repetida **pisa a la primera sin aviso** (la cantidad pasa de 10 a 12). `motor_espejo.py` (línea 594) sí avisa «Clave duplicada…», pero solo cuando lee tablas dentro de una transacción. Está POR VERIFICAR si salta al calcular.
3. **Criterio en cero (06).** `validar()` acepta MED_CAN = 0 porque es «≥ 0». El rechazo existe más adelante, en `metodos/reparto_etapas.py` línea 290 (regla I8). Si se adelantara la regla a la carga, el usuario lo sabría antes de calcular.
4. **Montos con texto.** `_num()` acepta «30000» escrito como texto, porque `float("30000")` funciona: no rechaza texto que parece número. `validar()` tampoco revisa LIN_MTO, LIN_CAN ni LIN_CU_DOC de LINEA. Un «5,344» en LINEA no se detecta en la carga.
5. **Cifras de control.** REB 22,975 y MPR 5,165 son las que dio el dueño. **No se pudieron recalcular aquí**, porque el repo ligero no trae `fuente/DBD_Fuente.xlsx` y `calcular()` se detiene con «CONSUME: la entidad o tabla «(sin MCD) KARDEX» no existe en DBD_4». La comprobación de los casos 00, 06 y 08 en el cálculo queda POR VERIFICAR con el repo completo.

## Cómo se reproduce

```
python -I _generador/hacer_hostiles.py SERVITEC_sintetico.xlsx libros_hostiles <repo>/src plantilla_dbd_vacia.xlsx
python -I _generador/correr_validar.py <repo>/src plantilla_dbd_vacia.xlsx libros_hostiles/*.xlsx
```

El arnés apunta `libro_dbd.PLANTILLA` a `plantilla_dbd_vacia.xlsx` del paquete, porque el repo ligero no trae `casos/plantilla_dbd.xlsx`. Se supone que ambos tienen las mismas cabeceras (POR VERIFICAR).
