# BITÁCORA · Sistema de planeamiento B (MN 02)

Regla fija: **spec.py manda** (B0–B9, eventos, tickets, R1–R9, PARAMS). No se cambia la arquitectura. Todo valor marcado S es un supuesto declarado. Nada de datos reales de empresas.

Entorno de prueba: Python 3.11 · PuLP 2.9.0 (trae CBC) solo en `calculadora.py`.

---

## Piezas 1–3 · casos_B.xlsx, calculadora.py (+ test), mn02_borrador.docx — 28/11/2026

### Qué se hizo
- **calculadora.py** (B4): `plan(datos) -> dict`. Es un modelo lineal entero mixto con R1–R9. Devuelve el programa, las tardanzas, el financiamiento, las compras, las inversiones elegidas, la caja, la utilidad descontada con sus componentes y, por cada restricción, si está activa, su holgura y su costo (re-resolviendo sin ella). Si no hay solución, re-resuelve con holguras artificiales y dice en castellano qué restricción lo impide; nunca devuelve una traza técnica.
- Ayudas en el mismo archivo (solo para probar los casos; sus dueños definitivos son las piezas 5, 6 y 7): `desviacion()` (B7), `parametro_vigente()` y `cambiar_parametro()` (B0), `evaluar_inversion()` (B6/B8) y `estados_proyectados()` (B8).
- **test_calculadora.py**: 12 pruebas, una por caso, más la prueba de tiempo. Corre con `python -m unittest -v test_calculadora.py`.
- **casos_B.xlsx**: 12 hojas más un Índice. En total tiene 466 fórmulas y 0 errores, recalculadas con LibreOffice. Cada hoja tiene datos, cálculo, resultado esperado y la columna «¿Coincide?» contra lo que devuelve la calculadora. Los 12 casos dan OK.
- **mn02_borrador.docx**: 7 páginas, con fuentes.

### Tiempo medido (una corrida, en el entorno de prueba)
50 OT × 4 recursos × 12 periodos, con semilla 2026:
- plan: unos 5 s;
- plan más el costo de cada restricción: unos 32 s (son 6 re-solves).

### Dict de entrada (contrato que usarán las piezas siguientes)
```
periodos, hoy, caja_inicial, caja_minima, tasa_prestamo, tasa_descuento, limite_prestamo,
plazo_cobro, flujos_externos{t: S/}, tiempo_max, analisis,
recursos{id: {capacidad: n|[n..], costo_hora}},
materiales{id: {stock, costo, llegadas{t: q}, compra{permitida, ventanas[t], plazo, costo}}},
ot[{id, cantidad, horas_unidad{r: h}, material_unidad{m: u}, precio, entrega, multa, estado, plazo_cobro}],
inversiones[{id, costo, recurso, capacidad, periodo, periodo_pago, vida_util, valor_residual, estado}],
incompatibles[(a, b)]
```
Las tasas y la caja mínima aceptan un escalar, una lista de T valores o un dict `{t: v}`.

### Supuestos agregados
1. Una OT se hace completa dentro de un periodo y en un solo recurso (R3).
2. R5 es conservadora: con el par (a, b), b no puede ir ni en el mismo periodo que a ni en el siguiente, en el mismo recurso.
3. La multa es por **periodo** de tardanza (por defecto, 1 % del precio). PARAMS la define por día.
4. El préstamo es a un periodo: se toma en t y se devuelve en t+1 con la tasa de t. Lo que queda al final del horizonte se reporta como `deuda_final`.
5. Momentos de pago:
   - la conversión se paga en el periodo de producción;
   - el material, al llegar;
   - el cobro entra `plazo_cobro` periodos después de terminar la OT;
   - la multa rebaja el cobro.
6. `flujos_externos` (cobros y pagos ya comprometidos) mueven la caja pero no la utilidad.
7. Inversiones:
   - su capacidad cuenta desde el periodo de instalación y dura `vida_util` periodos;
   - el valor residual es un dato explícito;
   - se pagan en el periodo de instalación, salvo que se dé `periodo_pago`.
