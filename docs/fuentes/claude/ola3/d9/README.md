# Evidencia histórica de D9 · cuentas suplementarias

Estos cuatro archivos se copiaron en modo lectura desde `patrickpaucara-eng/sistema-costos-reyna`, rama `desarrollo/deuda` en `0b8f63cef1a94ab7602d880a814ce068b4d7a814` (16 de noviembre de 2026). El manifiesto verifica las copias. Se conservaron para continuidad; no se ejecutó ni se integró su código al motor del consolidado.

## Qué documenta la rama histórica

- `DIAGNOSTICO_GLOBAL_2026-11-16.md` ubica D9 entre las deudas de cálculo del grupo E. Declara que requiere cambiar el origen de las cuentas, no solo añadir una prueba.
- `ESCRITORES_CUENTAS_2026-11-16.md` enumera siete tablas `CTA_*`, sus servicios escritores y transacciones. Reporta de 1 a 7 servicios escritores en línea o en T23.x; el cierre que publica `RESULTADO_METODO` no escribe dichas cuentas. El caso O-1 no contiene las siete hojas.
- `test_cuadre_cuentas_historico.py` define 14 casos estrictos pendientes: uno de escritor único y uno de cuadre por cada tabla. Añade pruebas del informe, los escritores presentes y los conceptos publicados.
- `escritores_historico.py` genera el inventario y la comparación usada por ese informe y sus pruebas.

## Contraste con MCD/DBD

La copia del DBD de Tino, leída directamente, explica en pp. 44–45 que se pueden crear tablas suplementarias para simplificar consultas críticas sin sacrificar la información original, con redundancia controlada. La p. 171 indica que las vistas no tienen datos propios y pueden ser más lentas. Eso sustenta investigar materialización; no define por sí solo qué importe debe ir a cada cuenta.

La propuesta histórica D-I0b-1 dispone cuentas físicas suplementarias, escritas una vez en el cierre, y cuadre con `RESULTADO_METODO`. La siguiente implementación necesita fijar para cada tabla el concepto/fuente, llave, periodo, signo, agregación, redondeo y política de reversión; validar los campos contra MCD/DBD y cerrar con un caso numérico independiente. `CTA_ACTOR` no tiene una correspondencia de costo en los resultados V4.1 listados en el informe; se debe mantener fuera del MVP de costos hasta definir su función de comportamiento.

## Consecuencia para el MVP

El cierre técnico que se implementó en el consolidado ejecuta los pasos marcados `OFICIAL` o `CIERRE` en `CIERRE_PASO` y persiste la cadena como una unidad. El libro de prueba define T23.1, T23.2, T23.3, T23.5 y T23.9. No incorpora el escritor suplementario D9. Por ello, el cierre visible **no** se presenta como cierre contable conciliado ni como costo integral oficial.

El requisito D9 queda como siguiente tarea crítica del [plan de ejecución](../../../../entrega/PLAN_MVP_Y_PENDIENTES.md). No copiar las pruebas con marcas `xfail` al conjunto aceptado: sirven como contrato histórico y deben convertirse en casos que pasan después de especificar el diseño.
