# Primer recorrido Python y Excel

La versión 0.1 es un ensayo técnico de compra y consumo usando el motor de Ola 1. Las reglas se leen de una copia del libro. Python ejecuta las operaciones desde HTML y guarda el estado en Excel. El costo integral de una orden y el cierre mensual corresponden a lotes posteriores.

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

## Reintento y fallo

Conservar el identificador y contenido de una solicitud y repetirla. Debe devolver el resultado registrado sin duplicar. Cambiar el contenido conservando el identificador debe generar conflicto.

Una operación rechazada conserva el estado de negocio anterior. Un rechazo de negocio y un fallo técnico al guardar se muestran como errores distintos. Las pruebas inyectan un fallo técnico para comprobar el estado y el respaldo.

## Alcance actual

El ensayo requiere un operador local de confianza y usuarios de referencia. El formulario avanzado solicita los campos en JSON. La captura empresarial con campos y listas de negocio se completa después.

Los espacios aíslan copias de libros. Dos empresas dentro de un mismo libro necesitan su prueba y corrección. La recuperación del archivo debe validarse además en el equipo de destino, incluida una interrupción real del proceso y la interacción con Excel abierto.

El servicio debe ser el único editor del libro gestionado: cerrar Office y usar copias para inspección. El respaldo guarda una escritura anterior en el mismo disco. La [nota del adaptador](evidencias/ADAPTADOR_EXCEL.md) describe la recuperación en frío y sus límites. Conservar además respaldos separados para protegerse de pérdida del disco.

El VBA está preservado en referencia/vba-congelado. SQLite se aplaza. La adaptación futura del almacenamiento debe mantener los contratos y repetir las pruebas. El [registro de capacidades](REGISTRO_CAPACIDADES.md) enlaza los resultados y las limitaciones de esta versión.

Para repetir la aceptación desde la raíz, con el entorno donde se instaló el paquete:

```sh
python -m unittest discover -s tests -v
```

El test copia la fixture a directorios temporales. No necesita ejecutar VBA ni tener Excel instalado. La prueba de Excel nativo bajo Windows se realiza por separado y sigue pendiente.
