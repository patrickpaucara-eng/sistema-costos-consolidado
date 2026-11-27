# C34-6 — Prueba de pedidos en cuatro rubros

## Cobertura

Cuatro pruebas separadas recorren `cotizar_pedido` desde la receta guardada en un libro XLSX mínimo hasta el costo del pedido. Cada test deja escrito su cálculo esperado con constantes independientes del resultado de la función.

| Rubro y pedido | Cálculo manual | Esperado |
|---|---|---:|
| Metalmecánica: cinco ejes, peso 1.200 kg cada uno | `(2 + 0,005×1.200) h/eje × 5 × S/20/h + S/100 preparación` | **S/ 900,00** |
| Construcción: cinco módulos de 100 m² | `5×100×0,2 bolsas/m²×S/8 + S/75 transporte + 10 %×(S/800+S/75)` | **S/ 962,50** |
| Imprenta: tiraje de 1.000 hojas | `1.000×S/0,05 papel + 0,4 h×S/30 + S/40 preparación + S/8 generales` | **S/ 110,00** |
| Servicios: cuatro consultas de dos horas | `4×(0,5+0,5×2) h×S/35 + S/50 subcontrato` | **S/ 260,00** |

El libro de cada prueba se guarda temporalmente y contiene la familia parametrizada que la lectura productiva recupera. Resultado REAL sintético, medidas de inductor y kardex están declarados explícitamente en el test; estos fixtures no pretenden validar el DBD de un proveedor ni sustituir la corrida Chromium completa de C34-5.

## Prueba

`pytest -q tests/test_c34_6_cuatro_rubros.py` → **4 passed**. Los nombres de test identifican cada rubro y cada aserción compara el costo final con su cifra manual.

## Límites

Las cuatro familias ejercitan el cálculo del pedido con actividades y materiales, costos por lote y conceptos fuera del ABC. No certifican que una empresa real tenga la parametrización, tasa, receta, calendario o datos de mercado correctos. Para operar, se requiere revisar el REAL, las medidas y las reglas del libro propio.
