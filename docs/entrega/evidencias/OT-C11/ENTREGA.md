# OT-C11 · Taxonomía de hojas

La tabla `docs/diseno/TAXONOMIA_HOJAS.csv` clasifica las hojas de `casos/plantilla_dbd.xlsx` como catálogo, movimiento, configuración o resultado. Incluye responsable, frecuencia y el significado conservado en `TABLAS_LOGICAS` cuando existe. Es una clasificación de la hoja: algunas hojas de entrada tienen columnas calculadas y requieren reglas por campo antes de permitir edición.

## Cómo probar

Abrir el CSV, filtrar `MOVIMIENTO` y revisar EVENTO, LINEA, MEDIDA y VENTA. Ejecutar `PYTHONPATH=src python -m pytest tests/test_taxonomia_hojas.py -q` para comprobar cobertura, unicidad y clases del mandato. Ejecutar `python tools/verificar.py` para la compuerta completa.

## Siguiente decisión

Claude debe revisar los casos mixtos y la correspondencia campo a campo con `TRX_CAMPO` antes de usar esta tabla para habilitar escritura directa. La taxonomía no habilita un formulario ni modifica el motor.

Compuerta en Linux: **VERDE**, 369 pruebas y 26 subpruebas. La prueba nueva verificó las 122 hojas de la plantilla.
