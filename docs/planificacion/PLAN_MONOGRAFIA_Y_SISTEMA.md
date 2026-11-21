# Plan de inicio a fin · Monografía MN_01 (GE704W, Oria) y sistema robusto

Fecha: 21-nov-2026. Entrega: **miércoles 9-dic-2026, 18:00** (UNI Virtual, carpeta de la Semana 15). Quedan 18 días.
Repo de trabajo: `patrickpaucara-eng/sistema-costos-consolidado` (la de Codex). La repo anterior `sistema-costos-reyna` queda solo como referencia de lectura.
Regla de lectura: **todo lo que está sobre la línea «MÍNIMO VITAL» se hace antes del 9-dic. Todo lo que está debajo se hace después, sin rehacer lo anterior.**

---

## 0. Decisiones ya tomadas (no se vuelven a discutir)

| # | Decisión | Origen |
|---|---|---|
| D-1 | **Motor único en Python** (el espejo verificado 392/392 y O-1 66/66). VBA congelado como referencia. | Dueño, 21-nov |
| D-2 | **Excel solo para definir el DBD** (como Tino) y como plantilla de carga y almacenamiento. SQLite aplazado: el almacenamiento queda detrás de un contrato, así se cambia después sin tocar el motor. | Dueño, 21-nov |
| D-3 | **Pantallas en HTML** servidas localmente por Python, sin internet. | Dueño, 21-nov |
| D-4 | **.EXE al final:** se desarrolla con un equivalente en Linux; al terminar, la repo pasa a pública y GitHub fabrica el `.exe` gratis. | Dueño, 21-nov |
| D-5 | **Caso de desarrollo: Frenosa** (metalmecánica). Al final se carga **otra metalmecánica con la misma plantilla** para demostrar que el sistema se adapta a cualquier empresa sin código. | Dueño, 21-nov |
| D-6 | **Una sola plantilla de carga**, generada desde el DBD. La empresa adapta sus datos a la plantilla, no al revés. | Dueño, 21-nov |
| D-7 | **Todo costo sigue la misma cadena** (acumular → repartir → asignar al objeto → liquidar). Cambian el objeto, el método y la síntesis según el catálogo (tipología). | Dueño / Reyna |
| D-8 | **Tres síntesis con reglas propias en el catálogo:** REAL (gerencial), CONTABLE (NIC 2 / NIIF 18), ESTIMADO. **ESTIMADO no es estándar:** es el costo más fiel según la historia, por estadística (analogía con órdenes parecidas, regresión, banda de confianza), contra el que se detectan variaciones. | Dueño, 21-nov |
| D-9 | **Coproductos:** REAL puede usar unidades físicas; CONTABLE obliga el valor de venta relativo (VVR). **Gastos financieros:** REAL puede incluirlos en el costo integral; CONTABLE nunca los lleva al inventario (van a Financiación, NIIF 18). | Dueño, 16-nov |
| D-10 | **Material por kardex, gastos por reparto.** El material se consume (cantidades a la orden); los centros reparten gastos. Nunca se «reparte» el material físico. | Dueño, 16-nov |
| D-11 | **Costo de adquisición:** los costos directos de una compra se asignan al documento y se prorratean entre sus líneas (no es reparto). Los indirectos van al centro COMPRAS → actividades ABC con su propio inductor → objetos (lotes). El costo viaja pegado al material: lo que sigue en almacén queda inventariado, lo consumido pasa a la orden, lo devuelto revierte el directo de ese documento. **El indirecto de un lote devuelto queda en el inventario del resto** (rastreo de CIF por objeto). En CONTABLE solo entra lo marcado como directamente atribuible; el resto va a gasto de administración. | Dueño, 21-nov |

---

## 1. Cómo se trabaja (los mecanismos de Karpathy y de la ingeniera de SpaceX, aplicados)

| Mecanismo | Cómo se aplica aquí | Quién |
|---|---|---|
| **Revisión automática** | Un solo comando `verificar` corre: pytest, historia 392/392, O-1 66/66, coherencia del DBD en 0 errores, arranque del sistema y recorrido de pantallas. Ningún cambio se entrega sin pasarlo. Cuando la repo sea pública, corre solo en GitHub en cada cambio. | Automático |
| **Barreras que bloquean** | Las reglas D-7…D-11 se vuelven **pruebas que fallan**, no consejos. Ejemplos: «CONTABLE rechaza un costo no capitalizable»; «ninguna regla de reparto mueve material»; «el indirecto de un lote devuelto sigue en el inventario». | Automático |
| **Cada error se vuelve una regla** | `REGLAS_APRENDIDAS.md`: cada fallo encontrado agrega una línea y una prueba que impide repetirlo. Ya entra el error de I-5 (referencias mal declaradas → prueba de coherencia). | Claude |
| **Modelo caro dirige, barato ejecuta** | Claude diseña, decide la metodología y revisa. Codex hace el volumen con órdenes cortas (`ordenes/OT-xxx.md`): objetivo, archivos, criterio de aceptación y comando de verificación. Codex trabaja en ramas propias, abre PR y nunca une a main. | Claude dirige; Codex ejecuta |
| **Tu rol: decidir y probar resultados** | Por entrega recibes **una página**: qué cambió, qué probar (15 min) y qué decides. Frases cortas. No lees código. | Dueño |
| **Esfuerzo como perilla** | Esfuerzo alto solo para metodología, cálculo y persistencia; medio para pantallas y documentos; bajo para formato e inventarios. | Claude |

