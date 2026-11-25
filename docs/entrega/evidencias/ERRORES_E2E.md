# Errores de la prueba de punta a punta

| # | Paso | Esperado | Obtenido | Causa probable | Corrección propuesta | Estado |
|---|---|---|---|---|---|---|
| E1 | Cotizar sin periodo cerrado (Frenosa y SERVITEC) | Usar el último mes calculado con aviso | Antes 422; ahora los casos con actividades operativas devuelven una cotización y aviso | El servicio exigía cierre | Usar último resultado REAL disponible del libro y advertir tasas provisionales | Corregido; `tests/test_c25_cotizacion_provisional.py` |
| E2 | Frenosa: cotizar pedido especial en `tools/e2e_recorrido.py` | 200 | 422: «La actividad A-CC no tiene un inductor único» | El recorrido elige las dos primeras actividades, de apoyo P4E; el cotizador exige una regla P4C única | Acordar un caso válido de actividades operativas para el recorrido; no modificar la prueba para hacerla pasar ni cambiar el motor sin autorización | Pendiente; `tests/test_c25_cotizacion_provisional.py` confirma el rechazo |
