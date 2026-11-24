# OT-C23 · Cotizador de pedidos especiales TDABC y costo objetivo (tarea 2.4b) — Codex nivel MEDIO
Rama `codex/C23` desde `desarrollo/mono`; PR contra `desarrollo/mono`. Decisión del dueño 24-nov: TDABC solo para cotizar pedidos especiales
(el costo real sigue siendo el ABC del motor). Módulo nuevo `src/reyna_local/cotizador.py`; no toques el motor.

## Cálculo
1. Tasa por actividad = costo de la actividad del último mes cerrado (`r["actividades"]` del resultado publicado REAL) / capacidad práctica
   (MEDIDA nivel CAP de su inductor; si no hay CAP, el total usado del inductor, y avisar «sin capacidad práctica: tasa sobre uso»).
2. Pedido = {actividad: cantidad de inductor} + materiales {recurso: cantidad} (costo unitario = último CPU del kardex; si C22 aplicó consumo estándar, se informa).
3. Costo del pedido = Σ tasa × cantidad + materiales. Costo objetivo = precio de mercado × (1 − margen objetivo). Brecha = costo − objetivo (kaizen si > 0).
4. API `POST /api/cotizar {empresa, actividades, materiales, precio_mercado, margen_objetivo}`. Guardar nada en el libro.

## Caso a mano (prueba obligatoria `tests/test_cotizador.py`, datos sintéticos)
TORNO 6,000 / 100 h = 60 · SOLD 4,000 / 100 m = 40 · PINT 2,500 / 100 m² = 25 · INSP 1,000 / 10 = 100.
Pedido 12 h, 30 m, 40 m², 3 inspecciones = 720 + 1,200 + 1,000 + 300 = 3,220; material 500 → **3,720**.
Precio 5,000, margen 30 % → objetivo **3,500** → brecha **+220**.
Más: sin CAP aparece el aviso; actividad inexistente → error claro.
Aceptación: COMPUERTA VERDE; publicación idéntica.
