# OT-C12 · Formulario guiado sin JSON (tarea 2.2)

**Rama:** `codex/C12` desde `desarrollo/mono` (después de C11). PR contra `desarrollo/mono`. Solo `src/reyna_local/web/index.html`, un endpoint de lectura nuevo en `src/reyna_local/__main__.py` y pruebas. No toques el cálculo ni `motor_espejo.py`.

**Hoy:** la pantalla «Ejecutar transacción» pide cabecera y líneas en JSON (`#json-header`, `#json-lines`).

**Qué hacer:**
1. Endpoint `GET /api/trx-campos?id=<espacio>&trx=<código>` que lee `TRX_CAMPO` del libro del espacio: `TCA_SEC, TCA_VAR, TCA_ETQ, TCA_NIVEL (C=cabecera, L=línea), TCA_LISTA (tabla.columna)`; para cada `TCA_LISTA` devuelve los valores existentes de esa columna.
2. El formulario arma los campos desde esa respuesta: `TCA_LISTA` con valor → `<select>`; sin lista → `<input>`; las líneas en una tabla con «agregar línea». Etiqueta = `TCA_ETQ`.
3. Al enviar, construye el mismo JSON que hoy y usa el mismo endpoint de ejecución (no cambies el motor).
4. Campo «documento de soporte»: nombre de archivo y su huella SHA-256 calculada en el navegador; se envía en la cabecera como `DOC` y `DOC_SHA` (solo si `TRX_CAMPO` los declara; si no, se muestran pero no se envían).
5. Habilitar solo T14, T14.1, T15, T16, T17, T18, T19 y T20 (las que tienen prueba); las demás se ven deshabilitadas con «sin prueba».
6. Mantén el modo JSON como «avanzado» (oculto por defecto).

**Pruebas:** `tests/test_formulario_guiado.py`. Por cada transacción habilitada: arma el JSON desde el formulario (o desde el endpoint) con datos de `casos/libros/frenosa.xlsx` en una copia temporal, ejecuta y verifica código 200 y que el evento quedó en el libro.

**Aceptación:** `python tools/verificar.py` → COMPUERTA: VERDE.
