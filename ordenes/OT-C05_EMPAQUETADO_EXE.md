# OT-C05 · Empaquetado del sistema completo (Codex · medio)
Rama `codex/ot-c05` desde `desarrollo/mono`. PR contra `desarrollo/mono`. No unir.
**Objetivo:** que el paquete del `.exe` incluya TODO lo que hoy usa el sistema, y probarlo en Linux con el equivalente (el `.exe` real se fabrica al final con la repo pública; GitHub rechazó Windows por facturación, no por código).
1. Actualizar el empaquetado (PyInstaller y `tools/windows`) para incluir: `src/metodos`, `src/analitica`, `src/analitica2`, `src/casos`, `puerto_lectura.py`, `rutas.py`, `integra_env.py`, `fuente/*.xlsx`, `casos/plantilla_caso.xlsx`, `casos/frenosa/`, `datos/frenosa/`, `datos/frenosa_supuestos/`, `web/`. Respetar `rutas.py` (`REYNA_FUENTE`) para que las rutas funcionen dentro del ejecutable.
2. Prueba de humo en Linux con el binario empaquetado: arranca sin internet, abre la interfaz, calcula julio 2010 REAL y exporta el HTML.
3. Dejar `tools/windows/LEEME.md` con los pasos exactos para el día de la entrega (repo pública → Actions → descargar → probar sin internet).
**Aceptación:** humo del binario Linux en VERDE con evidencia en `docs/entrega/evidencias/OT-C05/`; `python tools/verificar.py` en VERDE; tiempos en `codex.csv`.
