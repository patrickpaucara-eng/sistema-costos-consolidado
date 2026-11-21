# OT-C07 · Analítica del caso Frenosa

El dashboard muestra ventas, costo y margen por periodo, con distinción entre histórico, actual, proyección determinística y banda estocástica. Análisis incluye relevancia, hallazgos y escenarios; ESTIMADO muestra la banda por producto y la etiqueta de estimación estadística. El HTML descargado incluye las secciones del contrato y gráficos sin conexión. Los datos contienen supuestos académicos y cantidades simuladas.

## Cómo probar

1. Iniciar `PYTHONPATH=src python -m reyna_local --data-dir /tmp/reyna-c07 --port 8765` y abrir la dirección indicada.
2. Elegir diciembre 2010 en REAL, CONTABLE y ESTIMADO; pulsar Consultar. Revisar la banda, las tarjetas, los escenarios, las propuestas y la tabla de estimación.
3. Elegir marzo 2010 y confirmar el aviso de historia corta. En Reportes, descargar el HTML y abrirlo sin conexión.
4. Con Playwright y Chromium disponibles, ejecutar `PYTHONPATH=src python -m pytest tests/test_c07_analitica.py -q`; ejecutar también `python tools/verificar.py`.

## Pendiente

La prueba visual automatizada necesita Playwright y Chromium; si faltan, se omite y debe ejecutarse en un entorno que los tenga. El costo y los modelos son generados por los módulos de Claude; la pantalla representa su contrato. El HTML usa gráficos SVG autónomos y tablas, con un diseño simplificado respecto de la interfaz.
