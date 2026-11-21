# OT-C03 · Entrega para revisión

Se recuperaron 18 hojas de entrada como CSV de los doce meses de 2010 desde el JSONL. La columna `periodo` identifica el mes. La procedencia y las limitaciones constan en `datos/frenosa/FUENTES.md`. Los importes de julio incluyen datos del caso según la exportación; las compras y cantidades vendidas son simuladas. No se asignaron transacciones ni se calcularon costos.

## Cómo probar en 15 minutos

1. Abrir `datos/frenosa/FUENTES.md` y comparar la línea y el hash con la fuente JSONL.
2. Abrir `datos/frenosa/Compras.csv` y filtrar por `periodo = 2010-07`; observar las columnas de fuente y observación.
3. Ejecutar `python -m pytest tests/test_frenosa_fuentes.py -q`: compara todas las filas y celdas con las entradas textuales del JSONL. Ejecutar `python tools/verificar.py` para la compuerta completa.

## Pendiente y decisión

La exportación contiene dos entradas `frenosa_datos_entrada_abc.xlsx` distintas; no se mezclaron con el archivo mensual de julio. Falta cotejarlas y verificar los originales XLSX si se desea acreditar fórmulas, formatos o procedencia original. Claude debe decidir cómo transformar las entradas aceptadas a operaciones del sistema.
