# OT-C35 — Usabilidad: navegación, cabecera y Pedido en lenguaje del cliente

Base: `desarrollo/mono` (HEAD cc4b49f o posterior). Origen: `docs/entrega/evidencias/ERRORES_E2E.md` § E30, E31, E32, E33 (leerlos completos antes de empezar).
Reglas: una rama `codex/C35-N` y un PR contra `desarrollo/mono` por punto; nunca fusionar ni ir a main; no tocar `reparto_etapas.py` ni `motor_espejo.py`; no editar pruebas existentes sin decisión en `DECISIONES_DUENO.md` (si una prueba depende de un id o texto que cambias, lo dices en el PR y esperas decisión; no la edites). Durante el trabajo corre solo tus pruebas; compuerta completa UNA vez al final de cada rama. Lo ambiguo va a `ordenes/RESPUESTAS_CODEX_24NOV.md` y sigues. No cambies ningún cálculo: es una orden de interfaz y de captura de datos.
Orden obligatorio: C35-1 → C35-4. Los id de secciones (`#cotizador`, `#dashboard`, etc.) y los endpoints se conservan; solo cambian agrupación y presentación.

## C35-1 Navegación por ciclo del pedido (E30)
Reemplazar los 5 grupos / 26 opciones por 6 destinos, en este orden. Solo el destino activo muestra sus opciones (acordeón: abrir uno cierra los demás):
- **Pedido:** Cotizar pedido, Órdenes, Ruta de la orden.
- **Operación:** Registrar movimiento, Importar libro, Cierre y aprobación.
- **Costos:** Inicio, Planta del costo, Periodos, Reportes, Inventarios y pérdidas, Costeo normal.
- **Futuro:** Futuro, Laboratorio, Familias, Comparar síntesis, Decidir, Propuestas.
- **Aprendizaje:** Lo que aprendió, Relevancia.
- **Configuración** (plegado por defecto): Modelo de costeo, Datos del libro, Cargar empresa, Espacios de trabajo, Consultar tablas, Calidad y cuadre.
Criterios: máximo 6 títulos visibles al cargar; el destino de la sección abierta se resalta; se llega a cualquier pantalla en 2 clics. Prueba Chromium que recorre las 26 pantallas desde el menú nuevo y verifica que ninguna quedó huérfana.

## C35-2 Cabecera de una línea (E32)
La barra Empresa / Síntesis / Periodo / Suficiencia / Sello / botones deja de ocupar ~190 px.
- Una sola línea ≤ 48 px en pantalla ancha: empresa, síntesis, periodo, sello y estado de suficiencia como texto/etiquetas compactas.
- «Plantilla de nivel», «Descargar plantilla», «Consultar resultados» y «Calcular» pasan a un menú «Más» dentro de la cabecera o a la pantalla donde se usan.
- Solo la cabecera compacta queda fija; el resto se desplaza.
- Medir con Chromium: altura de la cabecera ≤ 48 px a 1366×768 y la zona útil crece al menos 140 px respecto a hoy (dejar la medición en la evidencia).

## C35-3 Pedido en lenguaje del cliente (E31, E33)
Rediseñar `#cotizador` como asistente de 3 pasos, sin cambiar el motor:
1. **Qué pide el cliente:** familia o producto, cantidad, fecha requerida, contrato y condición de pago (máx. 6 campos). Aquí van además los parámetros que declara la familia como «cliente» (p. ej. kg, m², unidades).
2. **Resultado:** costo esperado con rango P05–P95, precio sugerido frente a mercado, plazo («llega» / «N días tarde»), nivel de suficiencia, y el fundamento en 4 líneas (fórmula, supuesto, dato, límite) ya existente. Si el rango es ancho o falta un dato, la marca es **«preliminar»**.
3. **Aceptar:** crea la OT por el flujo atómico existente (T09→T13) o «Guardar como preliminar».
Cada parámetro de la plantilla de familia (C34-1) gana un campo `quien_sabe` con valores `cliente | derivado | tecnico`:
- `cliente`: se pide en el paso 1.
- `derivado`: se calcula con la receta aprendida; no se muestra como campo, solo en el fundamento.
- `tecnico`: aparece en un bloque «Falta confirmar» únicamente si no se pudo derivar; es la **cotización firme por excepción**.
Políticas que dejan de pedirse en cada pedido y se leen de Definir (con valor por defecto y editables allí): días de capacidad, margen objetivo, intervalo, curva de reparto, preparación fija por lote, contingencia, subcontrato, transporte, gastos generales. Valor por defecto de los datos del cliente = el del último pedido de la misma familia.
Eliminar los campos duplicados (contrato, intervalo, curva, margen, precio, cliente aparecían dos veces). El modo antiguo (actividades, inductores, material) queda como «Avanzado», plegado, una sola vez.
Umbral de firme: parámetro `umbral_firme` (monto y ancho de rango P05–P95/costo) en Definir; por encima, el resultado dice «requiere confirmación técnica».
Pruebas: (a) Chromium: un pedido completo de punta a punta con ≤ 6 campos hasta la OT; (b) unitaria: familia con un parámetro `derivado` y uno `tecnico` — con el derivable calculado no pide nada técnico; si falta, lo pide y marca «preliminar»; (c) las 4 pruebas de rubro de C34-6 siguen verdes sin cambiar el número esperado.

## C35-4 Manual y evidencia
Actualizar `docs/entrega/MANUAL_DESCRIPTIVO.md` (80/20, sin crecer más de 150 palabras) con el menú nuevo y el Pedido en 3 pasos. Evidencia en `docs/entrega/evidencias/C35_N_*.md` con medición de cabecera y recorrido de 26 pantallas. Capturas nuevas de Pedido y menú para el entregable 10. Tiempos en tu CSV.

## Cierre
Reporte final: PRs, compuerta, pendientes y cualquier prueba que haya requerido decisión del dueño.
