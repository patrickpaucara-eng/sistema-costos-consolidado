# ENTREGA MN 01 · apoyo a la monografía (olas 4 y 5)

Reglas: no se modifica código del repo, solo se agregan documentos y archivos de prueba. Lo que no se pudo comprobar va marcado **POR VERIFICAR**.

## Avance

| Pieza | Estado | Archivo |
|---|---|---|
| 24 libros_hostiles/ | **Hecha y verificada** (28/11): `verificar_pieza24.py` → OK con validar() y calcular() | `libros_hostiles/` |
| 25 MONOGRAFIA_1_textos.docx | **Hecha y verificada** (28/11): `verificar_pieza25.py` → OK | `pieza25/` (6 páginas) |
| 26 INFORME_PRUEBAS_MN1_plantilla.docx | pendiente | — |
| 27 PRESENTACION_MN1.pptx | pendiente | — |
| 28 PREGUNTAS_JURADO_MN1.md | pendiente | — |
| 29 REVISION_INDEPENDIENTE_MN1.md | pendiente | — |
| 30 oraculo_SERVITEC.xlsx | **Hecha y verificada** (28/11): `verificar_pieza30.py` → OK; oráculo = motor en las 2 órdenes, 10 elementos y 27 flechas | `pieza30/` |
| 31 prototipos_C37.html | pendiente | — |
| 32 GUION_PRUEBA_DUENO.md | pendiente (usará 01, 03, 05 y 07 de libros_hostiles) | — |

## Cómo se verifica cada pieza

Cada verificación toma la raíz del repo, que debe tener `fuente/DBD_Fuente.xlsx` y `casos/plantilla_dbd.xlsx`. Ninguna modifica nada.

| Pieza | Comando | Qué comprueba | Resultado 28/11 |
|---|---|---|---|
| 24 | `python -I libros_hostiles/verificar_pieza24.py <repo>/src` | Los 9 libros: mensaje de validar() y resultado de calcular() de julio | OK |
| 25 | `python -I pieza25/verificar_pieza25.py <repo> SERVITEC_sintetico.xlsx` | Secciones, los 6 límites, misión aprobada textual, todas las cifras contra el repo, rutas y afirmaciones sobre el código (14) y sobre el libro (2), fuentes citadas | OK |
| 30 | `python -I pieza30/verificar_pieza30.py <repo> SERVITEC_sintetico.xlsx` | Recalcula con LibreOffice (777 fórmulas, 0 errores), solo fórmulas fuera de DATOS, DATOS igual al libro, oráculo = calcular() por orden, elemento y etapa | OK; diferencia 0.00 en REB y MPR |

Las verificaciones de las piezas 25 y 30 también se probaron al revés, con copias alteradas a propósito: las dos fallaron y nombraron el error. En la 30, además, ubicaron la etapa donde estaba (P4C).

## Hallazgo nuevo (pieza 24, con el motor completo)

**El libro 05, con una orden duplicada, se acepta y calcula mal sin aviso.** REB queda con cantidad 12 y costo unitario 1,914.58, cuando lo correcto es 2,297.50; el margen del mes sube de 9,860 a 13,422.33. Lo corrige otro agente antes del 9-dic. Cuando lo corrija, `verificar_pieza24.py` fallará a propósito en el 05; ahí hay que actualizar lo esperado.

## Lo que quedó POR VERIFICAR

| Pieza | Punto | Qué falta |
|---|---|---|
| 24 | 07 truncado en el ejecutable (sin traza, sin reemplazar el libro bueno) | Probarlo en el .exe (pieza 32) |
| 25 | Referencias de Oria (GE704W) y de los libros MCD/DBD | Título, año y editorial |
| 25 | «562 pruebas» y «30/30» | Cifras de ETAPAS_DESARROLLO.md que no volví a correr. Van a la pieza 26 |
| 25 | Siglas de los modelos (EC, CA, ACE…) | Las tomé del código; contrastar con los apuntes de Oria |

## Pieza 24: qué probar en 15 minutos
1. Abre `libros_hostiles/LEEME.md` y lee la tabla.
2. En el sistema, sube `01`, `03` y `07`. El mensaje debe ser el de la tabla, sin traza de Python.
3. Sube `05`. Hoy lo acepta sin aviso: es el hallazgo 2.
4. Sube `00` y `08`, y calcula 2025-07. Los dos deben dar REB 22,975 y MPR 5,165; ya comprobado con calcular().

## Qué decides tú
- ~~¿Se corrigen los hallazgos antes del 9-dic?~~ Respondido el 28/11: sí; lo hace otro agente.
- ~~Misión~~ Resuelto el 28/11: se usa la v2.1 aprobada (E-041), con el ajuste del dueño.

## Orden de trabajo (indicado por el dueño el 28/11)

Pieza 30 → **auditoría independiente (AUDITORIA_MN1.md)** → piezas de MN 2 sin empezar (5–18) → piezas de documentos 26–29 → 31–32.
