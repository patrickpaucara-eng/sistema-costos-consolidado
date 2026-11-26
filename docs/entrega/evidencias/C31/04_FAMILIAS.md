# C31 · Punto 4: familias

Operación: en Estimar → Familias, ingrese historia JSON por actividad o recurso; opcionalmente agregue componente y segunda familia. Analice y use la receta en el cotizador, con duración mayor que cero.

Verificación: `python -m pytest tests/test_c31_4_familias.py -q`; dos casos manuales, límites de entrada, navegación en Chromium y cotización proyectada mediante API.

Límites: historia y selección no se guardan; es una propuesta que requiere revisión. Un componente fuera del intervalo no puede seleccionarse para cotizar. No se crea OT ni se aprueba fusión. Ver la captura `04_familias.png`.
