# D9 · decisión semántica de cuentas

**Fecha:** 20 de noviembre de 2026 (hora de Lima).

**Ámbito:** interpretación metodológica y corrección técnica acotada en `desarrollo/mvp-ola3`.

## Decisión del propietario

El propietario indicó que la semántica debe seguir el libro MCD de Tino Reyna y autorizó proceder. Para este trabajo, las tablas físicas `CTA_*` que representan saldos de entidades se tratan como cuentas impactadas por eventos: el evento aceptado actualiza el saldo afectado, y el cierre verifica y concilia esos saldos. El cierre no reemplaza esas mismas filas con una reconstrucción agregada.

`CTA_ACTOR` conserva su propósito conductual y queda fuera de las cifras de costo, aunque también registre el efecto de hechos del actor. Un informe o agregado auxiliar para acelerar consultas puede existir como proyección derivada y reconstruible; debe distinguirse de la cuenta operativa.

## Fundamento consultado

- *Modelamiento Conceptual de Datos* (MCD, edición 2025), p. 194, §6.2.1: el saldo representa el resultado neto de los eventos que afectan a una entidad. Las explicaciones de cuentas y acumuladores también aparecen en la p. impresa 13 (página 37 del PDF) y pp. impresas 18–19 (páginas 99–100 del PDF).
- *Administración de Bases de Datos* (DBD), p. 75: las tablas maestras mantienen saldos y se actualizan transaccionalmente cuando un evento los afecta.
- DBD, pp. 44–45, admite tablas físicas suplementarias para consultas críticas si se controla la redundancia; p. 171 explica que una vista no conserva datos propios y puede ser más lenta. Esa recomendación puede servir para proyecciones, pero no determina por sí sola que las siete cuentas actuales sean solo proyecciones de cierre.

## Relación con el diseño histórico

El documento recuperado de Claude `DBD_4f_Alineacion_I0b!A23:G31` clasificaba las siete tablas como `SUPLEMENTARIA (cierre, D-I0b-1)` y dejaba la decisión pendiente. Esa etiqueta queda preservada como evidencia histórica, pero la instrucción metodológica posterior del propietario resuelve la semántica de estas cuentas siguiendo MCD. No se altera el archivo histórico ni el libro DBD.

Por tanto, el requisito de cierre de D-I0b-1 que proponía regenerar las mismas cuentas a partir de un resultado agregado no se aplica a las cuentas operativas aquí interpretadas. El cierre conserva su función de validación y conciliación. Una futura proyección derivada tendría nombre, fuente, regla de reconstrucción y estado propios.

## Cambio técnico aplicado en el piloto

Los servicios configurados por DBD continúan usando el motor genérico Python `m_ACUMULAR` y `m_ACTUALIZAR`; no se codificaron métodos de costo ni nombres de cuenta individuales. Se corrigió el ámbito de escritura de las tablas `CTA_*` para que una búsqueda y actualización queden limitadas a la empresa (`*_EMP`) del evento. Al crear una fila, el motor registra esa empresa incluso cuando la clave DBD no la incluye; cuando DBD sí la asigna, verifica que coincida con el evento. La resolución de la columna se deriva del esquema.

La corrección no cambia el XLSX fuente, las reglas del DBD ni VBA. No incorpora SQLite ni un escritor nuevo de cierre. Las cuentas siguen actualizándose dentro de la transacción del evento; un fallo revierte los cambios de saldo junto con el resto de ese evento.

## Evidencia reproducible

Las pruebas nuevas en `tests/test_d9_event_accounts.py` usan copias temporales de `tests/fixtures/ola1/Sistema_Costos.xlsx` y cubren:

1. Filas A y B con las mismas claves de negocio en `CTA_OBJ_REC` y `CTA_GASTO`: el evento de B conserva A intacta y registra/actualiza solo B. `CTA_OBJ_PER` también conserva su fila A.
2. Repetición de la misma solicitud: devuelve el recibo existente y no altera ninguna de las siete hojas `CTA_*`.
3. Excepción inyectada después de escribir `CTA_OBJ_REC`: la transacción revierte las siete cuentas y las tablas de movimiento/inventario del evento.
4. Prueba de `m_ACTUALIZAR` con dos empresas y una clave DBD que omite empresa: solo cambia el saldo de B.

Los importes comprobados en este fixture (`CTA_OBJ_PER`, `CTA_OBJ_REC`, `CTA_GASTO`) son valores de regresión del recorrido configurado. **No son un oráculo independiente ni una aceptación contable.** El detalle de la línea base histórica O-1 sigue en [D9_MATRIZ_Y_CASO.md](D9_MATRIZ_Y_CASO.md) y [D9_CONTROL_O1.csv](D9_CONTROL_O1.csv).

## Pendiente para declarar D9 conciliado

- Crear un caso persistido que contenga hechos, las cuentas afectadas y el resultado de método en el mismo libro, con esperado independiente de la implementación que se prueba.
- Definir por campo fuente del importe/cantidad, signo, clave completa, periodo, moneda, redondeo, reversión y tratamiento de correcciones.
- Obtener las dimensiones fuente necesarias para conciliar `CTA_GASTO`, `CTA_FUNCION` y `CTA_OBJ_REC`; no distribuir totales de O-1 ni inventar claves.
- Verificar duplicados de clave dentro de una empresa, causalidad entre BITACORA, evento, línea y servicio DBD, y recuperación/reapertura a través del cierre.
- Mantener bloqueado el resultado contable oficial hasta completar la conciliación independiente.
