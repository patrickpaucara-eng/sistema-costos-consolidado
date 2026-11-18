# Contratos de Base, Síntesis y Analítica

Borrador de diseño del 18 de noviembre de 2026. Recoge la dirección del dueño y explicita criterios para validarla con MCD/DBD. Stack aprobado — SQLite local, Python como motor único, Excel/CSV e interfaz HTML.

## Nivel 1 · Base estable

La estructura conceptual debe soportar nuevas variantes de costo mediante registros y relaciones definidos. Los datos crecen con las operaciones. Los catálogos y las reglas evolucionan por vigencia. Una modificación estructural durante desarrollo requiere explicar el concepto que faltaba, justificar su alcance, migrar una copia y verificar el historial. Antes de fijar el esquema se probará una capacidad de costo adicional.

La identidad de cada hecho incluye su empresa, documento/evento, detalle y referencia de origen. Un recurso puede compartir código entre empresas manteniendo identidades distintas. Los saldos deben explicarse mediante movimientos. Las correcciones preservan el evento original y registran su efecto.

Cada dato temporal distingue, cuando sea necesario para reproducir historia, cuándo ocurrió y cuándo fue conocido por el sistema. Por ejemplo, una factura de enero ingresada en febrero no pertenecía al conocimiento del cierre original de enero. Consultar enero según lo conocido entonces y consultar enero con ajustes posteriores son solicitudes distintas.

La regla estable puede describirse de forma conceptual, mientras sus formatos físicos se validan en el modelo interno del DBD. Una estructura universal con cualquier clave/valor sin semántica, unidades o restricciones debe rechazarse en la revisión del modelo por no permitir comprobar integridad.

### Aceptación

Agregar una configuración de costo de proyectos mediante las entidades y contratos aprobados debe conservar el esquema de la Base y los resultados del caso de órdenes. La prueba debe definir primero proyecto, hitos, recursos, medidas y forma de atribución. Si hace falta una magnitud o una regla fuera del vocabulario admitido, registrar esa carencia antes de prometer que puede configurarse.

## Nivel 2 · Instancia reproducible de costo

El procedimiento común recibe una solicitud, resuelve datos y reglas aplicables, ejecuta sus pasos, verifica cuadres y entrega un resultado trazable. Cada método conserva un contrato con unidades, entradas, salidas y criterio de aceptación.

La solicitud identifica empresa, objeto de costo, periodo o fecha, finalidad, escenario y fecha de conocimiento. La instancia conserva una copia o referencia inmutable de los hechos usados, las reglas y parámetros vigentes, versiones de métodos/motor, redondeo, dependencias y resultados. Esta elección de implementación se ensayará contra los requisitos de volumen.

Consultar la instancia original entrega lo publicado en aquel momento. Una nueva corrida con información posterior recibe identidad propia y una explicación de diferencia. Para un algoritmo estocástico se conservan semilla, modelo y entorno que determinen el resultado; los importes oficiales se producen mediante reglas deterministas.

Un nombre de costo es configuración de finalidad, objetos, hechos, medidas, criterios de atribución y método. El motor usa catálogos y protocolos para seleccionar procedimientos. Una regla genuinamente nueva que quede fuera de sus operaciones admitidas necesita una extensión versionada del módulo correspondiente. Se valida sin modificar los contratos ya aceptados.

### Aceptación

- Abrir una instancia por identificador tras cambiar parámetros actuales y obtener exactamente sus importes publicados.
- Recalcular con los insumos y versiones de aquella instancia y cotejar resultados internos y publicados según la política numérica.
- Comparar el cierre original con el revisado tras una factura tardía, identificando la causa y cada diferencia.
- Añadir un tipo de costo admitido mediante configuración y comprobar que los casos anteriores mantienen sus resultados.
- Verificar desde el formulario hasta el archivo reabierto el aislamiento de dos empresas con códigos iguales.

## Nivel 3 · Autonomía que aprende

El punto de partida incluye reglas metodológicas, contratos de datos, acciones posibles y límites del negocio. La experiencia de la empresa se acumula al observar operaciones y resultados. El aprendizaje puede estimar parámetros, elegir propuestas o ajustar una política dentro de los límites autorizados.

