# OT-C03 · Datos del caso Frenosa normalizados (Codex · esfuerzo medio)
Rama: `codex/ot-c03` desde `desarrollo/mono`. PR contra `desarrollo/mono`. No unir.
**Objetivo:** tener los datos del caso Frenosa limpios y con fuente, para que Claude los convierta en operaciones del sistema.
**Fuente:** la exportación JSONL del proyecto pasado (ya indexada en `docs/fuentes`): los 12 Excel mensuales `frenosa_datos_entrada_abc_2010_MM.xlsx` y el de julio. **Solo datos; cero código del proyecto pasado.**
**Hacer:** `datos/frenosa/` con un CSV por hoja de entrada (Empresa, Periodo, Objetos_Costo, Ordenes_Trabajo, Personal_directos, costo_otros_recursos, Actividades, Inductores, EC_AC_Inductores, Soporte_*, AC_OT_Pesos_*, Ventas, Compras, Servicios_Directos) y columna `periodo` para los 12 meses; `datos/frenosa/FUENTES.md` con hash de cada origen y qué datos son reales (julio 2010, caso PUCP) y cuáles simulados (otros meses, compras, cantidades vendidas).
**No hacer:** no mapear a transacciones ni calcular costos (eso es de Claude).
**Aceptación:** prueba que relee los CSV y comprueba totales por hoja contra los del JSONL (mismos importes); `python tools/verificar.py` en VERDE. Registrar tiempos.
