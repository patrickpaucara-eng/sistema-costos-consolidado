# Respuestas de Claude a los bloqueos de Codex (24-nov, tarde)

## C12 (PR #9)
Revisado: alcance correcto (sin store.py ni cálculo, prueba nueva sin editar las existentes). Lo uno yo tras la compuerta.
Fechas finales inválidas de Frenosa: **era un error real del adaptador** (todos los meses terminaban en 31). Corregido en
`casos/frenosa/generar.py` y libro regenerado (solo cambia la hoja PERIODO; costos idénticos). Quité el `xfail` de tu prueba al unir C12: ahora pasa.
Borrador guiado al cambiar de espacio/transacción: queda como mejora menor dentro de C17.

## C13 — sí, se mantiene la continuidad del inventario
Tenías razón: con 200 kg comprados al mes el saldo de julio no podía ser 100 kg. Diseño corregido en `docs/diseno/SEGUNDO_CASO.md`
(sección «Meses»): saldo inicial 100 kg a 40; enero–junio se compra exactamente lo consumido a 40; motores enteros por mes.
**Los esperados de julio no cambian** (22,975 / 21,374 y 5,165 / 3,880). Continúa C13.

## C16 — el .pptx no va dentro del EXE
Decisión: la presentación se genera con `tools/` en la máquina de desarrollo (python-pptx en `dependencias de desarrollo de pyproject.toml`), no desde el EXE.
El EXE conserva tu HTML imprimible. Aceptación de C16: el .pptx de 8 diapositivas se genera y se abre con python-pptx en la compuerta;
la compilación de Windows sigue verde sin esa dependencia. Saca el PR de borrador cuando cumpla eso.

## C18 — aclaraciones metodológicas
1. **ESTIMADO no tiene trazas:** la fracción variable de cada (orden, elemento) se calcula SIEMPRE con las trazas raíz de REAL del mismo
   periodo (`R.trazar`, como `resultados._trazas`, todos los elementos) y se aplica a los montos por elemento de la síntesis que se publica.
   En ESTIMADO se usan las fracciones del último periodo real. Fórmula: variable(orden, e) = monto_síntesis(orden, e) × Σ_rec(raíz × v_rec) / Σ_rec raíz.
2. **Propuestas por elemento, no por recurso:** controlabilidad del elemento en ese producto = parte de su monto raíz que viene de recursos con REC_CTRL = S.
   - 0 % controlable → la propuesta se elimina y va a `no_controlables`.
   - Entre 0 y 100 % → se mantiene con impacto × fracción controlable y la nota «impacto ajustado a la parte controlable (x %)».
   - 100 % → sin cambio. Agrega estos tres casos a la prueba.
3. Puedes tocar `resultados.construir` solo para la llamada a `variable.py` y el campo del contrato.

## C19
Correcto declarar límites en vez de suponer cifras. El efecto mensual de las propuestas lo dará C21 (proyección) y la controlabilidad C18;
cuando se unan, el informe los toma del contrato. Abre el PR como está, con los límites explícitos.

## Orden para mañana
C13 → (PR de C14, C15, C19 si sus compuertas terminaron VERDE) → C16 → C18 → C20 → C21 → C22 → C23 → C17 al final.

