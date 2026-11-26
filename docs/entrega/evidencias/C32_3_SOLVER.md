# OT-C32 · Punto 3 — Exportador a Solver

## Alcance implementado

El panel Decidir ofrece una descarga Excel disponible únicamente para un resultado REAL. El libro usa el margen de contribución unitario ya publicado en `decidir.er_gerencial`, las ventas del periodo y las medidas de capacidad del contrato. No vuelve a calcular costos. Incluye las hojas `Modelo`, `Instrucciones` y `Lectura`, fórmulas `SUMPRODUCT` (mostradas por Excel en español como `SUMAPRODUCTO`) y los nombres internos locales al modelo: `solver_opt`, `solver_adj`, `solver_lhs1..n`, `solver_rel1..n`, `solver_rhs1..n`, `solver_num`, `solver_typ=1`, `solver_lin=1`, `solver_neg=1` y `solver_eng=2` (Simplex). Añade también nombres de rango `solver_rel` y `solver_rhs` para facilitar inspección.

El mínimo de demanda empieza en cero y el máximo en 1.5 veces la venta REAL; ambas celdas se marcan SUPUESTO y quedan editables. Las restricciones de recurso se exportan solo si hay trazas que relacionan el recurso/actividad y medidas `OBJ` para las órdenes involucradas. No se infieren consumos ante datos incompletos.

## Evidencia de prueba

Comando focalizado:

```sh
PYTHONPATH=src /tmp/reyna-c32-2-venv/bin/python -m pytest -q tests/test_c32_3_solver.py
```

Resultado: **3 pruebas aprobadas**. `openpyxl` comprobó fórmulas, nombres definidos y el libro de Frenosa; `scipy.optimize.linprog` evaluó el caso independiente:

| Producto | MC unitario | Máquina | Mano de obra | Venta de referencia |
|---|---:|---:|---:|---:|
| A | S/ 30 | 2 h/unidad | 1 h/unidad | 100 u |
| B | S/ 20 | 1 h/unidad | 1 h/unidad | 100 u |

Con capacidades de 100 h máquina y 80 h de mano de obra, el óptimo esperado y observado es **A = 20, B = 60, MC = S/ 1,800**.

Compuerta final `python tools/verificar.py`: **COMPUERTA: VERDE**, 489 pruebas aprobadas, 1 advertencia y 26 subpruebas aprobadas; el contrato de resultados cumple.

## Límites y siguiente comprobación

Frenosa 2010-07 no publica filas `MEDIDA` de nivel `CAP`; por eso su libro de Solver muestra una advertencia y no inventa capacidad. La prueba valida la estructura OOXML de los nombres y la optimización del caso manual, pero no ejecuta Solver en Excel nativo. La siguiente comprobación es abrir el archivo en Excel, verificar que el complemento cargue la configuración guardada y solicitar el Informe de sensibilidad; también hace falta un resultado empresarial con `CAP` y medidas `OBJ` completas.
