# OT-C15 · Vista «Modelo de costeo» y explicación de avisos (tarea 2.8)
Rama `codex/C15`. Solo `index.html`, exportadores si hace falta, y pruebas. Lee SOLO el contrato (`r["modelo"]`, `r["trazas"]`, `r["control"]`, `r["objetos"]`).
- Título exacto: «Modelo de costeo» y subtítulo «Metodología ABC escalonada de W. Oria» (nunca «Modelo de Oria»).
- Diagrama por niveles con los datos del libro: recursos → centros de actividad (estratégico/apoyo/operativo) → actividades (E/A/O, campo `nivel`) → objetos; las reglas `r["modelo"]["reglas"]` como flechas con su inductor; etapas P1…P7, P4D, P4E, OCIO con su nombre (`etapa_nombre`).
- Hoja de costos por orden en formato de Oria: MD, MOD, CIF, pérdida, ocio, adm., ventas, financiero, total y unitario.
- En el panel de calidad, cada control con `ok=false` cuyo texto contenga «suma» muestra: «Aviso del dato fuente: los porcentajes del libro no suman 100 %; el sistema reparte en proporción y conserva el costo (efecto si se usaran tal cual: …)».
Prueba: la página renderiza la vista con `datos/resultados/frenosa_2010-07_REAL.json` sin errores de consola (Chromium headless como en las pruebas existentes).
Aceptación: COMPUERTA VERDE.
