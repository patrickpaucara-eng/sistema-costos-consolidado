# Capacidades verificadas y pendientes

**Corte:** 19 de noviembre de 2026 (hora de Lima).

**Trabajo:** candidato 0.2.0 en `desarrollo/mvp-ola3`; motor Ola 1 conservado como referencia histórica.

**Alcance:** piloto técnico con fixture didáctica. No representa aprobación comercial ni validación de todos los métodos.

El recorrido actual es HTML local → Python → copia del XLSX → reapertura. SQLite se aplaza. VBA histórico está congelado. El detalle de esta entrega, sus dependencias y las siguientes puertas están en [PLAN_MVP_Y_PENDIENTES.md](PLAN_MVP_Y_PENDIENTES.md).

| ID | Capacidad | Estado | Evidencia y límite |
|---|---|---|---|
| CAP-01 | Importar un libro compatible a un espacio local | Verificada | Copia identificada por SHA-256; origen intacto. Fixture Ola 1. |
| CAP-02 | Registrar compra T14 y consumo T15 con Python | Verificada | Dos compras y un consumo dejan 400 unidades, S/ 3,054 por unidad y S/ 1.221,60. Rechazo multilínea conserva las tablas de negocio. |
| CAP-03 | Reabrir y consultar movimientos y saldos | Verificada | Reinicio del proceso y lectura de XLSX confirman versión y saldo. |
| CAP-04 | Reintentar sin duplicar | Verificada | Misma identidad y contenido recuperan el recibo; otro contenido produce conflicto. Se probaron dos procesos cooperantes. |
| CAP-05 | Operar compra, consumo y consultas desde HTML | Verificada | Recorrido real en Chromium en Linux. Operador local de confianza y formulario JSON técnico. |
| CAP-06 | Cerrar el periodo mediante la cadena configurada del libro | Verificada en alcance técnico | Cinco pasos se muestran desde HTML y se guardan con un reemplazo del XLSX. El fallo inyectado en T23.3 deja igual el estado de negocio y la versión; el rechazo queda anotado. No acredita D9, cuenta correcta ni método universal. |
| CAP-07 | Aislar completamente varias empresas dentro de un libro | Pendiente; hay guardia | Se rechaza importar cuando usuarios con permisos para T14/T15 pertenecen a más de una empresa y ejecutar una operación con `EMP` distinta. No se probó equivalencia de costo entre libros separados y combinados; el MVP queda limitado a una empresa por espacio. |
| CAP-08 | Reconciliar costo integral de orden, cuentas y ventas contra MCD/DBD/ORIA | Pendiente | Requiere oráculos independientes, D9, flete y D14. La fixture no verifica el costo de `OS-01` contra una fuente ORIA. |
| CAP-09 | Conservar una instancia histórica de costo reproducible | Pendiente | Debe fijar entradas, fecha, reglas, revisión del motor y resultado. El recibo de un movimiento o cierre no representa una publicación inmutable del costo. |
| CAP-10 | Analítica con aprendizaje y autonomía | Pendiente | Requiere resultados aprobados, medición de calidad, trazabilidad, controles, posibilidad de reversión y permisos por capacidad. |

## Evidencia de este incremento

- [Pruebas y recorrido MVP Ola 3](evidencias/MVP_OLA3.md): suite completa, fallo inyectado, cierre desde HTML y resultados del caso.
- [Matriz y caso D9](evidencias/D9_MATRIZ_Y_CASO.md) y [línea base CSV O-1](evidencias/D9_CONTROL_O1.csv): 119 valores calculados en memoria; no acreditan un cuadre de cuenta ni habilitan resultados oficiales.
- [Guía de instalación y reproducción](GUIA_PILOTO_EXCEL.md).
- [Pruebas del primer piloto](evidencias/REVISION_INDEPENDIENTE.md) y [ejecución original](evidencias/pruebas-excel.log): nueve pruebas del incremento CAP-01–CAP-05.
- [Recorrido HTML de la primera entrega](evidencias/RECORRIDO_HTML.md).
- [Notas del adaptador y recuperación](evidencias/ADAPTADOR_EXCEL.md).
- [Medición acotada de rendimiento](evidencias/rendimiento-excel.json): un libro de 267.417 bytes, importación 0,391 s y operaciones 0,448–0,554 s. No estima capacidad de producción.

## Límites actuales

Un espacio es una copia de un libro, no una base multiempresa. La guardia identifica una empresa activa por los operadores habilitados para T14/T15, pero el filtro de empresa no se ha demostrado en toda la cadena del motor. El usuario se declara en la solicitud; no existe sesión empresarial autenticada.

El cierre ejecuta los pasos `OFICIAL` o `CIERRE` definidos en `CIERRE_PASO`. El test comprueba que el periodo `2026-04` de B termina cerrado y que el saldo del recurso permanece en 400 unidades a S/ 3,054. No concilia las tablas de cuentas D9 ni publica el costo de una orden. Si una cadena falla, las tablas de negocio y la versión no cambian; se escribe en `RECEIPTS` un rechazo idempotente.

La persistencia usa temporal, respaldo anterior y reemplazo atómico; el respaldo comparte disco. No se probó corte físico. Debe cerrar Office y reservar el XLSX gestionado al servicio. La prueba en Windows/Excel nativo y en el equipo del dueño sigue pendiente. Una versión anterior del espacio debe reimportarse para activar los metadatos de cierre y empresa de esta iteración.

El generador integral, D9, flete/T14.2, D14, devoluciones EVE_ORI, coproductos, costo financiero, múltiples empresas, autenticación, volúmenes reales, varios operadores y analítica autónoma siguen sin aceptación. El motor es copia exacta del espejo Python de Ola 1; esa paridad de origen no demuestra que sus reglas representen íntegramente el método ORIA.
