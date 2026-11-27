# Capacidades verificadas y pendientes

**Corte:** 20 de noviembre de 2026 (hora de Lima).

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
| CAP-07 | Aislar completamente varias empresas dentro de un libro | Pendiente; hay guardia | Se rechaza importar cuando usuarios con permisos para las transacciones habilitadas del piloto pertenecen a más de una empresa y ejecutar una operación con `EMP` distinta. No se probó equivalencia de costo entre libros separados y combinados; el MVP queda limitado a una empresa por espacio. |
| CAP-08 | Reconciliar costo integral de orden, cuentas y ventas contra MCD/DBD/ORIA | Pendiente | Requiere oráculos independientes, D9, flete y D14. La fixture no verifica el costo de `OS-01` contra una fuente ORIA. |
| CAP-09 | Conservar una instancia histórica de costo reproducible | Pendiente | Debe fijar entradas, fecha, reglas, revisión del motor y resultado. El recibo de un movimiento o cierre no representa una publicación inmutable del costo. |
| CAP-10 | Analítica con aprendizaje y autonomía | Pendiente | Requiere resultados aprobados, medición de calidad, trazabilidad, controles, posibilidad de reversión y permisos por capacidad. |
| CAP-11 | Registrar costos de centro T17, pérdidas T19 y ventas T20 | Verificada en el servicio/API y formulario JSON | T17 y T19 usan escenarios de la fixture; T20 prueba dos líneas con saldo inicial sintético explícito. Cada evento persiste su cuenta y pasa por `PERFIL_TRX`; esto no concilia `RESULTADO_METODO` ni valida producción real de producto terminado. |
| CAP-12 | Producir una orden con T18 y liquidar T23.3/T23.5 por la ruta base | Verificada en un caso de control aislado | `OS-01` (10 t) produce 2.500 cajas según la tarifa de producto de la fixture; el caso compara transferencia, costo unitario, rebaja VNR y existencia con aritmética independiente, mantiene aislada la fila A, repite sin duplicar y revierte el cierre si falla T23.5. En esta ruta base, `RESULTADO_METODO` permanece vacío. La ruta externa sintética se documenta por separado en CAP-15. |
| CAP-13 | Auditar recibos y versión del XLSX | Verificada en el servicio/API | `GET /api/workspaces/{id}/audit` comprueba SHA-256 del comando, ID único, coherencia de la respuesta y versión acumulada. Las pruebas cubren importación, éxitos, rechazos, cierre multipaso, respaldo anterior y ediciones de control en copias. Su alcance es la coherencia interna de una captura. |
| CAP-14 | Conservar la traza de un evento confirmado y del rechazo tras reinicio | Verificada para T14/T15 en el recorrido D2 | La prueba reabre el XLSX y comprueba `LOG_TRX`, `BITACORA`, enlaces `BIT_LOG`, conteos, reintento idempotente y rechazo sin cambio de versión. No cierra D2 completa: R02/DIARIO, D3 y D4 siguen pendientes. |
| CAP-15 | Recibir y seleccionar una corrida VNR externa mediante T25.4/T23.5 | Verificada con método sintético en XLSX temporal | 26 pruebas distinguen huellas textuales (`001`/`1`), método y versión vigentes, aíslan existencias por empresa, aplican permisos y vigencia, persisten `RESULTADO_METODO`, concilian el periodo completo (existencia, CPU, `AJUSTE_VNR` y `CTA_GASTO`) y revierten cuando falta un escritor o la rebaja excede el saldo. La revisión independiente confirmó que T25.4 recibe un método aprobado y efectivo y T23.5 consume la versión vigente al inicio del periodo. No valida proveedor comercial, método ORIA ni toda la conciliación D9. |

