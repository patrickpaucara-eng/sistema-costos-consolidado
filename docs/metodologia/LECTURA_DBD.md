# Del modelo externo al cierre reproducible

**Fuente primaria.** Tino Reyna Monteverde, *Administración de bases de datos*, archivo suministrado `LIBRO COMPLETO DBD.pdf`, 238 páginas. La numeración impresa coincide con el índice del PDF, comenzando en 1. SHA-256 `d5dfe7e8bf564dd780148fa08fce47269b89433b67fe9d1c22b406465035568e`. Se cotejaron los pasajes que fundamentan este documento. Las opciones técnicas del proyecto son SQLite local, motor único en Python, interfaz HTML e intercambio Excel/CSV.

## Evidencia del libro

| Tema | Qué indica Reyna | Páginas del PDF |
|---|---|---|
| Secuencia | Primero delimita módulos. Después especifica las pantallas y reportes, y estima el coste de acceso. El diseño interno deriva del modelo conceptual y aporta atributos, formatos y claves primarias y alternas para satisfacer las interfaces previstas. El perfil de diseño incluye modalidad interactiva o por lotes, magnitud, tiempo de respuesta, seguridad, auditoría y reversa. | 3–9, 33 |
| Información y acceso | El modelo externo debe «satisfacer al usuario su necesidad de información». El libro busca cobertura del conjunto de los datos mediante las interfaces. Vincula cada interfaz con un módulo y un perfil. Los perfiles limitan qué datos y operaciones puede usar cada persona. | 23–24, 201–202 |
| Pantallas y aceptación | Propone «Presentación de Detalle, Masiva y Resumen». El flujo ilustrado pasa de la lista o búsqueda a la selección y su detalle y admite un resumen. Pide rutas naturales, valores por defecto, oportunidad de confirmar o deshacer cambios, mensajes uniformes y aprobación del usuario. Las búsquedas admiten identificadores que los usuarios conozcan. | 25–29 |
| Consultas críticas | Cruza la frecuencia real de la consulta con los recursos y tiempos requeridos. Una operación por lotes también resulta crítica si excede su ventana. Recomienda medir el uso de índices y verificar su coste. | 30–32, 167 |
| Redundancia | Concilia economía de espacio y tiempo de respuesta. Justifica materializar una tabla suplementaria después de demostrar una consulta crítica. Para estos derivados propone «tablas extras de consultas con fines precisos y prácticos». Una vista también puede reunir tablas y restringir el acceso. | 34, 49, 167–168, 171 |
| Estabilidad | Distingue maestros, movimientos, catálogos, parámetros e historia. En las tablas históricas pide que permanezcan «congeladas». Los movimientos explican los saldos de las cuentas en un momento dado. En otro contexto usa estabilidad para hablar del almacenamiento físico y del espacio libre. | 74–75, 110, 159–160 |
| Recuperación, integridad y control | Describe restaurar un respaldo de D, recuperar los movimientos de D+1 y aplicar en lote la misma funcionalidad del proceso en línea. Indica identificar el último evento aplicado y efectuar cuadres de totales. Trata integridad de dominio y claves, atomicidad y durabilidad de la transacción y bitácora cronológica con los valores anterior y nuevo. | 161–162, 178–185, 195–196, 199–201 |

## Aplicación propuesta al proyecto

### Contrato de la interfaz HTML antes del esquema físico

El primer artefacto sería una matriz con una fila por tarea del usuario. Cada fila indica perfil, empresa, pregunta que necesita responder, datos de entrada y procedencia, resultado visible, filtros, navegación, acción permitida, mensaje de error y criterio observable de aceptación. El vocabulario se enlaza con el MCD para que una orden, una fecha de corte o un importe tengan el mismo sentido en pantalla, importación y reporte.

| Perfil y tarea de ejemplo | Recorrido HTML a validar | Criterio observable |
|---|---|---|
| Operador que importa movimientos | Elegir archivo y empresa, ver conteos y filas rechazadas con motivo, abrir la fila y su documento, confirmar la carga válida según la política acordada. | Las filas, totales y rechazos permiten conciliar archivo y lote. Un reintento identifica el mismo lote. |
| Responsable de costos que practica un cierre | Elegir empresa, periodo y corte, revisar hechos incluidos y exclusiones, observar conciliaciones y vista previa, confirmar y abrir el comprobante del cierre. | Quedan visibles el alcance temporal y la versión oficial. Cancelar antes de confirmar conserva el estado anterior. |
| Gerente o auditor que explica un costo | Consultar resumen de un cierre identificado, filtrar por orden o elemento y seguir el importe hasta los hechos, reglas y documentos. | Se puede explicar el importe publicado y volver al mismo resumen, con idénticos filtros y permisos. |
| Responsable de métodos y parámetros | Consultar vigencia actual e histórica, proponer el cambio, consultar su impacto y registrar aprobación donde corresponda. | Se identifica quién aprobó, cuándo entra en vigor y cuáles cierres se calcularon con cada versión. |