Coordinación con Codex: la repo es el punto de encuentro. Tú solo le dices: «Ejecuta `ordenes/OT-xxx.md` en una rama nueva y abre un PR».

---

## 2. Arquitectura final

```
 DBD_Fuente.xlsx (definición, editable como en Tino)
        │  generador
        ▼
 Base (almacenamiento Excel detrás de un contrato; SQLite después)
        │
 Motor Python (transacciones, servicios, métodos; síntesis REAL / CONTABLE / ESTIMADO)
        │
 Capa analítica (diagnóstico → descriptivo → predictivo → prescriptivo)
        │
 Servidor local Python ──► Pantallas HTML (navegador, sin internet)
        │
 Exportadores: Excel de resultados, HTML sin conexión, Word (informe, manuales), presentación
        │
 Lanzador → .EXE (PyInstaller, al final)
```

---

## 3. Etapas del MÍNIMO VITAL (21-nov → 9-dic)

### Etapa 0 · Puesta en marcha (21–22 nov, 1 día)
| Tarea | Detalle | Quién | Aceptación |
|---|---|---|---|
| 0.1 Acceso de escritura a la repo consolidada | Conectar con permiso de escritura | Dueño + Claude | Claude puede crear ramas |
| 0.2 Estado real | Correr la suite de Codex (55/55) y la compuerta propia; inventario de lo que funciona | Claude | Informe de una página |
| 0.3 Comando `verificar` + `REGLAS_APRENDIDAS.md` + `AGENTS.md` actualizado | Las reglas de la sección 1 escritas para Codex | Claude | `verificar` corre en local y falla si algo se rompe |
| 0.4 Registro de tiempos (entregable 13) | Excel con actividad, hora de inicio y hora de término, desde hoy | Claude lo lleva; tú confirmas | Archivo vivo en la repo |
| 0.5 Fuentes de Oria actualizadas | Indexar `materialAcademicoOria20262.zip` con hash en `docs/fuentes` | Codex (orden corta) | Índice actualizado |

### Etapa 1 · Caso Frenosa cargado y calculado (23–25 nov, 3 días)
| Tarea | Detalle | Quién | Aceptación |
|---|---|---|---|
| 1.1 Plantilla única desde el DBD | `CARGA_MES.xlsx` con hojas Diccionario y Reglas generadas del DBD (nunca se desfasan) | Codex | La plantilla se regenera sola desde el DBD |
| 1.2 Datos de Frenosa en la plantilla | Empresa, periodos (12 meses de 2010), recursos, centros (producción y soporte), 7 actividades, inductores, 3 productos/órdenes, compras, consumos, mano de obra, ventas. **Solo datos del caso, cero código del proyecto pasado** | Codex con revisión de Claude | La plantilla valida 100 % |
| 1.3 ABC de producción | Recursos → actividades → órdenes, con reparto proporcional (pedido explícito de la mono) | Claude | Costo por orden de julio 2010 cuadra **a mano** con el caso publicado |
| 1.4 Material por kardex | Promedio ponderado; compras, consumos y devoluciones (D-10) | Motor existente | Barrera D-10 en verde |
| 1.5 Multiperiodo | 12 meses importados y cerrados en orden; un mes cerrado no se reescribe | Claude | Encadenamiento: inventario final del mes = inicial del siguiente |

### Etapa 2 · ABC integral y síntesis (26–28 nov, 3 días) — la parte que más pesa en el «nivel técnico» (40 %)
| Tarea | Detalle | Quién | Aceptación |
|---|---|---|---|
| 2.1 Síntesis en el catálogo | REAL / CONTABLE / ESTIMADO con sus reglas por tipología (D-8) | Claude | Las barreras de capas en verde |
| 2.2 ABC integral | Producción + **administración + ventas + financieros**, asignados a los objetos de costo | Claude | Estado de resultados por objeto que cuadra con el total |
| 2.3 Estado de resultados NIIF 18 | Categorías Operación, Inversión y Financiación; en CONTABLE, los financieros fuera del inventario; ocio y pérdidas a gasto del periodo | Claude | Prueba: CONTABLE nunca capitaliza financieros ni ocio |
| 2.4 Costo de adquisición mínimo | **Solo los costos directos de compra** (flete de la factura prorrateado entre sus líneas), si Frenosa los tiene | Codex con caso a mano de Claude | El costo unitario sube lo esperado en un caso a mano |
| 2.5 «N» modelos | Demostrar un segundo modelo ABC (por ejemplo con centros de soporte escalonados) **solo con datos** | Claude | Dos modelos en la misma base, sin código nuevo |

