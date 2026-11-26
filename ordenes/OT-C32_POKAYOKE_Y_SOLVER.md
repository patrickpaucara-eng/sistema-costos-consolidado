# OT-C32 · Poka-yoke de códigos y exportador a Solver — Codex nivel MEDIO (después de subir C31 puntos 2, 4, 5 y 6)
Base: `desarrollo/mono` último. Decisiones del dueño 26-nov. Una rama y un PR por punto; solo tus pruebas mientras trabajas; compuerta completa al final, UNA rama a la vez.

## 1 · CRÍTICO — Código de OT asignado por el sistema (poka-yoke)
- Nadie teclea el código de una OT. El sistema lo asigna: `OT-<EMP>-<PRODUCTO>-<NNNN>` (correlativo por empresa y producto, 4 dígitos, sin huecos aunque haya rechazos).
- `store.aceptar_cotizacion`: `objeto` deja de ser obligatorio; si no viene, se genera; si viene, se ignora y se informa el asignado en la respuesta. En la pantalla del cotizador el campo «Código de la OT» se muestra lleno y bloqueado.
- Formulario guiado: en T13 (y toda transacción que cree OBJETO) el campo OBJ aparece precargado con el siguiente código y en solo lectura.
- Prueba: dos aceptaciones seguidas dan `...-0001` y `...-0002`; un rechazo no consume número.

## 2 · CRÍTICO — Clave única en el motor (defensa en profundidad, RA-32)
- En `src/reyna_local/motor_espejo.py`, método de tipo CREAR: si la tabla destino ya tiene una fila con la misma clave primaria (primera columna, o las columnas K de MCA si las hay), la transacción falla con «ya existe <tabla> <clave>» y se revierte.
- Antes de cambiar, corre TODAS las pruebas: si alguna creación legítima repite clave (versiones, acumulados), exclúyela explícitamente y documéntalo en REGLAS_APRENDIDAS.md.
- Prueba: T13 directo con un código existente → error y libro sin cambios.

## 3 · ALTO — Exportar a Excel para Solver (mezcla con varias restricciones)
- Nuevo tipo de exportación `solver` (`exportar.py`), botón en el panel Decidir. Datos del resultado REAL: MC unitario por producto (`decidir.er_gerencial`), consumo por unidad de cada recurso/actividad con capacidad (trazas + MEDIDA CAP), capacidades; demanda máx./mín. por producto = editable (por defecto: máx. = 1.5 × vendido, mín. = 0; celdas marcadas SUPUESTO).
- Hoja «Modelo» con fórmulas (SUMAPRODUCTO) ya enlazadas; modelo de Solver guardado en el libro (nombres definidos `solver_opt`, `solver_adj`, `solver_lhs1..n`, `solver_rel`, `solver_rhs`, `solver_typ=1`, `solver_lin=1` del complemento Solver), para que el usuario solo pulse «Resolver».
- Hoja «Instrucciones»: 3 pasos, incluido marcar **Informe de sensibilidad**; hoja «Lectura»: precio sombra = valor de una unidad más del recurso; la solución es óptima solo dentro de los rangos «aumento/disminución permitidos»; fuera de ellos hay que volver a resolver.
- Prueba: con openpyxl, las fórmulas existen, los nombres de Solver están definidos y un caso a mano (2 productos, 2 recursos) evaluado con `scipy.optimize.linprog` en la prueba da la mezcla esperada.
  Caso a mano: A MC 30/u, B MC 20/u; máquina: A 2 h, B 1 h, cap. 100 h; mano de obra: A 1 h, B 1 h, cap. 80 h → óptimo **A = 20, B = 60, MC = 1,800**.

## 4 · MEDIO — Una sola restricción en el panel Decidir
- Elegir el recurso escaso → ordenar productos por MC por unidad de ese recurso → asignar capacidad en ese orden hasta la demanda máxima.
- Caso a mano: solo la máquina (100 h), demanda máx. A 40, B 70: MC/h A = 15, B = 20 → B 70 u (70 h), A 15 u (30 h) → MC = 1,850.

## 5 · BAJO — Seguir procesando o vender
- Calculadora en el panel Decidir: ingreso incremental − costo incremental después del punto de separación → «procesar» si > 0. Caso: vender a 10 o procesar con costo 3 y vender a 14 → +1 por unidad → PROCESAR.
