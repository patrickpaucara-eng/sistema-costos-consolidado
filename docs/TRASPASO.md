# TRASPASO — empieza aquí (para cualquier agente que retome el coordinador)
*28-nov-2026. Escrito por Claude (coordinador). Léelo completo antes de tocar nada; luego `AGENTS.md`, `ordenes/COLA_CODEX.md` y las últimas 30 líneas de `docs/planificacion/DECISIONES_DUENO.md`.*

## 1. Qué es esto en una frase
Dos sistemas del dueño (Patrick, estudiante de Ing. Industrial, curso del Prof. **W. Oria**, método **MCD/DBD de Tino Reyna**):
- **A · Costos (MN 01, entrega 9-dic 18:00; código congelado 6-dic):** Python + Excel (libro DBD) + HTML local + EXE Windows. Ya funciona; se está puliendo y corrigiendo.
- **B · Planeamiento (MN 02, se muestra a Oria el 16-dic):** diseño cerrado (`tools/mapa_b/spec.py`), piezas 1, 2, 4 y `sintesis.py` hechas en `docs/entrega/otra_ia/B/`; el resto lo construye Codex después de la MN 01.
- **C · Aprendizaje:** vive dentro de A (no es otro sistema). Dos bases de datos, **no tres**; **no hay datawarehouse**: B solo lee el contrato publicado de A.
Mapa general: `docs/diagramas/mapa-sistemas-AB.html` (botón Gerente/Desarrollador). Detalle: `mapa-detalle-mn01.html`, `mapa-detalle-mn02.html`.

## 2. Roles (no cambiarlos)
| Quién | Hace | No hace |
|---|---|---|
| Dueño | Decide y prueba; aprueba todo cambio de prueba existente | — |
| Coordinador (Claude) | Arquitectura, cálculo/metodología, órdenes, revisa y **une** PRs en `desarrollo/mono` | No escribe volumen; no une a `main` |
| Codex | Construye por órdenes en `ordenes/`; ramas `codex/<orden>-N`, PR contra `desarrollo/mono` | Nunca fusiona; nunca `main` |
| Otra IA (cuenta sin GitHub, sin créditos ahora) | Piezas sueltas por zip | Nada en el repo |

## 3. Cómo se trabaja (reglas del dueño)
- **Unir PRs:** `python tools/unir_pr.py <n> <n>…` (une, resuelve conflictos de .csv/.md, corre la compuerta, publica y cierra solo si VERDE). Conflicto en código → se detiene. GraphQL está bloqueado: usar `gh api` REST.
- **Compuerta:** `python tools/verificar.py` → `COMPUERTA: VERDE` antes de todo commit/publicación (≈15 min; córrela en segundo plano). Las pruebas de `tests/auditoria_mn1` y `tests/datos` están **excluidas** de la compuerta a propósito (`tests/conftest.py`); se corren con su propio script.
- **Pruebas existentes:** no se editan aserciones ni cifras. Codex puede cambiar solo pasos de navegación/selectores (autorizado). Cualquier otra edición necesita una línea del dueño en `DECISIONES_DUENO.md`.
- **Durante una revisión del dueño:** NO corregir; registrar cada hallazgo como `E<n>` en `docs/entrega/evidencias/ERRORES_E2E.md` y corregir en lote con una orden. Último: **E46**.
- **Commits:** terminar con las líneas de atribución que indique la sesión. Nunca tokens en repo ni mensajes.
- **Documentos:** 80/20, breves. Mapas: **visuales, poco texto** (el dueño lo pidió explícitamente).
- **Principios del dueño para todo:** práctico (≤3 pasos, ≤6 campos, nunca pedir lo que el sistema ya sabe), aporta valor (cada pantalla termina en un número accionable), **entorno hostil** (sin 0 silenciosos ni trazas técnicas), Tino (evento = transacción consumada; ticket = evento futuro con recursos comprometidos; hechos inmutables; parámetros con vigencia), Oria (matriz de configuración + matriz de cálculo; lo repartido = lo gastado).

