# OT-C22 · Evidencia y límites

- Operación: calibrar con libro y resultados REAL publicados; conservar candidatos y decisiones en JSON local; aplicar solo estados vigentes a hallazgos y prioridades.
- Caso de control: [10, 10.2, 9.9, 10.1, 15, 10] frente a 12 produce 10,05, marca 15 como atípico y pasa la guarda; frente a 20 queda pendiente. Beta(1,1) con dos éxitos de tres produce 0,6.
- Auditoría: cada candidato registra identidad por evidencia, fecha, estado y vigencia. Rechazos con idéntica evidencia no reaparecen; la aprobación manual posterior no altera meses anteriores.
- Pruebas: `tests/test_aprendizaje.py` y `tests/test_cotizador.py`; se compara el resultado REAL y CONTABLE con y sin la capa activa.
- Limitación: C21 todavía no está integrada en la base de esta rama. Existe `factor_estandar` probado para conectar la proyección, pero falta incorporarlo al flujo de C21 y verificar el escenario integral antes de declarar completa esta capacidad.
