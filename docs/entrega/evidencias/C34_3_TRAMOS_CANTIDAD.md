# C34-3 · Tramos de costo variable por cantidad

**Dependencia:** apilado sobre `codex/C34-2`; las ramas previas deben integrarse antes de considerar completo este PR. **Alcance:** cálculo y tabla opcional.

La hoja opcional `COSTO_TRAMO` contiene recurso, límite inferior, límite superior y tasa marginal. Los tramos deben iniciar en cero, ser contiguos y tener tasas no negativas. El último puede quedar abierto; si se define un máximo final, una cantidad que lo exceda se rechaza. Solo se aplican a recursos declarados. En ausencia de hoja/tabla, se conserva la multiplicación lineal existente `cantidad × tasa base` sin redondeo intermedio.

## Caso manual independiente

Soldadura: 0–160 h a S/ 30/h y por encima de 160 h a S/ 45/h. Para 200 h: `160×30 + 40×45 =` **S/ 6.600**. A 160 h: **S/ 4.800**. La prueba de regresión compara la ruta sin tramos con la misma multiplicación lineal para cantidades decimales.

Pruebas propias: `python -m unittest discover -s tests -p 'test_c34_3_tramos_cantidad.py' -v`; también comprueban el libro sin hoja, guardado/lectura, varios recursos y límites incompletos.

## Límites

- La pantalla guiada de C34-5 muestra cantidades, costos y adicionales; no activa `COSTO_TRAMO`. Falta decidir qué granularidad identifica el recurso (código de recurso, material, actividad o inductor) y cómo se aplica cuando un pedido cruza varios intervalos proyectados. La función queda probada aislada hasta cerrar ese contrato.
- Se interpreta el contrato como tramos marginales progresivos; aplicar la última tarifa a toda la cantidad sería otro contrato y cambiaría el caso manual.
- El modelo no contempla negociación, descuentos retroactivos ni cambios simultáneos de pedidos; no forma parte de este punto.

## Verificación integral de la rama

La prueba focalizada terminó **6/6 OK**. `python tools/verificar.py` terminó **COMPUERTA: VERDE**: 548 pruebas, 1 advertencia y 26 subpruebas pasaron en 850,83 s; el contrato de resultados también pasó. Incluye la cadena apilada C34-1 y C34-2, cuyos intentos individuales habían detenido la suite en el test Chromium C07. No se modificaron las pruebas existentes ni los módulos excluidos.
