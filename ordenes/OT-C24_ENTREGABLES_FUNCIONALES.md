# OT-C24 · Entregables generados desde el sistema (3, 4, 6, 7, 8, 10, 12) — Codex nivel MEDIO
Rama `codex/C24` desde `desarrollo/mono`; PR contra `desarrollo/mono`. Solo lees el contrato de resultados; no tocas cálculo ni motor.
Lista oficial: `docs/planificacion/PLAN_MONOGRAFIA_Y_SISTEMA.md` (Etapa 5). Salida en `entregables/` vía `tools/entrega/armar.py`.

1. **6, 7, 8 (Excel):** que los exportadores incluyan lo nuevo del contrato: rechazos, costeo variable (MC, punto de equilibrio,
   no controlables), estratégico (COQ y gobierno del dato), proyección granular y sensibilidad (API de C21), capa de aprendizaje (C22).
   Una hoja por bloque; cifras idénticas al JSON (prueba que lo compare celda a celda en Frenosa 2010-12 y SERVITEC 2025-07).
2. **4 Prueba de funcionamiento (Word):** recorrido con capturas en Chromium: registrar T14 → calcular → ver orden y su ruta →
   periodos → proyección → aprendizaje → cotizar → exportar. Para cada paso: esperado vs obtenido. Incluye los dos casos a mano
   (SERVITEC julio: 22,975 / 21,374 y 5,165 / 3,880; MINI de proyección; cotizador 3,720).
3. **10 Manual de usuario (Word):** pantalla por pantalla según el menú de C17 (Definir · Estimar · Registrar · Entregar · Aprender),
   con captura, para qué sirve y qué hacer. T14.1 y T16 se marcan «en habilitación» (Claude las cierra; actualizas al final).
4. **12 HTML sin conexión:** regenerar con todos los bloques nuevos; prueba que abre sin red.
5. **3 Código fuente (Word):** regenerar con el script existente (índice + archivos nuevos).
No generes 1, 2, 5, 9, 11 ni 13 (son de Claude o del dueño).
Aceptación: COMPUERTA VERDE; `armar.py` produce los 7 archivos; las cifras coinciden con el contrato.