### Etapa 3 · Analítica y proyección (29 nov – 2 dic, 4 días)
| Tarea | Detalle | Quién | Aceptación |
|---|---|---|---|
| 3.1 Descriptivo | Qué pasó: costo por orden, actividad, elemento y periodo; evolución mensual | Codex (lee lo publicado) | Cifras iguales a las publicadas |
| 3.2 Diagnóstico | Causa raíz con los hallazgos existentes (H-03 a H-14): elemento dominante, ocio, mermas, desviaciones contra la familia | Claude conecta; Codex presenta | Cada hallazgo con impacto en S/ y su traza |
| 3.3 Relevancia | Pareto de la estructura de costos (qué 20 % explica el 80 %), por orden y por actividad; marca de **crítico** | Codex | Recalculado a mano en un caso |
| 3.4 Predictivo a 6 meses | **Determinístico:** pronóstico por método elegido con su error medido fuera de muestra (ya existe). **Estocástico:** Monte Carlo con semilla, percentiles P5/P50/P95, CVaR (ya existe) | Claude conecta | Proyección reproducible con la misma semilla |
| 3.5 ESTIMADO estadístico | Costo más fiel por analogía con órdenes parecidas, con banda; variaciones contra ese costo (D-8) | Claude | Una orden nueva estimada con sus órdenes de referencia |
| 3.6 Simulación de escenarios | Cambiar supuestos (precio, volumen, capacidad, tasa) → recalcular **en copia** → comparar antes y después | Claude | La base nunca cambia al simular |
| 3.7 Prescriptivo | Propuestas de reducción de costos con impacto en S/ y plan; catálogo + aprobación + seguimiento (ya existe) | Claude | Cada propuesta con impacto y supuesto |

### Etapa 4 · Pantallas y dashboard (3–5 dic, 3 días) — «flexibilidad y facilidad de uso» (20 %)
| Tarea | Detalle | Quién | Aceptación |
|---|---|---|---|
| 4.1 Navegación | Inicio → Cargar (Elegir, Validar, Importar) → Cerrar mes → Costos → Análisis → Proyección → Simulación → Propuestas → Reportes | Codex | Recorrido completo sin errores |
| 4.2 Dashboard dinámico | Histórico, actual y proyectado (determinístico y estocástico); filtros por periodo, orden y síntesis; cada número abre su traza | Codex con diseño de Claude | Mismas cifras que lo publicado |
| 4.3 Errores en español | «Error en la fila X de la hoja H: motivo»; nunca un error técnico | Codex | Prueba con plantilla dañada |
| 4.4 Aspecto profesional | Diseño limpio y consistente, gráficos legibles, modo claro | Codex | Revisión visual del dueño (15 min) |
| 4.5 HTML sin conexión | Un archivo con el dashboard y los resultados embebidos (entregable 12) | Codex | Abre sin internet en otra PC |

### Etapa 5 · Entregables (6–8 dic, 3 días)
| Nº | Entregable de la mono | Cómo se produce | Quién |
|---|---|---|---|
| 1 | Word con la cadena de chats con la IA | Exportación de esta conversación + los chats de Codex | Dueño exporta; Claude arma el Word |
| 2 | Word con las etapas del desarrollo | Desde `ESTADO.md`, las olas y las decisiones | Claude |
| 3 | Word con todo el código fuente | Generado desde la repo (índice + archivos) | Codex (script) |
| 4 | Word con la prueba de funcionamiento | Recorrido real con capturas y resultados esperados vs obtenidos | Codex + dueño |
| 5 | Excel de carga | `CARGA_MES.xlsx` de Frenosa | Ya existe (Etapa 1) |
| 6 | Excel de resultados | Exportador | Codex |
| 7 | Excel de la analítica | Exportador | Codex |
| 8 | Excel de proyección y propuestas | Exportador | Codex |
| 9 | Word Manual Descriptivo | Arquitectura, DBD, métodos, síntesis | Claude |
| 10 | Word Manual de Usuario | Pantalla por pantalla, con capturas | Codex + revisión de Claude |
| 11 | **.EXE** | Repo pública → GitHub fabrica el `.exe` → **prueba en tu Windows sin internet** | Dueño + Claude |
| 12 | HTML sin conexión | Etapa 4.5 | Codex |
| 13 | Excel de actividades y tiempos | Registro vivo desde la Etapa 0 | Claude |
| + | Informe técnico y presentación ejecutiva | Generados desde los datos: resumen del análisis, conclusiones, propuestas, plan de implementación e impacto económico | Claude |

