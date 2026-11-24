# OT-C14 · Pantalla «Periodos» sobre /api/periodos (tarea 2.6, interfaz)
Rama `codex/C14` desde `desarrollo/mono`; PR contra `desarrollo/mono`. Solo `src/reyna_local/web/index.html` y pruebas. No tocar cálculo.
- Controles: desde, hasta (fecha), agrupar por (día, quincena, mes, bimestre, trimestre, semestre, año), síntesis.
- Llama `GET /api/periodos?empresa=&sintesis=&desde=AAAA-MM-DD&hasta=AAAA-MM-DD&grano=` y muestra una tabla por cubeta: hechos por transacción
  (eventos, cantidad, importe) y, si `costo` no es nulo: ventas, costo total, margen y productos (cantidad, costo, costo unitario).
- Si `costo.completo` es falso o hay `nota`, mostrar la nota en ámbar. Día y quincena: mostrar la nota «solo hechos».
Prueba: `tests/test_pantalla_periodos.py` (endpoint con Frenosa julio–agosto bimestral = suma de los dos meses; la página contiene los controles).
Aceptación: `python tools/verificar.py` → COMPUERTA: VERDE.