## 4. Estado al 28-nov 09:45 (verifica PRs abiertos y compuerta antes de confiar en esto)
- `desarrollo/mono` en VERDE (571 pruebas). Unidas: C32–C35, C37-0, C37-1, C37-2.
- **Cola de Codex** (`ordenes/COLA_CODEX.md`): E45+E46 (vista de matrices) → C37-3…7 → **C38** (10 correcciones de cálculo de la auditoría; si al 3-dic C37 no terminó, C38 va primero) → **C41** (lo que pide Oria en su SIC-ABCDIEP: precisión contra modelo ingenuo, Monte Carlo honesto, margen por capas; ver `docs/diseno/CONTRASTE_CLEIN.md`) → **C40** (archivar código que no corre; E43 aprobado) → documentos MN 1 → manual → C39 (contrato A→B) → B piezas 5–23.
- **K4 aprobado (28-nov):** K4 de `CONTRASTE_CLEIN.md` (autonomía: el sistema solo «propone» salvo habilitación escrita del dueño; Oria prohíbe cambios automáticos de precios, compras o personal).
- **Pendiente del coordinador:** unir PRs que lleguen; generar el EXE final (GitHub Actions, workflow de Windows; `tools/windows/build.py`) cuando C37+C38 estén unidas; llenar cifras finales en documentos.
- **Pendiente del dueño:** probar el EXE sin internet con el guion; horas (`docs/entrega/tiempos/`); exportar chats (entregable 1); decidir qué código que no corre se archiva (E43: `analitica/`, `analitica2/`, métodos «cáscara»); zip de 13 entregables; ensayo.

## 5. Decisiones que una IA nueva suele equivocar
| Tema | Lo correcto | Error típico |
|---|---|---|
| Misión de A | v2.1 (E-041) sin «y Presupuestos» | inventar otra |
| Misión de B | la del 27-nov: **programación de recursos comprometidos**; todo presupuesto es **síntesis** del plan (catálogo en `sintesis.py`: reloj devengo/caja + clases + agrupación). M6 queda cubierta como síntesis | crear un módulo por tipo de presupuesto |
| Eventos | transacciones consumadas (pedido, recepción, parada, cobro/pago, no conformidad, cambio de dato maestro) | llamar «evento» a restricción, oportunidad, urgencia |
| Datos | B lee solo `contrato.py`; si falta un dato, se amplía el contrato (C39) | leer el libro de costos desde B |
| SERVITEC | empresa sintética (REB 22,975 / MPR 5,165); oráculo independiente en `tests/datos/oraculo_servitec` (0.00). **No prueba el recíproco** (un solo centro productivo): eso lo prueba `tests/test_modelo3_oria.py` | citar SERVITEC como prueba del recíproco |
| Frenosa | caso real del curso; **no** se envía a la otra IA ni a terceros | adjuntar `frenosa*.json/xlsx` |
| Diferencias en matrices (E45/E46) | son de **pantalla**; los totales del motor son correctos | «corregir» el motor |
| Prohibido / archivado | caso palta, VBA (congelado), SQLite (después), repo `sistema-costos-reyna` (solo lectura), OT-C36 y OT-B01 (reemplazadas), «93 %» histórico | usarlos como vigentes |
| Fuentes externas | Meta AI, DeepSeek y otras IA son opinión, no fuente; lo útil ya está en `METODO_PLANEAMIENTO.md` §7 | adoptar sus cifras o afirmaciones |

