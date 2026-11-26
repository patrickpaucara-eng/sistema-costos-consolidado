# Punto 5 · Laboratorio

- Seleccionar un espacio original en «Espacios de trabajo»; abrir «Laboratorio» y crear copia.
- Registrar hechos con las transacciones del libro en la copia; elegir mes y síntesis; pulsar «Recalcular y comparar».
- Pruebas: `tests/test_c31_p5_laboratorio.py` recorre API y Chromium con T15, compara órdenes y elementos y comprueba SHA del original.
- Si el original cambió después de crear la copia, la comparación se rechaza y debe crearse otra copia.
- Limitación: REAL/CONTABLE y transacciones habilitadas; no es un editor libre de todas las celdas. Revisar la normalización de fechas en formularios fuera del laboratorio.
