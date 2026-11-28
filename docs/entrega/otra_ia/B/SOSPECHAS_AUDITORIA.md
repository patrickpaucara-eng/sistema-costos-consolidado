# Sospechas de la auditoría MN 1 (sesión del 28/11, sin ejecutar)

Estado: **todas son SOSPECHA**. Salen de leer el código; todavía no se escribió ni se corrió ninguna prueba contra el motor. Solo cuentan como hallazgo las que una prueba confirme. El código no se modificó.

Base revisada: repo ligero + motor_completo.zip (`fuente/DBD_Fuente.xlsx`, `casos/plantilla_dbd.xlsx`) + paquete_MN1 (SERVITEC_sintetico.xlsx). Las líneas citadas son las de esa copia.

Ya conocido, no se repite: E1–E44 de ERRORES_E2E.md. E44 son los defectos de la pieza 24: fechas al revés, clave duplicada en OBJETO, criterio que suma 0, números como texto y montos de LINEA sin revisar. Las sospechas 2 y 5 se relacionan con E44, pero el defecto está en otro archivo (se explica en cada una).

Severidad tentativa: CRÍTICO = da un costo incorrecto o pierde datos · ALTO = falla en la puesta en marcha · MEDIO · BAJO.

---

## S1 · Un elemento de costo que el motor no reconoce se descarta en silencio — tentativa CRÍTICO
- **Dónde:**
  - `src/metodos/reparto_etapas.py:57`: `ELEM = {"MD","MAT","PD","MOD","SD","IND"}`;
  - `src/metodos/reparto_etapas.py:140`: en `_origenes()`, `if e is None: continue`.
- **Por qué es sospecha:** `src/reyna_local/libro_dbd.py:24` documenta que TIPO_RECURSO → elemento puede ser «MAT, PER, IND, ADM, VTA, FIN…». Si una empresa usa `TRE_ELE = ADM`, `PER`, `VTA` o `FIN`, o lo escribe distinto («Ind», «IND »), sus líneas no entran al reparto. `validar()` no revisa los valores de TRE_ELE.
- **Escenario para probar:** en una copia de SERVITEC, crear el tipo `GASTO_ADM` con `TRE_ELE = ADM` y asignárselo a ADM01. Calcular 2025-07.
  - Lo que se espera hoy: la administración (S/ 2,000) desaparece del costo de las órdenes y el control de conservación da OK.
  - Lo correcto: incluirla o rechazar el libro nombrando el recurso.
- **Corrección propuesta:** en `validar()`, aceptar solo los elementos que el motor reconoce, con un mensaje claro. En `_origenes()`, levantar `Rechazo` en lugar de `continue` cuando una línea con monto no tiene elemento.
- **Principio:** nunca un 0 silencioso; lo repartido = lo gastado (Oria).

## S2 · Una línea con monto pero sin costo unitario vale 0 — tentativa CRÍTICO
- **Dónde:** `src/metodos/reparto_etapas.py:151`: `m = CANTIDAD × COSTO_UNITARIO_DOCUMENTO`. Ignora LIN_MTO.
- **El mismo monto se calcula con reglas distintas:**
  - `src/reyna_local/flujo.py:93` usa LIN_MTO y, si falta, cantidad × costo unitario;
  - `src/reyna_local/variable.py:112` usa LIN_MTO primero;
  - el reparto usa solo cantidad × costo unitario.
- **Escenario para probar:** dejar `LIN_CU_DOC` vacío en la línea T17 de energía de julio (LIN_MTO = 1,500). Calcular.
  - Lo que se espera hoy: energía = 0 en el reparto, CIF menor y control de conservación en OK.
  - Lo correcto: S/ 1,500, o rechazo.
