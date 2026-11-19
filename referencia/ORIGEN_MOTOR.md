# Procedencia del motor operativo

`src/reyna_local/motor_espejo.py` conserva byte a byte `kit/motor_espejo.py` de `patrickpaucara-eng/sistema-costos-reyna`, revisión `cac2501d9f712655dda466d216dc5bff2dd446a5` (Ola 1). SHA-256: `8c962583170cbb200c564bef8edfd95ae931602b82fa2f89f2bb48bcd9ce2a11`.

El adaptador `store.py` ejecuta ese intérprete sobre las reglas cargadas del libro y persiste sus cambios. La UI y HTTP no calculan costos. La habilitación inicial de T14/T15 limita el alcance aceptado; no introduce fórmulas de costos nuevas. Las políticas siguen en la configuración heredada y requieren su verificación contra MCD/DBD y ORIA.

El contrato de operación del servicio —crear espacio, ejecutar solicitud, consultar tabla, reabrir— separa la interfaz del almacenamiento. Reemplazar Excel en el futuro requerirá otro adaptador y repetir equivalencia, recuperación e historia. Este contrato no promete compatibilidad automática con cualquier tecnología ni implementa SQLite.

La fixture y sus hashes están en `tests/fixtures/ola1`. El VBA original está archivado en `referencia/vba-congelado`; el piloto no lo ejecuta ni lo modifica. El historial documental del consolidado y el del original tienen ascendencias diferentes. Para devolver cambios a Claude se debe preparar una integración con procedencia y pruebas, sin presuponer un merge directo.
