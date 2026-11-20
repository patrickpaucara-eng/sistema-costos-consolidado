# Decisión técnica · Python y Excel

Registrada el 18 de noviembre de 2026 y precisada después por el dueño. La ejecución vigente está en [PLAN_MVP_Y_PENDIENTES.md](../entrega/PLAN_MVP_Y_PENDIENTES.md).

## Mandato y alcance

El dueño precisó quitar VBA del flujo nuevo, conservar Excel y completar el trabajo de Claude mediante capacidades verificadas. Su instrucción posterior congela el VBA histórico en vez de borrarlo. SQLite se aplaza. Primero se valida el motor en Excel; después se revisa el generador y los métodos de costos contra MCD/DBD y ORIA; luego se evalúa robustez, adaptabilidad y BI.

## Recorrido de entrega

1. Fijar la revisión de referencia y recuperar cambios de Ola 1 solo cuando correspondan.
2. Operar con Python sobre copias Excel; conservar contrato para separar en el futuro el motor del adaptador de almacenamiento.
3. Probar guardado temporal, reemplazo, respaldo, reintento, concurrencia cooperativa y cierres con inyección de fallo.
4. Mantener identidad de solicitud, empresa y periodo para prevenir duplicación o contaminación.
5. Completar compra, consumo y cierre técnico desde HTML. El costo oficial por orden y las cuentas requieren oráculos adicionales.
6. Verificar métodos con MCD/DBD, casos ORIA y conciliación antes de modificarlos.
7. Cerrar D9, flete/T14.2 y D14 por dependencias; después validar integración, Windows/Excel y varios periodos.
8. Evaluar BI/autonomía solo con costos publicados, calidad medida y límites autorizados.

## Integración y retorno de Claude

El coordinador realiza la integración técnica y su verificación. Una rama de entrega reúne los cambios aceptados y conserva hitos. Los agentes trabajan por módulos y encargos acotados; cada cambio de cálculo o persistencia tiene revisión independiente.

La rama de entrega de código debe basarse en la revisión histórica identificada y registrar sus incorporaciones. El repositorio consolidado ya tiene un historial documental distinto. Un merge convencional entre ambos repositorios requiere revisar su ascendencia. Si Claude retoma el repositorio histórico, se preparará una rama basada en esa ascendencia o una serie de cambios reproducibles, con manifiesto de origen y pruebas. No se presupone que fusionar ramas de nombres similares traslada correctamente todo el trabajo.

Claude podrá revisar el resultado y continuar desde el último hito aceptado, con estado, documentación y pruebas. La revisión no se pospone hasta su regreso.

## Recursos

Orquestador en razonamiento alto para diseño, dependencias, diagnóstico e integración. Las tareas de búsqueda, copia e inventario usan esfuerzo bajo o medio. Las implementaciones rutinarias usan medio. Cálculos, persistencia y auditoría independiente usan alto cuando su complejidad lo requiere.

La medición disponible informa tiempos, ejecuciones y resultados. El coste real en tokens por tarea no está expuesto en esta sesión. Se limita el contexto compartido a contrato, rutas y evidencia relevante.

## Ensayo aplazado

Los archivos SQLite ya iniciados se conservan como ensayo. Sus resultados pendientes no acreditan operación empresarial. Los tres especialistas recibieron el cambio de prioridad para evitar continuar con una persistencia distinta de la elegida para la entrega.
