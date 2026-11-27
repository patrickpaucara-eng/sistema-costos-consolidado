# OT-C33 — Cierre del sistema antes de E29

Base: `desarrollo/mono` (incluye C32 completa). Una rama por punto: `codex/C33-N`. PR contra `desarrollo/mono`; nunca fusionar, nunca a main.
Reglas vigentes: no tocar `reparto_etapas.py`; no editar pruebas existentes sin decisión en `DECISIONES_DUENO.md`; mientras trabajas corre solo tus pruebas; compuerta completa (`tools/verificar.py`) UNA vez al final de cada rama, nunca dos ramas en paralelo. Si algo es ambiguo: documenta en `ordenes/RESPUESTAS_CODEX_24NOV.md` y sigue con el siguiente punto.

Orden por criticidad:

## C33-1 Clave única: prueba de cobertura (crítico)
Demostrar que la defensa de C32-2 rechaza duplicados en TODAS las tablas que se crean con el método CREAR, usando la clave declarada en el DBD (MCA rol 'K' / hoja del modelo), no la primera columna.
- Prueba parametrizada: por cada tabla creable en Frenosa y SERVITEC, insertar dos veces la misma clave → la segunda rechazada; claves compuestas (LINEA = LIN_EVE+LIN_NUM) aceptan filas distintas.
- Caso colisión de OT: dos T13 con el mismo código sugerido (simula dos sesiones) → la segunda rechazada con mensaje claro, sin escritura parcial.
- Si alguna tabla no tiene clave declarada: listarla en la evidencia, no inventar la clave.

## C33-2 Tope de demanda en recurso escaso (trivial)
`decidir.asignar_recurso`: respetar `demanda_maxima` por producto antes de pasar al siguiente en el orden MC/recurso; la capacidad sobrante pasa al siguiente. Caso a mano: recurso 100 h; A (MC/h 10, tope 4 u × 10 h), B (MC/h 6) → A 40 h, B 60 h. Mostrar en UI la capacidad no usada si sobra.

## C33-3 Avisos de límites del modelo en pantalla (bajo)
Texto fijo, breve, junto al resultado (no modal):
- Futuro y Cotizador: "El costo variable se proyecta lineal dentro del rango observado de cantidades."
- Familias: "Supone que el proceso no cambió; si cambió máquina, proveedor o método, reinicie la historia de la familia."
- Decidir/recurso escaso: "Una sola restricción. Con varias, use Exportar a Excel para Solver."
- Sistema: "Uso de un solo usuario a la vez."
Prueba Chromium que verifica que cada aviso aparece.

## Cierre
Evidencia por punto en `docs/entrega/evidencias/C33_N_*.md`, tiempos en `docs/entrega/tiempos/codex.csv`. Reporte final: PRs, resultado de compuerta, pendientes.