Un caso nuevo conserva contexto, decisión propuesta, incertidumbre, razones para consultar, respuesta humana, acción ejecutada, resultado observado y versión de política. La aprobación humana por sí sola no demuestra que una decisión mejore el negocio. Se mide su efecto frente a un objetivo y una referencia definidos.

Las correcciones humanas pueden alimentar aprendizaje supervisado y recuperación de casos parecidos. El aprendizaje por refuerzo será pertinente si se puede definir estado, acciones, recompensa y horizonte de efecto y probarlo en historia o simulación. Su algoritmo específico se seleccionará por evidencia. Un indicador de recompensa debe comprobar costos, calidad, plazos y restricciones para evitar optimizar una sola cifra a costa del negocio.

### Madurez por capacidad

| Estado | Comportamiento | Evidencia requerida |
|---|---|---|
| Sin experiencia local | Usa reglas y contratos iniciales, registra incertidumbres. | Validación de entradas y límites. |
| Aprende con asistencia | Pide criterio en casos que no puede resolver de forma confiable y conserva el resultado posterior. | Casos con respuesta y efecto medido. |
| Evalúa en sombra | Propone sin aplicar y compara decisiones con los resultados. | Evaluación temporal sobre datos futuros al entrenamiento, errores e impacto. |
| Autónoma en un ámbito | Aplica decisiones dentro de una política autorizada y versionada. | Calidad y límites aceptados por capacidad, reversión y trazabilidad. |
| En revisión | Reduce autonomía o consulta cuando cambia el contexto o cae el desempeño. | Detección de deriva, causas y recuperación verificadas. |

La meta es operar sin consultas rutinarias en los ámbitos maduros. El desempeño en un ámbito conocido no garantiza resolver todo caso nuevo. La política define qué decisiones puede ejecutar y cuándo una excepción requiere intervención. Una promoción automática podrá aplicarse si el dueño autorizó esa política y se cumplen sus pruebas. Los niveles del histórico AUT-01 tienen su propia numeración, que se mapeará por significado.

## Modularidad y configuración

Los módulos se separan por responsabilidad — registro y persistencia, síntesis, analítica, intercambio y presentación. Cada uno declara qué acepta, qué entrega, qué puede escribir y cómo comunica un fallo. Los contratos y su prueba preceden a su implementación.

Empresa, periodo, recurso, tipo de costo, tasa, umbral, vigencia, método y política se resuelven por datos dentro del modelo aprobado. Los ejemplos y fixtures se mantienen como casos. El código contiene las operaciones del motor y sus validaciones con nombres explícitos y legibles. La configuración admite vocabulario y operadores validados.

## Entrega por capacidades activas

Cada capacidad declara una operación que el usuario puede ejecutar, sus dependencias, escenario de demostración, revisión de código y evidencia. Una capacidad de registro o cálculo queda activa cuando puede recorrerse desde la interfaz HTML hasta la persistencia y la consulta del resultado al reabrir. Las capacidades transversales, como exportar, respaldar, restaurar y consultar, demuestran su efecto con un archivo verificado, restauración reconciliada o lectura reproducible según corresponda. Una función aislada o un resultado en memoria tiene el alcance de prueba que le corresponde.

El registro incluye estados diseñada, construida, en prueba, activa y suspendida, con revisión independiente en cálculos y persistencia. El HTML muestra la revisión de producto y los recorridos disponibles. El histórico a96ba79 conserva su mapa y evidencia propios hasta que la implementación consolidada tenga sus capacidades.

## Ejemplo que enlaza los tres niveles

Dos empresas compran un material con el mismo código y precios diferentes. Base conserva cada movimiento con identidad y fecha de conocimiento. Síntesis produce una instancia por orden/empresa y versión. Analítica explica una desviación y consulta una excepción si corresponde. Una respuesta crea experiencia con resultado medido; cualquier regla nueva tiene vigencia y sus nuevas corridas conservan procedencia.

La prueba se repetirá con costos reales y proyectados antes de fijar el esquema. Esta prueba permite descubrir qué es estable y qué necesita un catálogo o procedimiento.