- **Diferencia con E44:** E44 es que `validar()` no revisa los montos de LINEA. Aquí el monto es válido, pero el motor lo ignora.
- **Corrección propuesta:** una sola función de «importe de la línea» (LIN_MTO si existe; si no, cantidad × costo unitario; si ambos faltan, error), usada por el reparto, flujo y variable. Si están los dos y no coinciden, avisar.
- **Principio:** nunca un 0 silencioso; un dato, una regla.

## S3 · Una compra sin LIN_MTO entra al kardex a valor 0 — tentativa CRÍTICO
- **Dónde:** `src/reyna_local/flujo.py:62`: `val = round(_num(l.get("LIN_MTO")) or 0, 2) if can > 0`. Afecta solo a las filas de kardex que se derivan de las transacciones.
- **Escenario para probar:** quitar de KARDEX la fila de la compra de julio (evento 50) y dejar LIN_MTO vacío en su línea (LIN_CU_DOC = 43). Calcular.
  - Lo que se espera hoy: la entrada vale 0, el costo promedio de julio baja de 42 a unos 13.33 y el material de REB y MPR sale muy por debajo.
  - Lo correcto: valuar a 200 × 43 = 8,600, o rechazar.
- **Corrección propuesta:** usar la misma función de importe de S2. Una entrada sin valor calculable detiene el cálculo con un mensaje claro (`validar()` ya lo exige para la hoja KARDEX, pero no para las filas derivadas).
- **Principio:** nunca un 0 silencioso.

## S4 · Un exceso de merma mayor que el consumo da material normal negativo — tentativa ALTO
- **Dónde:** `src/metodos/reparto_etapas.py:147`: `parte = (q - x) / q`. Si LIN_EXC > LIN_CAN, la parte normal es negativa.
- **Escenario para probar:** en la línea T15 de REB de julio, poner LIN_EXC = 160 con LIN_CAN = 150.
  - Lo que se espera hoy: MD normal negativo y una pérdida mayor que lo consumido.
  - Lo correcto: rechazo «exceso mayor que el consumo».
- **Corrección propuesta:** validar `0 ≤ LIN_EXC ≤ LIN_CAN`, en `validar()` y en el reparto.
- **Principio:** entorno hostil, con un mensaje claro.

## S5 · Un exceso de merma escrito como texto se vuelve 0 — tentativa MEDIO
- **Dónde:** `src/reyna_local/resultados.py:21-22`: `try: float(LIN_EXC) except: x = 0`.
- **Escenario para probar:** poner LIN_EXC = «3 kg» en la línea T15 de REB.
  - Lo que se espera hoy: pérdida 0 y los 126 pasan al material normal, sin aviso.
  - Lo correcto: rechazo.
- **Diferencia con E44:** E44 cubre que `validar()` no revisa los montos. Aquí el 0 se inventa en `previos()`, que sigue tragándose el error aunque se corrija `validar()`.
- **Corrección propuesta:** rechazar en lugar de poner 0.
- **Principio:** nunca un 0 silencioso.

## S6 · El control de conservación no detecta lo que se pierde a la entrada — tentativa ALTO
- **Dónde:** `src/reyna_local/resultados.py:349-350`. «Recursos del periodo» suma las aristas que salen de un recurso, o sea, lo que **ya entró** al reparto, y no lo registrado en LINEA y KARDEX.
- **Consecuencia:** con S1, S2 o S3 el control da OK aunque falte dinero. Es el control que se muestra como garantía en «Calidad y cuadre».
- **Escenario para probar:** el mismo de S1 o S2. El control debería dar «NO CUADRA» y hoy daría OK.
- **Corrección propuesta:** comparar contra un total independiente: Σ importe de las líneas del periodo con efecto en costo + salidas valorizadas del kardex.
- **Principio:** lo repartido = lo gastado (Oria); los controles deben comparar contra los hechos, no contra el propio cálculo.

