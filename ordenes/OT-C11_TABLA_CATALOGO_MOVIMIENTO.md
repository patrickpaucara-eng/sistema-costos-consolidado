# OT-C11 · Tabla «se teclea a diario / es catálogo» (tarea 2.1)

**Rama:** `codex/C11` desde `desarrollo/mono`. PR contra `desarrollo/mono`. No toques `src/metodos/` ni `src/reyna_local/resultados.py`.

**Objetivo:** clasificar cada hoja del libro DBD (`casos/plantilla_dbd.xlsx`) para que el formulario guiado (OT-C12) pida solo lo que se teclea en el día.

**Regla (taxonomía de Tino, MCD):**
- CATALOGO: maestros que se definen una vez y se eligen de una lista (EMPRESA, RECURSO, CENTRO, ACTIVIDAD, CRITERIO, OBJETO, CLIENTE, TIPO_RECURSO, COMPONENTE…).
- MOVIMIENTO: hechos del día con fecha (EVENTO, LINEA, MEDIDA del mes, VENTA…).
- CONFIGURACION: reglas del método y del motor (REGLA_REPARTO, TRX, TRX_CAMPO, PERFIL_TRX, PARAMETRO…).
- RESULTADO: lo que escribe el sistema (KARDEX derivado, EXISTENCIA, RESULTADO_METODO…).

**Entrega:**
1. `docs/diseno/TAXONOMIA_HOJAS.csv` con columnas `hoja,clase,quien_la_llena,frecuencia,motivo` (una fila por hoja de la plantilla).
2. `tests/test_taxonomia_hojas.py`: falla si una hoja de la plantilla no está en el CSV o si `clase` no es una de las 4.

**Aceptación:** `python tools/verificar.py` → COMPUERTA: VERDE.
