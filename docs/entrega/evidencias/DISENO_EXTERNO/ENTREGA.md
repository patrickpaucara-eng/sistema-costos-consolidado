# Diseño externo según Tino (DBD pp. 23–29) — 21-nov
| Recomendación del libro | Implementación |
|---|---|
| Interfaces por módulo y tipo de usuario | Menú «Gerencial · Consultas» y «Operativo · Mantenimiento» |
| Consistencia: ruta natural | Una pantalla a la vez; el menú marca dónde estás |
| Masiva → Detalle → Resumen | Órdenes (buscador, clic) → Ficha de la orden (elementos, 3 síntesis, ruta, kardex) → Resumen |
| Opciones por defecto | Abre en Resumen, último periodo de la empresa, síntesis REAL |
| Arrepentimiento | Reemplazar un libro pide confirmación; la versión previa se guarda y se puede restaurar (nada se pierde) |
| Mensajes uniformes | Catálogo único `MSG` en la interfaz |
| Búsqueda por índice alterno | Buscar órdenes por producto/código; medidas por inductor/destino |
| Todo dato guardado se muestra | Pantalla «Datos del libro» (ventas, órdenes, centros, clientes, medidas) |
Capturas: v1…v7. Prueba: `tests/test_libro_dbd.py::test_reemplazar_pide_confirmacion_guarda_version_y_restaura`.
