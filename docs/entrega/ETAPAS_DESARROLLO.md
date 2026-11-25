# Etapas del desarrollo del sistema de costos

Sistema universal de costos por órdenes (MCD/DBD de Tino Reyna), con la metodología ABC escalonada de W. Oria como modelo de costeo.
Construido del 20-nov al 9-dic-2026 por el dueño (decisiones y pruebas), Claude (arquitectura, cálculo, revisión) y Codex (pantallas, exportadores, documentos).

## 1. Método de trabajo
- **Fuente de la verdad:** un libro Excel con el modelo de datos (DBD). Python es el único motor de cálculo; la interfaz es HTML local; un .exe la empaqueta.
- **Compuerta:** ningún cambio entra sin `tools/verificar.py` en VERDE (pruebas automáticas + contrato de resultados).
- **Caso a mano primero:** cada cálculo nuevo se diseña con cifras calculadas a mano y su prueba debe darlas exactas.
- **Roles:** Claude diseña y revisa; Codex ejecuta órdenes escritas con prueba de aceptación; nadie une a `main`.
- **Aprendizaje del error:** cada falla deja una regla (`REGLAS_APRENDIDAS.md`, RA-01 a RA-30) y una prueba.

## 2. Etapas
| Etapa | Fechas | Resultado |
|---|---|---|
| 0. Arranque | 20–21 nov | Plan de la monografía, repositorio consolidado, compuerta, registro de tiempos |
| 1. Base del costo | 21–23 nov | Motor ABC por etapas P1–P7; kardex promedio; síntesis REAL, CONTABLE (NIC 2) y ESTIMADO; caso Frenosa cuadrado |
| 1b. Naturaleza del costo | 23 nov | Pérdida (merma en exceso) y ocio (capacidad no usada) viajan a la orden; la síntesis decide si son costo o gasto |
| 1c. Modelo 3 y recíproco | 23–24 nov | Actividades estratégicas, de apoyo y operativas; método recíproco exacto entre pares; escalonado como caso particular |
| 1d. Banda y sello | 24 nov | Proyección con banda conformal validada hacia atrás; sello SHA-256 de cada resultado |
| 2. Cobertura funcional | 24–25 nov | Periodos por fecha libre; propuestas por causa; rechazos como pérdida; costeo variable y controlabilidad; segundo caso (SERVITEC, servicios) |
| 2b. Gestión estratégica | 25 nov | Proyección por hechos con bloques y sensibilidad; aprendizaje con guardas; cotizador TDABC con costo objetivo; costo de calidad y gobierno del dato |
| 3. Operación | 24–25 nov | Formulario guiado de 8 transacciones (compras, consumos, devoluciones, gastos, producción, ventas); pantallas por el ciclo Definir · Estimar · Registrar · Entregar · Aprender |
| 4. Entregables y cierre | 25 nov – 9 dic | Exportadores Excel/Word/HTML, prueba de punta a punta (30/30), .exe, empaquetado |

## 3. Decisiones clave del dueño
| Fecha | Decisión |
|---|---|
| 22 nov | Pérdida y ocio se quedan asociados a la orden; REAL los muestra, CONTABLE los manda a gasto |
| 23 nov | El método preferido entre centros de apoyo es el recíproco |
| 23 nov | La simulación que editaba el pasado se reemplaza por proyección de hechos futuros |
| 24 nov | Inductor único por actividad; regresión solo para separar fijo y variable |
| 24 nov | Retrabajo y rechazo = costo de no calidad; coproducto sin valor de venta = residuo |
| 24 nov | Bloques de costo escalonado solo para proyectar; el costo real siempre sale de hechos |
| 25 nov | Prueba de punta a punta sin parches; documentación breve (80/20) |

## 4. Errores relevantes y cómo se corrigieron
| Error | Corrección |
|---|---|
| Redondear antes de sumar movía el margen 0.02 | Redondeo por clave al publicar; comparación de resultados antes/después |
| La banda de proyección cubría 0 de 5 meses reales | Banda conformal con el sesgo incluido; «no estimable» con menos de 3 errores |
| El sello no cubría sus propios metadatos | La huella incluye todo el resultado salvo ella misma |
| El adaptador de datos ponía día 31 en todos los meses | Fin de mes real con calendario |
| Diseño del segundo caso con inventario discontinuo (detectado por Codex) | Saldo encadenado mes a mes; cifras de julio intactas |

## 5. Resultado
- 432 pruebas automáticas en VERDE; recorrido de punta a punta 30/30.
- Dos casos cuadrados a mano: Frenosa (manufactura, 12 meses) y SERVITEC (servicios, 8 meses: REB 22,975 / MPR 5,165 en julio).
- Pendiente declarado (no funcional): base de datos SQLite, integración con ERP/MES, rendimiento a gran escala.
