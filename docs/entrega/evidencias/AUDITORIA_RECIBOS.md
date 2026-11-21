# CAP-13 · Auditoría de recibos y versión

`GET /api/workspaces/{id}/audit` lee una captura de `libro.xlsx` resuelta por el almacén local. La respuesta HTTP 200 incluye `valid`, `workbook_version`, `expected_version`, `receipt_count` e `issue_count`. Cada entrada de `issues` contiene código, hoja, fila física y detalle. Se muestran las primeras 100 incidencias y el recuento incluye todas las observadas. La versión calculada es `null` si la hoja de recibos no se puede leer completa o un recibo impide determinar su incremento. Un identificador de espacio inexistente devuelve HTTP 404, un XLSX ilegible devuelve 422 y se mantienen los límites de tamaño del piloto.

El lector recorre `_ReynaRecibos` en orden físico desde la versión cero. Calcula el SHA-256 del texto UTF-8 del comando almacenado, comprueba que los identificadores sean únicos y coincidan con los de las respuestas, y contrasta el resultado HTTP, la operación y la versión. Para el cierre también compara el periodo y la empresa, y verifica la coherencia de los resultados de cada paso. Los informes exponen las coordenadas del recibo y omiten el identificador, la huella, el comando y la respuesta almacenados.

## Incrementos que aplica el servicio

| Recibo | Estado HTTP | Incremento |
|---|---:|---:|
| Transacción con resultado `OK` | 200 | 1 |
| Cierre con uno o más pasos, todos `OK` | 200 | Número de pasos en la respuesta |
| Transacción o cierre con resultado `ERROR` persistido | 422 | 0 |

El cierre ejecuta los pasos `OFICIAL` o `CIERRE` configurados y, si todos terminan en `OK`, aplica un solo reemplazo del archivo. Un rechazo persistido conserva la versión y añade su recibo. Las validaciones previas que interrumpen la operación antes de escribir y los reintentos idempotentes no añaden recibos. `respaldo.xlsx` guarda la captura anterior al último recibo escrito. El lector Python `reyna_local.receipt_audit.audit_receipts(path)` permite verificarlo contra sus propios recibos y metadatos. [Código de persistencia](../../../src/reyna_local/store.py).

## Evidencia

```sh
python -m unittest discover -s tests -p test_receipt_audit.py -v
```

Seis pruebas pasaron en Linux con Python y las dependencias del proyecto. Usaron copias temporales de la fixture histórica Ola 1 (`43c9170c04b23e678de7abf7bab39f43c4251ea14695b351d884639ea972be40`). El cierre exitoso sumó cinco pasos a una versión previa de 3 y el respaldo validó su versión 3. Los rechazos de transacción y cierre conservaron la versión 0. Las alteraciones aisladas de huella, comando, respuesta, identificador, estado, pasos y versión produjeron diagnósticos con coordenadas. Se comprobó que el comando de cierre conserva compatibilidad con una huella textual opcional de 1–20 caracteres, conforme al ancho DBD, sin imponer un algoritmo SHA. La prueba HTTP verificó el informe sanitizado y el 404. Las comparaciones de bytes confirmaron que la auditoría es de solo lectura. [Pruebas focalizadas](../../../tests/test_receipt_audit.py).

## Límites y revisión siguiente

La huella cubre solo el comando y se guarda en el mismo archivo. Cambios coordinados de comando y huella, cambios de texto libre coherentes con el contrato y la eliminación de un último rechazo pueden pasar sin incidencias. El lector usa los pasos registrados, y una captura coherente no acredita que el motor ejecutó el cálculo ni que sus tablas de negocio sean correctas. La publicación contable y la autenticidad requieren evidencia independiente. La siguiente validación operativa es repetir el ensayo con el XLSX del piloto en Windows/Excel nativo.
