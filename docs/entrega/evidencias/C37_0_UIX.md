# C37-0 · Plantilla UIX

Base: `desarrollo/mono@ff09bec`; rama `codex/C37-0`.

`docs/diseno/PLANTILLA_UIX.md` define un patrón común para las pantallas que se modifiquen en C37-1 a C37-7: pestañas, entradas, resultado, fundamento y siguiente acción. Incluye accesibilidad de teclado, límites de pasos/campos, uso de datos precargados, representación explícita de faltantes y errores locales en español. El documento tiene menos de una página y no cambia código ni comportamiento.

Verificación de cierre: `python tools/verificar.py` → **COMPUERTA VERDE, 563 pruebas pasaron; contrato de resultados válido**. El estándar no prueba por sí solo la conformidad de todas las pantallas actuales; cada punto C37 debe demostrarla en sus pruebas y evidencia.
