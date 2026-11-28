# AUDITORÍA MN 1 · sospechas S1–S9 probadas contra el motor real (28/11/2026)

## Resumen (10 líneas)
1. Las 9 sospechas se convirtieron en pruebas (`pruebas_auditoria/`) y se corrieron contra `calculo_local.calcular()` real.
2. Escenario: copias de SERVITEC_sintetico.xlsx, julio 2025, REAL. Base sin cambios: REB 22,975 · MPR 5,165 · total 28,140.
3. **9 de 9 CONFIRMADAS** en el código. Cada prueba tiene un control sin defecto que pasa, así que el escenario es válido.
4. CRÍTICAS (5): S1, S2, S3 y S4 dan un costo incorrecto sin aviso; S6 hace que el panel diga OK en todos esos casos.
5. S1: un TRE_ELE mal escrito («IND » o «Ind») borra S/ 9,000 de indirectos (total 19,140) y el panel sigue en OK.
6. S4 es peor de lo sospechado: el material negativo de REB (−420) cae en **otra orden** (MPR baja de 840 a 420).
7. ALTA (1): S7. Se puede editar el JSON del cierre a «REVISADO» y la gerencia lo aprueba sin revisión de contabilidad.
8. MEDIA (1): S5. «3 kg» en LIN_EXC se vuelve 0; el total no cambia, pero la pérdida de 126 pasa a costo normal.
9. BAJAS (2): S8 (5 de 30 en el código; 0 de 2 con el calcular real) y S9 (crece lineal; 50 órdenes = 3.6 s).
10. No se modificó código del repo. Lo que no se llegó a medir va como POR VERIFICAR (al final).

Severidad: CRÍTICO = costo incorrecto o pérdida de datos · ALTO = falla de control o de puesta en marcha · MEDIO · BAJO.
Cómo correr todo: `python3.11 -I pruebas_auditoria/correr_auditoria.py <repo>` (unos 4 min). Imprime CONFIRMADO o SOSPECHA por prueba.

---

## Hallazgos confirmados, por severidad

### CRÍTICO

**S1 · Un elemento de costo no reconocido se descarta en silencio** — `metodos/reparto_etapas.py:57` (ELEM) y `:140` (`continue`).
| Prueba | Cambio | Resultado hoy | Correcto |
|---|---|---|---|
| S1a | ADM01 con tipo nuevo, TRE_ELE = ADM (valor que `libro_dbd.py:24` documenta) | total 26,140; administración 0 en las órdenes **y** en el estado de resultados | 28,140 o rechazo |
| S1b | TRE_ELE de INDIRECTO = «IND » (espacio al final) | total 19,140 (faltan ALQ, ENE, SUP y ADM01: S/ 9,000) | 28,140 o rechazo |
| S1c | TRE_ELE = «Ind» | igual que S1b | 28,140 o rechazo |
| control | tipo nuevo con TRE_ELE = IND | 22,975 / 5,165 (OK) | — |

**S2 · Una línea con LIN_MTO pero sin LIN_CU_DOC vale 0** — `reparto_etapas.py:151` usa solo cantidad × costo unitario.
- Energía de julio (evento 55, LIN_MTO 1,500) sin LIN_CU_DOC: total 26,640 (REB 21,737.50 · MPR 4,902.50), sin aviso. Control con LIN_CU_DOC = 1,500: base exacta.
- **Corrección a la sospecha:** `variable.py:112` **no** usa LIN_MTO primero. Usa la valuación del kardex y, si no hay, cantidad × LIN_CU_DOC, igual que el reparto. Solo `flujo.py:93` (`ajustes_compra`) usa LIN_MTO primero. Esto sale de leer el código; no tiene prueba propia.

**S3 · Una compra sin LIN_MTO entra al kardex derivado a valor 0** — `reyna_local/flujo.py:62`.
- Se quitó la fila del evento 50 de KARDEX y se dejó LIN_MTO vacío (200 × 43). La entrada vale 0 y la salida a REB se valúa a 13.33 en lugar de 42. Resultado: REB 18,675 · MPR 4,591.67. Ningún control del panel lo marca (S6c).
- Control: sin la fila de KARDEX pero con LIN_MTO, el kardex derivado da la base exacta.

**S4 · Un exceso de merma mayor que el consumo pasa sin rechazo y mueve costo a otra orden** — `reparto_etapas.py:147` y `:148`.
- LIN_EXC = 160 con LIN_CAN = 150 en REB. Pérdida de REB 6,720 (160 × 42, más de lo consumido). El material normal −420 entra al criterio CONSUMO, que filtra los destinos > 0, y **se lo queda MPR**: su MD baja de 840 a 420 y su costo, de 5,165 a 4,745. El total sigue en 28,140 y los 9 controles dan OK.
- Severidad elevada de ALTO (tentativa) a CRÍTICO: da el costo equivocado de una orden que no tiene el error.
- Control: LIN_EXC = 10 → MD 5,880 y pérdida 420 (correcto).

**S6 · El control de conservación no detecta lo que se pierde a la entrada** — `reyna_local/resultados.py:349-353`.
- Con S1a faltan 2,000 y con S2 faltan 1,500; en los dos casos el control «Conservación del reparto» da OK (26,140 = 26,140; 26,640 = 26,640).
- Con S3 (compra a 0), **todos** los controles del panel dan OK, incluido «Salidas del kardex = material de las órdenes + merma», porque las dos cifras salen del mismo kardex mal valuado.
- Severidad elevada de ALTO a CRÍTICO: es el control que se presenta como garantía y hoy no puede fallar por estas causas.

