# OT-C01 · Pantallas y dashboard

## Qué cambió

El panel consulta `/api/resultados` y muestra el contrato de resultados Frenosa julio 2010 REAL, con cinco indicadores y costos por orden. Los gráficos y tablas se generan localmente desde los datos del contrato, sin calcular costos. El selector permite cambiar síntesis y periodo; cuando no hay un resultado publicado se muestra un contrato rotulado **EJEMPLO**, con su síntesis y periodo originales. Las entradas de compras y cantidades vendidas del caso son simuladas, incluso en julio. Este resultado académico está sujeto a validación.

El JSON real no estaba presente en el árbol Git de la base: se generó con el productor y el generador ya existentes de Claude en un XLSX temporal, sin modificar cálculo. SHA-256 del contrato: `33dd1f6a6c1dc3b0f0cb7e530c4fd52d5c67ebabe7442e19046d4ea3e31a3a9e`. Generador `casos/frenosa/generar.py`: `bc8daa4897123659d7be70f62f8ba25effa8f6eed6a32ed551160fb5d94beb9a`; plantilla: `9f0847fef88a140621b7c0fb430cb265832efa595dfd3ffab184c55343e78fa3`; Ventas.csv: `ec7480f286037396fee7f8ed7f8c86b72e7dc1456e596c7b52b837af9a599608`. El archivo publicado se empaqueta junto a la pantalla para operación local, y la carpeta `<data-dir>/resultados/` permite añadir contratos posteriores.

## Cómo probar en 15 minutos

1. Con las dependencias instaladas, ejecutar `python -m reyna_local --data-dir /tmp/reyna-piloto --port 8765` y abrir `http://127.0.0.1:8765/` en el mismo equipo.
2. Elegir REAL y 2010-07. Debe verse Frenosa y ventas de S/ 888.730. Revisar costos por objeto; las capturas de las diez secciones están en esta carpeta.
3. Cambiar a ESTIMADO o a un periodo que aún no exista y pulsar «Consultar resultados»: debe aparecer «EJEMPLO». Las secciones sin información deben indicarlo.
4. Ejecutar `python tools/verificar.py` y comprobar `COMPUERTA: VERDE`. La prueba `tests/test_api_resultados.py` comprueba contrato real, fallback y parámetros inválidos.

## Qué queda pendiente

Claude conectará los contratos de los demás periodos y síntesis, análisis, proyecciones y propuestas cuando estén calculados; las listas vacías actuales no representan cero ni resultados finales. La acción de cerrar mes requiere importar y seleccionar un espacio válido. Los reportes descargables corresponden a OT-C02. El análisis independiente de la exactitud metodológica y la validación en Windows siguen pendientes.
