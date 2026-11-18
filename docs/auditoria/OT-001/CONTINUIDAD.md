# Continuidad de OT-001

El trabajo se guarda en el directorio temporal de la auditoría exterior al repositorio. El espejo y las tres carpetas de prueba se pueden reconstruir desde los SHA del índice. Los archivos de evidencia deben conservarse por hito porque la persistencia de la máquina Cloud depende de la sesión.

## Reproducción de la evidencia Git

1. Obtener una copia temporal bare de solo lectura y cotejar sus ramas con las referencias remotas. Si cambian las puntas, mantener el primer manifiesto y fijar una segunda captura.
2. Usar `inventariar.py` sobre la copia bare. Su CSV inspecciona cada rama a nivel de referencias, commits, árboles y rutas. Para selección funcional, consultar la cronología y los cambios de las ramas candidatas.
3. Ejecutar `git fsck --full --no-dangling` sobre el espejo y cotejar el recuento, las puntas y los árboles.

## Reproducción de pruebas

`run_audit.sh` documenta los comandos y el contenedor. Se usa una extracción por SHA, Git local con HEAD separado e índice materializado solo en la copia, dependencias instaladas desde ruedas con hash e interfaz de red limitada a loopback. `image/Dockerfile` documenta el sistema de prueba con LibreOffice. Los logs completos contienen el hash de las ruedas, las versiones y códigos de salida. El espejo permanece fuera del contenedor.

La sonda `comprobar_valuacion.py` usa datos sintéticos. Evalúa la función de valuación con los movimientos de una empresa y con la mezcla de dos empresas de claves iguales. Para validar el flujo completo aún se requiere comprobar que el puerto y los llamadores entregan solo los hechos autorizados.

## Reanudación

La decisión de auditoría es mantener main como linaje integrado de trabajo y Ola 1 como candidata de recuperación. Quedan por cotejar originales MCD/DBD, reproducir los casos de Excel, demostrar un cierre atómico y verificar la cadena multiempresa con equivalencia contra libros separados. Los archivos del expediente indican el orden de la consolidación. Hace falta autorización expresa para un repositorio privado nuevo o cualquier intervención sobre el original.
