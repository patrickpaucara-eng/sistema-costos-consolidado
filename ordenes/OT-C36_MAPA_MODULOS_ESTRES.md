# OT-C36 — Ficha por módulo y prueba de estrés (insumo del mapa detallado)

Base: `desarrollo/mono`. Origen: E36. Esta orden NO cambia código del sistema; produce datos para el mapa y una lista de hallazgos. Una rama `codex/C36`, un PR, sin fusionar.

## C36-1 Inventario de módulos
Para cada pantalla/sección del menú (26 actuales, 6 destinos de C35 si ya está unida) generar `docs/diagramas/modulos.json` con: id, nombre, destino, para qué sirve (1 línea), entradas (campo → fuente: libro / OT / usuario / derivado), salidas, endpoints/funciones Python, tablas DBD que lee y escribe, concepto de Oria o Tino que aplica (cita de documento y sección, sin copiar código), pruebas que lo cubren. Todo extraído del código; lo que no se pueda extraer se marca `SIN_DATO`.

## C36-2 Prueba de estrés por módulo (5 criterios, nota 0/1/2 con evidencia)
1. **Autosuficiencia de datos:** ¿cada campo que pide al usuario es dato o decisión? Todo dato que el sistema ya tiene (libro, OT, capacidad, histórico) y se vuelve a pedir es hallazgo. Campos que arrancan en 0 sin aviso, hallazgo.
2. **Oria coherente:** ¿el cálculo corresponde al concepto citado (escalonado, recíproco, ABC, normal, etc.)? Cita sección; si falta, hallazgo.
3. **Practicidad:** número de campos obligatorios, de clics para el caso típico, y si hay valor por defecto razonable.
4. **Decisión ágil:** ¿da una recomendación o un número accionable en ≤ 3 pasos? ¿qué falta para decidir?
5. **UIX estándar:** formato de presentación repetido (cabecera, pestañas superiores, bloque de entrada, bloque de resultado, fundamento), uso por teclado (tab/enter/atajos), conserva estado al actualizar.
Salida: `docs/entrega/evidencias/C36_ESTRES_MODULOS.md` con tabla módulo × criterio y lista de hallazgos numerados H1… ordenados por impacto. Medir con Chromium los clics y campos reales, no estimar.

## C36-3 Plantilla UIX estándar (propuesta)
Describir en `docs/diseno/PLANTILLA_UIX.md` la estructura única para toda pantalla (pestañas superiores fijas → entradas → resultado → fundamento → siguiente acción) y listar qué módulos la incumplen. No implementar.

## Cierre
Reporte: PR, número de hallazgos por criterio, los 10 de mayor impacto.
