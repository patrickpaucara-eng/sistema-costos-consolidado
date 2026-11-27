# OT-C32-1b · correlativo guiado de objeto

## Alcance

Al seleccionar una transacción guiada, el sistema consulta su secuencia configurada en TOP→OME→MET/MCA. Si esa secuencia crea filas en OBJETO, identifica la variable del código y cómo obtener el producto: directamente del formulario o de una lectura previa definida por el DBD. El formulario obtiene el menor correlativo disponible para empresa y producto, lo muestra como solo lectura y lo incluye al enviar la operación.

El resumen del espacio conserva el límite de transacciones del piloto. El endpoint del formulario usa las tablas TRX, TRX_CAMPO y TOP para habilitar únicamente las transacciones permitidas cuya secuencia crea OBJETO; los demás códigos del libro siguen deshabilitados. El cálculo del correlativo es auxiliar de interfaz: no reserva números. La creación real conserva la validación de clave única del libro, que protege una colisión concurrente.

## Evidencia

Prueba propia: `tests/test_c32_1b_formulario_objeto.py`.

- La inspección de DBD encuentra que T13 crea OBJETO mediante la variable OBJ y que el producto se obtiene de ESTIMACION usando EST; T15 no se clasifica como creadora.
- El recorrido en Chromium importa una copia temporal del libro Frenosa con dos estimaciones pendientes SW50, selecciona T13 y verifica que el campo OBJ es `readOnly`. Un intento de editarlo con teclado no cambia su valor.
- Al registrar las dos estimaciones, el formulario anticipa y persiste `OT-FRE-SW50-0001` y `OT-FRE-SW50-0002`; después de cada registro muestra el próximo correlativo disponible.
- El libro de la fixture y el XLSX original permanecen intactos; la prueba trabaja en un directorio temporal.

Comando focalizado:

```sh
PYTHONPATH=src /tmp/reyna-c32-2-venv/bin/python -m pytest -q tests/test_c32_1b_formulario_objeto.py
```

Resultado: **2 pruebas aprobadas**, incluida la prueba de recorrido en Chromium.

Verificación completa de la rama (`python tools/verificar.py`): **504 pruebas aprobadas, 1 advertencia, 26 subpruebas aprobadas; contrato de resultados conforme; COMPUERTA: VERDE**.

## Límite conocido

Una sugerencia no es una reserva distribuida. Dos sesiones simultáneas podrían mostrar el mismo próximo código; al guardar, la clave única del DBD debe rechazar una de las operaciones. El recorrido verifica dos registros secuenciales en una sesión local, no concurrencia multiusuario.