### ALTO

**S7 · El cierre no sella el estado ni el historial** — `reyna_local/cierre.py:141`.
- Se emitió el cierre real de julio. Para que la conciliación no lo bloqueara se agregó CTA_OBJ_PER.COP_PERD = 126 (ver observación 1).
- S7a: estado «APROBADO» más una aprobación falsa en el historial → `verificar()` da INTEGRO.
- S7b: estado «REVISADO» puesto a mano (sin contabilidad) → `accion(APROBAR, GERENTE)` lo acepta. El historial queda [EMITIR, APROBAR].
- S7c: se reescribe quién emitió → INTEGRO. Con eso se burla la separación de funciones (`cierre.py:130-131`).
- Controles: el paquete recién emitido da INTEGRO, y una cifra alterada da ALTERADO (la huella sí protege el contenido).

### MEDIO

**S5 · Un exceso de merma escrito como texto se vuelve 0** — `reyna_local/resultados.py:21-22`.
- LIN_EXC = «3 kg»: pérdida 0 (con 3 sería 126) y MD normal 6,300 (sería 6,174). El total de la orden no cambia, pero la pérdida anormal (NIC 2 §16 a) desaparece del estado de resultados y se capitaliza. No hay aviso.

### BAJO

**S8 · Dos emisiones simultáneas: la segunda pisa a la primera** — `cierre.py:104-115`.
- Con resultados ya calculados (sin espera), en 30 pares lanzados a la vez, **5** terminaron con dos respuestas «versión 1» y un solo archivo. La ventana medida entre `listar()` y la escritura es de unos 4 ms.
- Con el calcular real: 0 de 2 pares. El `_lock` de `calculo_local.calcular()` serializa el cálculo y, de rebote, separa las escrituras. La protección es accidental: depende de que emitir llame a calcular.
- Baja de MEDIO a BAJO por la poca probabilidad en el uso real. `accion()` tiene el mismo patrón leer-modificar-escribir y no se probó.

**S9 · Las trazas recalculan el reparto por cada orden y elemento** — `resultados.py:287` y `reparto_etapas.py:386`.
| Órdenes | Llamadas a `correr()` | `calcular()` |
|---|---|---|
| 2 | 31 | 2.8 s |
| 10 | 91 | 3.0 s |
| 20 | 171 | 3.1 s |
| 50 | 411 | 3.6 s |
- Confirmado que las llamadas crecen (unas 8 por orden). Con 50 órdenes el tiempo sigue siendo bajo, así que baja de ALTO a BAJO **con los datos medidos**. POR VERIFICAR: la corrida con 100, 200 y 400 órdenes se interrumpió y no hay cifras. Las órdenes sintéticas no tienen material propio; el costo de cada `correr()` crece con las aristas, por lo que con cientos de órdenes podría volverse cuadrático.

---

## Sospechas que no se pudieron reproducir
Ninguna del todo. La parte de S8 con el calcular real (0 de 2) y la de S9 con cientos de órdenes (no medida) quedan como SOSPECHA dentro de hallazgos ya confirmados.

## Observaciones de la auditoría (no son sospechas)
1. **El cierre de julio de SERVITEC no se puede emitir tal como viene el libro.** La conciliación compara la merma del costeo (126) con CTA_OBJ_PER.COP_PERD, que está vacía, y bloquea. Hay que decidir si el libro de ejemplo debe traer esa cuenta o si la conciliación no debe aplicarse cuando el motor operativo no la llevó.
2. Las líneas citadas en SOSPECHAS_AUDITORIA.md coinciden con esta copia del repo, salvo `variable.py:112` (ver S2).

## Correcciones propuestas (sin aplicar: el código es de otro agente)
- S1–S3: una sola función «importe de la línea» (LIN_MTO; si falta, cantidad × costo unitario; si faltan los dos, error). `validar()` debe aceptar solo los TRE_ELE que el motor reconoce (normalizando mayúsculas y espacios) y `_origenes()` debe levantar `Rechazo` en vez de `continue`.
- S4–S5: validar `0 ≤ LIN_EXC ≤ LIN_CAN` y numérico, en `validar()` y en `previos()`.
- S6: comparar contra un total independiente: Σ importe de las líneas del periodo con efecto en costo + salidas valorizadas del kardex, con el kardex valuado desde LINEA.
- S7: incluir estado e historial en una huella encadenada (cada paso sella el anterior).
- S8: crear el archivo con `open(..., "x")` y tomar un bloqueo propio en emitir() y accion().
- S9: calcular las aristas una vez y trazar todas las órdenes sobre ellas.

## Lo que queda POR VERIFICAR
| Punto | Qué falta |
|---|---|
| S9 | Medir con 100, 200 y 400 órdenes: `AUDIT_S9_N=2,100,200,400 python3.11 -m unittest test_S9_trazas_cuadraticas` |
| S8 | Más intentos con el calcular real (`AUDIT_S8_REALES`) y una prueba de `accion()` concurrente |
| S2 | Prueba propia del comportamiento de `variable.py` (hoy solo hay lectura de código) |
