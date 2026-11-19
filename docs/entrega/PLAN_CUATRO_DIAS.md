# Ejecución de la entrega en cuatro días

18 de noviembre de 2026. Complementa el plan maestro y cambia su prioridad de ejecución. El plazo es un objetivo con aceptación por capacidades. Cada día termina en una versión ejecutable y evidencia guardada. El alcance se revisa con los resultados del primer recorrido.

## Decisiones y supuestos

El stack aprobado sigue siendo SQLite local + Python como motor único + interfaz HTML + Excel/CSV para intercambio. Se reutilizan métodos y reglas del trabajo de Claude y se modifica la integración que necesitan para operar y conservar estado. La referencia técnica candidata es Ola 1, cac2501d9f712655dda466d216dc5bff2dd446a5. El repositorio histórico se consulta en lectura.

Para comenzar se asume Windows, un operador local a la vez y el recorrido obligatorio carga → costo por orden → cierre → consulta. Estos supuestos se consultaron al dueño. Su respuesta ajustará el alcance. La autonomía avanzada se abordará después de demostrar sus datos, señales de resultado y permisos.

La prueba inicial se limita a importar un libro de referencia, ejecutar compra/consumo mediante el motor Python heredado y persistir el estado en SQLite. Las tablas del libro se conservan en un adaptador transitorio por espacio de trabajo. Su finalidad es comprobar operación, reapertura, reintento y límites de migración. El modelo relacional definitivo sigue el contrato y la validación metodológica.

## Recorrido y puertas

| Lote | Trabajo y dependencia | Salida observable | Condición para seguir |
|---|---|---|---|
| Día 1 · G1 | Importación de un libro, lectura de reglas, operación por Python y guardado SQLite. Después, formulario HTML y lectura del resultado. | Ejecutar compra y consumo, cerrar el proceso, volver a abrir y recuperar los mismos movimientos y saldos. | Motor heredado identificado por SHA; operación no duplica al reintentar con la misma identidad; fallo no deja cambios parciales. |
| Día 1 · G2 | Diagnóstico del caso numérico de dos empresas y trazabilidad de la fila de origen. Depende de G1. | Separar ámbitos de datos y localizar los filtros o claves que faltan. | Definir exactamente qué aislamiento se demuestra y qué recorrido todavía falla. |
| Día 2 · G3 | Integrar valuación, reparto y liquidación del histórico con el estado persistido de G1. Depende de G1–G2 y de los contratos de datos. | Una orden real de referencia, costo por elemento, cantidad terminada y saldo en proceso. | Cuadre con oráculo manual y referencia histórica; datos de otra empresa no alteran el resultado. |
| Día 2 · G4 | Publicación identificada de una instancia y consulta de su explicación. Depende de G3. | Volver a un costo pasado con sus entradas, regla y versión. | Una tarifa nueva o un hecho tardío no reescribe la instancia publicada. |
| Día 3 · G5 | Cierre integral, consistencia de cuentas y recuperación. Depende de G4. | Dos periodos consecutivos y el mismo saldo al reabrir. | Fallo inducido en publicación y repetición del cierre conservan una única versión válida. |
| Día 3 · G6 | Intercambio y distribución offline. Depende de G5. | Importar el lote de datos, ver rechazos y exportar resultados de la misma instancia. | Instalación limpia en el equipo de destino y respaldo/restauración reconciliados. |
| Día 4 · G7 | Caso empresarial completo, rendimiento y correcciones de aceptación. Depende de G6. | Paquete candidato con HTML actualizado, guía y datos de demostración. | Autor independiente reproduce el recorrido y el dueño puede operarlo con instrucciones. |
| Día 4 · G8 | Entrega del alcance verificado y lista explícita de pendientes. | Versión, evidencias, límites, respaldo y procedimiento de retorno. | Cada capacidad marcada activa tiene operación reproducible y resultado verificable. |

Si un lote no cumple su puerta, se corrige o se reduce alcance acordado. Se preserva el último paquete aceptado. La validez de cálculos, persistencia e identidad por empresa condiciona cualquier entrega de resultados oficiales.

## Equipo y consumo

El orquestador coordina contratos, plan, integración, rendimiento y evidencia. Tres especialistas trabajan inicialmente en archivos distintos:

- Motor/persistencia — razonamiento alto por atomicidad, reintentos y recuperación.
- Interfaz y flujo de operador — esfuerzo medio para formulario, lista, detalle y mensajes.
- Verificación independiente — pruebas de estado, aislamiento, idempotencia y errores. Su autor no modifica el motor para hacer pasar su prueba.

Se reutilizan agentes con conocimiento pertinente y encargos acotados, con ruta, contrato y salida esperada. Se comparte el contrato API una vez. Los archivos de fuentes y evidencia se citan por ruta y SHA. Se limita la concurrencia a tareas que puedan entregarse e integrarse por separado.

Al terminar un encargo se conserva el resultado y se reasigna el agente si hay una tarea necesaria. No se relanza la auditoría de todas las ramas ni se distribuyen los libros completos a cada tarea. Los modelos/esfuerzos se eligen entre las opciones reales disponibles, según complejidad. Se registra duración observada por encargo y repetición necesaria. El entorno no ofrece en este flujo una medición verificable de tokens/costo por agente; las estimaciones de ahorro no se presentan como consumo medido.

## Rendimiento

Antes de optimizar se registran equipo, Python, datos, reglas y revisión. Para el primer lote se mide importación, ejecución, reapertura y consulta. Después se mide la cadena completa con dos periodos y volumen representativo.

Se separa el tiempo de lectura de archivo, cálculo y persistencia. Se conserva evidencia de repetición y crecimiento del volumen. Se verifican memoria, bloqueo del escritor y tiempo de consulta. Los umbrales empresariales definitivos dependen del equipo y volumen del dueño. La medición de una fixture sintética informa sobre esa fixture.

## Cambios y evidencia

Cada lote tiene rama acotada en el consolidado, revisión independiente, evidencia y actualización del HTML cuando cambie una capacidad o se conozca un límite nuevo. Las pruebas antiguas se usan como referencia con sus datos y tolerancias. Una diferencia legítima se explica por caso y regla. El mapa histórico conserva su SHA; las capacidades del consolidado se muestran con su estado propio.

## Inicio de ejecución

G1 se encuentra en construcción. La arquitectura implementa servicio local y persistencia. La interfaz consume el contrato acordado. La verificación prepara pruebas independientes. Los contratos de Base estable, instancias históricas y autonomía continúan vigentes. La prueba transitoria es la primera comprobación de viabilidad y no acredita el cierre integral.
