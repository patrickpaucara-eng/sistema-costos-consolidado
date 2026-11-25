"""Inventario de encabezados DBD, sin declarar nivel de suficiencia."""
from openpyxl import load_workbook
from .libro_dbd import OBLIGATORIAS, OPCIONALES, DESCRIPCION


def catalogo(libro):
    wb = load_workbook(libro, read_only=True, data_only=True)
    try:
        salida = []
        for nombre in OBLIGATORIAS + OPCIONALES:
            if nombre in wb.sheetnames:
                encabezados = next(wb[nombre].iter_rows(min_row=1, max_row=1, values_only=True), ())
                campos = [str(x) for x in encabezados if x not in (None, '')]
            else:
                campos = []
            salida.append({'tabla': nombre, 'descripcion': DESCRIPCION.get(nombre, ''),
                           'obligatoria': nombre in OBLIGATORIAS, 'campos': campos,
                           'presente': nombre in wb.sheetnames})
        return salida
    finally:
        wb.close()
