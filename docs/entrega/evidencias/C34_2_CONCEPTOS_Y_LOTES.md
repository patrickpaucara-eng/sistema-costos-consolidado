# C34-2 · Conceptos adicionales y preparación por lote

**Dependencia:** apilado sobre `codex/C34-1`; usa la rama anterior hasta que se integre. **Alcance:** cálculo en un módulo independiente; la interfaz Pedido y su comparación visual quedan para C34-5.

La preparación se calcula como `cantidad × costo variable unitario + número de lotes × preparación por lote`. Un lote incompleto cuenta como lote, con `ceil(cantidad / tamaño)`. Los conceptos `SUBCONTRATO`, `TRANSPORTE` y `GASTOS_GENERALES` se aceptan como importes fijos. `CONTINGENCIA` se expresa como porcentaje entre 0 y 100 y se aplica a una base común: costo del lote más importes fijos. Varias líneas porcentuales no se componen; el orden de las líneas no altera el total.

## Caso manual independiente

50.000 cajas × S/ 0,354 = S/ 17.700 variables. Con preparación de S/ 1.200:

| Lotes | Preparación | Variable | Total | Diferencia |
|---:|---:|---:|---:|---:|
| 1 × 50.000 | S/ 1.200 | S/ 17.700 | **S/ 18.900** | referencia |
| 2 × 25.000 | S/ 2.400 | S/ 17.700 | **S/ 20.100** | **+S/ 1.200** |

Pruebas propias: `python -m unittest discover -s tests -p 'test_c34_2_costos_lote.py' -v` comprueba ambos resultados, la diferencia visible en la respuesta, el lote incompleto, conceptos y validaciones.

## Límites

- La comparación de alternativas se entrega como estructura para la interfaz que llegará en C34-5; en esta rama todavía no hay pantalla.
- No se conecta a una fuente real de tarifa ABC; recibe costo variable validado como argumento.
- Tratamiento fiscal, redondeos contractuales y bases de contingencia requieren definición por caso antes de usarse comercialmente.

## Verificación integral de la rama

Las seis pruebas propias terminaron **6/6 OK**. `python tools/verificar.py` terminó **ROJA**: 33 pruebas pasaron y falló `tests/test_c07_analitica.py::test_pantallas_analitica_y_proyeccion`; el contrato de resultados pasó. Es el mismo fallo externo a C34-1 observado en la rama base de esta pila. La compuerta no se repitió; `AGENTS.md` bloquea abrir PR hasta obtener VERDE.
