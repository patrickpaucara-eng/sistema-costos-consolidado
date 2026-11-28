# 07_archivo_truncado.xlsx — LEEME

- **Defecto:** el archivo se cortó en la mitad exacta de sus bytes. Simula una descarga o una copia por USB que se interrumpió.
- **Qué se tocó:** se tomó el libro completo, ya con su hoja LEEME, y se guardaron solo los primeros 50 % de los bytes. Por eso la hoja LEEME está dentro, pero no se puede abrir.
- **Mensaje que debería dar el sistema:** «El archivo no es un libro Excel (.xlsx) legible.»
- **Mensaje real de `validar()`:** el mismo. ✔
- **Qué no debe pasar:** que aparezca una traza de Python, que el sistema se cuelgue o que reemplace el libro bueno de la empresa. `calculo_local.registrar()` valida antes de guardar, así que el libro anterior no se toca. Que esto se cumpla en el ejecutable queda POR VERIFICAR.
