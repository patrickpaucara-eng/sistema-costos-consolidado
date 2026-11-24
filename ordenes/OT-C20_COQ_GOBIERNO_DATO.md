# OT-C20 · Costo de calidad (COQ) y gobierno del dato (envoltorio estratégico, decisión 24-nov) — Codex nivel MEDIO
Rama `codex/C20` desde `desarrollo/mono`; PR contra `desarrollo/mono`. Solo lee el resultado publicado y el libro; no toques el motor.
Módulo nuevo `src/reyna_local/estrategico.py` + campo opcional del contrato `r["estrategico"]`.

## COQ (4 categorías)
- Columna opcional `RECURSO.REC_COQ` ∈ PREVENCION | EVALUACION (vacío = no es calidad). Monto = lo que llegó a las órdenes desde ese recurso (trazas raíz).
- Falla interna = `r["rechazos"]` (rechazos sin reproceso, ya calculados) + `r["perdidas"]` (merma en exceso).
- Falla externa = devoluciones de cliente (VENTA con VTA_CAN < 0, al costo unitario de la devolución que ya publica inventarios).
- Salida: `{coq: {prevencion, evaluacion, falla_interna, falla_externa, total, pct_ventas}}`.

## Gobierno del dato (KPI)
- Columnas opcionales `CRITERIO.CRI_RESP` (responsable) y `CRITERIO.CRI_EVID` (evidencia/fuente).
- KPI = criterios usados en el periodo con responsable y evidencia / criterios usados. Lista de los que faltan.

## Caso a mano (prueba obligatoria `tests/test_estrategico.py`)
Prevención 300, evaluación 200, rechazos 450 + merma 50, devoluciones 250, ventas 10,000 → total **1,250**, **12.5 %**.
3 criterios usados, 2 con responsable y evidencia → KPI **66.67 %**, falta el tercero.
Aceptación: COMPUERTA VERDE; Frenosa sin columnas nuevas = costos idénticos; columnas añadidas a `libro_dbd.COLUMNAS_OPCIONALES`, plantilla y DBD.