Estos perfiles son ejemplos para verificar con el dueño. Para cada campo de negocio se documenta dónde lo ve un usuario autorizado. Los datos técnicos de recuperación o seguridad necesitan una finalidad y un control de acceso propios. El HTML puede ofrecer búsqueda, detalle y resumen adaptados a cada tarea. El orden concreto de navegación se valida con prototipos navegables y casos reconocibles por el usuario. Python recibe las mismas órdenes desde HTML y desde la importación. Comparte las reglas de cálculo y contabilización en línea y por lotes.

### Qué significa consultar un cierre «por fecha»

Un único campo «fecha» admite respuestas diferentes. Por ejemplo, una recepción del 28 de abril registrada el 4 de mayo pertenece al hecho de abril, pero un cierre autorizado el 2 de mayo pudo haberse emitido sin ella. La consulta debe identificar si se pide **lo que quedó publicado entonces** o **la reconstrucción con la información admitida hasta un corte de conocimiento elegido**. Esta distinción y las decisiones siguientes son propuestas de ingeniería fundamentadas en el tratamiento de movimientos e historia del libro.

1. **Determinar el conjunto de hechos.** Registrar empresa, identidad estable del documento y línea, fecha efectiva, instante de registro y orden de admisión. Fijar calendario, zona horaria y límite inclusivo o exclusivo del corte. Aplicar una política explícita a hechos tardíos, correcciones y anulaciones.
2. **Fijar el contexto de cálculo.** Asociar al cierre un identificador inmutable, periodo, momento de corte, última secuencia admitida, saldo inicial o referencia al cierre previo, movimientos y versiones efectivamente usados. Preservar métodos ejecutables, parámetros, unidades, tipos de cambio, reglas de redondeo y orden determinista con sus versiones pertinentes. El inventario de entradas debe permitir recuperar su contenido. La huella permite verificarlo.
3. **Publicar de manera atómica.** En una transacción local guardar versión oficial, totales, conciliaciones y trazas de origen, autor y fecha de confirmación. Distinguir desde la interfaz borrador, publicado y rectificado. Una corrección posterior genera un evento o revisión enlazada conforme a la política acordada y mantiene consultable la versión emitida originalmente.
4. **Reproducir y restaurar.** Una reproducción lee el contexto histórico mediante el mismo motor Python. Un restablecimiento parte del respaldo consistente más reciente que anteceda al corte y reaplica ordenadamente los movimientos pendientes. Determinar los ya aplicados evita duplicación. Conciliar cantidades e importes por empresa, etapa y orden antes de declarar la recuperación completa.
5. **Probar con un hecho tardío.** Publicar una orden de abril, conservar su comprobante, registrar en mayo un hecho efectivo en abril y cambiar después un parámetro. Reabrir la aplicación y reproducir el cierre original. Verificar las mismas partidas, centavos y huella del contenido canónico, además del resultado previsto para la revisión según la política aprobada. Restaurar una copia por separado, repetir el mismo lote y comprobar que los totales se mantienen.

Una tabla suplementaria para consultas se justificaría si la medición con volumen representativo demuestra que una vista o índice resulta insuficiente. En ese caso se documentarían fuente, mecanismo de regeneración, vigencia, responsable de escritura y cuadre. Un cierre oficial conserva la versión de lo emitido por una razón funcional y de auditoría distinta de la optimización de consultas.

### Decisiones que preceden al DDL definitivo

- Acordar módulos, perfiles, tareas, carga representativa y ventana máxima aceptable del cierre. Aprobar los prototipos y su matriz de cobertura.
- Resolver granularidad e identidad de eventos, documentos, órdenes y recursos, alcance por empresa y reglas para parámetros compartidos. Definir qué representa cada cantidad e importe con su unidad, moneda y precisión.
- Acordar la semántica de cierre, vigencia y registro, precedencia de reglas, tratamiento de atrasos, reversas, reapertura, autorización y relación entre versiones oficiales.
- Definir origen y propietario de cada dato, qué saldos son reconstruibles y cuáles publicaciones requieren conservación histórica. Seleccionar conciliaciones y casos de aceptación.
- Con esas decisiones, derivar claves y referencias, restricciones, índices, transacciones y plan de respaldo y restauración de SQLite. La ficha del diseño físico debe explicar cualquier tabla suplementaria o control delegado al motor.

Esta secuencia permite prototipar pantallas y probar importaciones y cálculos en un entorno local mientras se precisa el modelo. La equivalencia entre SQLite y el DBD de origen requiere comprobar las dieciocho columnas ausentes del derivado histórico y las claves por empresa. La referencia de la auditoría es `main@a96ba794a6171a325836a5a56bf1c9392dbd8482`, `kit/salida_b/informe_diseno.txt`, líneas 1–20.
