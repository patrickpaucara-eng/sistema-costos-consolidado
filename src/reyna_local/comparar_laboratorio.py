"""Comparación preliminar de dos resultados ya calculados; no modifica libros."""
from decimal import Decimal

ELEMENTOS = ('md', 'mod', 'cif', 'admin', 'gasto_venta', 'financiero', 'perdida', 'ocio')


def comparar(original, copia):
    if original.get('empresa', {}).get('codigo') != copia.get('empresa', {}).get('codigo'):
        raise ValueError('Las empresas deben coincidir.')
    if (original.get('periodo_actual'), original.get('sintesis')) != (copia.get('periodo_actual'), copia.get('sintesis')):
        raise ValueError('Periodo y síntesis deben coincidir.')
    def indice(r):
        filas = r.get('objetos', [])
        resultado = {x['codigo']: x for x in filas}
        if len(resultado) != len(filas): raise ValueError('Órdenes duplicadas.')
        return resultado
    a,b=indice(original),indice(copia)
    filas=[]
    for orden in sorted(a.keys() | b.keys()):
        for campo in ELEMENTOS:
            anterior=Decimal(str(a.get(orden, {}).get(campo) or 0))
            nuevo=Decimal(str(b.get(orden, {}).get(campo) or 0))
            filas.append({'orden':orden,'elemento':campo,'original':anterior,'copia':nuevo,'diferencia':nuevo-anterior})
    return filas
