# OT-R01 · Revisión independiente (solo lectura): naturaleza del costo

**Rol:** revisor. **No modifiques ningún archivo, no crees ramas ni PR.** Solo lees, ejecutas pruebas y reportas.
**Alcance (no leas más que esto):** el commit `ba04138` en `desarrollo/mono`:
`git show ba04138 -- src/metodos/reparto_etapas.py src/reyna_local/resultados.py src/reyna_local/contrato.py src/reyna_local/libro_dbd.py tests/test_naturaleza_costo.py`

## Qué hace el cambio
Cada monto del reparto ABC lleva una naturaleza en la clave del elemento: `MD` (normal), `MD|PERDIDA` (merma en exceso, va a la
orden que la causó), `PD|OCIO` (capacidad no usada; se queda en el origen y baja por la misma cadena, con el mismo inductor o con
la regla `OCIO` del libro). `resultados.POLITICA_NATURALEZA` decide por síntesis: REAL las suma al costo de la orden en columnas
`perdida` y `ocio`; CONTABLE las deja fuera (NIC 2 §13, §16 a).

## Verifica (marca cada punto: CUMPLE / FALLA / DUDA, con evidencia)
1. Conservación: Σ recursos = Σ llegado a objetos, en total y por naturaleza. ¿Hay algún camino donde un monto quede varado o se duplique? (mira `correr`, el bloque de `f_ocio` y el de `perdida`).
2. Un monto que ya trae `|OCIO` o `|PERDIDA` y llega a un origen con capacidad: ¿se vuelve a separar ocio? (no debe).
3. Regla `OCIO` con destinos de otro nivel o vacíos: ¿se rechaza con mensaje claro?
4. Ocio en un centro de administración (`GAD|OCIO`): ¿sigue siendo gasto de administración en todas las síntesis?
5. Redondeo: `_por_naturaleza` redondea por clave; ¿puede descuadrar `contrato.validar` (suma de elementos = `costo_total`)?
6. Trazabilidad: `trazar(..., "MD|PERDIDA")` y `"CIF|OCIO"` suman exacto el valor del objeto.
7. Legibilidad para un auditor: ¿los nombres, docstrings y la tabla de política se entienden sin leer el resto del sistema?

## Cómo ejecutar
`python -m pytest -q tests/test_naturaleza_costo.py tests/test_capacidad_y_merma.py tests/test_modelo3_oria.py`
Si quieres probar un caso propio, hazlo en un archivo temporal fuera del repo.

## Entrega (en el chat, máximo 40 líneas)
Tabla: `# | punto | veredicto | archivo:línea | evidencia | sugerencia`. Al final, una línea: APROBADO / APROBADO CON OBSERVACIONES / RECHAZADO.
