# Capacidades y evidencia de la entrega

Rama `desarrollo/capacidad-inicial`, piloto 0.1.0. Verificación del 18 de noviembre de 2026, hora de Lima.

El recorrido vigente es HTML local → Python → copia Excel → reapertura. SQLite está aplazado y no tiene implementación en esta entrega. El VBA histórico permanece congelado en `referencia/vba-congelado`.

| ID | Operación | Estado | Evidencia y límite |
|---|---|---|---|
| CAP-01 | Importar un libro compatible a un espacio local | Verificada en el piloto | Copia identificada por SHA-256; origen intacto. Fixture Ola 1. |
| CAP-02 | Registrar compra T14 y consumo T15 con Python | Verificada en el piloto | Dos compras y un consumo dejan 400 unidades, S/ 3,054 por unidad y S/ 1.221,60. Rechazo multilínea conserva el estado de negocio. |
| CAP-03 | Reabrir y consultar movimientos y saldos | Verificada en el piloto | Reinicio del proceso y lectura directa del XLSX confirman versión y saldo. |
| CAP-04 | Reintentar sin duplicar | Verificada en el piloto | Misma identidad y contenido recuperan el recibo; otro contenido devuelve conflicto. También se probaron dos procesos cooperantes. |
| CAP-05 | Operar desde HTML local | Verificada en Chromium | Importar, ejecutar, consultar, repetir y ver errores. Formulario técnico con JSON; operador local de confianza. |
| CAP-06 | Cerrar y publicar costo por orden | Pendiente | Requiere validar método, cuadre, aislamiento y cierre recuperable completo. |
| CAP-07 | Conservar instancia histórica de costos | Pendiente | Debe fijar insumos, reglas y resultados y demostrar reproducción por fecha. El recibo de un movimiento no acredita esta capacidad. |
| CAP-08 | Analítica con aprendizaje y autonomía | Pendiente | Requiere medición del efecto, límites y políticas autorizadas por capacidad. |

## Evidencia reproducible

- [Guía de instalación y caso manual](GUIA_PILOTO_EXCEL.md).
- [Pruebas independientes](evidencias/REVISION_INDEPENDIENTE.md): 9 aprobadas, ninguna omitida. [Ejecución del coordinador](evidencias/pruebas-excel.log): 9 aprobadas en 15,520 segundos.
- [Recorrido del navegador](evidencias/RECORRIDO_HTML.md).
- [Notas del adaptador y recuperación](evidencias/ADAPTADOR_EXCEL.md).
- [Medición de rendimiento](evidencias/rendimiento-excel.json): libro de 267.417 bytes, importación 0,391 s y operaciones de 0,448–0,554 s. Una corrida del adaptador en Linux; no establece capacidad empresarial ni incluye HTTP.

## Límites de aceptación

Los espacios separan copias de libros. Falta resolver el aislamiento de dos empresas dentro del mismo libro, ya observado como riesgo en OT-001. El motor se recuperó exactamente de Ola 1; la coincidencia de bytes no acredita su equivalencia metodológica completa con ORIA.

El usuario operativo es declarado al motor para aplicar sus permisos. No existe todavía una sesión autenticada empresarial. Los archivos contienen las tablas históricas privadas y deben custodiarse localmente.

La escritura utiliza temporal, recibo, respaldo anterior y reemplazo atómico. Se probó una falla inyectada antes del reemplazo y recuperación en frío. El respaldo conserva una escritura y comparte disco. No se probó un corte físico ni Excel nativo en Windows. Reservar el libro gestionado al servicio: cerrar Office y consultar copias separadas. La edición externa entre operaciones puede alterar reglas y recibos sin incrementar la versión del piloto.

No están aceptados aún el generador integral, cierre mensual, todas las transacciones heredadas, publicación histórica, BI autónomo ni distribución comercial.