8. El stock inicial no es costo en el objetivo (ya está pagado), pero sí entra al costo de ventas en B8.
9. El IR (29.5 %) se devenga por periodo y se paga fuera del horizonte. No hay pagos a cuenta y las pérdidas no generan crédito.
10. Desempate: a igual valor, la calculadora prefiere el periodo más temprano y el menor préstamo (ε = 1e-6).
11. Los casos que no prueban descuento (a–e, h–l) usan una tasa de descuento de 0, para que se verifiquen con calculadora de mano.
12. La desviación dispara solo si es **mayor** que el umbral (igual no dispara).
13. Vigencia: el valor viejo se cierra el día anterior al nuevo «desde».
14. Diagnóstico de infactibilidad: usa pesos fijos por familia (R1 = 1, R2 = 1, R3 = 1000, R5 = 100, R8 = 0.01).

### Preguntas abiertas
1. **R5**: ¿la incompatibilidad es «inmediatamente después» dentro del periodo, o exige limpieza? ¿Se puede ordenar dentro del periodo?
2. **R3**: «un recurso por vez», ¿quiere decir una sola máquina, o una ruta que pasa por varias actividades en secuencia?
3. ¿Una OT puede partirse entre periodos o en lotes?
4. La multa está en «S/ por día y OT», pero el periodo base es la semana. ¿Se multiplica por los días hábiles?
5. La caja mínima es «un mes de costos fijos», pero EXT no trae costos fijos. ¿Quién los publica?
6. CPPC: faltan Ke, Kd, D y E. ¿Los da finanzas como parámetros de B0?
7. **B7**: ¿la desviación se mide en horas, unidades, costo o fecha? ¿Por ticket o en total?
8. Préstamo: ¿cuál es el plazo real, el límite de la línea y la comisión?
9. ~~Referencia de Tino Reyna~~ **Resuelta con el repo**: MCD §3.4 (evento) y TECNIA 2016, pp. 84-85 (ticket). Sigue POR VERIFICAR el título del artículo de TECNIA.
10. **contrato.py / resultados_ejemplo.json** (llegaron con la segunda ola): traen actividades (costo, inductor, tasa) y objetos (OT con cantidad y costos). **No traen** capacidad práctica, receta por producto (horas y material por unidad), fecha de entrega ni avance de las órdenes, que EXT de spec.py sí pide. ¿A los agregará al contrato? Esto bloquea parte de la pieza 12.
11. ¿B4 debe usar la tasa ABC completa como costo por hora, o solo su parte variable?
12. «Tiempo real»: ¿cuántos segundos son aceptables para recalcular?

### Cómo se conecta
- B2 (pieza 12) llena `recursos`, `ot` y las recetas.
- B1/B3 (pieza 4) cambian `estado` y `hoy`.
- B0 (pieza 5) produce tasas por periodo a partir de la vigencia.
- B5/B8 (pieza 6) leen `res["flujo"]` y `res["programa"]`.
- B7 (pieza 7) arma el estado actual y vuelve a llamar a `plan()` con `hoy`.
- Ajuste posterior (pieza 4): la calculadora rechaza estados de OT que no estén en spec.TICKETS («en curso» ya no se acepta en silencio).

---

## Pieza 4 · eventos.py (B1 y B3) + test_eventos.py — 28/11/2026

### Qué se hizo
- **B1** (`validar_forma` y la primera parte de `EstadoPlan.registrar`). Valida los 6 hechos de spec.EVENTOS. Revisa:
  - campos obligatorios por acción y campos que no existen;
  - tipos (no convierte "10" en 10);
  - fechas que existan, en formato AAAA-MM-DD, y no al revés;
  - rangos (cantidad > 0; tasa como fracción < 1);
  - que el hecho no esté fechado en el futuro;
  - documento repetido.

  Si algo falla, rechaza con un mensaje en castellano; nunca corrige en silencio. Cada rechazo queda en `rechazados` para auditoría.
- **B3** (`EstadoPlan`). Guarda los tickets OT, COMPRA, FINANCIAMIENTO e INVERSIÓN con la máquina de estados de spec.TICKETS:
  - solo se avanza;
  - una transición inválida, como «terminado» → «en ejecución», se rechaza indicando a qué estados sí se puede pasar.
- **Estado derivado**. El estado no se edita: se **reproduce** desde el estado base con todos los hechos válidos. Eso permite:
  - correcciones como hechos nuevos (`"corrige": "E-0002"`). El original queda en el registro, marcado `anulado_por`, y la corrección ocupa su lugar en la reproducción;
  - recalcular «desde el estado actual» sin encadenar deltas (METODO_PLANEAMIENTO.md §3).
