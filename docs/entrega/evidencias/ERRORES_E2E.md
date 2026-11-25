# Errores de la prueba de punta a punta (para corrección en lote; sin parches)
| # | Paso | Esperado | Obtenido | Causa probable | Corrección propuesta |
|---|---|---|---|---|---|
| E1 | Cotizar pedido especial (Frenosa y SERVITEC) | Cotización con tasas del último mes | 422 «No hay un periodo cerrado para cotizar» | Los libros de demostración no tienen meses con PER_EST = C; la API exige cierre | Si no hay mes cerrado, usar el último mes calculado y devolver `aviso: «tasas provisionales: mes no cerrado»`; prueba con ambos casos |
