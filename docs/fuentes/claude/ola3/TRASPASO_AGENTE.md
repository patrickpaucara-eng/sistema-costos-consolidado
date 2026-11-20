# Traspaso para el siguiente agente (16-nov-2026 08:15 Lima) — léelo completo antes de tocar nada

Repo: `patrickpaucara-eng/sistema-costos-reyna`. Proyecto claude.ai: «Desarrollo de modelo de costos intento 2» (docs `claude/*.md`).
Dueño: Patrick (estudiante de costos; profesor exigente). Mensajes simples, sin código a la vista, **con % de avance en cada mensaje**.
Avance: plan ≈ 93 %. Plan maestro: `informes/FINAL/PLAN_CIERRE_SISTEMA.md` (rama `arq/documentos-finales`; también doc de proyecto).
Estado del sistema: `claude/SISTEMA_ACTUAL.md`. No hay tareas programadas activas (todas detenidas).

## 1. Reglas que no se rompen
1. Nunca escribir tokens en el repo ni en mensajes.
2. **Nada a main sin compuerta completa:** `python3 -m pytest pruebas -q` verde · historia `cd kit && python3 motor_espejo.py salida_b/Sistema_Costos.xlsx` = 392/392 · O-1 `python3 informes/V41/integra_env.py` = 66 valores, dif ≤ 1e-9 · un valor recalculado a mano · y si toca motor/estructura/cálculo: **prueba del dueño en Excel + paridad COINCIDE + visto bueno escrito**.
3. Anti-parche: si una prueba vieja falla, decidir si cambió el contrato (documentar [ARQ] y avisar) o es error. Nunca ajustar un esperado para que pase.
4. Motor VBA (`kit/vba/*.bas`) y espejo (`kit/motor_espejo.py`) **idénticos** (P19). VBA con `Option Explicit`: revisar nombres de variables (error real visto: `emp` vs `empA`). Correr `cd kit && python3 lint_vba.py` (hallazgo previo aceptado: P20 en ui.bas).
5. Los binarios (`fuente/*.xlsx`) se cambian **solo por script** `.dsh/build/aplicar_*.py` (idempotentes). Receta al unir ramas: tomar binarios de main → `aplicar_I1 → I0b → I2 → I10 → I2b → I3 → I5 → D12 → D1 → OLA1B` → `cd kit && python3 construir.py` → compuerta. Revisar en la salida de construir: «Coherencia del DBD: 0 error(es)» y «Base desde DBD_4: Relaciones a revisar: 0» (no bloquean, pero deben estar en 0).
6. Demo intocable: rama `prototipo/v41-congelado` (3a28500) y zip entregado. Caso palta prohibido (ya limpiado). Solo valuación promedio. Etiquetas [VERIFICADO]/[INFERIDO]. No desarrollar métodos nuevos sin permiso del dueño. Material de Oria: solo conceptos citados, cero código copiado.
7. Git: `export GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=safe.directory GIT_CONFIG_VALUE_0='*'`. Unión a main: squash por `gh api` REST (GraphQL no disponible), título «[ARQ] …». Commits con `Co-Authored-By: Claude …`. Cuidado con `git stash` al cambiar de rama (se perdió un cambio una vez): preferir commit en la rama antes de cambiar.
8. Obreras (si hay créditos): rama propia, PR contra `desarrollo/*`, nunca main, nunca merge; encargos ≤ 40 min con entregable verificable.