- **Códigos**. Los asigna el sistema (E-0001, OT-0001, CO-0001, FI-0001, IN-0001) y no se reutilizan. Si el hecho trae «id», se rechaza (poka-yoke).
- **Consultas** para B7 y B4:
  - `capacidad(recurso, fecha)`: el valor maestro vigente, o 0 si hay parada ese día;
  - `valor_vigente(campo, objeto, fecha)`;
  - `historial_maestro()`;
  - `vencidos()`: tickets con fecha pasada y sin su hecho. Es la «desviación de oportunidad» de MCD §6.2.3.4 (el camión que no llegó).
- **Movimientos fuera de un hecho**: `crear_ticket()` (origen plan) y `mover()` (origen gerente o costos). El origen costos es C.carga, que informa «en ejecución» y «terminado».
- **test_eventos.py**: 25 pruebas, todas calculables a mano y sin la calculadora. Una de ellas comprueba que los nombres de eventos, tickets y estados coinciden con spec.py; se salta si no encuentra spec.py (se le da la ruta con la variable SPEC_B).

### Supuestos agregados
1. `tipo` es el nombre exacto del evento en spec.py. Las acciones se escriben en el campo `accion` (PEDIDO: entra / cancela; PLANTA: para / reinicia) o `movimiento` (COBRO_PAGO: cobro / pago).
2. Un pedido que entra crea una OT **comprometida** (pedido firme). Si hay catálogo de recetas, el producto debe estar en él.
3. «cancelado» existe solo en OT y COMPRA, y se alcanza desde cualquier estado que no sea final. FINANCIAMIENTO e INVERSIÓN no se cancelan.
4. Un hecho no puede tener fecha posterior a hoy. Una parada que empieza en el futuro es un ticket de mantenimiento, no un hecho: se rechaza.
5. Llegada de material:
   - sin una COMPRA comprometida que corresponda, se rechaza;
   - si es parcial, la compra sigue comprometida;
   - si excede lo pendiente, se rechaza (el exceso es otra compra).
6. Cobros y pagos con datos válidos siempre se aceptan, porque son hechos. Si la caja queda bajo el mínimo, se emite un **aviso**, no un rechazo.
7. FINANCIAMIENTO: el desembolso debe ser igual al monto; el pago debe ser ≥ al principal, y la diferencia se registra como interés pagado.
8. No conformidad:
   - sobre una OT en ejecución, suma reproceso;
   - sobre una OT terminada, crea otra OT comprometida de reproceso (precio 0) y la original no vuelve atrás;
   - sin receta, avisa y no asume 0 horas.
9. Un cambio de dato maestro con fecha anterior al valor abierto se rechaza (corregir el hecho que abrió ese valor).
10. Una corrección debe ser del mismo tipo que el hecho corregido y conserva los códigos que este asignó. Si rompe hechos posteriores, se rechaza entera.

### Preguntas abiertas
13. spec.py no tiene un hecho de «avance / terminación de OT». Supuse que llega de costos (A.ordenes_abiertas → C.carga → B3). ¿Es así?
14. ¿Una OT en ejecución se puede cancelar? ¿FINANCIAMIENTO e INVERSIÓN necesitan «cancelado»?
15. ¿El mantenimiento programado debe ser un quinto ticket? Hoy no existe en spec.
16. ¿Se aceptan pagos parciales de un préstamo, o recepciones con exceso dentro de una tolerancia?
17. ¿Un pedido puede entrar como cotización (OT propuesta) en lugar de comprometida?

### Cómo se conecta
- **B1 → B3 → B7**: `registrar()` devuelve `afectados` y `recalcular`. La pieza 7 usa eso y `vencidos()` para decidir si reprograma.
- **B3 → B4**: la pieza 7 arma el dict de la calculadora con `tickets`, `stock`, `caja` y `capacidad(recurso, fecha)`:
  - OT terminada → no entra;
  - COMPRA comprometida → `llegadas`;
  - FINANCIAMIENTO tomado → `deuda_inicial`.
- **B0** (pieza 5): parametros.py se quedará con la tabla de vigencias. eventos.py ya guarda la historia con la misma forma (`valor`, `desde`, `hasta`, `evento`) para delegarla sin cambiar la interfaz.

