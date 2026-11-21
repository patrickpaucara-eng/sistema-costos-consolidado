# Cargador único con formato DBD y sello (21-nov)
- **Entrada única:** el sistema solo acepta libros con la estructura del DBD (`src/reyna_local/libro_dbd.py`). Valida hojas,
  columnas, referencias (LINEA→RECURSO, REGLA_REPARTO→CRITERIO, VENTA→productos…), periodos AAAA-MM, cantidades y
  entradas de kardex con valor. **No corrige**: rechaza y explica en español qué fila arreglar.
- **Adaptadores fuera del sistema:** `casos/frenosa/generar.py` convierte los CSV del caso al libro DBD (`casos/libros/frenosa.xlsx`).
  Otra empresa escribe su propio adaptador o llena la plantilla vacía (`/api/plantilla`, hoja LEEME).
- **Sin Frenosa en el cálculo:** empresa, productos (OBJ_PRO) y ventas (tabla VENTA) se leen del libro.
- **Sello:** cada resultado guarda la huella SHA-256 del libro, la versión, el método, semilla y simulaciones; el panel
  «Calidad y cuadre» verifica si el libro sigue intacto (VIGENTE / LIBRO_MODIFICADO).
- Pruebas: `tests/test_libro_dbd.py` (libro válido, libro roto rechazado, plantilla, otra empresa cargada por la interfaz,
  calculada y sellada; el sello detecta el cambio del libro).
