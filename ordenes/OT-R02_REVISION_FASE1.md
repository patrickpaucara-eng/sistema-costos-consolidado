# OT-R02 · Revisión independiente (solo lectura): recíproco, banda y sello

**Rol:** revisor. No modifiques archivos ni crees ramas o PR. Rama `desarrollo/mono`.
**Alcance:** `git show 2a4ab17 1a05f27 -- src/metodos/reparto_etapas.py src/reyna_local/analisis.py src/reyna_local/calculo_local.py tests/test_modelo3_oria.py tests/test_banda_y_sello.py`

## Verifica (CUMPLE / FALLA / DUDA, con evidencia)
1. Recíproco (`_reciproco`): con servicios mutuos entre pares, ¿el resultado coincide con resolver X = propio + Pᵀ X? Prueba un caso propio de 3 pares. ¿Conserva el total?
2. Sin servicio de vuelta, ¿da el escalonado? ¿Un par sin regla o un ciclo cerrado (100 % entre pares) se rechaza con mensaje claro?
3. Capacidad (ocio) en un par del recíproco: ¿se mide con el uso del inductor original y conserva?
4. Banda (`proyectar`, `_errores_horizonte`): ¿hay fuga de datos futuros en los errores de cada horizonte? ¿La banda nunca tiene ancho cero y los horizontes sin errores suficientes se declaran en `banda_no_estimable`?
5. Sello (`huella_resultado`, `verificar_sello`): ¿cambiar cualquier cifra del resultado da `RESULTADO_ALTERADO`? ¿Hay campos que cambien solos entre guardar y verificar (orden, flotantes) y den falsos positivos?

Pruebas: `python -m pytest -q tests/test_modelo3_oria.py tests/test_banda_y_sello.py tests/test_naturaleza_costo.py`

## Entrega (chat, máximo 30 líneas)
Tabla `# | punto | veredicto | archivo:línea | evidencia | sugerencia` y una línea final: APROBADO / APROBADO CON OBSERVACIONES / RECHAZADO.
