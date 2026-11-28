# Plantilla UIX para pantallas locales

Toda tarea operativa sigue este orden visible: **pestañas → entradas → resultado → fundamento → siguiente acción**. El usuario debe completar el caso típico en tres pasos o menos y con seis campos o menos; los datos que ya existen se precargan y siguen editables.

## 1. Pestañas y orientación

Conservar la barra superior, indicar destino y pestaña activa y permitir llegar a la pantalla con teclado. No ocultar una acción principal dentro de una vista distinta.

## 2. Entradas

Usar campos tipados con nombre y unidad claros. Ofrecer búsquedas o listas para recursos, centros y órdenes. Precargar desde el libro o el resultado vigente; nunca sustituir un dato ausente por cero. Marcarlo como **«Falta [dato] en [hoja/columna]»** y conservar lo demás que el usuario haya ingresado. Validar números, fechas y claves antes de enviar.

## 3. Resultado

Mostrar primero el número o recomendación que responde a la tarea, con unidad, periodo, síntesis y estado. Usar estados explícitos: disponible, preliminar, falta dato o no estimable. La misma entrada y libro deben dar el mismo resultado.

## 4. Fundamento

En cuatro líneas: **Fórmula**, **Dato usado** (incluida hoja/fuente y periodo), **Supuesto** y **Límite**. La pantalla presenta el resultado del motor; no reimplementa ni cambia el cálculo.

## 5. Siguiente acción y errores

Dejar una acción principal visible (registrar, exportar, aprobar o volver a editar). Tab recorre los campos en orden; Enter ejecuta solo la acción enfocada. Ante dato inválido, llevar el foco al campo y explicar en español qué falta o dónde está, sin traza técnica. Un error conserva la captura y permite corregirla. Funcionar sin internet con los datos locales disponibles.