### Observación sobre el repo
docs/diseno/METODO_PLANEAMIENTO.md dice «No se construye antes del 9-dic» y AGENTS.md da prioridad absoluta a la MN 01. Seguí con B porque lo pediste; si la prioridad cambió, conviene actualizar ese documento.

**Siguiente**: pieza 5 (parametros.py), o la cuarta ola de la MN 01 (piezas 24–29) si se adelanta.

---

## ESTADO PARA RETOMAR — 28/11/2026, 06:16

### Qué está hecho
| Pieza | Estado | Verificación |
|---|---|---|
| 1 casos_B.xlsx | TERMINADA y verificada | Recalculado con LibreOffice: 466 fórmulas, 0 errores. Los 12 casos dan «OK» contra calculadora.py |
| 2 calculadora.py + test_calculadora.py | TERMINADA y verificada | `python3.11 -m unittest -v test_calculadora.py`: 13/13. El tiempo con 50 OT: plan ≈5 s; plan más costo de restricciones ≈33 s |
| 3 mn02_borrador.docx | TERMINADA, **sin verificación automática** | Revisada a ojo: 7 páginas. Cita de Tino Reyna corregida (MCD §3.4; TECNIA 2016, pp. 84-85). Falta un script que compruebe sus cifras contra casos_B / calculadora |
| 4 eventos.py + test_eventos.py | TERMINADA y verificada | `SPEC_B=<ruta a spec.py> python3.11 -m unittest -v test_eventos.py`: 25/25 |
| A · Auditoría MN 1 | **HECHA** (28/11, 06:35); falta medir S9 con cientos de órdenes | `pruebas_auditoria/correr_auditoria.py <repo>`: 9/9 CONFIRMADAS, todos los controles OK. Ver AUDITORIA_MN1.md |
| 5–18 | NO EMPEZADAS | — |
| 19–23 | NO EMPEZADAS (enunciado recibido el 28/11, abajo) | — |

Las piezas de MN 1 (24, 25 y 30) están hechas y verificadas; su registro está en ENTREGA_MN1.md, no aquí.

### Orden de la cola (dueño, 28/11)
~~A) Auditoría MN 1~~ (hecha el 28/11) → B) piezas 5–18 → C) piezas 19–23 → D) piezas MN 1: 26–29 y 31–32.

### Entorno
- **Python 3.11** con `pulp==2.9.0`. La 2.9.0 trae CBC incluido; PuLP 4.x ya no lo trae y la calculadora no corre. Las piezas 4 en adelante usan Python puro.
- **Motor de costos (para la auditoría y la pieza 12).** El repo necesita `fuente/DBD_Fuente.xlsx` y `casos/plantilla_dbd.xlsx` (de motor_completo.zip). Sin ellos, `calcular()` se detiene con «CONSUME: la entidad o tabla «(sin MCD) KARDEX» no existe en DBD_4».
- **Arnés que funcionó:** `sys.path.insert(0, "<repo>/src")`, después `reyna_local.calculo_local.registrar(carpeta_tmp, bytes, nombre)` y luego `calcular(carpeta_tmp, "2025-07", "REAL", ficha["id"])`. Para SERVITEC, julio da REB 22,975 y MPR 5,165.

### Reglas del dueño que aplican a lo que falta
- spec.py manda. No modificar código existente. Cada pieza con su verificación automática. Lo no comprobado va como POR VERIFICAR. Entregar en lotes de 3–4 piezas en zip.
- **Pieza 12:** si el contrato de costos (contrato.py / resultados JSON) no trae capacidad práctica, receta o fecha de entrega, esos tres datos salen de plantilla_PLAN.xlsx (hoja propia, marcados SUPUESTO), **nunca del libro de costos**. Dejar dicho que se reemplazan cuando el contrato los publique. (Hoy contrato.py no los trae: pregunta 10.)
- **Piezas 19–23:** B vive **solo** en `src/planeamiento/`, `tests/planeamiento/` y `docs/planeamiento/`. No tocar `src/reyna_local`, `src/metodos`, `web/index.html` ni las pruebas existentes. B lee costos solo por el JSON de resultados (formato contrato.py).
  - 19. Mover las piezas 1–18 a `src/planeamiento/` como paquete (imports relativos, sin rutas fijas) y los tests a `tests/planeamiento/`; correrlos y entregar la salida.
  - 20. `src/planeamiento/__main__.py`: servidor local solo con biblioteca estándar. Sirve pantallas_B.html y `/api/plan/cargar`, `/evento`, `/calcular`, `/desviacion`. Se arranca con `python -m planeamiento`, funciona sin internet y devuelve los errores en JSON, en español.
  - 21. `docs/planeamiento/DBD_B.xlsx` (tablas, campos, tipo, clave, relaciones, quién escribe: evento o mantenimiento) y `MCD_B.md` (misión, funciones, eventos, entidades), coherentes con diccionario_B.md.
  - 22. `docs/planeamiento/`: MANUAL_USUARIO_B.docx, INFORME_PRUEBAS_B.docx, ETAPAS_DESARROLLO_B.md y PRESENTACION_B.pptx (10 diapositivas, Oria 16-dic).
  - 23. Un zip solo con lo nuevo (`src/planeamiento/`, `tests/planeamiento/`, `docs/planeamiento/`, construir_exe_B.bat) y ENTREGA_B.md.

