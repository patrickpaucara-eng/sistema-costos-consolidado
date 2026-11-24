# OT-C16 · Generador de presentación ejecutiva (tarea 3.2)
Rama `codex/C16`. Nuevo tipo `presentacion` en `src/reyna_local/exportar.py` (salida .pptx) que lee SOLO el contrato de resultados.
- Primero: comprobar que `python-pptx` entra en el EXE (`tools/windows/` / `build.py` hidden imports) y que la compilación de GitHub pasa. Si no entra, generar HTML imprimible como alternativa y avisar.
- 8 diapositivas: portada (empresa, periodo, síntesis, sello); KPI; costo por producto; relevancia (Pareto); hallazgos y causa; proyección 6 meses con banda (o «no estimable»); propuestas con impacto y responsable; plan de implementación (propuestas ordenadas por impacto con plazo).
- Cifras con 2 decimales, idénticas al contrato.
Prueba: el .pptx se abre con python-pptx, tiene 8 diapositivas y las cifras de KPI coinciden con el JSON.
Aceptación: COMPUERTA VERDE y build de Windows en verde.