## 2. Dónde está cada cosa
| Rama | Contenido | Estado |
|---|---|---|
| `main` | I-0…I-10, I-5 (PR #277) | Compuerta verde. **Tiene un defecto de metadatos de I-5** (FK de empresa mal declaradas) corregido en `desarrollo/ola1` |
| `desarrollo/ola1` | D12 (empresa gana al común: comodín «*» en Buscar/coincide), D1 (UMBRAL→PARAMETRO), Ola 1b (pantalla OPERAR MES, `kit/vba/operar.bas`, `kit/usuario/operar_mes.py` referencia, `plantilla_mes.py`, `informes/OLA1B/`), corrección FK de I-5 | pytest 520, 392/392, 66/66. **Falta: prueba del dueño en Excel + visto bueno** |
| `desarrollo/deuda` | `informes/DEUDA/DIAGNOSTICO_GLOBAL.md` (D1…D14), cuadre de cuentas (J), 6 meses (K), OT-107 protección | Solo informes/pruebas |
| `desarrollo/I-9` | `ordenes/V41/OT-106_I9_PREDICTIVO_DISENO.md` | Solo diseño |
| `arq/documentos-finales` | GUION_DEMO, CHEATSHEET_DEFENSA, RESUMEN_EJECUTIVO, PLAN_CIERRE_SISTEMA, SISTEMA_ACTUAL, COMPARACION_PROYECTO_FRENOSA, este traspaso | Documentos |

## 3. Siguiente paso exacto
1. **Esperar al dueño:** probará Ola 1b en Excel. El paquete que tiene (`PRUEBA_OLA1B.zip`) es **anterior a D1**: generar uno nuevo desde `desarrollo/ola1` (`cd kit && python3 construir.py`; copiar `kit/entrega/Sistema_Costos` + `informes/OLA1B/CARGA_MES.xlsx` + `GUIA_USUARIO.md`; regenerar la plantilla con `python3 kit/usuario/plantilla_mes.py kit/salida_b/Sistema_Costos.xlsx informes/OLA1B/CARGA_MES.xlsx`). Login `JCOSTOS` / `1234`. Esperado: Validar «8 de 8 filas OK», Importar «7 registradas», Cerrar 2026-09 «6 registradas», OS-01 = S/ 28,321.87, margen venta 880.20.
   - **Riesgo:** `operar.bas` y la pantalla nunca corrieron en Excel real; si el dueño reporta error de compilación, corregir en `kit/vba/` y repetir.
2. Con su visto bueno → PR squash `desarrollo/ola1` → main («[ARQ] Integrar Ola 1 y 1b»), rehacer compuerta en main.
3. Luego, en este orden (PLAN_CIERRE_SISTEMA.md):
   - **Ola 1b+** (solo lectura, sin riesgo): plantilla con hojas Diccionario/Reglas generadas del DBD → **dashboard** → **análisis por periodos** (ver COMPARACION_PROYECTO_FRENOSA.md §7-8: leer solo lo publicado, con traza).
   - **D13** índice en Buscar/coincide (rendimiento; VBA = espejo; medir antes/después).
   - **Ola 2** (D3 KARDEX derivada, D2 DIARIO→LOG_TRX, D4 ACTOR) en paralelo.
   - **Ola 3** en serie con caso a mano y Excel del dueño: D9 un solo escritor de cuentas (14 xfail de J), flete en T14 (NIC 2), D5…D8, D14 reexpresión del costo provisional de venta.
   - **Ola 4** OT-107 huella + retirar tabla UMBRAL (ya sin lectores) · **Ola 5** I-9 (analogía → enrutador por evidencia → regresión → MC calibrado) + simulación en copia + consulta guiada · **Ola 6** caso 6 meses dos empresas, etiqueta v5.0.

## 4. Decisiones del dueño vigentes
- I-5: un usuario = una empresa; PAR_EMP con «*» común; R-1..R-4 aprobados (filas actuales a empresa B; COSTOS1 → B; comodín en motor; pruebas al contrato).
- Cuentas: tablas físicas con un solo escritor (D-I0b-1). MCD v3.2 aprobado como borrador (D-I0b-2). Orden de arreglos D-I0b-3.
- Reparto del indirecto por tiempo dentro del mes: investigación futura (no construir).
- Método «MOD por tiempo estándar» (de Frenosa): **pendiente de permiso**.

## 5. Hallazgos abiertos (no olvidar)
D9 (cuentas con 1-7 escritores), D13 (carga 110→767 ms/línea en 6 meses), D14 (costo provisional de venta no se reexpresa si el plan está en otra unidad), flete ausente en T14, LINEA.LIN_REC referencia lógica (LINEA sin columna de empresa).
