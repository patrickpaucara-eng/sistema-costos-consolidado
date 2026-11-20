# Inventario y estrategia de integración de ramas

**Corte de lectura:** 20 de noviembre de 2026 (hora de Lima).  
**Repositorio consultado:** `patrickpaucara-eng/sistema-costos-reyna`.  
**Alcance de este registro:** consulta de referencias; ninguna rama se modificó ni fusionó.

## Censo remoto

`git ls-remote --heads` y la búsqueda paginada de GitHub devolvieron **292 nombres de rama**, **290 SHA de punta distintos** y 292 nombres únicos. El censo se conserva en [`INVENTARIO_BRANCHES_2026-11-20.csv`](INVENTARIO_BRANCHES_2026-11-20.csv), con SHA-256 `86a2533c3a81762c40fe0ae16890585a6b59d6974fceb506f8927fdde85de989` y el SHA actual de cada punta.

El censo se comparó con [`OT-001/INVENTARIO_RAMAS.csv`](OT-001/INVENTARIO_RAMAS.csv): los 292 nombres y los SHA de punta coinciden exactamente; no hay ramas añadidas, retiradas ni movidas desde ese corte. Por lo tanto, la clasificación de contenido de OT-001 sigue refiriéndose a las mismas puntas. Esa revisión clasificó 47 como cambios ya presentes en `main`, 108 como documentación/artefactos a contrastar, 95 como divergencias históricas, 20 como desarrollo/verificación a contrastar, 8 como bloqueo/iteración, 4 como candidatas de recuperación selectiva, 5 como aportes incluidos en la candidata, 2 como hitos congelados integrados, 1 como base integrada, 1 como antecesora y 1 como estudio aislado.

Las ramas se agrupan por prefijos visibles como `arq/` (55), `obra/` (23), `desarrollo/` (14), `obrera/` y variantes (14), `prueba/` (7), `verif/` (2), `prototipo/` (1), `version/` (1), `estudio/` (1) y 174 nombres sin `/`. Hay nombres de integración, tarea, prueba, versión, respaldo y pausa. El nombre y el número de ramas no demuestran que cada punta contenga una capacidad única ni que todas sean compatibles con el stack vigente.

## Recomendación

**No fusionar las 292 ramas en bloque.** La auditoría existente encontró que 47 ya tienen su delta en `main`, 108 se clasificaron como documentación/artefactos y solo 4 como posibles recuperaciones selectivas. Las demás corresponden principalmente a divergencias históricas, desarrollo/verificación, bloqueos o bases congeladas. Una fusión masiva podría duplicar trabajo o reintroducir VBA, rutas históricas, contratos incompatibles o decisiones anteriores sobre SQLite. Además, 292 ramas apuntan a 290 SHA únicos, así que ni siquiera equivalen a 292 puntas de código distintas.

Las cuatro candidatas señaladas por OT-001 requieren tratamientos distintos:

| Rama | Contenido que OT-001 separó | Tratamiento recomendado |
|---|---|---|
| `arq/documentos-finales` | Directrices, arquitectura, resumen, guion y traspaso | Contrastar cada documento con la última decisión del dueño y usarlo como referencia; copiar solo lo que no esté ya preservado. |
| `desarrollo/I-9` | Diseño documental del análisis predictivo | Revisar después de las puertas de costo y resultados reproducibles; no incorporarlo como analítica implementada. |
| `desarrollo/deuda` | Diagnóstico D9, escritores/cuentas, pruebas de cuadre, protección y proyección de seis meses | Reusar casos, matrices y pruebas como evidencia; adaptar selectivamente al contrato actual, sin presumir que su código pertenece al MVP. |
| `desarrollo/ola1` | Cambios de Ola 1b, incluidos módulos VBA y herramientas | El espejo Python ya parte de esa revisión en el consolidado. Mantener como fuente; no volver a fusionar todo el árbol. |

La prioridad de recuperación es documentación fuente y pruebas independientes. El trabajo funcional se incorpora solo cuando la arquitectura y los contratos vigentes lo acepten.

Cuando termine el trabajo pendiente de Ola 3, integrar por capacidades y evidencia en una rama limpia del consolidado:

1. Fijar la revisión base y capturar los 292 nombres y SHA para que el análisis sea reproducible.
2. Agrupar por objetivo (D9, flete/D14, empaquetado, pruebas, informes, etc.) y dependencia, no por cantidad de ramas.
3. Para cada grupo, comparar commits y rutas modificadas con el consolidado, buscar equivalentes ya integrados y leer los cambios y sus pruebas.
4. Elegir el cambio mínimo que conserve evidencia útil: extracción selectiva o `cherry-pick` de commits concretos cuando la historia sea limpia; adaptación manual si la rama incorpora código mezclado o decisiones obsoletas.
5. Ejecutar su aceptación desde un entorno temporal contra la versión base elegida y registrar SHA, diferencia, resultado y límites.
6. Rechazar o archivar como referencia —sin borrar del original— lo duplicado, incompleto, incompatible o sin oráculo.
7. Revisar la integración por una persona/agente independiente antes de incorporarla al producto.

La selección final debe respetar las decisiones vigentes: Python como motor único, Excel como libro, HTML local, VBA congelado y SQLite aplazado. La integración pertenece al repositorio consolidado; el original permanece de solo lectura.

## Límite del censo

Este registro confirma que la lectura remota actual no cambió el censo OT-001. No reejecuta las pruebas de cada punta: esa auditoría previa y sus logs son la evidencia de contenido. Las cuatro candidatas requieren cotejar dependencias y valor contra el estado del consolidado antes de decidir si se extrae algún componente. Nada de esto valida el 93 % declarado.