| CAP-16 | Calcular y descargar reportes del caso Frenosa | Verificada en entorno Linux y navegador local | Conecta el productor existente a REAL, CONTABLE y ESTIMADO; guarda el contrato y permite descargar exportaciones. Faltan empaquetado Windows y aceptación con datos de operación. Ver [OT-C04](evidencias/OT-C04/ENTREGA.md). |
| CAP-17 | Exportar un modelo de mezcla para Solver desde resultados REAL | Verificada por pruebas Python | El libro incluye objetivo, restricciones, rangos de demanda SUPUESTO y nombres definidos `solver_*`; el caso manual A/B arroja 20/60 unidades y S/ 1,800 con `linprog`. No se probó el complemento Solver en Excel nativo. Frenosa 2010-07 no declara medidas CAP; el libro informa que queda sin restricción de capacidad. Ver [OT-C32 punto 3](evidencias/C32_3_SOLVER.md). |
| CAP-18 | Asignar una capacidad escasa desde Decidir | Verificada con caso manual, API y Chromium | Selecciona una capacidad REAL, ordena por margen de contribución por unidad de recurso y asigna hasta los máximos editables. Caso exacto: B=70, A=15 y MC S/ 1,850. Es una sola restricción y no incorpora costos de oportunidad de otros recursos. Ver [OT-C32 punto 4](evidencias/C32_4_RECURSO_ESCASO.md). |
| CAP-19 | Comparar procesamiento adicional con venta en el punto de separación | Verificada con caso manual, API y Chromium | La calculadora del panel muestra ingreso incremental, costo incremental y beneficio neto por unidad; procesa solo cuando el neto es positivo. Caso exacto: S/ 14 − S/ 10 − S/ 3 = S/ 1; PROCESAR. Ver [OT-C32 punto 5](evidencias/C32_5_PROCESAR_VENDER.md). |
| CAP-20 | Precargar el siguiente código de OBJETO en formularios guiados | Verificada para T13 con DBD y Chromium | Descubre la creación por la secuencia DBD, muestra el correlativo como solo lectura y registra dos órdenes consecutivas `OT-FRE-SW50-0001` y `OT-FRE-SW50-0002`. La vista previa no reserva el código: en uso concurrente, la PK única del DBD debe rechazar la colisión para que se reintente. Ver [C32-1b](evidencias/C32_1b_FORMULARIO_OT.md). |
| CAP-21 | Mostrar límites del modelo en las vistas que los usan | Verificada en Chromium | Futuro y cotizador declaran la proyección lineal dentro del rango observado; Familias avisa que un cambio de proceso exige reiniciar la historia; Decidir explica la restricción única y la alternativa Solver; Registrar advierte uso de un usuario a la vez. Ver [C33-3](evidencias/C33_3_AVISOS_LIMITES.md). |
| CAP-22 | Definir parámetros obligatorios por familia y aprender recetas lineales con OT reales | Verificada como modelo de datos y cálculo aislado | Hoja opcional `FAMILIA_PARAM`; QR en Python estándar; Tolva 1.300 kg → 75 h. No está enlazada aún al formulario ni al libro operativo. Ver [C34-1](evidencias/C34_1_RECETAS_PARAMETRIZADAS.md). |
| CAP-23 | Separar preparación fija por lote, costo variable y conceptos fuera del ABC | Verificada por cálculo aislado | 50.000 cajas: un lote S/ 18.900; dos lotes S/ 20.100; diferencia S/ 1.200. Conceptos fijos y contingencia con base explícita; la pantalla comparativa queda en C34-5. Ver [C34-2](evidencias/C34_2_CONCEPTOS_Y_LOTES.md). |

## Evidencia de este incremento

- [Pruebas y recorrido MVP Ola 3](evidencias/MVP_OLA3.md): suite completa, pruebas nuevas de aislamiento/rollback D9, fallo inyectado, cierre desde HTML y límites del caso.
- [Decisión D9](evidencias/D9_DECISION_SEMANTICA.md), [contrato de datos](evidencias/D9_CONTRATO_DE_DATOS.md), [cuadre T15](evidencias/D9_CUADRE_T15.md), [casos T17/T19/T20](evidencias/D9_CUADRE_EVENTOS.md), [matriz O-1](evidencias/D9_MATRIZ_Y_CASO.md) y [línea base CSV](evidencias/D9_CONTROL_O1.csv): filas persistidas comparadas con aritmética independiente por evento. Los 119 valores O-1 y la conciliación integral siguen pendientes; no hay aceptación contable oficial.
- [Caso base T18/T23.3/T23.5](evidencias/D9_CUADRE_T23_3_T23_5.md): liquida una orden pequeña y prueba VNR con tramas sintéticas y configuración cotejada con SHA. No equivale a cerrar D9.
- El [paquete Windows](../../tools/windows/INICIO.txt) y el [workflow offline](../../.github/workflows/windows-offline.yml) están preparados. El artefacto EXE, la acción de Windows, el uso en un equipo desconectado y la aceptación con Excel nativo todavía no están verificados.
- [Guía de instalación y reproducción](GUIA_PILOTO_EXCEL.md).
- [Pruebas del primer piloto](evidencias/REVISION_INDEPENDIENTE.md) y [ejecución original](evidencias/pruebas-excel.log): nueve pruebas del incremento CAP-01–CAP-05.
- [Recorrido HTML de la primera entrega](evidencias/RECORRIDO_HTML.md).
- [Notas del adaptador y recuperación](evidencias/ADAPTADOR_EXCEL.md).
- La auditoría de recibos verifica el libro actual por API y el respaldo guardado mediante el lector local. [Pruebas y alcance de CAP-13](evidencias/AUDITORIA_RECIBOS.md).
- [Evidencia D2 de Ola 2](evidencias/OLA2_D2_TRAZA.md): una compra T14 confirmada conserva log y bitácora al reiniciar; el reintento no duplica, y un consumo rechazado conserva su recibo sin alterar la traza ni la versión.
- [Caracterización D3 de Ola 2](evidencias/OLA2_D3_CARACTERIZACION.md): T14/T14/T15 cuadran con `EXISTENCIA`, mientras el piloto deja `KARDEX` y `KARDEX_SALDO` vacías. El documento registra el hueco; D3 sigue pendiente.
- [Ruta externa VNR de D9](evidencias/D9_PUERTO_VNR.md): 26 pruebas focalizadas de T25.4/T23.5 en proveedor sintético, incluidas identidad método/versión, huellas exactas, permisos, aislamiento, dos productos, conciliación y rollback.
- [Medición acotada de rendimiento](evidencias/rendimiento-excel.json): un libro de 267.417 bytes, importación 0,391 s y operaciones 0,448–0,554 s. No estima capacidad de producción.

