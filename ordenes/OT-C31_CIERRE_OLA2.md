# OT-C31 · Cierre de la ola 2 (lo que queda tras el trabajo de Claude del 25-nov) — Codex nivel MEDIO, una tarea por punto
Base: `desarrollo/mono` (97d1c3b o posterior). Ya hecho por Claude: registro completo (E26), minuto real (E6), sello VIGENTE (E5), tramos (E21),
desglose del costo proyectado + precisión + retiro de ESTIMADO (A), Futuro (E8), panel Decidir (H), cotizador por intervalos y familias (B+G).
No toques `reparto_etapas.py`, `resultados.py`, `proyeccion.py`, `decidir.py`, `familias.py` ni `cotizador.py` salvo lo indicado. Solo tus pruebas mientras trabajas; compuerta completa al final.

1. **E4 · Planta del costo enlazada** (continúa codex/C29b): nodos recurso → centro → actividad → OT unidos por flechas con `monto_tramo`; clic en un nodo = su detalle. Prueba en Chromium.
2. **E7 · Detalle por persona** en SERVITEC: registra 3 técnicos como recursos en una copia y muestra la ruta por persona. Aviso en Frenosa (ya existe).
3. **Aceptar cotización → abrir OT**: botón «Aceptar» en el cotizador: escribe TARIFA con las tasas usadas y ejecuta T09 → T13 por el servicio (`store.execute`), con prueba de que nace la OT con su costo proyectado. Puedes tocar `cotizador.py` solo para devolver lo necesario.
4. **Pantalla de familias**: cargar historia por familia (tabla o importación), ver receta (media, rango 95 %), probar pertenencia y sugerencia de fusión, usando `familias.py`; cotizar por componentes (`cotizar_proyectado(..., familia=, unidades=)`).
5. **Laboratorio** (continúa codex/C30): crear copia del espacio, editar hechos, recalcular y comparar por OT y elemento con la función existente; el original no cambia (SHA).
6. **Niveles de suficiencia** (mínimo): detectar nivel 0–4 por capacidad desde las tablas con datos; aviso «qué falta para subir» en cada pantalla; plantilla descargable por nivel.
Cierre: `python tools/e2e_recorrido.py` todo OK; capturas en `docs/entrega/evidencias/C31/`; PR por punto contra `desarrollo/mono`.
