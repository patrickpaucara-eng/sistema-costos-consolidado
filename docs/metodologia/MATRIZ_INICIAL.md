# Matriz inicial de reglas y aceptación

18 de noviembre de 2026. Las páginas MCD indican página física del PDF desde su portada. Las páginas DBD indican página del PDF. Las lecturas adjuntas permiten ubicar el pasaje. Esta matriz registra requisitos del consolidado y su verificación pendiente.

| Regla | Fuente y página | Interpretación aplicada | Caso de aceptación | Estado |
|---|---|---|---|---|
| Misión y dominio guían el modelo | MCD pp. 21–23, 108–111 | Definir productos de costo y sus conceptos antes de fijar tablas. | Una orden y un proyecto trazan cada atributo hasta una pregunta de costo. | Diseño |
| La macrofunción se desarrolla en eventos, operaciones y métodos | MCD pp. 40–41 | Relacionar Entrega con publicación de una instancia de costo y sus datos. | Seguir una entrega hasta cada hecho y regla utilizados. | Diseño |
| Catálogo y parque tienen significado distinto | MCD p. 169 | Distinguir definición de transacción, evento ocurrido, método y corrida. | Dos ejecuciones de un método tienen identidad y procedencia propias. | Diseño |
| Secuencia de proceso parametrizable | MCD pp. 95–96 | Datos validados definen el protocolo entre operaciones admitidas. | Añadir una capacidad configurada conserva contratos y resultados anteriores. | Diseño |
| Eventos explican saldos y cambios | MCD pp. 37, 99–100; DBD pp. 159–162 | Conservar origen de cantidades e importes y conciliaciones. | Detalle y saldo cuadran por empresa/objeto y al restaurar. | Diseño |
| Modelo externo deriva de necesidades del usuario | DBD pp. 23–29 | HTML permite lista, búsqueda, detalle, resumen y acciones reconocibles. | Operador completa carga y auditor sigue un costo hasta su fuente. | Diseño |
| Acceso por perfil y función | DBD pp. 23–24, 201–202 | La misma autorización rige interfaz y servicios del motor. | Entrada y consulta de una empresa respetan el ámbito autorizado. | Diseño |
| Consultas críticas se miden | DBD pp. 30–32, 167 | Índices y materializaciones responden a mediciones. | Tiempo del cierre y consulta cumplen el volumen acordado. | Falta volumen |
| Historia congelada y reconstrucción | DBD pp. 74–75, 161–162 | Preservar instancia, entrada y versiones para volver al resultado histórico. | Factura tardía y tarifa nueva conservan el cierre emitido. | Diseño |
| Transacción, bitácora y recuperación | DBD pp. 178–185, 195–201 | Publicación consistente y reintento identificable. | Fallo intermedio y repetición dejan un solo cierre confirmado. | Diseño |
| Base estable ante nuevas capacidades | Dueño, 18-nov | Datos nuevos se expresan dentro de un vocabulario con integridad. | Costear un proyecto por configuración sin alterar contratos aceptados. | Pendiente modelo del caso |
| Instancias siempre reproducibles | Dueño, 18-nov | Conservar fecha efectiva, conocimiento, vigencia y corrida como ejes distintos cuando corresponda. | Dos consultas de la instancia devuelven idéntico importe después de un cambio. | Diseño aplicado a requisito |
| Analítica autónoma y experiencia | Dueño, 18-nov; REQUISITOS histórico R25/R44 | Aprender de la decisión y su efecto, con evaluación temporal y por ámbito. | Mejorar en casos no usados al entrenar y detectar pérdida de desempeño. | Diseño |
| Refuerzo para casos especiales | Dueño, 18-nov | Registrar excepciones y feedback; seleccionar aprendizaje adecuado a la señal disponible. | Caso especial resuelto conserva resultado medido y puede compararse con futuras propuestas. | Evaluar técnica |
| Capacidades activas rastreables | Dueño, 18-nov | Operación demostrable, dependencia, versión y evidencia. | Capacidad recorre interfaz, motor, persistencia y reapertura. | Protocolo documentado |

## Aplicación numérica por completar

Caso A — Dos empresas compran 10 unidades del recurso R al almacén L. A paga S/ 100 y B paga S/ 900. Cada una consume una unidad para su propia orden. El material directo de las órdenes debe ser S/ 10 y S/ 90 respectivamente, tanto en una base compartida como en ejecuciones separadas. El método directo del histórico dio S/ 50 para la salida de A al recibir entradas de ambas empresas, según PRUEBAS_FOCALIZADAS.log de OT-001.

Caso B — Publicar enero con la información conocida al cierre. Registrar luego una factura efectiva en enero y cambiar una tarifa para un periodo posterior. Abrir la instancia original y recuperar la misma entrada y resultado. La corrida revisada explica sus diferencias.

Caso C — Costear un proyecto mediante un protocolo y datos configurados. Se debe definir cómo se expresa proyecto/actividad/hito y el avance, las medidas de consumo y la entrega esperada. Cerrar ese caso antes del esquema evita que una nueva etiqueta oculte una regla sin especificar.

Los casos A–C requieren comprobación del modelo y del recorrido. El caso A tiene una reproducción focalizada del fallo del histórico. Esa reproducción se conserva con su alcance y SHA.
