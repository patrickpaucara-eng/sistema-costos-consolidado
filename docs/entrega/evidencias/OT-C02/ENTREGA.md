# OT-C02 · Exportadores

## Qué cambió

Se añadieron tres libros Excel: resultados (objetos, actividades y estado por categorías NIIF 18), analítica (relevancia y hallazgos), y proyección (serie, escenarios y propuestas). El HTML autónomo presenta los datos del contrato y no descarga librerías. El documento Word reúne las fuentes de `src/` y `tools/` con índice. Los exportadores copian resultados suministrados y no calculan costos. El texto de ejemplo queda identificado mediante `_nota` cuando está disponible.

## Cómo probarlo en 15 minutos

1. Instala el proyecto con sus dependencias y ejecuta `python -m pytest tests/test_exportar.py -q`.
2. Inicia `python -m reyna_local --data-dir /ruta/de/trabajo`.
3. Envía un `POST /api/exportar?tipo=resultados` con cuerpo JSON `{"resultados": <contrato>}`; usa `tests/fixtures/contrato/resultados_ejemplo.json` como objeto completo. Tipos adicionales: `analitica`, `proyeccion`, `html` y `codigo` (para código, cuerpo `{}`). La respuesta contiene la ruta en `exportaciones` de la carpeta de datos.
4. Abre el XLSX con Excel o LibreOffice; abre el HTML con el navegador desconectado. El Word también puede generarse con `python tools/codigo_a_word.py salida.docx` desde la raíz del repositorio.

La compuerta `python tools/verificar.py` terminó en VERDE: 71 pruebas y 26 subpruebas en Linux.

## Pendientes y límites

El endpoint requiere que la interfaz de C01 envíe el contrato y muestre los controles de descarga; esta orden no modifica `web/`. La vista HTML usa un diseño propio sencillo, pendiente de armonizar con C01. El estado de resultados reproduce categorías y cifras proporcionadas; su clasificación metodológica debe ser validada por Claude. El Word enumera fuentes textuales disponibles en el árbol de trabajo y no incorpora libros binarios; para una instalación empaquetada se requiere incluir el árbol fuente. El paquete Windows requiere actualizar sus dependencias fijadas y verificarse con python-docx antes de entregar el EXE. Los datos de ejemplo están marcados como tales. Para integrar ramas, combinar las adiciones a `src/reyna_local/__main__.py` y las filas independientes de `docs/entrega/tiempos/codex.csv`.
