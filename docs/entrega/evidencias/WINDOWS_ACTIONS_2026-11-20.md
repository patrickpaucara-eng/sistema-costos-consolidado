# Evidencia · workflow Windows sin runner

**Fecha:** 20 de noviembre de 2026 (hora de Lima).  
**Repositorio:** `patrickpaucara-eng/sistema-costos-consolidado`.  
**Revisión:** `3eb743502fe7e088bfc5aea5dc3ba6c0dd79c047`, rama `desarrollo/mvp-ola3`.  
**Workflow:** `.github/workflows/windows-offline.yml`, job `paquete`, etiqueta solicitada `windows-2022`.

## Observación

GitHub registró el run [44823532080](https://github.com/patrickpaucara-eng/sistema-costos-consolidado/actions/runs/44823532080) como fallido en dos intentos:

| Intento | Hora UTC | Job | Duración observada | Runner | Pasos |
|---:|---|---:|---:|---|---:|
| 1 | 2026-11-20 21:48:19 | 136590207172 | 2 s | `runner_id=0`, nombre vacío | 0 |
| 2 | 2026-11-20 21:49:56 | 136590989719 | 2 s | `runner_id=0`, nombre vacío | 0 |

El API de artefactos devolvió una lista vacía. La descarga de logs respondió 404 y el conector de GitHub no expuso el cuerpo de la anotación del check run. Por eso se puede afirmar que el job no alcanzó sus pasos en un runner, pero no cuál fue la causa de esa denegación o fallo de asignación. No hay evidencia de que `build.py` se haya ejecutado en Windows ni de que el empaquetador haya fallado.

## Alcance de la verificación local

El empaquetador y su smoke aislado sí pasaron en Linux con Python y PyInstaller de la versión fijada; se comprobaron importación del XLSX, API, HTML, cierre y reapertura, y el arranque con `PATH` restringido. La validación de sintaxis del workflow y de hashes de wheels también pasó según el registro del especialista. Esto reduce riesgo de configuración, pero **no** sustituye un build de Windows x64 ni una prueba física desconectada.

## Acción para reanudar

1. Abrir el enlace del run y obtener el mensaje de anotación/plataforma asociado al job.
2. Resolver el acceso o asignación del runner Windows en la configuración/plan de Actions, si el mensaje lo indica; no cambiar el código del empaquetador sin evidencia.
3. Reejecutar el workflow y verificar que publique `ReynaCostos-Windows-x64.zip`.
4. Descargarlo, guardar SHA-256 y ejecutar el EXE en Windows x64 sin Internet.

Desde este entorno se pudo consultar y reintentar el workflow, pero no leer su anotación ni la configuración administrativa de Actions; además, el entorno de ejecución disponible es Linux. El dueño o Claude con acceso a GitHub debe obtener el mensaje y revisar los permisos/límites señalados. La prueba con Excel y Windows nativo requiere un equipo Windows x64. El procedimiento completo está en [ESTRATEGIA_CIERRE_OLAS.md](../../planificacion/ESTRATEGIA_CIERRE_OLAS.md).

Hasta completar esos pasos, el ejecutable está pendiente y la aceptación offline para la monografía no está demostrada.
