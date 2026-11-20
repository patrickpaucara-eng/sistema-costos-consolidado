# Alineación del MVP con la Monografía 01

**Corte:** 20 de noviembre de 2026 (hora de Lima).  
**Fuente:** [MN 01 GE704W 2026 02.pdf](../fuentes/originales/MN%2001%20GE704W%202026%2002.pdf), SHA-256 `ca889881b6a743c3836a9bf51767b16e7385b2ce9cad08a1ead0602fae0b9de6`.  
**Plazo indicado:** miércoles 9 de diciembre de 2026, 18:00 (19 días desde este corte).

## Evaluación breve

La dirección técnica actual coincide con varios requisitos explícitos: trabajo local sin Internet, Python como motor, Excel para entrada/almacenamiento, salida HTML local, métodos repetibles y una entrega EXE prevista. Esta es una base útil para continuar Ola 3.

La implementación actual sigue siendo un piloto acotado, no una solución que cumpla la monografía. Opera una empresa por espacio, presenta un formulario JSON y no demuestra ABC integral, análisis de cuatro tipos, previsión de seis meses, escenarios estocásticos, reportes ejecutivos ni entrega completa. El caso nuevo T23.3/T23.5 ayuda a comprobar una ruta del costo de una orden; no cubre ese salto de alcance. Por tanto, la arquitectura va en una dirección compatible con la tarea, pero el trabajo restante es grande y debe medirse contra los entregables y la rúbrica, no contra el avance de ramas ni el 93 % histórico.

## Requisitos funcionales frente al candidato

| Requisito de la monografía | Evidencia actual | Estado al corte |
|---|---|---|
| Ejecutar local y sin conexión a Internet | Servidor de loopback y wheel; se preparó compilación Windows y smoke local | Parcial: falta primera ejecución en Windows y prueba física desconectada |
| Entrada desde Excel y registro de datos | Importación de libro y T14/T15/T17/T18/T19/T20 por servicio/API | Parcial: el formulario principal requiere JSON y el esquema de captura no es guiado |
| Base para datos y resultados | El XLSX se copia, edita en una transacción y se reabre | Parcial: es una fixture de una empresa por espacio, no repositorio empresarial multiempresa |
| Crear N modelos ABC para cualquier organización | Sin evidencia de configuración, selección y validación de varios modelos organizacionales | Pendiente crítico |
| Costeo integral ABC: producción, administración, ventas, financiero y conceptos NIIF 18 | Hay recorridos parciales de producción, gasto, centro y venta; no hay aceptación integral ni oráculo ORIA | Pendiente crítico |
| Análisis descriptivo, diagnóstico, predictivo y prescriptivo | Analítica autónoma y reportes aún no implementados | Pendiente crítico |
| Métricas actuales y proyección de seis meses | No se ha demostrado la serie de seis meses | Pendiente crítico |
| Dashboard histórico/actual/proyectado, determinístico y estocástico | No existe evidencia de dashboard con esos cuatro cortes | Pendiente crítico |
| Análisis de relevancia y simulación de escenarios estocásticos | No hay aceptación implementada para la monografía | Pendiente crítico |
| Interfaz flexible, simple y profesional | Hay HTML local, pero el formulario operativo es técnico/JSON | Parcial con riesgo alto para el 20 % de usabilidad |
| Informe técnico, propuestas y efecto económico | No hay el informe final requerido | Pendiente |
| Presentación ejecutiva | No hay la presentación final requerida | Pendiente |
| Ejecutable EXE | Hay una receta reproducible y workflow Windows; aún no se ha obtenido un artefacto de Actions | Pendiente de compilación y aceptación nativa |
| Archivo HTML offline | Se incluye el HTML; el código llama a `/api/...` del servidor local | Parcial: sirve desde el EXE/servidor local; abrir el archivo por doble clic no es una operación aceptada y debe aclararse/probarse |

## Los 13 entregables

| N.º | Entregable | Estado actual | Acción de cierre |
|---:|---|---|---|
| 1 | Word con chats y resultados de IA | Pendiente | Exportar la interacción pertinente y documentar decisiones/hallazgos |
| 2 | Word con etapas de desarrollo | Parcial | Convertir el plan y registro de capacidades en memoria final de etapas |
| 3 | Word con código fuente | Pendiente | Generar documento indexado desde la revisión entregada |
| 4 | Word con prueba de funcionamiento | Parcial | Usar evidencia repetible de API, Excel y Windows; convertirla al entregable requerido |
| 5 | Excel de entrada | Parcial | Preparar una plantilla/caso de monografía identificable y reproducible |
| 6 | Excel de resultados del sistema | Parcial | Exportar y conservar resultados de la misma revisión y datos de entrada |
| 7 | Excel de analítica | Pendiente | Implementar/validar resultados descriptivos, diagnósticos, predictivos y prescriptivos |
| 8 | Excel de proyección y alternativas | Pendiente | Incluir seis meses, escenarios y beneficio económico con supuestos visibles |
| 9 | Manual descriptivo Word | Pendiente | Documentar arquitectura, modelo, reglas, límites y dependencias |
| 10 | Manual de usuario Word | Parcial | Traducir la guía actual en tareas de usuario y errores comunes |
| 11 | EXE | Pendiente | Obtener ZIP del workflow, verificar hash, arrancar offline en Windows x64 |
| 12 | HTML | Parcial | Entregar archivo de la misma revisión y demostrar el modo offline exigido |
| 13 | Excel de actividad y horas | Pendiente | Registrar fechas, hora inicial/final y actividad desde ahora; no reconstruir horas no registradas |

## Rúbrica y prioridades

La rúbrica asigna 10 % a asistencia, 10 % a los entregables, 20 % a flexibilidad/facilidad de uso, 40 % al nivel técnico y 20 % a la presentación e informe. La instrucción indica que, si el EXE no funciona, la calificación se limita a asistencia. Por eso la primera puerta académica es generar y probar el EXE en Windows; la prueba de un Linux equivalente no sustituye esta aceptación.

Secuencia recomendada con 19 días calendario:

1. Obtener el artefacto Windows y probarlo en un equipo Windows sin Internet, incluyendo apertura, importación, cierre, salida HTML, cierre del proceso y reapertura de datos. Si el HTML debe abrirse sin ejecutar el EXE, resolver esa interpretación con el docente antes de diseñar otro modo.
2. Asegurar un caso organizacional representativo con entradas, método de costos aprobado, salida de Excel y respuesta independiente. Cerrar Ola 3 con evidencia y límites; no presentar D9 parcial como costo oficial.
3. Reducir fricción de la interfaz para tareas del caso: listas y formularios claros, validación y mensajes comprensibles. Priorizar los recorridos que afectan al demo y a la rúbrica de usabilidad.
4. Entregar archivos de carga, resultados, analítica/proyección y manuales solo cuando sus resultados se puedan reproducir desde el mismo caso y revisión.
5. Mantener desde hoy un registro de horas y preparar el informe técnico, la presentación ejecutiva, el ZIP final y sus hashes.

El alcance universal, el aprendizaje autónomo y la aceptación integral MCD/DBD/ORIA son objetivos de producto mayores que esta entrega académica. Para la monografía hay que elegir y documentar un caso acotado demostrable, explicar qué está probado y no afirmar cobertura universal que el sistema aún no tiene.
