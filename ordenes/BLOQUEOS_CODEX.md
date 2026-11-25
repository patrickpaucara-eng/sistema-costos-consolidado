# Bloqueos de Codex

- **OT-C21:** desbloqueada el 25-nov: C18 fue integrada en `8dff870`; la proyección está en revisión.
- **OT-C22:** las guardas piden comparar el error fuera de muestra de cada calibración contra «el valor del libro», pero el diseño no identifica referencia ni función de error para probabilidad de éxito, umbral de diagnóstico o modelo de pronóstico. Se prepararon únicamente cálculos puros y sus pruebas en `codex/C22`; faltan la decisión, calibración sobre libro, persistencia, API e integración. C21 y C23 aún no están integradas para consumir la capa.
- **OT-C23:** el caso manual y la API TDABC funcionan, pero C22 no expone todavía el consumo estándar aprendido; coordinar su lectura cuando se defina e integre el contrato de C22.
- **OT-C17:** desbloqueada; C12, C14 y C15 están integradas en `8dff870`.
- **OT-C21:** C18 integrada; proyección entregada en PR #18, pendiente de integración externa.
- **OT-C22:** guardas aclaradas y cálculo, persistencia, API y cotizador implementados; falta conectar `factor_estandar` a C21 cuando el PR #18 esté integrado en la base.
- **OT-C23:** el cotizador consulta estándares vigentes en la rama C22 cuando el pedido identifica producto; pendiente integración conjunta.
- **OT-C17:** C12, C14 y C15 integradas en `8dff870`; orden desbloqueada.
