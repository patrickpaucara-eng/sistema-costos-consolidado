# OT-C27 · Ola 2 completa de la revisión del dueño — Codex nivel ALTO
Rama `codex/C27` desde `desarrollo/mono`; PR contra `desarrollo/mono`. Especificación: `docs/diseno/OLA2_REVISION_DUENO.md` (léela entera).
Orden de corrido: **D** (registro y E6) → **A** (pronóstico único, desglose, Futuro, retiro de ESTIMADO) → **B** (cotizador por intervalos) → **C** (niveles de suficiencia) → **E** (laboratorio) → **F** (pantallas).
- No toques `src/metodos/reparto_etapas.py`. Puedes tocar `resultados.py`, `contrato.py`, `proyeccion.py`, `cotizador.py`, `store.py` y la web.
- Retirar ESTIMADO y E2 están AUTORIZADOS por decisión del dueño (25-nov) a cambiar pruebas existentes: cita la fila de DECISIONES_DUENO.md en cada prueba que cambies. Ninguna otra prueba existente se edita.
- Los 3 casos a mano de B son pruebas obligatorias con cifras exactas.
- Costos REAL y CONTABLE publicados deben quedar idénticos (compara antes/después).
- Un commit por bloque; si un bloque se traba, anótalo en ERRORES_E2E.md y sigue con el siguiente.
Aceptación: COMPUERTA VERDE; `python tools/e2e_recorrido.py` todo OK (actualízalo si ESTIMADO desaparece); capturas en `docs/entrega/evidencias/C27/`.
