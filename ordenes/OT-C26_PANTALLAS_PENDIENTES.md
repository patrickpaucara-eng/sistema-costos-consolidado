# OT-C26 · Ola 1 de la revisión del dueño: pantallas sobre lo que YA calcula el sistema — Codex nivel ALTO
Rama `codex/C26` desde `desarrollo/mono`; PR contra `desarrollo/mono`. Fuente: `docs/entrega/evidencias/ERRORES_E2E.md`.
Solo lees el contrato y las API existentes; no toques cálculo ni motor. Trabaja de corrido, un commit por error, una prueba por pantalla.

Corrige en este orden: **E22** (menú por grupos con ícono, desplegable, estilo Odoo) → **E23** (quitar Simulación) → **E2** (Desde/Hasta solo en Periodos) →
**E3** (colores de datos fijos) → **E4** (Planta del costo clicable: recursos → centros → actividades → órdenes desde `trazas`) → **E21** (tramos: monto del tramo vs parte de la orden; tasa CIF en P4C) →
**E15** (pantalla Cotizador: elegir actividades y cantidades, materiales, precio y margen → `/api/cotizar`) → **E16** («Lo que aprendió» lee `/api/aprendizaje`, botones aprobar/rechazar) →
**E13** (tornado de sensibilidad en Futuro desde `/api/proyeccion`) → **E17** (costeo variable) → **E18** (costo de calidad y gobierno del dato) → **E19** (rechazos en «Inventarios y pérdidas») →
**E24** (propuestas por decisor con descarga por sección) → **E9** («cómo se calculó» en cada propuesta) → **E11** (texto de Periodos) → **E7** (aviso de detalle por persona).

NO hagas aún (esperan cálculo de Claude): E5, E6, E8, E10, E12, E14 y los niveles de suficiencia.
Regla 80/20: pantallas simples, sin adornos. Errores nuevos que veas: anótalos en ERRORES_E2E.md y sigue.
Aceptación: COMPUERTA VERDE; `python tools/e2e_recorrido.py` 30/30; capturas de cada pantalla en `docs/entrega/evidencias/C26/`.
