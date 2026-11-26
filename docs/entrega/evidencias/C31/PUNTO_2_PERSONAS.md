# OT-C31 punto 2: detalle por recurso de mano de obra

- Operación: en «Ficha de la orden», revisar «Detalle de mano de obra por recurso»; elegir una orden del periodo.
- Datos: copia temporal de SERVITEC (`casos/libros/segundo.xlsx`, SHA-256 `f46c5c57d3350092e41aade1ed8dfb3597cf3a7d533b41771703142f268222b7`). El ensayo divide el recurso agregado MOD en tres técnicos **sintéticos**, cada uno con S/ 4 000; no son personas ni datos reales identificados.
- Resultado: para julio de 2025, el resultado REAL conserva MOD REB S/ 9 600 y MPR S/ 1 920 y la ruta presenta los tres técnicos. Chromium verificó la pantalla; el SHA del libro original se conserva. Ver `tests/test_c31_2_personal.py` y `punto-2-personal.png`.
- Revisión: la vista solo muestra los tramos raíz P2 del contrato cuyo recurso tiene tipo `PERS_DIR`, sin calcular una distribución propia. Un recurso agregado sigue viéndose como agregado.
- Límite: este ensayo no valida los datos de planilla reales, ni demuestra asignación individual medida. No modifica el libro de SERVITEC ni incorpora datos ficticios al catálogo.
- Siguiente acción: revisión de la evidencia y prueba con datos individuales reales, cuando existan.
