# OT-C06 · Documentos de entrega

Un generador produce cinco archivos Word: cadena de conversaciones, etapas, resultados de pruebas, plantilla del manual descriptivo y manual de usuario. El documento de pruebas incluye cada caso en el JUnit, su propósito cuando está documentado, su resultado y las capturas disponibles de OT-C01 y OT-C04. La plantilla descriptiva deja marcadores `[CLAUDE]` para contenido técnico.

## Cómo probar

1. Poner las conversaciones exportadas como Markdown en `docs/entrega/chats/`, nombradas con fecha al inicio para ordenarlas cronológicamente. Mantener el nombre de cada hablante en el texto.
2. Ejecutar `PYTHONPATH=src python tools/documentos/generar.py --salida /tmp/documentos-reyna`. El comando ejecuta pytest, guarda sus resultados en el Word y genera los cinco archivos.
3. Abrirlos con Word o LibreOffice. En Word, actualizar el índice. Comprobar las capturas y completar las que aparezcan como pendientes.
4. Ejecutar `PYTHONPATH=src python -m pytest tests/test_documentos_generados.py -q` y la compuerta `python tools/verificar.py`.

## Pendiente

La rama base no incluye los chats exportados ni las capturas C04, que llegarán por su PR. El documento de pruebas debe regenerarse después de integrar el código y ejecutarse en el entorno de entrega; un resultado omitido se identifica como tal. El manual descriptivo requiere revisión y contenido de Claude. El índice usa un campo de Word y requiere actualizarse al abrir. La apertura se verificó con `python-docx`; sigue pendiente la revisión visual en Word y LibreOffice.

**Evidencia:** la generación con pytest real terminó con 88 pruebas y 26 subpruebas aprobadas (se excluyó la prueba del propio generador para evitar recursión). Se abrieron los cinco archivos con `python-docx`; el documento de etapas contiene 31 tablas y el de pruebas incorpora 10 capturas disponibles. La compuerta completa de esta rama pasó 89 pruebas y 26 subpruebas.
