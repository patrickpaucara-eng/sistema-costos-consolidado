# Construir y revisar el paquete Windows

El paquete necesita la integración previa de OT-C04 y OT-C05 en la rama que se use para construir. En el repositorio público de entrega, habilitar GitHub Actions y ejecutar manualmente **Paquete offline de Windows** (`windows-offline.yml`, `workflow_dispatch`) sobre la rama de entrega. Descargar `ReynaCostos-Windows-x64.zip` desde el artefacto del flujo y verificar el SHA-256 según `SHA256SUMS.txt`.

En Windows x64, descomprimir y ejecutar `ReynaCostos.exe`. Cerrar Excel si está abierto sobre el libro que se probará. Desconectar internet y comprobar: abrir la interfaz local; elegir julio 2010/REAL y calcular; ir a Reportes y descargar HTML; abrirlo y comprobar los resultados. Cerrar y volver a abrir para comprobar la recuperación de datos. Guardar el resultado y el log.

El humo de Linux es una evidencia del empaquetado equivalente, no una prueba de Windows, Excel nativo ni del EXE final. La descarga del flujo puede requerir resolver la disponibilidad y facturación del runner de GitHub Actions.
