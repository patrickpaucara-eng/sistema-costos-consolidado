# Primer recorrido Python y Excel

La primera entrega 0.1 demostró compra y consumo usando el motor de Ola 1. La rama MVP Ola 3 agrega una cadena de cierre configurada desde HTML, con un guardado único del XLSX. El libro de prueba permanece intacto. El costo integral de una orden y la corrección de sus cuentas siguen pendientes.

## Preparar el entorno

Se requiere Python 3.11 o posterior. El entorno de verificación usa Python 3.12, openpyxl 3.1.5 y defusedxml 0.7.1. Desde una copia del repositorio, instalar el paquete una vez.

En Windows PowerShell, desde la raíz del repositorio:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install .
.\.venv\Scripts\python.exe -m reyna_local --data-dir datos --port 8765
```

En Linux:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/python -m reyna_local --data-dir datos --port 8765
```

La instalación descarga dependencias si no se dispone de una copia local. La operación posterior funciona sin conexión. Abrir en el navegador de ese mismo equipo la dirección que imprime el programa. Si el puerto está ocupado, usar `--port 0` y copiar la dirección elegida. `Ctrl+C` detiene el servidor.

## Libro de prueba

La fixture está en `tests/fixtures/ola1/Sistema_Costos.xlsx`. Es una copia inalterada de la revisión histórica indicada en su README y manifiesto. Se importa a un espacio de trabajo para preservar el archivo de origen.

En la pantalla crear un espacio con un nombre reconocible y la ruta local completa de la fixture. Elegir ese espacio y consultar sus tablas. Las reglas, usuarios y fechas del ejemplo son los del libro de prueba.

## Caso comprobable a mano

Elegir T14 y usuario ALMACEN1. La cabecera de la primera compra es:

```json
{"FECHA":20260310,"PER":"2026-03","EMP":"B","REC":"CAJA4KG","ALM":"ALM1","CANT":2000,"CU_DOC":0.80,"MON":"USD","IMP":"IGV"}
```

Las líneas son `[]` porque se usa una trama plana. Utilizar un identificador de solicitud propio para esa compra.

La segunda compra también es T14 con ALMACEN1:

```json
{"FECHA":20260405,"PER":"2026-04","EMP":"B","REC":"CAJA4KG","ALM":"ALM1","CANT":1000,"CU_DOC":0.85,"MON":"USD","IMP":"IGV"}
```

Para consumir 2.600 unidades, elegir T15 con SUPERV1:

```json
{"FECHA":20260410,"PER":"2026-04","EMP":"B","OBJ":"OS-01","CEN":"LINEA1","REC":"CAJA4KG","ALM":"ALM1","CANT":2600}
```

Usar un identificador distinto por operación y `[]` en líneas. Las reglas de cambio e impuesto del libro producen compras por S/ 6.000 y S/ 3.162. El promedio es S/ 3,054 por unidad. Tras el consumo quedan 400 unidades por S/ 1.221,60.

Consultar EXISTENCIA para CAJA4KG, ALM1, empresa B. La representación interna heredada usa coma flotante; el monto se verifica al céntimo. Detener y reiniciar el servidor con la misma carpeta de datos. Debe recuperar el mismo saldo.

## Cerrar el periodo de prueba

Después de registrar las dos compras y el consumo anterior, seleccionar **Cerrar un periodo**. Escribir `2026-04`, el usuario autorizado `JCOSTOS` y usar el identificador que la pantalla genera. Presionar **Cerrar periodo**. Para la fixture, la pantalla debe mostrar en orden T23.1, T23.2, T23.3, T23.5 y T23.9; la versión termina en 8 y el periodo B/2026-04 pasa a C. El saldo de CAJA4KG sigue en 400 unidades, S/ 3,054 por unidad y S/ 1.221,60.

El servicio toma los pasos marcados `OFICIAL` o `CIERRE` de `CIERRE_PASO`; por eso la secuencia depende de la configuración del libro. El mismo identificador y contenido recuperan el resultado registrado. Si un paso falla, la versión y las tablas de negocio quedan sin cambios, pero se anota el intento en `RECEIPTS`; repite con el mismo identificador para consultar ese resultado. Para una operación nueva, genera uno nuevo.

Este recorrido prueba el mecanismo de cierre y persistencia sobre la fixture. No valida la corrección de las cuentas D9, el costo integral de la orden, flete/T14.2 ni D14. No uses su resultado como costo oficial.

## Reintento y fallo

Conservar el identificador y contenido de una solicitud y repetirla. Debe devolver el resultado registrado sin duplicar. Cambiar el contenido conservando el identificador debe generar conflicto.

Una operación rechazada conserva el estado de negocio anterior. Un rechazo de negocio y un fallo técnico al guardar se muestran como errores distintos. Las pruebas inyectan un fallo técnico para comprobar el estado y el respaldo.

## Alcance actual

El ensayo requiere un operador local de confianza y usuarios de referencia. El formulario avanzado permite seleccionar T14, T15, T17, T19 y T20; solicita los campos en JSON y el motor valida el perfil y los campos declarados en DBD. La captura empresarial guiada con listas de negocio se completa después. Los casos independientes de T17/T19/T20 y sus límites están en [D9_CUADRE_EVENTOS.md](evidencias/D9_CUADRE_EVENTOS.md). En particular, su saldo inicial sintético de producto terminado sirve para probar T20, no como ejemplo de una orden producida. La cadena configurada de cierre ya se ejecuta desde HTML; la corrección contable y metodológica del cierre sigue pendiente.

Los espacios aíslan copias de libros. El MVP limita cada espacio a una empresa operativa y rechaza los operadores detectados en otra empresa; la separación completa en cada tabla/método no se ha probado. Reimporta espacios creados antes de esta versión para habilitar los metadatos de empresa y cierre. La recuperación del archivo debe validarse además en el equipo de destino, incluida una interrupción real del proceso y la interacción con Excel abierto.

El servicio debe ser el único editor del libro gestionado: cerrar Office y usar copias para inspección. El respaldo guarda una escritura anterior en el mismo disco. La [nota del adaptador](evidencias/ADAPTADOR_EXCEL.md) describe la recuperación en frío y sus límites. Conservar además respaldos separados para protegerse de pérdida del disco.

El VBA está preservado en referencia/vba-congelado. SQLite se aplaza. La adaptación futura del almacenamiento debe mantener los contratos y repetir las pruebas. El [registro de capacidades](REGISTRO_CAPACIDADES.md) enlaza los resultados y las limitaciones de esta versión.

Para repetir la aceptación desde la raíz, con el entorno donde se instaló el paquete:

```sh
python -m unittest discover -s tests -v
```

Los tests copian la fixture a directorios temporales. No necesitan ejecutar VBA ni tener Excel instalado. La prueba de Excel nativo bajo Windows se realiza por separado y sigue pendiente. La [evidencia MVP Ola 3](evidencias/MVP_OLA3.md) documenta el cierre y sus límites.
