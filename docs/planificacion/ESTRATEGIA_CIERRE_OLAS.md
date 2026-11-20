# Estrategia rápida para cerrar las seis olas

**Corte:** 20 de noviembre de 2026.  
**Objetivo:** terminar el trabajo de Claude reutilizando su contexto y reducir retrabajo, sin adelantar la auditoría posterior que el dueño quiere hacer después de las seis olas.

## Decisión operativa

Claude mantiene el hilo de implementación de las seis olas y su conocimiento del repositorio histórico. Este consolidado conserva los acuerdos posteriores del dueño, los criterios de aceptación y la evidencia independiente. No se asignan dos autores al mismo módulo ni se relanza una lectura de las 292 ramas en cada ola. El repositorio original permanece en lectura desde este entorno.

La revisión del consolidado muestra brechas de evidencia y capacidades parciales. Eso no determina que haya que reescribir: una función declarada pendiente aquí puede existir en una rama o módulo de Claude. Para cada tema se debe comprobar primero la última revisión, el código y su prueba.

## Complejidad: qué puede ser pequeño y qué requiere análisis

| Tipo de trabajo | Ejemplos | Estimación antes de revisar el código de Claude |
|---|---|---|
| Ajuste localizado | Mensajes de error, errores de importación o salida, guías, formularios que llamen a servicios existentes | Menor si hay caso reproducible y contrato estable |
| Adaptación moderada | Configurar otro modelo ABC, completar datos de una instancia, hacer un reporte a partir de resultados ya conciliados | Moderada si la estructura, parámetros y pruebas ya existen; mayor si el contrato no está definido |
| Trabajo metodológico amplio | Conciliación D9 integral, flete/D14, varias categorías de costo o una base ABC extensible | Alto: exige reglas MCD/DBD, fuentes ORIA, dimensiones, claves y oráculos independientes |
| Capacidad nueva de análisis | Pronóstico de seis meses, escenarios estocásticos, prescripción y evaluación de aprendizaje | Alto si faltan datos, criterios de error, permisos o medición de resultado |

Por tanto, los huecos de la monografía no son todos problemas menores. Algunos pueden resolverse adaptando trabajo existente; los cálculos integrales y la analítica necesitan validación metodológica y aceptación. La auditoría posterior dirá qué casos aplican.

## Protocolo por ola

Al iniciar una ola, guardar rama y SHA base, objetivo del alcance y criterio de salida. Claude comprueba primero lo que ya funciona mediante el flujo o prueba existente.

1. **Si pasa:** marcar la capacidad aceptada con su comando, datos y resultado observados.
2. **Si hay una falla localizada:** reproducirla y corregir solo el componente afectado.
3. **Si el componente existe en otra rama:** comparar dependencia, contrato y pruebas; adaptar solo la unidad necesaria.
4. **Si no existe:** implementar la pieza mínima que cumple el criterio de la ola y registrar riesgos de robustez pendientes.
5. **Al cerrar:** producir una ficha con rama/SHA final, cambios, pruebas ejecutadas, resultado, límites y siguiente dependencia. Un revisor distinto al autor comprueba cálculos, persistencia o permisos.

Una ola se cierra por capacidad reproducible, no por porcentaje declarado, cantidad de archivos o cantidad de ramas. Si una prueba falla, se conserva la revisión previa y se registra el bloqueo concreto.

### Ficha breve de cierre para Claude

```text
Ola y criterio de salida:
Rama y SHA inicial/final:
Capacidades aceptadas (ruta o módulo):
Cambios y motivo:
Pruebas ejecutadas / resultado observado:
Fuentes MCD/DBD/ORIA usadas:
Limitaciones o fallas reproducibles:
Qué queda para la siguiente ola:
```

Esta ficha conserva el contexto de trabajo entre olas y permite revisión independiente sin releer todo el repositorio.

## Orden y paralelismo

Mantener las seis olas históricas como secuencia. La relación detallada está en [PLAN_MAESTRO.md](PLAN_MAESTRO.md).

