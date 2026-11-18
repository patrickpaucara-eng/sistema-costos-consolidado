# OT-001 · Auditoría forense de Sistema de Costos Reyna

## Dictamen

**Usar main `a96ba794a6171a325836a5a56bf1c9392dbd8482` como línea base de trabajo.** Integra I-5 y concentra el linaje revisable. La entrega de producción sigue abierta. Conservar la demo `3a2850060c96b2f7eaeae613c8a402aa9486c079` para aceptación histórica. `desarrollo/ola1` en `cac2501d9f712655dda466d216dc5bff2dd446a5` es la principal candidata de recuperación, con cambios en DBD, motor, pruebas, empaquetado y experiencia mensual.

La captura Git contiene **292 ramas, 290 puntas, 289 árboles y 819 commits alcanzables**. Las 292 referencias coincidieron con GitHub al inicio y al cierre de la comprobación. 47 ramas tienen deltas ya presentes por ruta en main pese a divergencias de historia. 241 presentan alguna diferencia de contenido, modo o presencia. La presencia de una diferencia por ruta permite ubicar variantes y no certifica su vigencia funcional. El inventario cubre cada rama; la revisión dirigida de código y reproducción dinámica se concentra en componentes de riesgo y tres revisiones de producto.

## Hallazgos que condicionan la entrega

1. **Construcción e integridad del DBD.** `main` regenera el libro Excel, pero el generador de SQLite falla con `IndexError`. La coherencia arroja 16 errores y 62 avisos, y la automatización da 3/5. El archivo SQLite versionado omite 18 columnas del DBD actual. `7b0ec58` en Ola 1 contiene la corrección de las referencias a empresa.
2. **Aislamiento por empresa incompleto.** El método Python de valuación agrupó por recurso/almacén. En la sonda sintética, una salida de A valió S/ 10 con hechos de A y S/ 50 al incorporar entradas de B con las mismas claves. Se obtuvo el mismo resultado en main y Ola 1. Esto reproduce el fallo del método bajo mezcla de entradas. La validación de extremo a extremo debe comprobar el filtro de los llamadores e incluir empresas con claves coincidentes.
3. **Entrega estricta bloqueada.** El verificador VBA detecta P20 en `NumPropuesta` y detiene `construir.py --entrega`. Es un bloqueo reproducido de empaquetado. La repercusión funcional en Excel es un pendiente.
4. **Trazabilidad, cuentas y cierre.** Dos resultados de proyección y diferencias del caso ENV tienen huella de entrada vacía. Siete cuentas requieren validar escritor único y cuadre. El expediente de cierre identifica una recuperación por transacción y una restauración de la secuencia completa pendiente.
5. **Desalineación documental y metodológica.** El README describe v14 y palta. La guía de reanudación antecede a I-5. El MCD congelado versionado es v3 y la ficha cita v3.1 con otra huella. El DBD contiene 103 tablas físicas y 62 alias clasificados. El 93 % declarado carece de una matriz y denominador auditados. Mantener separados el expediente implementado y la conformidad con los textos de Reyna.

## Pruebas de main

Con Python 3.11.18, Git 2.47.3 y LibreOffice 25.2.3.2 en el contenedor sin red, pytest dio **486 aprobadas, 2 fallidas, 27 fallos esperados y 2 éxitos inesperados**. Los dos fallos son comparaciones exactas de floats en simulación. Los mismos dos casos pasaron al repetirlos en Python 3.13.5. Se reprodujeron **392/392** comprobaciones históricas tras regenerar el XLSX y **66/66** valores ENVASE con máxima diferencia de **1,84 × 10⁻¹²**. La comparación contra el CSV de I-5 archivado de Excel dio **COINCIDE** para 148 celdas de CRITERIO, PARAM_CAMBIO y RECURSO. La ejecución de macros por UNO agotó el tiempo asignado. La comparación archivada no equivale a una nueva ejecución en Excel nativo.

## Recuperación y consolidación

- Conservar por procedencia el DBD, el núcleo de eventos y cierre, los contratos de métodos, los casos/oráculos y la capa de importación, exportación y pruebas.
- Recuperar de Ola 1 los cambios de FK, D12 y D1 y evaluar OPERAR MES con Excel nativo. Comparar fuente y salida regenerada antes de trasladar artefactos.
- Recuperar selectivamente `informes/FINAL/`, el diagnóstico de deuda, el escenario de seis meses, el diseño I-9 y las lecciones de Oria. Se localizaron y contrastaron el PDF funcional y el prototipo de Oria. Siguen fuera de alcance los libros completos de Reyna, las conversaciones privadas de Claude y materiales originales sin copia identificada.
- Proponer un repositorio privado con trazabilidad por SHA, fuentes reproducibles, revisión independiente y pruebas por contrato. Su creación, cualquier cambio remoto y la reforma tecnológica requieren autorización expresa.

## Comparación de la candidata y la demo

| Evidencia | main | Ola 1 | Demo congelada |
|---|---:|---:|---:|
| Pytest Python 3.11.18 | 486 aprobadas, 2 fallidas, 27 xfail, 2 xpass | 519 aprobadas, 2 fallidas, 25 xfail, 2 xpass | 41 aprobadas en su suite propia |
| Regresión histórica | 392/392 | 392/392 | 392/392 |
| Oráculo ENVASE | 66/66 | 66/66 | 66/66 |
| Construcción estricta | P20, salida 1 | P20, salida 1 | P20, salida 1 |
| Errores de coherencia DBD | 16 | 0 | 0 |
| Automatización desde DBD | 3/5 | 5/5 | 5/5 |

La suite de Ola 1 suma pruebas y cambia marcas de expectativa en I-5. Sus totales no constituyen una comparación ciega de funcionalidad. Las dos diferencias numéricas de simulación en Python 3.11.18 también pasaron bajo Python 3.13.5 en Ola 1. La regeneración candidata produjo 0 errores, 62 avisos y 0 relaciones a revisar en el generador. Es un candidato más sano para la estructura y para recuperar OPERAR MES. El acoplamiento del método al conjunto de hechos y el bloqueo de entrega permanecen.

## Límites de ejecución y entrega

La prueba histórica de macros con LibreOffice/UNO ejecutó sondas básicas en Ola 1 y la demo, entre ellas inicio de sesión, mantenimiento y lectura de tablas. La autoprueba completa alcanzó el límite asignado. Excel nativo, los artefactos originales metodológicos y el historial privado de Claude quedan fuera de lo verificado. La cobertura de pruebas de software pertenece a las tres revisiones fijadas; cada una de las 292 ramas tiene cobertura de inventario y divergencia.

La ruta de salida para descargas no está montada en esta máquina Cloud. El expediente se conserva temporalmente en `/workspace/work/ot001/`. Incluye inventario CSV, cronología, conocimiento recuperado, mapa de arquitectura, riesgos, índice, recomendación de consolidación, revisión independiente, comandos, evidencias y manifiesto SHA-256.
