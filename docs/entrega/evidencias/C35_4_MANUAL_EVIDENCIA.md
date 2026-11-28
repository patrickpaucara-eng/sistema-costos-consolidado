# C35-4 · Manual y capturas

Base: rama apilada `codex/C35-4` sobre `codex/C35-3` (`5c952af`).

## Cambios

- El manual describe los seis destinos del menú y el flujo Pedido en tres pasos. El conteo aumentó de 1.021 a 1.070 palabras: **49 palabras netas**, por debajo del máximo de 150.
- Se guardaron capturas nuevas del menú y de la pantalla Pedido desde la E2E propia de Chromium:
  - [Menú de seis destinos](C35_4_MENU.png)
  - [Pedido: resultado revisado antes de aceptar](C35_4_PEDIDO.png)

## Estado

Las capturas se generaron con el libro Frenosa copiado en un espacio temporal y una OT de prueba; no se alteró el libro fuente. C35-4 no cambia código ni cálculo. La compuerta completa no se ejecutó en esta rama: la prueba funcional heredada C34-5 usa los campos retirados del pedido antiguo y su actualización requiere la decisión documentada en `ordenes/RESPUESTAS_CODEX_24NOV.md`. Las pruebas propias de C35-3 que generaron las capturas pasaron (5/5).

![Menú del sistema](C35_4_MENU.png)

![Resultado del pedido antes de abrir la OT](C35_4_PEDIDO.png)
