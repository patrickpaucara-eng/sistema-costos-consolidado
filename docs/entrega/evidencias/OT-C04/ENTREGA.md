# OT-C04 · Calcular y exportar

El selector permite calcular el caso Frenosa para 2010 en REAL, CONTABLE y ESTIMADO con el productor existente. Los reportes se descargan desde la pantalla. El HTML autónomo presenta indicadores, gráficos y tablas sin conexiones externas. La información incluye supuestos académicos; compras y cantidades vendidas son simuladas.

## Cómo probar

1. Iniciar `PYTHONPATH=src python -m reyna_local --data-dir /tmp/reyna-piloto --port 8765` y abrir la dirección indicada.
2. Elegir julio de 2010 y REAL, CONTABLE o ESTIMADO; pulsar **Calcular** y esperar la confirmación.
3. En **Reportes**, descargar Excel o HTML; abrir el HTML con internet desconectado. Cambiar el selector exige volver a consultar o calcular antes de exportar.
4. Ejecutar `PYTHONPATH=src python -m pytest tests/test_c04_calcular_exportar.py -q` y `python tools/verificar.py`.

## Pendiente

El libro generado se reutiliza en la carpeta de datos; se debe recrear explícitamente si cambian los insumos. El ejecutable nativo Windows y la portabilidad de las rutas de fuentes requieren OT-C05. La analítica visual detallada y la equiparación completa del HTML sin conexión corresponden a OT-C07.
