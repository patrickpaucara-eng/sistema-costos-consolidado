# ENTREGA MN 01 · apoyo a la monografía (olas 4 y 5)

Reglas: no se modifica código del repo, solo se agregan documentos y archivos de prueba. Lo que no se pudo comprobar va marcado **POR VERIFICAR**.

## Avance

| Pieza | Estado | Archivo |
|---|---|---|
| 24 libros_hostiles/ | **Hecha** (28/11) | `libros_hostiles/` (8 + control, LEEME por archivo, generador) |
| 25 MONOGRAFIA_1_textos.docx | pendiente | — |
| 26 INFORME_PRUEBAS_MN1_plantilla.docx | pendiente | — |
| 27 PRESENTACION_MN1.pptx | pendiente | — |
| 28 PREGUNTAS_JURADO_MN1.md | pendiente | — |
| 29 REVISION_INDEPENDIENTE_MN1.md | pendiente | — |
| 30 oraculo_SERVITEC.xlsx | pendiente | — |
| 31 prototipos_C37.html | pendiente | — |
| 32 GUION_PRUEBA_DUENO.md | pendiente (usará 01, 03, 05 y 07 de libros_hostiles) | — |

## Pieza 24: qué probar en 15 minutos
1. Abre `libros_hostiles/LEEME.md` y lee la tabla.
2. En el sistema, sube `01`, `03` y `07`. El mensaje debe ser el de la tabla, sin traza de Python.
3. Sube `05`. Hoy lo acepta sin aviso: es el hallazgo 2.
4. Sube `00` y `08`, y calcula 2025-07. Los dos deben dar REB 22,975 y MPR 5,165.

## Qué decides tú
- ¿Los hallazgos 1–4 (fechas al revés, duplicados, criterio en cero y texto en montos) se corrigen antes del 9-dic? La corrección es de Claude, en el motor; aquí solo se reporta.
- **Hace falta el repo completo, o al menos `fuente/DBD_Fuente.xlsx` y `casos/plantilla_dbd.xlsx`**, para correr el cálculo. Con eso se verifican las cifras de control, y la pieza 30 (oráculo) se puede contrastar con el motor.
