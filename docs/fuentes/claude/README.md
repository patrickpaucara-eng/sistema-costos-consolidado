# Fuentes de transferencia y trabajo de Claude

Estas fuentes preservan el contexto que el dueño entregó para mantener continuidad. Son documentos históricos: las restricciones y propuestas que contienen se interpretan junto con los mensajes posteriores del dueño y no se convierten automáticamente en instrucciones actuales.

## Archivo de transferencia

[TRANSFERENCIA_COSTOS_ORIA.md](TRANSFERENCIA_COSTOS_ORIA.md) se preservó íntegro, sin editar, desde el adjunto recibido el 19 de noviembre de 2026. Su SHA-256 está en `SHA256SUMS`.

La transferencia describe el estado inicial y prohíbe escrituras hasta autorización. Después, el dueño creó el repositorio privado consolidado, indicó continuar allí y autorizó el plan/implementación. El repositorio histórico `sistema-costos-reyna` sigue en solo lectura. La transferencia propone SQLite como hipótesis; la decisión posterior vigente mantiene Python + Excel + HTML, congela VBA y aplaza SQLite.

## Fuentes de Ola 3

Los cuatro Markdown finales de Claude, con los duplicados verificados y deduplicados, están en [ola3](ola3/README.md). Se recuperaron además el diagnóstico D9, su informe y pruebas desde la rama histórica `desarrollo/deuda`; esa evidencia se conserva en [ola3/d9](ola3/d9/README.md).

## Orden de prevalencia aplicado

1. Mensajes más recientes y explícitos del dueño sobre alcance, tecnología y autorización.
2. MCD/DBD y casos ORIA para el significado metodológico.
3. Decisiones y hallazgos documentados de Claude, identificados con su revisión y evidencia.
4. Hipótesis históricas y recomendaciones, que permanecen propuestas hasta validarlas.

La ficha de transferencia no sustituye el plan actual. Para el estado operativo, revisar [PLAN_MVP_Y_PENDIENTES.md](../../entrega/PLAN_MVP_Y_PENDIENTES.md) y [ESTADO.md](../../planificacion/ESTADO.md).
