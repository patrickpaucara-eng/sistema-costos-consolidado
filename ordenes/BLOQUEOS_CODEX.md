# Bloqueos de Codex

- **OT-C21:** la orden requiere crearla desde `desarrollo/mono` después de integrar C18. En `d6523c0`, C18 sigue en el PR #15; Codex no está autorizado a fusionar. Continuar cuando Claude lo integre.
- **OT-C22:** las guardas piden comparar el error fuera de muestra de cada calibración contra «el valor del libro», pero el diseño no identifica referencia ni función de error para probabilidad de éxito, umbral de diagnóstico o modelo de pronóstico. Se prepararon únicamente cálculos puros y sus pruebas en `codex/C22`; faltan la decisión, calibración sobre libro, persistencia, API e integración. C21 y C23 aún no están integradas para consumir la capa.
- **OT-C23:** el caso manual y la API TDABC funcionan, pero C22 no expone todavía el consumo estándar aprendido; coordinar su lectura cuando se defina e integre el contrato de C22.
- **OT-C17:** la orden requiere las pantallas de C12, C14 y C15 integradas. En `d6523c0` C14 y C15 siguen en los PR #11 y #12; esperar su integración externa para no perder pantallas.
