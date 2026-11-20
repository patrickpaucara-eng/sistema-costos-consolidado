# Fuentes para la consolidación

Se conservaron los seis adjuntos recibidos el 18 de noviembre de 2026. Ocupan 52.957.601 bytes. El [manifiesto SHA-256](SHA256SUMS.txt) permite verificar que los originales coinciden con los archivos recibidos.

| Fuente | Original | Material de consulta |
|---|---|---|
| REYNA-MCD-2025 y REYNA-DBD | [ZIP de Drive](originales/drive-download-20261118T142451Z-1-001.zip) | Contiene `LIBRO COMPLETO MCD 2025.pdf` (210 páginas) y `LIBRO COMPLETO DBD.pdf` (238 páginas). |
| CLEIN-01 | [Presentación de la sesión 1](originales/S01%20CLEIN%202026%20NOV%20WORIA.pdf) | PDF de 28 páginas. |
| CLEIN-02 | [Archivo de la sesión 2](originales/SESION%2002%20CLEIN%202026%20WORIA.rar) | Cinco archivos con herramientas de costeo ABC, un prototipo de cadena de suministro y documentos de sesión. |
| CLEIN-03 | [Archivo de la sesión 3](originales/SESION%2003%20CLEIN%202026%20WORIA.rar) | Trece archivos con modelos ABC y Montecarlo, el caso ALPROSA, el diseño funcional, la guía y prototipos. |
| ORIA-ACADEMICO | [Material académico de ORIA](originales/material%20academico%20oria.zip) | Siete libros Excel de casos resueltos, semanas 1 a 7. |
| FRENOSA-ANTECEDENTE | [Exportación JSONL del proyecto pasado](originales/proyectoPasado.jsonl) | 46 registros. Usar el número de línea para citar cada entrada. Los XLSX, PNG y ZIP se representan como texto. Cinco nombres se repiten. |
| CLAUDE-TRANSFERENCIA | [Ficha de transferencia](claude/README.md) | Archivo íntegro recibido el 19 de noviembre; SHA separado. Contiene contexto histórico cuya autorización inicial fue modificada por mensajes posteriores del dueño. |
| CLAUDE-OLA3 | [Transferencias y directrices finales](claude/ola3/README.md) | Se preservaron `SISTEMA_ACTUAL`, `TRASPASO_AGENTE`, `DIRECTRICES_OLA3_VALIDADAS` y `COMPARACION_PROYECTO_FRENOSA`, con manifiesto SHA-256. Duplicados idénticos se guardaron una sola vez. |

El [directorio de las sesiones 2 y 3](rar-directorios.json) identifica los archivos dentro de cada RAR. El [directorio del antecedente de Frenosa](antecedente-directorio.json) registra el nombre, el tipo y el número de línea de cada entrada. La exportación sirve para recuperar documentación y datos representados. Para verificar fórmulas, macros o componentes ejecutables se necesitarán los archivos originales correspondientes.

Para verificar los seis adjuntos desde la raíz del repositorio:

```sh
cd docs/fuentes
sha256sum -c SHA256SUMS.txt
```

## Uso previsto

La matriz metodológica citará el libro y la página del PDF, la regla, la evidencia del sistema y su prueba de aceptación. Los materiales de ORIA y Frenosa servirán para contrastar los casos. El problema de robustez señalado en Frenosa queda registrado como escenario prioritario por reconstruir.