### Etapa 6 · Ensayo y entrega (8–9 dic)
- 8-dic: el `.exe` corre en tu Windows sin internet; recorrido completo; segunda metalmecánica cargada **solo con datos** (prueba de adaptabilidad).
- 9-dic antes de las 18:00: zip con los 13 entregables subido a UNI Virtual (o Word con el enlace a Drive si supera el límite).

**Colchón:** si una etapa se atrasa, se recorta en este orden: 2.5 (segundo modelo) → 3.6 (simulación avanzada; queda la básica) → 4.4 (acabado visual). **Nunca se recorta el .EXE ni el ABC integral.**

```
════════════════════════════  LÍNEA DEL MÍNIMO VITAL  ════════════════════════════
     Todo lo de arriba se entrega el 9-dic. Todo lo de abajo se hace después,
     sobre la misma base, sin rehacer: son mejoras dentro del motor, no cambios de estructura.
```

---

## 4. Etapas POST-ESTABILIDAD (después del 9-dic)

| Etapa | Contenido | Por qué después |
|---|---|---|
| P-1 Credibilidad del cierre | **D9** (un solo escritor de cuentas, cuadre con lo publicado, reversa y recuperación); **D14** (reexpresar el costo de venta con el costo real liquidado) | No cambia lo que se muestra en la mono; sí la robustez contable |
| P-2 Costo de adquisición completo | Centro COMPRAS con actividades ABC y sus inductores (D-11); ajuste de costo posterior (T14.2); marca «capitalizable» en el catálogo | En la mono basta el flete directo |
| P-3 Estructura | D3 kardex derivado, D2 diario dentro de LOG_TRX, D4 PERSONA con CTA_CLIENTE/CTA_PROVEEDOR, D5–D8 del cierre | Alinea con el MCD; no cambia la experiencia |
| P-4 Rendimiento y almacenamiento | D13 índice en las búsquedas; **SQLite** detrás del mismo contrato | Hoy el volumen de un caso no lo necesita |
| P-5 Integridad | Huella de cada fila (OT-107), detección de cambios fuera del motor, protección | Seguridad para uso real |
| P-6 Analítica autónoma | Autonomía que aprende (SEG-01/AUT-01) con resultados medidos; consulta guiada en lenguaje cotidiano | Necesita historia real |
| P-7 Producto | Multiusuario, autenticación, despliegue para una empresa real | Fuera del alcance académico |

---

## 5. Riesgos y cómo se cortan

| Riesgo | Prob. | Corte |
|---|---|---|
| El `.exe` no arranca en Windows | Media | Fabricarlo el 6-dic (no el 9); probar en tu PC sin internet; plan B: compilarlo en tu PC con un archivo de doble clic |
| Datos de Frenosa incompletos para el ABC integral | Media | Completar con supuestos **declarados** en la hoja Fuentes (como el proyecto pasado), nunca ocultos |
| Se acaban los créditos | Alta | Órdenes cortas para Codex ya escritas por etapa; `ESTADO.md` actualizado al cierre de cada etapa |
| Lentitud con 12 meses (D13) | Media | Cargar el libro una vez por sesión; si no basta, adelantar el índice de P-4 |
| Mezclar capas al apurarse | Media | Barreras D-8/D-9 como pruebas desde la Etapa 2 |
| El profesor reconoce Frenosa del ciclo pasado | Alta | La demo final se hace con la **segunda metalmecánica**; Frenosa queda como caso de desarrollo |

---

## 6. Calendario resumido

| Días | Etapa | Resultado visible para ti |
|---|---|---|
| 21–22 nov | 0 Puesta en marcha | Página de estado real + `verificar` funcionando |
| 23–25 nov | 1 Frenosa cargado | Costo por orden de julio 2010 igual al caso publicado |
| 26–28 nov | 2 ABC integral | Estado de resultados NIIF 18 por orden, en REAL y en CONTABLE |
| 29 nov–2 dic | 3 Analítica | Diagnóstico, relevancia, proyección a 6 meses y simulación |
| 3–5 dic | 4 Pantallas | Sistema navegable con dashboard y HTML sin conexión |
| 6–8 dic | 5 Entregables + `.exe` | Los 13 entregables y el `.exe` probado en tu Windows |
| 9 dic | 6 Entrega | Zip subido antes de las 18:00 |

## 7. Lo que necesito de ti para empezar
1. **Aprobar este plan** (o corregir una línea).
2. **Conectarme la repo consolidada con permiso de escritura** (te lo pediré con un clic al empezar).
3. Avisarme cuando tengas créditos para Codex; sus órdenes estarán listas en `ordenes/`.
