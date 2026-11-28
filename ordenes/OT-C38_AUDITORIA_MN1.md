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