## Límites actuales

Un espacio es una copia de un libro, no una base multiempresa. La guardia identifica empresas activas por los operadores habilitados para las transacciones del piloto; el filtro de empresa no se ha demostrado en toda la cadena del motor. El usuario se declara en la solicitud; no existe sesión empresarial autenticada.

El cierre ejecuta los pasos `OFICIAL` o `CIERRE` definidos en `CIERRE_PASO`. El test comprueba que el periodo `2026-04` de B termina cerrado y que el saldo de materia prima permanece en 400 unidades a S/ 3,054. El caso sintético base T18/T23.3/T23.5 compara la salida de orden y rebaja VNR con cálculo independiente. CAP-15 agrega conciliación parcial del resultado externo con existencia, ajuste VNR y gasto, pero no publica el costo integral aceptado de una orden. Si una cadena falla, las tablas de negocio y la versión no cambian; se escribe en `RECEIPTS` un rechazo idempotente.

La persistencia usa temporal, respaldo anterior y reemplazo atómico; el respaldo comparte disco. No se probó corte físico. Debe cerrar Office y reservar el XLSX gestionado al servicio. La prueba en Windows/Excel nativo y en el equipo del dueño sigue pendiente. Una versión anterior del espacio debe reimportarse para activar los metadatos de cierre y empresa de esta iteración.

CAP-13 verifica cada captura contra su propia versión. La transacción exitosa suma uno, el cierre exitoso suma el número de pasos registrados y un rechazo persistido suma cero. La huella cubre únicamente el comando. Una edición coordinada de los campos de control puede conservar su coherencia. La autenticidad del historial y la conciliación con tablas de negocio requieren evidencia independiente.

El generador integral y la conciliación D9 completa siguen pendientes. T25.4/T23.5 está verificada solo con métodos sintéticos; no hay proveedor comercial ni aceptación del método ORIA. También siguen pendientes flete/T14.2, D14, devoluciones EVE_ORI, coproductos, costo financiero, operación conjunta de varias empresas, autenticación, volúmenes reales, varios operadores y analítica autónoma. El aislamiento se reforzó solo para existencia y resultados de método, además de las mutaciones `CTA_*`; no equivale a probar toda la cadena. El motor es copia del espejo Python de Ola 1 con cambios de guarda D9; la paridad de origen no demuestra que sus reglas representen íntegramente el método ORIA.

### OT-C02 · Exportación desde contrato

El endpoint `POST /api/exportar?tipo=...` genera libros de resultados, analítica y proyección, un HTML independiente y un Word de fuentes. Consume únicamente un contrato ya calculado; el enlace desde la interfaz y la validación metodológica de los datos siguen pendientes. Ver [entrega y pruebas](evidencias/OT-C02/ENTREGA.md).
## OT-C01 · Visualización del contrato de resultados

La navegación y el dashboard leen el contrato validado por `/api/resultados`; el ejemplo de reemplazo está rotulado. Frenosa julio 2010 REAL se distribuye como una captura académica: compras y cantidades vendidas simuladas, sujeta a validación. Las listas vacías se muestran como información no disponible. Ver [entrega y capturas](evidencias/OT-C01/ENTREGA.md); la salida aún no acredita un costo empresarial oficial.

### OT-C22 · Aprendizaje con guardas (revisión parcial)

