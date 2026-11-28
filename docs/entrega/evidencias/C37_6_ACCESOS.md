# OT-C37-6 · Accesos y pantallas

**Base:** `desarrollo/mono@d7d065d`. **Alcance:** navegación y presentación; no se modificó el cálculo.

Inicio conserva la consulta del periodo y presenta tres tarjetas: Cotizar pedido, Registrar y Planta del costo. «Word código» se encuentra en Configuración → Modelo de costeo, con estado de descarga propio y extensión `.docx` sugerida.

**Decisión sobre Simulación:** aporta los escenarios publicados con percentiles y probabilidad de pérdida, distintos de la proyección por recurso y del laboratorio de hechos. Se integró en la pantalla Futuro, accesible desde el menú Futuro → Futuro, para no dejarla huérfana ni duplicar una pestaña. El antiguo enlace `#simulacion` redirige a Futuro. La pantalla muestra el resultado publicado; no valida la capacidad predictiva de los escenarios.

**Pruebas:** `tests/test_c37_6_accesos.py` visita las tres tarjetas, comprueba la tabla de escenarios en Futuro, la compatibilidad del enlace anterior y descarga un Word real con extensión. `tests/test_c26_e23.py` y `tests/test_c35_2_cabecera.py` se mantienen intactas. Tres pruebas focalizadas verdes; compuerta completa VERDE con 572 pruebas y contrato válido.

**Uso:** Inicio → uno de los tres accesos; Futuro → Futuro para revisar escenarios; Configuración → Modelo de costeo → Word código para descargarlo.
