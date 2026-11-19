# Revisión independiente de la primera capacidad Excel/Python/HTML

## Alcance y oráculo

El ensayo inicia el adaptador HTTP local con directorios temporales. Cada espacio persiste su libro gestionado en Excel. Las pruebas usan una copia del XLSX de Ola 1, sin modificar el original. El SHA-256 del fixture es `43c9170c04b23e678de7abf7bab39f43c4251ea14695b351d884639ea972be40`. Comprobé por comparación de bytes que `src/reyna_local/motor_espejo.py` coincide con la copia de auditoría Ola 1 `cac2501d9f712655dda466d216dc5bff2dd446a5`. SHA-256 del motor `8c962583170cbb200c564bef8edfd95ae931602b82fa2f89f2bb48bcd9ce2a11`.

El oráculo deriva de los casos históricos 1–3. Dos compras ingresan 2 000 unidades a costo S/ 3 y 1 000 a S/ 3,162. La valuación media alcanza S/ 3,054. El consumo de 2 600 deja 400 unidades y S/ 1 221,60. La ejecución directa previa en una copia de Ola 1 confirmó los tres OK, el saldo y el costo unitario. La persistencia conserva los datos representables en el XLSX. Para moneda se evalúa el centavo y se conserva la tolerancia binaria donde corresponda.

## Pruebas ejecutadas

1. Importar, ejecutar T14/T15, comprobar importes y reabrir el servidor y el XLSX gestionado. Validar huella del libro de origen.
2. Reintentar la misma solicitud tras reiniciar y comprobar su respuesta; rechazar el mismo identificador con carga distinta.
3. Fallar en la segunda línea tras un control que acredita la validez de la primera. Comparar filas y versión en EVENTO, LINEA, KARDEX y EXISTENCIA tras reiniciar.
4. Operar dos espacios con el mismo identificador de solicitud y comparar saldos. Esta cobertura es aislamiento de espacios. No acredita aislamiento empresarial dentro del mismo libro.
5. Ejecutar dos solicitudes distintas y un duplicado concurrentemente contra dos procesos cooperantes, con el mismo directorio.
6. Interrumpir de forma controlada el reemplazo del XLSX, confirmar que el estado anterior conserva todos sus bytes, reintentar y restaurar una generación de respaldo en frío.
7. Comprobar que una hoja informativa con fórmula inocua, el tema y los estilos conservan sus bytes OOXML.
8. Excluir hojas de credenciales de la interfaz HTTP.
9. Rechazar orígenes y hosts ajenos y aceptar la misma solicitud desde el origen permitido.

Comando de aceptación, desde el consolidado.

```sh
/workspace/work/reyna-env/bin/python -m unittest discover -s tests -v
```

Resultado de la ejecución con entorno reducido, openpyxl 3.1.5 y defusedxml 0.7.1: **9 aprobadas, 0 omitidas, 15,598 s**. La lectura directa de `libro.xlsx` confirmó las mismas filas que HTTP. La inyección falla inmediatamente antes del reemplazo del libro principal. El reintento se aplicó una sola vez y el respaldo restaurado conservó el recibo de la operación anterior. Esta prueba no simula pérdida de alimentación, fallos físicos ni edición concurrente en Excel.

## Hallazgos de alcance

- El HTTP se vincula a 127.0.0.1. Exige Host local, valida un Origin cuando está presente y requiere JSON para mutaciones. El puerto limita las tablas y no devuelve `USUARIO` ni `SEM_USUARIO`. El campo usuario sigue siendo una identificación declarada al motor, sin autenticación del operador en HTTP. Los archivos de origen, trabajo y respaldo conservan las credenciales históricas del propio libro y requieren custodia local.
- El cierre de la ventana de escritura usa un bloqueo entre procesos cooperantes, control de archivos de bloqueo de Office y comprobación de bytes antes de reemplazar. Una edición externa entre operaciones puede alterar datos, reglas o recibos sin incrementar la versión. El contrato de este piloto debe reservar la modificación del libro gestionado al servicio y usar copias para inspección o trabajo externo.
- La prueba de integridad de partes OOXML comprueba el XML de una hoja ajena a la transacción, el tema y los estilos. También se verificaron una fórmula ajena y el formato de una celda operativa de EXISTENCIA después de contabilizar. No se abrió Excel nativo ni se comprobó el cálculo de fórmulas por Excel. Solo se habilitan las transacciones T14/T15, con estructura derivada de las tramas declaradas en el libro. Se mantiene pendiente la validación de toda la cadena multicompañía, la recuperación después de cortes físicos y el resto de las capacidades históricas.
