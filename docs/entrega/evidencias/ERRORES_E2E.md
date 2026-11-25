# Errores y límites observados en el recorrido C24

| Paso | Esperado | Obtenido | Causa probable |
|---|---|---|---|
| Abrir HTML local en Chromium de este entorno | Abrir el archivo directamente sin red | `ERR_BLOCKED_BY_ADMINISTRATOR` para `file://` | Política del Chromium administrado; falta confirmar apertura mediante doble clic en el equipo del usuario. |