## S7 · El cierre no sella el estado ni el historial — tentativa ALTO
- **Dónde:** `src/reyna_local/cierre.py:141`. `verificar()` calcula la huella sin `estado` ni `historial`.
- **Escenario para probar:** emitir un cierre y luego editar el JSON a `"estado": "APROBADO"`, agregando una aprobación falsa al historial.
  - Lo que se espera hoy: `verificar()` responde INTEGRO.
  - Lo correcto: ALTERADO.
- **Corrección propuesta:** encadenar la huella (cada paso del historial con la huella del paso anterior), o sellar estado e historial en cada acción.
- **Relación:** la falta de autenticación de usuarios ya figura como pendiente en el README; S7 es distinto, porque vale aunque haya autenticación.
- **Principio:** los hechos no se borran ni se alteran (Reyna); separación de funciones.

## S8 · Dos emisiones de cierre simultáneas: la segunda pisa a la primera — tentativa MEDIO
- **Dónde:**
  - `src/reyna_local/cierre.py:104-115`: lee las versiones previas, calcula `version = 1 + max(...)` y escribe con `write_text`, sin bloqueo ni escritura atómica;
  - el servidor es `ThreadingHTTPServer` (`src/reyna_local/__main__.py:31`);
  - `accion()` también lee, modifica y reescribe sin bloqueo.
- **Escenario para probar:** dos hilos llaman a `emitir()` del mismo periodo, con un `calcular` simulado que tarda.
  - Lo que se espera hoy: los dos devuelven la versión 1 y queda un solo archivo, el último.
  - Lo correcto: una versión 1 y un rechazo, o una versión 2.
- **Relación:** «un usuario a la vez» es un límite declarado en el manual; aquí la pérdida ocurre sin ningún aviso.
- **Corrección propuesta:** usar el mismo `_lock` o un archivo de bloqueo, crear con `open(..., "x")` y escritura atómica (temporal + `os.replace`).
- **Principio:** entorno hostil (dos usuarios), con el original intacto.

## S9 · Las trazas recalculan todo el reparto por cada orden y elemento — tentativa ALTO
- **Dónde:**
  - `src/reyna_local/resultados.py:287`: `_trazas()` llama a `R.trazar()` por cada orden y cada elemento;
  - `src/metodos/reparto_etapas.py:383-386`: `trazar()` vuelve a correr `correr()` entero.
- **Consecuencia:** el costo crece como n_órdenes × n_elementos × (costo de un reparto, que a su vez crece con las órdenes), o sea, de forma cuadrática. Con unos cientos de órdenes al mes el cálculo puede volverse muy lento.
- **Escenario para probar:** contar las llamadas a `correr()` en un cálculo de SERVITEC y medir el tiempo con 2, 20 y 100 órdenes sintéticas (copias de las órdenes de julio con sus medidas).
- **Corrección propuesta:** calcular las aristas una sola vez y trazar todas las órdenes sobre esas aristas.
- **Principio:** practicidad y decisiones ágiles; puesta en marcha con datos reales.

---

## Cómo retomar (punto A de la cola)

1. **Preparar el repo:** copiar `motor/DBD_Fuente.xlsx` a `repo/fuente/` y `motor/plantilla_dbd.xlsx` a `repo/casos/`.
2. **Preparar las pruebas:** crear `pruebas_auditoria/_comun.py`. Debe tomar una copia de SERVITEC, aplicarle el cambio con openpyxl, registrarla y calcularla con `calculo_local.registrar()` y `calculo_local.calcular()` en una carpeta temporal, y devolver el resultado o el mensaje de error.
3. **Escribir un `test_S<n>_*.py` por sospecha.** Cada test afirma el comportamiento **correcto**: si falla hoy, la sospecha queda CONFIRMADA; si pasa, sigue como SOSPECHA.
4. **Escribir AUDITORIA_MN1.md:**
   - un resumen de 10 líneas al inicio;
   - los hallazgos confirmados, ordenados por severidad;
   - las sospechas que no se pudieron reproducir, aparte.
