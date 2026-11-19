# Estado y reanudación

Actualizado el 18 de noviembre de 2026. Rama de trabajo desarrollo/capacidad-inicial, derivada de docs/plan-maestro.

## Mandatos vigentes

El dueño aprobó SQLite local + Python como motor único + Excel/CSV + interfaz HTML y autorizó ejecutar el plan. MCD y DBD de Tino Reyna son las fuentes primarias para dudas de método y presentación.

Se requiere Base estable ante nuevos costos, instancias históricas reproducibles, crecimiento mediante configuración, módulos, analítica que aprende y autonomía basada en madurez. La entrega se realiza por capacidades activas con recorrido y evidencia. Las formulaciones detalladas están en docs/modelo/CONTRATOS_DE_LOS_NIVELES.md.

## Trabajo realizado en este hito

| Tarea | Estado | Evidencia |
|---|---|---|
| P00 | Verificada para este hito | Los seis adjuntos originales coinciden con SHA256SUMS.txt. Revisiones de origen fijadas en OT-001. |
| P01 | Preservada en el hito documental, integridad verificada por manifiesto | docs/auditoria/OT-001 contiene 27 archivos cotejados con su manifiesto original. |
| P02 | En curso | Plan, contratos, aprobaciones y fuentes históricas identificadas. Falta matriz completa de requisitos. |
| P03 | Protocolo registrado | AGENTS.md, PLAN_MAESTRO.md y este archivo explican qué consultar y cómo actualizar el HTML. |
| M01 | Lectura y extracción en curso | Libros completos disponibles y análisis de MCD/DBD con páginas. La matriz deberá revisarse por regla. |
| M03 | Recuperación dirigida en curso | REQUISITOS.md, COMO_RETOMAR.md, ESPEC_ANALITICA2.md y expediente final consultados por SHA. |
| C01–C07 | Contratos preliminares | Documento de niveles con criterios de aceptación. Falta cotejar y resolver ejemplos completos. |

La aplicación consolidada todavía requiere diseño y construcción por lotes. El mapa HTML publicado corresponde al histórico main a96ba79, cuya referencia remota se confirmó al crear el mapa.

## Siguiente tarea reanudable

Completar la matriz metodológica con MCD y DBD y cerrar los conceptos para una orden, un proyecto y dos empresas. Preservar como caso la factura tardía para consultas por fecha y por conocimiento. Resolver cómo expresar datos y reglas del caso de proyectos antes de fijar el esquema.

Los borradores C01–C07 avanzan en paralelo. Su cierre requiere M02, M04–M06 y la revisión C08. Se puede reproducir A01 sobre copias del histórico como diagnóstico. Para validar el consolidado, primero se diseñan sus casos de aceptación y se ejecutan durante los lotes de implementación. Las capacidades nuevas se registran con operación, ejemplo, evidencia y versión. El stack está aprobado. El número de usuarios simultáneos y el volumen esperado siguen pendientes para M05.

## Capacidades del consolidado

| Capacidad | Estado y recorrido | Evidencia |
|---|---|---|
| Consultar fuentes y procedencia | Documentación disponible en Git | Índice y seis originales con hashes. |
| Consultar mapa del histórico | HTML local navegable | Mapa, catálogo DBD y enlaces por SHA. |
| Registrar y cerrar costos en el consolidado | Pendiente de construcción | Se implementará después del modelo y casos aceptados. |
| Adaptación autónoma del consolidado | Pendiente de diseño y entrenamiento | Requiere historial y evaluación de resultados. |

Los estados de documentación y los de operación empresarial indican capacidades distintas. Cada tabla explicita el recorrido que acredita su estado.

## Fuentes metodológicas de este hito

LECTURA_MCD.md documenta las páginas físicas de MCD y LECTURA_DBD.md los pasajes de interfaz, historia y recuperación de DBD. MATRIZ_INICIAL.md relaciona quince requisitos con casos y estado. CONOCIMIENTO_Y_FORMA_DE_TRABAJO.md recupera decisiones Markdown históricas y matiza la integración de autonomía. La revisión independiente corrigió una dependencia circular entre diseñar pruebas y construir producto, ubicó el modelo externo antes del diseño físico y añadió A10 para la extensión por proyectos.

## Ejecución priorizada en cuatro días

PLAN_CUATRO_DIAS.md fija el nuevo orden de ejecución. La construcción de G1/CAP-01–CAP-05 está asignada a tres agentes con áreas separadas y un contrato API común. El orquestador integra y mide rendimiento. Las preguntas de alcance prioritario y equipo de destino se enviaron al dueño; hasta su respuesta se usa el supuesto reversible de un operador local.

## Cambio de prioridad vigente

El dueño indicó posteriormente quitar VBA, conservar Excel, completar los pendientes de Claude y verificar los métodos de costos contra los casos de ORIA. SQLite se aplaza. Los agentes recibieron instrucción de pausar su ensayo y conservarlo. G1 cambia a HTML → Python → archivo Excel → reapertura. Ver PYTHON_EXCEL.md. El intento SQLite conserva estado de ensayo y no se declara capacidad activa.