### Cómo retomar la pieza 5 (la siguiente de B)
`parametros.py` (B0) debe quedarse con la tabla de vigencias que hoy vive dentro de `eventos.py`. La historia ya tiene la forma que hace falta: `{valor, desde, hasta, evento}`, con cierre del valor viejo el día anterior y sin borrar nada. Hay que agregar:
- la marca SUPUESTO / MEDIDO;
- la regla de paso a MEDIDO con n observaciones y su promedio (spec.PARAMS, columna «regla de cierre»);
- que `eventos.EstadoPlan` delegue en parametros.py sin cambiar su interfaz (`valor_vigente`, `historial_maestro`).

### Preguntas abiertas que siguen vigentes
Son la 1–8 y la 10–17 de esta bitácora; la 9 (referencia de Tino Reyna) quedó resuelta con el repo, salvo el título del artículo de TECNIA. La más urgente para B es la **10**: el contrato de costos no publica capacidad práctica, receta ni fecha de entrega. La pieza 12 ya tiene una regla de reemplazo para eso (arriba).

---

## Auditoría MN 1 (punto A de la cola) — 28/11/2026, 06:35

### Qué se hizo
- `pruebas_auditoria/`: `_comun.py` (arnés: copia de SERVITEC → cambio con openpyxl → registrar() y calcular() reales en una carpeta temporal), un `test_S<n>_*.py` por sospecha, cada uno con su control sin defecto, y `correr_auditoria.py`, que imprime CONFIRMADO / SOSPECHA. Trae su copia de SERVITEC en `datos/`.
- `AUDITORIA_MN1.md`: resumen, hallazgos por severidad, observaciones, correcciones propuestas y POR VERIFICAR.

### Resultado
- CRÍTICO: S1, S2, S3, S4 (sube: el material negativo cae en otra orden) y S6 (sube: el panel no puede fallar en esos casos).
- ALTO: S7 (se aprueba un cierre sin revisión de contabilidad editando el JSON).
- MEDIO: S5.
- BAJO: S8 (5 de 30 en el código; 0 de 2 con el calcular real) y S9 (50 órdenes = 3.6 s).
- Corrección a la sospecha S2: `variable.py:112` no usa LIN_MTO primero.

### Entorno usado
Python 3.11 con openpyxl 3.1.5, defusedxml 0.7.1, python-docx 1.1.2 y pulp 2.9.0. Repo: `repo/` + `fuente/DBD_Fuente.xlsx` + `casos/plantilla_dbd.xlsx`. La corrida completa tarda unos 4 min.

### Pendiente de la auditoría (POR VERIFICAR)
1. S9 con 100, 200 y 400 órdenes: la corrida se interrumpió a pedido del dueño. Comando: `cd pruebas_auditoria && AUDIT_REPO=<repo> AUDIT_S9_N=2,100,200,400 python3.11 -m unittest test_S9_trazas_cuadraticas`.
2. S8: más intentos con el calcular real, y `accion()` concurrente.
3. Observación para el dueño: el cierre de julio de SERVITEC se bloquea en la conciliación (COP_PERD vacío contra 126 del costeo). Las pruebas S7 y S8 agregan esa cuenta.

### Siguiente
Pieza 5 (`parametros.py`, B0): ver «Cómo retomar la pieza 5», arriba.
