# OT-C08 · Paquete de entregables (hecho por Claude, 21-nov)
**Comando:** `python tools/entrega/armar.py --periodo 2010-12` → carpeta `entrega_MN01/` con LEEME.txt (índice 1–13).
- Nuevos: Excel `entrada` (CSV del caso + supuestos + hoja FUENTES); total de impacto en hoja Propuestas.
- HTML sin conexión rediseñado: encabezado con mes y síntesis explicada, tarjetas KPI con formato S/, leyenda y ejes, escenarios sin solapamiento, etiquetas en español. Los valores crudos quedan en `data-valor` (trazabilidad).
- Prueba: `tests/test_entrega_armar.py` (13 ítems menos EXE; costo total de los Excel = contrato; HTML sin URL).
- Pendiente: EXE (Windows); Manual descriptivo con contenido técnico; chats exportados en `docs/entrega/chats/`.
