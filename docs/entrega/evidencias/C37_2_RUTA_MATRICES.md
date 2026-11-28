# OT-C37-2 · Ruta reproducible y matrices por etapa

**Estado:** verificado en la publicación sintética SERVITEC 2025-04 REAL.
**Base:** `desarrollo/mono@ff09bec`.
**Alcance:** solo presentación, prueba y documentación. No se modificaron `src/metodos/reparto_etapas.py`, `motor_espejo.py` ni los resultados publicados.

## Qué muestra

En «Ficha de la orden», cada tramo muestra la tasa, el total del inductor, la medida del destino, la base a distribuir (`tasa × total`), el cálculo (`base × medida ÷ total`), el importe que avanza por ese tramo y la parte atribuida a la OT. Cuando aún hay etapas posteriores, muestra también el factor de ruta; en un tramo final hacia la OT ese factor es 100 %.

Cada etapa tiene «Ver matrices»:

- **Configuración:** matriz de orígenes × destinos; cada celda identifica el inductor y la medida/total.
- **Cálculo:** base, medida, total, fórmula aplicada, importe que avanza y parte de la OT elegida. Agrupa cada origen y muestra `Σ = origen ✔` o `Σ = origen DIFERENCIA` con la diferencia observada.

Una diferencia se conserva visible, sin ajustar ni recalcular el resultado. La matriz se arma con los tramos únicos de la publicación para el elemento y etapa seleccionados; la parte de la OT se lee del mismo contrato de resultados.

## Comprobación manual

En `datos/resultados/segundo_2025-04_REAL.json`, para `OT-SRV-MPR-2025-04`, elemento CIF y etapa P4C:

| Origen | Tasa | Total | Medida de la OT | Cálculo | Parte atribuida |
|---|---:|---:|---:|---|---:|
| DES | S/ 7 | 300 | 100 | 7 × 300 × 100 ÷ 300 | S/ 700 |
| PRU | S/ 7 | 160 | 60 | 7 × 160 × 60 ÷ 160 | S/ 420 |

La prueba de Chromium recorre las matrices de cada etapa de CIF; para cada fila comprueba `base × medida ÷ total = monto_tramo` dentro de S/ 0,01 y que `monto_tramo × factor de ruta = parte de la OT`. En cada tramo final que llega a la orden comprueba que ese importe también es `base × medida ÷ total`. Además comprueba que un descuadre se presente como diferencia.

## Límite observado

En la publicación de muestra, `PD|OCIO`, etapa P2, origen MOD, inductor HORAS_MOD presenta una base de S/ 12.000 y tramos visibles por S/ 2.400; la pantalla señala la diferencia de S/ -9.600. La vista no atribuye su causa ni altera cifras: esta OT limita el trabajo a exponer las matrices del contrato. La publicación SERVITEC es sintética y no representa validación de una empresa real.

## Prueba y revisión

- `tests/test_c37_2_matrices_ruta.py`: Chromium con SERVITEC, operaciones independientes sobre la publicación, matriz por etapa y diferencia explícita.
- `tests/test_c29b_grafo.py`: conserva la comprobación del uso de `monto_tramo` en la planta.
- Pendiente de revisión: interpretar con el responsable metodológico la diferencia de `PD|OCIO` mostrada en la fuente, sin corregirla desde la interfaz.
