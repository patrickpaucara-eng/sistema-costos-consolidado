# Fuentes del caso Frenosa

Los datos provienen del texto de la exportación JSONL, no de los XLSX binarios originales. Los hash por entrada identifican el texto UTF-8 de `contenido`, no el Excel. La columna `periodo` añadida identifica el archivo mensual; la columna original `periodo` de la hoja Periodo se conserva como `periodo_descripcion_fuente` para evitar cabeceras duplicadas.

SHA-256 del JSONL: `d2c732e130876540c7ea1602c785e2cc43e55444625a4182d036cdad2c017a22`.

Julio recoge datos del caso PUCP según la fuente; compras/kardex y cantidades vendidas son simuladas, incluso en julio. Los demás meses son simulados. Esta atribución proviene de la exportación y debe cotejarse con los originales.

| Periodo | Línea JSONL | Nombre representado | SHA-256 del contenido textual |
|---|---:|---|---|
| 2010-01 | 33 | frenosa_datos_entrada_abc_2010_01.xlsx | `11559feff85b595f057ac9b8393ee3633a087e1e59949c99170638eb21d8249e` |
| 2010-02 | 22 | frenosa_datos_entrada_abc_2010_02.xlsx | `d72b5c1be34aca6bf19f6be993d955670b763ba3849d3dc957b48e80af8af668` |
| 2010-03 | 24 | frenosa_datos_entrada_abc_2010_03.xlsx | `bb6c2afa1c3788f8e370927176e68000ef45403536c776ff8b19579a57032210` |
| 2010-04 | 28 | frenosa_datos_entrada_abc_2010_04.xlsx | `242239a5ff6cd02dcb0f1694eabea71705221da70d8a3af1673c44a8f15bb49b` |
| 2010-05 | 31 | frenosa_datos_entrada_abc_2010_05.xlsx | `036bb31fa72275f5fa44beedde3e52182f07d241c8e7fd7d443557783b860d25` |
| 2010-06 | 25 | frenosa_datos_entrada_abc_2010_06.xlsx | `e3d46ce3ddfbe3fbf226aa7dd4a37408e41dceb9590387f399d064cbb58d8b3b` |
| 2010-07 | 26 | frenosa_datos_entrada_abc_2010_07.xlsx | `935b3a8c496677cedfdb7d134592464fc3dd4bc6b776ad3db30404337d24c70d` |
| 2010-08 | 29 | frenosa_datos_entrada_abc_2010_08.xlsx | `19bc7ead3fbba9e8dd98cca51641318a837e2aab588a0d3e53b1e7a66daa9750` |
| 2010-09 | 20 | frenosa_datos_entrada_abc_2010_09.xlsx | `bbcb7ef30fe017d752218a4017d1d3de23ec4d893e2fe0a7f9ec9cd1fa3183a1` |
| 2010-10 | 27 | frenosa_datos_entrada_abc_2010_10.xlsx | `3069b6333b6e10cc14cf7dceadb4e787a06d861eb25874c5fab8eddbbe1d04aa` |
| 2010-11 | 30 | frenosa_datos_entrada_abc_2010_11.xlsx | `bd5daf6cc83287279a18eab9ce9aa9c6f5d5375aea5d7354e765ad38915d50bc` |
| 2010-12 | 32 | frenosa_datos_entrada_abc_2010_12.xlsx | `807257ad2b51fd5cdac75eb3025c26846c001a79dd7fad131ea48e696692b8ca` |

El archivo de julio representado por `frenosa_datos_entrada_abc.xlsx` aparece dos veces con contenido distinto (líneas 11 y 34); no se mezcla con la versión mensual 2010-07 sin comparar las fuentes.