| Tramo | Ejecución más rápida con dependencias controladas |
|---|---|
| Olas 1–2 · base y estructura | Verificar las capacidades ya existentes y aceptar lo que pase. Corregir solo fallas que bloqueen los recorridos requeridos. |
| Ola 3 · credibilidad del costo | Concentrar al autor en D9, flete y D14; cerrar primero reglas, claves y cálculos reproducibles. Mantener el análisis de seis meses fuera del camino crítico. |
| Ola 4 · integridad | Definir huella, reversa, reapertura y recuperación sobre resultados ya aceptados; reutilizar la trazabilidad existente. |
| Ola 5 · analítica | Construir sobre resultados publicados y medibles; no mezclar reglas de costo con predicción. |
| Ola 6 · prueba global | Congelar la revisión candidata, recorrer los casos de punta a punta, probar volúmenes acordados y preparar la entrega. |

En paralelo pueden avanzar tareas sin archivos compartidos: Claude trabaja la ola en curso; el dueño o Claude con acceso a GitHub resuelve la asignación del runner Windows; documentación y entregables se preparan con evidencia ya cerrada. Si se usan agentes, limitar la concurrencia a tres especialistas: metodología/costos con razonamiento alto, implementación acotada con nivel medio y revisión independiente con alto; búsqueda e inventario rutinarios con nivel bajo. Cada agente recibe solo sus archivos, fuente, contrato y aceptación. No asignar escritores concurrentes al mismo módulo.

## Dependencia del EXE

El código de empaquetado, el workflow y el smoke equivalente en Linux ya están preparados en el consolidado. GitHub registró dos fallos antes de asignar `windows-2022`: cero pasos, `runner_id=0` y ningún artefacto. Desde las herramientas disponibles aquí se pudo consultar y reintentar la ejecución; la lectura de logs devolvió 404, no se expuso la anotación, y el conector no permite inspeccionar la configuración administrativa de Actions. Este entorno ejecuta Linux, no Windows.

**Intervención necesaria del dueño o de Claude con acceso a la configuración de GitHub:**

1. Abrir el [run de Actions 44823532080](https://github.com/patrickpaucara-eng/sistema-costos-consolidado/actions/runs/44823532080) y copiar el mensaje exacto de anotación o plataforma.
2. Según ese mensaje, revisar acceso a runners hospedados, límites/uso de Actions o políticas de ejecución del repositorio. Cambiar la configuración solo si el error lo indica.
3. Si el runner se habilita, volver a ejecutar el workflow y descargar `ReynaCostos-Windows-x64.zip`. Si no hay runner disponible, usar un Windows x64 con `python tools/windows/build.py`.
4. Probar el EXE sin Internet, registrar SHA-256 y comprobar importación, operación, Excel, cierre y reapertura.

Claude puede diagnosticar el mensaje y preparar cambios del workflow. El acceso de cuenta, permisos, cuotas y prueba en un Windows real dependen de una persona con esas capacidades. La evidencia detallada está en [WINDOWS_ACTIONS_2026-11-20.md](../entrega/evidencias/WINDOWS_ACTIONS_2026-11-20.md).

## Revisión posterior a las olas

Al completar Ola 6, registrar los SHA remotos y revisar el trabajo de Claude contra [ANALISIS_MONOGRAFIA.md](ANALISIS_MONOGRAFIA.md), [REGISTRO_CAPACIDADES.md](../entrega/REGISTRO_CAPACIDADES.md) y las reglas MCD/DBD/ORIA. Por cada requisito de la monografía, identificar el archivo, prueba y resultado que lo acredita; clasificarlo como presente, parcial, ausente o no reproducible.

Después, comparar capacidades seleccionadas con el inventario de ramas. Reusar primero pruebas, casos y documentación. Integrar por unidad funcional en el consolidado, revisar cada cambio y ejecutar su aceptación. No fusionar el conjunto de ramas en bloque. No estimar el avance global sin un denominador de requisitos acordado.
