# C34-1 · Recetas parametrizadas por familia

**Alcance:** modelo de datos y cálculo puro de la receta; no añade interfaz ni modifica el motor de registro.

La hoja opcional `FAMILIA_PARAM` almacena una fila por familia, inductor y parámetro: código/nombre/unidad, rango válido y base/coficiente de la receta. Un libro que no tenga la hoja sigue siendo legible y devuelve cero familias. La carga de la receta valida la cabecera y rechaza definiciones, coeficientes o claves duplicados/incompletos.

`aprender_familia` ajusta cada inductor como `base + Σ coeficiente × parámetro` con regresión lineal QR de Householder en Python estándar. Exige que todas las observaciones estén etiquetadas `REAL`, sean de la familia indicada y tengan los mismos inductores y parámetros completos. No importa scipy ni usa una cantidad faltante como cero.

## Caso manual independiente

| OT real | Peso | Horas soldadura |
|---|---:|---:|
| 1 | 1.000 kg | 60 h |
| 2 | 1.200 kg | 70 h |
| 3 | 1.500 kg | 85 h |

La recta resultante es `10 h + 0,05 h/kg × kg`. Para 1.300 kg calcula **75 h**. Se comprueban también parámetro obligatorio ausente, valor fuera del rango, historia no REAL, historia sin variación identificable y round-trip de la hoja. Prueba focalizada: `python -m unittest discover -s tests -p 'test_c34_1_recetas_pedido.py' -v`.

## Límites

- No se conecta aún el libro de trabajo operativo ni se incorpora un flujo para revisar/aprobar coeficientes aprendidos.
- El ajuste es lineal y no demuestra que el predictor sea causal ni metodológicamente adecuado; requiere suficientes OTs reales representativas y revisión técnica.
- La hoja es opcional y local; sincronización multiusuario, versionado histórico y auditoría de cambios quedan pendientes.

## Verificación integral de la rama

La prueba focalizada de C34-1 terminó **6/6 OK** y el contrato de resultados de la compuerta pasó. `python tools/verificar.py` terminó **ROJA** tras 92,66 s: 33 pruebas pasaron y falló `tests/test_c07_analitica.py::test_pantallas_analitica_y_proyeccion`. C34-1 no cambia la pantalla, el test ni el código C07. La compuerta integral no se repitió; se requiere resolver o confirmar ese fallo de base antes de abrir PR, según la barrera de `AGENTS.md`.