## 6. Dónde está cada cosa
- Decisiones del dueño: `docs/planificacion/DECISIONES_DUENO.md` (manda sobre todo lo demás).
- Errores y hallazgos: `docs/entrega/evidencias/ERRORES_E2E.md` (E1–E46), `AUDITORIA_MN1.md`.
- Órdenes: `ordenes/OT-C3x_*.md`, cola en `ordenes/COLA_CODEX.md`; dudas de Codex en `ordenes/RESPUESTAS_CODEX_24NOV.md`.
- Diseño B: `tools/mapa_b/spec.py` (manda), `validar.py` (11/11), `docs/diseno/B_TRES_DECISIONES.md`, `docs/entrega/otra_ia/B/BITACORA_B.md`.
- Proyecto de claude.ai (fuera del repo): misiones y diccionarios históricos (`claude/MODELO_FUNCIONAL.md`, `claude/PRES_*`); consultar, no copiar.

## 7. Cómo hablarle al dueño
Español, frases cortas, sin jerga; responder primero lo que preguntó; cuando haya algo que decidir, una pregunta concreta con recomendación. Le preocupa no cumplir la MN 01, el costo en tokens y que las IA supongan cosas: **verifica en el código antes de afirmar** y di «no lo sé» cuando no esté verificado.

## 8. Lo que el coordinador revisaba con Opus, ya convertido en reglas (para revisar sin Opus)
**Al unir C38 (cálculo), rechaza el PR si falla cualquiera de estas, aunque la compuerta esté VERDE:**
1. `python3 -I tests/auditoria_mn1/correr_auditoria.py .` → cada S1–S8 ya NO reproduce su defecto y su control sin defecto sigue igual.
2. `tests/datos/oraculo_servitec/verificar_pieza30.py` → diferencia 0.00 por orden, elemento y etapa (REB 22,975 · MPR 5,165).
3. `tests/test_modelo3_oria.py` sin cambios y en verde (recíproco y escalonado a mano).
4. `tools/e2e_recorrido.py` → 30/30.
5. El diff no toca ninguna prueba existente salvo la aserción final de `tests/auditoria_mn1/test_S*.py` (de «el defecto ocurre» a «ya no ocurre»).
6. Ningún monto se corrige en silencio: todo dato malo termina en rechazo con hoja, fila y valor (nunca en 0 ni en descarte).
7. CONTABLE: ocio, pérdida y financieros nunca en el costo del objeto (lo valida `contrato.py`).
Si 1–7 pasan, unir con `tools/unir_pr.py`. Si alguno falla, devolver a Codex con el número de regla.

**EXE final:** GitHub → Actions → «Paquete offline de Windows» → *Run workflow* sobre `desarrollo/mono` (también corre solo con cada push). El artefacto es `ReynaCostos-Windows-x64.zip`. Hacerlo cuando C37 y C38 estén unidas; luego el dueño lo prueba con `docs/entrega/GUION_PRUEBA_DUENO.md`.

## 9. Regla de recorte si Codex se atrasa (fechas fijas: congelar código 6-dic 18:00; entrega 9-dic 18:00)
Lo que no esté unido con compuerta VERDE el 6-dic 18:00 **no entra**: se declara como límite en el manual y la monografía. Si hay que elegir, se protege en este orden (1 = nunca se corta):
1. **C38-1…C38-5** (errores críticos de cálculo y control registrado = entrado).
2. **Entregables obligatorios:** informe de pruebas y manual de usuario (sin ellos la MN 01 no cumple).
3. **E45 + E46** (matrices y recíproco como Oria: lo ve el profesor).
4. **C41-1** (precisión contra modelo ingenuo: el criterio de Oria) y **C37-7** (entorno hostil: ya tiene libros listos).
5. **C37-3** (Decidir con datos propios) y **C37-4** (tramos en el Pedido).
6. **C41-2, C41-3**, presentación y preguntas del jurado.
7. **Se cortan primero:** C37-5 (una sola familia), C37-6 (pantallas sin valor), C38-6…C38-10, C40 (archivo), guion de prueba (el dueño puede probar con el manual).
Revisión de avance: 1-dic, 3-dic y 5-dic. En cada una, si lo pendiente de los niveles 1–4 no cabe en los días que quedan, sacar de la cola de Codex todo el nivel 7 y avisar al dueño.
