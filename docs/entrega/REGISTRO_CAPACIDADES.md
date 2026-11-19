# Capacidades y evidencia de la entrega

Rama desarrollo/capacidad-inicial. Estado del 18 de noviembre de 2026.

| ID | Operación | Dependencias | Estado | Alcance de aceptación |
|---|---|---|---|---|
| CAP-01 | Importar un libro de referencia en un espacio local | openpyxl, modelo heredado, SQLite | En construcción | Conteos/estado de tablas y copia identificada por hash. |
| CAP-02 | Ejecutar compra o consumo mediante Python | CAP-01 | En construcción | Motor heredado por datos, resultado de negocio y persistencia. |
| CAP-03 | Reabrir y consultar movimientos/saldos | CAP-02 | En construcción | Mismo estado después de cerrar proceso y reconectar. |
| CAP-04 | Reintentar una operación sin duplicarla | CAP-02 | En construcción | Misma identidad y contenido devuelven el resultado anterior. Identidad con otro contenido produce conflicto. |
| CAP-05 | Operar desde HTML local | CAP-01–CAP-04 | En construcción | Seleccionar espacio, ejecutar, ver error o éxito, consultar tabla permitida. |
| CAP-06 | Cerrar y publicar costo por orden | CAP-01–CAP-05, contratos de Síntesis | Pendiente | Cuadre, aislamiento y evidencia completa al reabrir. |
| CAP-07 | Conservar instancia histórica de costos | CAP-06 | Pendiente | Cambios posteriores no alteran lo publicado y la reproducción conserva sus insumos. |
| CAP-08 | Analítica con aprendizaje y autonomía | CAP-06–CAP-07 | Pendiente | Efecto medido y política autorizada por capacidad. |

## Ámbitos del primer ensayo

Los espacios separan las copias de libros. La prueba entre espacios no acredita el aislamiento de dos empresas dentro de un mismo libro. El motor heredado y sus transacciones conservan las limitaciones descubiertas en OT-001 hasta su corrección y verificación específica.

La persistencia de tablas de estado en SQLite es un adaptador transitorio. El modelo físico definitivo y el aislamiento por empresa se validan con MCD/DBD y los casos de negocio.

El primer ensayo local presupone un operador confiable en su equipo. La presencia de un nombre de usuario de referencia no equivale a una sesión autenticada de distribución empresarial. La aceptación de permisos y autenticación se incluye al preparar el paquete y su alcance.
