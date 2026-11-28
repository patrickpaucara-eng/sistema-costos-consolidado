# C35-2 · Cabecera compacta

## Medición Chromium

Medición en 1366 × 768 con la aplicación local y el mismo perfil Chromium antes y después:

| Medida | Antes | C35-2 | Cambio |
|---|---:|---:|---:|
| Alto de cabecera | 332,44 px | 48 px | −284,44 px |
| Inicio del panel principal | 396,44 px | 64 px | −332,44 px |
| Zona útil hasta el pie del viewport | 371,56 px | 704 px | +332,44 px |

La prueba `tests/test_c35_2_cabecera.py` afirma cabecera ≤48 px, inicio pegado arriba, controles en una sola línea y una ganancia mínima de 140 px. También comprueba que «Más» lleve a Inicio y que allí funcionen la consulta y las plantillas.

## Cambio

Empresa, síntesis, periodo, sello y suficiencia permanecen en la barra fija de una línea. La suficiencia se recorta visualmente con el mensaje completo en su atributo accesible `title`. Plantilla por nivel, descarga, consultar y calcular viven en la pantalla Inicio; «Más» da acceso directo a esa sección. Los identificadores y eventos existentes se conservan.

## Límite

Las capturas de menú y Pedido forman parte de C35-4.

## Verificación de integración (27-nov-2026)

Las pruebas focalizadas de navegación, cabecera y modelo pasan juntas: **3 pasaron** en Chromium. Tras la autorización del dueño del 27-nov, `tests/test_pantalla_modelo_costeo.py` ahora navega Inicio → consultar → Modelo → Calidad con destino → pestaña; no se modificaron sus aserciones de modelo, trazas, actividades o avisos.

La primera compuerta completa dio **ROJA**: 521 pasaron, 1 falló, 15 subpruebas pasaron y el contrato de resultados cumple. Tras la autorización y el ajuste limitado de navegación, la segunda compuerta completa dio **VERDE: 564 pruebas, 1 advertencia y 26 subpruebas; contrato de resultados válido**. La corrida final fue `PATH=/tmp/reyna-costos-test/bin:$PATH python tools/verificar.py`.