# 25-nov (Claude)
- Unidos a `desarrollo/mono`: C13, C14, C15, C19, C16, C18, C20 y C23 (PR #10–#17). Conflictos resueltos por Claude (exportar: informe + presentación; columnas opcionales de C18 y C20 juntas; plantilla y DBD reconstruidos con ambas).
- **C21:** desbloqueada (C18 ya está en la base).
- **C22:** guarda por calibrador definida en `docs/diseno/APRENDIZAJE.md` (sección «Guarda por calibrador»). Solo los estándares pueden quedar PENDIENTES.
  Expón `aprendizaje.estandar_vigente(...)` y conéctala en `cotizador.py` (C23) y en `proyeccion.py` (C21).
- **C17:** desbloqueada (C12, C14 y C15 integradas).
- Orden: C21 → C22 → C17.

# 25-nov 10:00 (Claude) — C24 unido (PR #21)
- **Proyección granular en el Excel 8:** el exportador la pide en el momento a `proyeccion.proyectar_granular(libro, empresa, meses=6)` (es de solo lectura); no entra al JSON publicado. Hoja «Proyección por hechos» + hoja «Sensibilidad». Prueba: mes 1 con factores 1 = costos del mes base.
- **Recorrido completo y casos a mano (entregable 4):** lo hace Claude en la prueba de punta a punta; tú solo regeneras el Word con lo que deje en `docs/entrega/evidencias/`.
- **Manual:** 7 pantallas basta si cubre las 5 secciones del menú (regla 80/20); agrega solo las que falten para cubrirlas.
- **HTML file://:** lo prueba el dueño en otra PC.
- T14.1 y T16 ya están habilitadas: quita «en habilitación» del manual.

# 25-nov 13:40 (Claude) — C26 unido (PR #24), ola 1 parcial
- **E2:** autorizado por decisión del dueño (25-nov) cambiar `tests/test_esqueleto_navegacion.py` líneas 29 y 34: las fechas Desde/Hasta deben verse SOLO en «Periodos». Hazlo en la ola 2.
- **E21:** Claude agrega al contrato `monto_tramo` en cada traza (ola 2 de cálculo); luego lo muestras.
- **E4, E15, E7, E13:** quedan para la ola 2 (planta con nodos enlazados; cotizador con varias actividades y materiales por OT; detalle por persona con SERVITEC; tornado completo).
- Prueba en navegador del aprendizaje con una calibración pendiente: incluir en la ola 2.

# 25-nov 16:15 (Claude) — C27 parcial unido (PR #25). Continúa en codex/C27b
- **D AUTORIZADO:** la decisión del dueño E26 (25-nov) autoriza cambiar `tests/test_capacidad_inicial.py` (lista exacta de transacciones) para incluir las nuevas. Regla: `validate_model` exige solo las 8 base; las demás se habilitan si el libro las define (TRX + TRX_CAMPO + TOP) y se listan por libro.
  Si una transacción necesita maestros vacíos en Frenosa (ESTIMACION, PERSONA), la prueba los crea en la copia temporal (como en C12). Prioridad: T13, T18.3, T18.7, T20.1; el resto con prueba de humo (campos + rechazo limpio).
- **Prioridad para el 9-dic:** D → A → B integrado al cotizador + G → F → C → E. Si el tiempo no alcanza, C y E quedan con lo mínimo (detección de nivel con aviso; laboratorio = copia + recalcular + comparar).
- Lo que ya pasó (casos de B, E2, inventario DBD, copia de espacio) se conserva; no lo rehagas.

# 26-nov 15:00 (Claude) — C31 puntos 2, 4, 5 y 6 unidos (PR #32–#35). Autorización para C32-1
- **C32-1 AUTORIZADO** (decisión del dueño 26-nov, poka-yoke): actualizar `tests/test_aceptar_cotizacion.py` para el comportamiento nuevo:
  el código de la OT lo asigna el sistema; el campo `objeto` enviado se ignora y la respuesta informa el asignado. Mantén en la prueba:
  atomicidad (T13 simulado que falla → nada se escribe), idempotencia por identificador, y que la OT nace con su costo proyectado.
  Cita la decisión en el comentario de la prueba. Ninguna otra prueba se edita.
- Sigue de corrido con C32 puntos 2 → 5. Base: desarrollo/mono último (ya incluye C31).

# 26-nov 15:30 (Claude) — C32-1 unido (PR #36). C32-2: corrección
- La clave única NO es la primera columna: es la clave del DBD de cada tabla. Para LINEA es (LIN_EVE, LIN_NUM); en general usa las columnas
  con rol K del método CREAR en MCA, o la clave primaria declarada en el DBD (`fuente/DBD_Fuente.xlsx`, hoja del modelo interno). Si una tabla
  no tiene clave declarada, no se valida (y se lista en REGLAS_APRENDIDAS.md). Con eso la compuerta debe volver a VERDE.
- C32-1 pendiente: precargar y bloquear el código de OT en el formulario guiado (T13).

# 27-nov — C34-5, integración de tramos en Pedido
- La interfaz guiada calcula cantidades técnicas y aplica el costo REAL de las actividades/materiales identificados por la receta. La hoja opcional `COSTO_TRAMO` de C34-3 no se aplica automáticamente en este flujo: el pedido no define si `COD_RECURSO` se compara con el código de recurso, material, actividad o inductor, ni cómo distribuir una cantidad entre tarifas marginales cuando el costo se proyecta por intervalos.
- Hasta acordar la clave y la interacción con proyección, se conserva C34-3 como capacidad de cálculo aislada; el Pedido deja visible el costo con tasa REAL y documenta este límite. No se inventa una conversión de códigos ni se aplica una tasa por tramo a una base distinta.
# C34-4 · aclaraciones de implementación (27-nov)

- **Curva S para un número distinto de seis intervalos:** la OT fija los seis pesos `1-2-3-3-2-1` pero no define cómo reducirlos o ampliarlos. Implementación provisional: interpolar linealmente los seis puntos en una malla uniforme con el número de intervalos requerido y normalizar; seis intervalos conservan exactamente los pesos del caso manual. Revisar si Oria prefiere otra discretización.
- **Capacidad y plazo:** la OT no define calendario, turnos ni un esquema validado para traducir una OT abierta a carga pendiente diaria. El cálculo recibe capacidad práctica y carga comprometida por actividad/día, ambas en la misma unidad; no infiere automáticamente carga pendiente desde el estado de OBJETO ni trata datos históricos como reservas. El resultado expresa días de capacidad, no fecha de calendario. C34-5 debe integrar una fuente con semántica aprobada antes de presentar una fecha empresarial.
