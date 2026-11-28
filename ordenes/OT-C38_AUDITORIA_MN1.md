# OT-C38 — Correcciones confirmadas por la auditoría independiente (MN 01)

Base: `desarrollo/mono` con C37 unida (si C37 aún corre, C38-1 a C38-3 pueden ir en paralelo: tocan el motor de entrada, no pantallas). Origen: `docs/entrega/evidencias/AUDITORIA_MN1.md` y `tests/auditoria_mn1/` (9 hallazgos CONFIRMADOS contra el motor real, cada uno con control sin defecto).
Reglas de siempre (rama `codex/C38-N`, PR por punto, nunca fusionar ni main, compuerta una vez al final). **Excepción autorizada por el dueño: esta orden SÍ toca el cálculo** (`flujo.py`, `libro_dbd.py`, `resultados.py`, `cierre.py`, y en C38-1/C38-4 la normalización de entrada de `reparto_etapas.py`); cada cambio de cálculo exige su prueba de la auditoría en verde y el oráculo SERVITEC (`tests/datos/oraculo_servitec`) en 0.00.
Criterio de aceptación de cada punto: la prueba `tests/auditoria_mn1/test_SN_*.py` pasa a demostrar la corrección (adaptar su aserción final de «el defecto ocurre» a «el defecto ya no ocurre», declarándolo en el PR) y su control sin defecto sigue igual.

## C38-1 (CRÍTICO, S1) Elemento de costo no reconocido
Normalizar TRE_ELE (quitar espacios, mayúsculas) al cargar; un elemento fuera del catálogo se **rechaza en `validar()`** con hoja, fila y valor. Nunca se descarta en silencio.
## C38-2 (CRÍTICO, S2) Línea con monto y sin costo unitario
Regla única para el valor de una línea en `flujo.py`, `variable.py` y reparto: monto si existe; si no, cantidad × costo unitario; si faltan ambos, rechazo con mensaje.
## C38-3 (CRÍTICO, S3) Compra sin monto entra a valor 0
Rechazo en validación (la compra sin valor no entra al kardex). Material de la prueba vuelve a 42.
## C38-4 (CRÍTICO, S4) Exceso de merma mayor que el consumo
Rechazo con mensaje; nunca material negativo. Prueba: MPR vuelve a 5,165.
## C38-5 (CRÍTICO, S6) Control de conservación que no controla
Agregar control «registrado en el libro = entrado al reparto» por elemento (además del actual «entrado = llegado a las órdenes»). Con S1–S3 debe dar DIFERENCIA.
## C38-6 (MEDIO, S5) Exceso de merma escrito como texto
«3 kg» → rechazo con mensaje, no 0.
## C38-7 (ALTO, S7) Sello del cierre sin estado ni historial
La huella del paquete incluye estado e historial de aprobaciones; editar el JSON invalida el sello.
## C38-8 (BAJO, S8) Dos emisiones simultáneas
Bloqueo en `cierre.emitir()` (mismo candado que el cálculo) y versión asignada dentro del bloqueo.
## C38-9 (BAJO, S9) Trazas
Solo medir con 100–400 órdenes (`correr_auditoria.py`) y dejar el tiempo en la evidencia; optimizar solo si supera 30 s con 200 órdenes.
## C38-10 Libro SERVITEC cerrable
`casos/segundo/generar.py` agrega la cuenta de merma del motor operativo (126) que hoy impide emitir el cierre de julio. Las cifras REB 22,975 / MPR 5,165 no cambian.
Reporte final: PRs, compuerta, estado de cada prueba de auditoría.

## Diseño preciso (Claude, 28-nov) — seguirlo al pie de la letra
**Cifra ancla SERVITEC julio:** total del periodo = **28,140** (REB 22,975 + MPR 5,165). Toda corrección debe dejar este número intacto con el libro sano.

- **C38-1 (S1):** en `libro_dbd.validar()` normalizar `TRE_ELE` con `strip().upper()` y compararlo contra el dominio {MD, MAT, PD, MOD, SD, IND} (más los que declare el DBD como sinónimos). Un valor fuera del dominio → rechazo «TIPO_RECURSO fila N: elemento «X» no reconocido». En `reparto_etapas._origenes` NO cambiar la lógica; solo recibe valores ya normalizados.
- **C38-2 (S2), una sola regla de valor de línea** en una función nueva `valor_linea(linea)` en `flujo.py`, usada por `flujo.py`, `variable.py` y (solo esa llamada) `reparto_etapas.py:151`: si `LIN_MTO` es número → `LIN_MTO`; si no, si `LIN_CAN` y `LIN_CU_DOC` son números → producto; si no → rechazo «LINEA evento E número N: falta monto o costo unitario». Si existen los dos y difieren en más de 0.01 → rechazo (dato contradictorio), nunca elegir uno en silencio. Caso: energía julio con solo LIN_MTO 1,500 → total vuelve a 28,140.
- **C38-3 (S3):** compra (entrada al almacén) con valor no determinable por `valor_linea` → rechazo en validación; nunca entra al kardex a 0. Caso: REB 22,975, material a 42.
- **C38-4 (S4):** `LIN_EXC > LIN_CAN` o `LIN_EXC < 0` → rechazo «exceso mayor que lo consumido». Caso con LIN_EXC = 160 y LIN_CAN = 150: rechazo; con 10: MD 5,880 y pérdida 420.
- **C38-5 (S6), control nuevo independiente** en `resultados._control`, ANTES del actual: «Registrado en el libro = entrado al reparto», por elemento. *Registrado* = Σ `valor_linea` de las líneas del periodo con efecto en costo (MD por salidas valorizadas con el kardex valuado desde LINEA, no desde la hoja KARDEX; PD, SD, IND por `valor_linea`). *Entrado* = Σ aristas con `org_tipo == "REC"`. Tolerancia 0.05 por elemento. Con S1/S2/S3 debe dar diferencia (2,000 · 1,500 · la del kardex); con el libro sano, 0.
- **C38-7 (S7):** la huella del paquete de cierre se calcula sobre {resultado, estado, historial de aprobaciones con usuario y fecha}; `verificar` recalcula y compara. Editar el estado a mano → «sello inválido».
- **Orden de commits sugerido:** C38-2 primero (crea `valor_linea`), luego C38-1, 3, 4, 5. C38-5 es el que más protege: no lo saltes.