Las pruebas de `tests/test_aprendizaje.py` cubren la mediana y los cinco casos manuales, rechazo persistente, vigencia sin cambios retroactivos y estabilidad de costos REAL/CONTABLE. El cotizador consulta el estándar vigente cuando se indica producto y conserva la cantidad explícita. La conexión de proyección queda pendiente hasta integrar C21; la evidencia y límites están en `evidencias/C22_APRENDIZAJE.md`. Esta capacidad no acredita autonomía comercial ni valida estándares con las fuentes de Tino.

### OT-C24b · Excel de proyección y manual breve

El botón de exportación y el comando de entregables consultan la proyección granular C21 del libro cuya empresa y huella coinciden con el resultado; las hojas identifican la base y la proyección integral REAL aunque se exporte otra síntesis. `tests/test_c24b_proyeccion.py` comprueba la identidad del primer mes con factores 1, la sensibilidad, seis meses mediante API, que el libro no cambia y el rechazo de libro distinto. El manual cubre las cinco secciones con siete capturas. La aceptación metodológica y el recorrido E2E completo siguen pendientes de revisión independiente y del responsable correspondiente.

### OT-C25 · Cotización con tasas provisionales

Si no existen periodos cerrados, la API usa el último periodo del libro con resultado REAL disponible y añade «tasas provisionales: mes no cerrado». Si hay un periodo cerrado, mantiene su prioridad. Las pruebas cubren Frenosa y SERVITEC, ausencia de resultados y rechazo de una actividad de apoyo sin inductor P4C. El recorrido integrado permanece en 29/30 por E2; no acredita todavía el objetivo de todos los pasos OK. Ver `evidencias/ERRORES_E2E.md`.

### OT-C26 · Vistas de analítica (parcial)

La interfaz consulta cotización, aprendizaje y sensibilidad; presenta bloques de trazas, costeo variable, calidad, rechazos y propuestas por responsable. `tests/test_c26_interaccion.py` recorre las pantallas en Chromium y la evidencia está en `evidencias/C26/`. La aceptación sigue parcial por E2, E21 y los límites de E4 y E15; consultar `evidencias/ERRORES_E2E.md`. No acredita las funciones expresamente diferidas ni validación metodológica.

### OT-C27 · adelantos parciales

E2 mueve los controles de rango a Periodos y se verifica en Chromium. Los casos aislados de intervalos y el inventario DBD son prototipos sin conexión a pantallas; la separación física de una copia de espacio no constituye un laboratorio. Los bloques D, A, B, C, E y F no se declaran completos; ver `evidencias/ERRORES_E2E.md`.

### OT-C31 punto 2 · detalle de mano de obra por recurso

La ficha de orden muestra los tramos raíz P2 de recursos `PERS_DIR` que el contrato ya identifica. Una copia temporal de SERVITEC con tres técnicos sintéticos conserva el costo MOD y muestra sus rutas en Chromium; el original no cambia. El detalle no identifica personas si el libro solo contiene un recurso agregado. Ver [evidencia](evidencias/C31/PUNTO_2_PERSONAS.md).
### OT-C31 punto 4 · Análisis de familias (alcance acotado)
La pantalla acepta historia JSON por actividad o recurso, presenta la receta y su intervalo, comprueba pertenencia y compara dos familias con ANOVA. La receta puede enviarse a una cotización proyectada por unidades. `tests/test_c31_4_familias.py` prueba los casos manuales, entrada incompleta, la vista en Chromium y la API real de cotización. La historia y selección son temporales de la sesión; no se guardan ni representan aprobación de una familia o fusión. La aceptación de una cotización y la persistencia de historia quedan fuera de esta entrega; el uso metodológico requiere revisión.
### OT-C31 punto 5 · Laboratorio
La interfaz crea una copia de un espacio, permite registrar transacciones en ella y comparar resultados por orden y elemento. La prueba de API y navegador registra un consumo T15 y verifica que el SHA-256 del libro original no cambia. La comparación se rechaza si el original cambió desde la copia. Alcance: REAL y CONTABLE; edición mediante transacciones habilitadas, no edición libre de celdas. Evidencia: `evidencias/C31/PUNTO5_LABORATORIO.md`.
### OT-C31 punto 6 · diagnóstico preliminar de suficiencia
La barra común muestra la presencia de datos del libro seleccionado y el siguiente requisito faltante. La descarga ofrece el formato DBD completo con una guía del nivel elegido. `tests/test_c31_6_suficiencia.py` prueba ausencia, datos sintéticos, libros existentes, las cinco descargas y navegador. Es una guía conservadora de presencia, no valida la calidad, no demuestra que el motor calcule con ese nivel ni crea reglas de reparto. Los libros con plantillas vacías no se consideran evidencia de datos.
