"""Exporta exclusivamente datos de un contrato de resultados ya calculado."""
from html import escape
import json
from pathlib import Path
from uuid import uuid4

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from .contrato import validar

TIPOS = {'resultados': '.xlsx', 'analitica': '.xlsx', 'proyeccion': '.xlsx', 'solver': '.xlsx', 'html': '.html', 'codigo': '.docx', 'informe': '.docx', 'presentacion': '.html', 'entrada': '.xlsx', 'sistema': '.html'}
SIN_RESULTADOS = ('codigo', 'entrada')          # se generan desde el repositorio, no desde un contrato
from .raiz import RAIZ
SECCIONES = {
    'resultados': [('Objetos', 'objetos'), ('Actividades', 'actividades'), ('Estado NIIF 18', 'estado_resultados'),
                   ('Kardex', 'kardex'), ('Calidad y cuadre', 'control')],
    'analitica': [('Relevancia', 'relevancia'), ('Hallazgos', 'hallazgos')],
    'proyeccion': [('Serie', 'serie'), ('Escenarios', 'escenarios'), ('Propuestas', 'propuestas')],
}


def _celda(value):
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True)
    # Excel no debe interpretar contenido procedente del contrato como fórmula.
    if isinstance(value, str) and value.startswith(('=', '+', '-', '@')):
        return "'" + value
    return value


def _columnas(rows):
    return list(dict.fromkeys(key for row in rows for key in row))


def _libro(resultados, tipo, destino, proyeccion_granular=None):
    libro = Workbook()
    resumen = libro.active
    resumen.title = 'Identificación'
    for key, value in [('Empresa', resultados['empresa'].get('nombre')), ('Periodo', resultados['periodo_actual']),
                       ('Síntesis', resultados['sintesis']), ('Moneda', resultados['moneda']),
                       ('Origen', resultados.get('_nota', 'Resultado suministrado'))]:
        resumen.append([key, _celda(value)])
    for nombre, campo in SECCIONES[tipo]:
        hoja = libro.create_sheet(nombre)
        rows = resultados.get(campo) or []
        columnas = _columnas(rows)
        if not columnas:
            hoja.append(['Sin datos disponibles'])
            continue
        hoja.append(columnas)
        for cell in hoja[1]:
            cell.font = Font(bold=True)
        hoja.freeze_panes = 'A2'
        for row in rows:
            hoja.append([_celda(row.get(col)) for col in columnas])
        if campo == 'propuestas':
            hoja.append([])
            hoja.append(['TOTAL impacto anual (S/)', round(sum(float(r.get('impacto_anual') or 0) for r in rows), 2)])
            hoja.cell(hoja.max_row, 1).font = Font(bold=True)
    if tipo == 'resultados':
        _hojas_ruta_y_modelo(libro, resultados)
    # Cada hoja transcribe hojas escalares del bloque, sin cálculos ni redondeos.
    bloques = {
        'resultados': [('Rechazos', 'rechazos')],
        'analitica': [('Costeo variable', 'costeo_variable'),
                      ('Estratégico COQ', 'estrategico.coq'),
                      ('Gobierno del dato', 'estrategico.gobierno_dato'),
                      ('Aprendizaje', 'aprendizaje')],
        'proyeccion': [('Proyección granular', 'proyeccion_granular'),
                       ('Sensibilidad', 'sensibilidad'), ('Aprendizaje', 'aprendizaje')],
    }
    for nombre, ruta in bloques[tipo]:
        dato = resultados
        for parte in ruta.split('.'):
            dato = dato.get(parte) if isinstance(dato, dict) else None
        hoja = libro.create_sheet(nombre)
        hoja.append(['Campo del contrato', 'Valor'])
        filas = list(_hojas_valores(dato, ruta))
        if not filas:
            hoja.append(['Sin datos disponibles', None])
        for campo, valor in filas:
            # Excel/openpyxl almacena 16 cifras significativas; texto exacto si perdería precisión.
            exacto = repr(valor) if isinstance(valor, float) and float(format(valor, '.16g')) != valor else valor
            hoja.append([campo, _celda(exacto)])
        hoja.freeze_panes = 'A2'
    if tipo == 'proyeccion' and proyeccion_granular is not None:
        # C21 devuelve proyección integral REAL sobre el último periodo del libro.
        # No debe confundirse con la síntesis o periodo histórico seleccionado.
        for nombre in ('Proyección granular', 'Sensibilidad'):
            del libro[nombre]
        hoja = libro.create_sheet('Proyección por hechos')
        hoja.append(['Base del libro', proyeccion_granular['base'], 'Síntesis proyectada', 'REAL integral'])
        filas = []
        for mes in proyeccion_granular['meses']:
            for producto in mes['productos']:
                fila = {'periodo': mes['periodo'], **{k: v for k, v in producto.items() if k != 'elementos'}}
                fila.update({'elemento_' + k: v for k, v in producto.get('elementos', {}).items()})
                filas.append(fila)
        _tabla_en_hoja(hoja, filas); hoja.freeze_panes = 'A3'
        hoja = libro.create_sheet('Sensibilidad')
        hoja.append(['Base del libro', proyeccion_granular['base'], 'Unidad', 'Variación del margen'])
        _tabla_en_hoja(hoja, proyeccion_granular['sensibilidad']); hoja.freeze_panes = 'A3'
    libro.save(destino)
    libro.close()


def _modelo_solver(resultados):
    """Prepara datos de Solver desde el contrato REAL, sin volver a calcular costos."""
    if resultados.get('sintesis') != 'REAL':
        raise ValueError('El modelo de Solver requiere un resultado REAL.')
    decidir = resultados.get('decidir') or {}
    er = (decidir.get('er_gerencial') or {}).get('productos') or []
    objetos = resultados.get('objetos') or []
    cantidades = {}
    codigos_producto = {}
    for objeto in objetos:
        codigo = str(objeto.get('codigo') or '')
        producto = str(objeto.get('producto') or '')
        if codigo and producto:
            codigos_producto[codigo] = producto
            cantidades[producto] = cantidades.get(producto, 0.0) + float(objeto.get('cantidad') or 0)
    ventas = {}
    for venta in (resultados.get('datos_libro') or {}).get('ventas') or []:
        producto = str(venta.get('producto') or '')
        ventas[producto] = ventas.get(producto, 0.0) + float(venta.get('cantidad') or 0)
    productos = []
    for fila in sorted(er, key=lambda x: str(x.get('producto') or '')):
        producto = str(fila.get('producto') or '')
        q = float(fila.get('cantidad') or cantidades.get(producto, 0.0))
        if not producto or q <= 0:
            continue
        mc = float(fila.get('margen_contribucion') or 0.0)
        productos.append({
            'producto': producto,
            'mc_unitario': mc / q,
            'vendido': ventas.get(producto, 0.0),
            'minimo': 0.0,
            'maximo': ventas.get(producto, 0.0) * 1.5,
            'cantidad_objeto': cantidades.get(producto, q),
        })
    if not productos:
        raise ValueError('El resultado REAL no contiene productos con cantidad para el modelo Solver.')

    medidas = (resultados.get('datos_libro') or {}).get('medidas') or []
    inductores = {str(i.get('codigo')): i for i in ((resultados.get('modelo') or {}).get('inductores') or [])}
    traza_llaves = {
        (str(t.get('criterio') or ''), str(t.get('origen') or ''), str(t.get('destino') or ''))
        for t in resultados.get('trazas') or []
    }
    medidas_obj = {}
    for medida in medidas:
        if str(medida.get('nivel') or '').upper() != 'OBJ':
            continue
        clave = (str(medida.get('inductor') or ''), str(medida.get('destino') or ''))
        medidas_obj[clave] = medidas_obj.get(clave, 0.0) + float(medida.get('cantidad') or 0.0)

    capacidades = []
    avisos = []
    seen = set()
    for medida in medidas:
        if str(medida.get('nivel') or '').upper() != 'CAP':
            continue
        criterio, destino = str(medida.get('inductor') or ''), str(medida.get('destino') or '')
        clave = (criterio, destino)
        if clave in seen:
            raise ValueError(f'La capacidad {criterio}/{destino} está duplicada en el resultado REAL.')
        seen.add(clave)
        capacidad = float(medida.get('cantidad') or 0.0)
        relacionada = any(c == criterio and (o == destino or d == destino) for c, o, d in traza_llaves)
        if not relacionada:
            avisos.append(f'{criterio}/{destino}: no hay una traza que vincule la capacidad con el costo del periodo; se excluyó.')
            continue
        filas_por_producto = {}
        completos = True
        for codigo, producto in codigos_producto.items():
            key = (criterio, codigo)
            if key not in medidas_obj:
                completos = False
                break
            filas_por_producto[producto] = filas_por_producto.get(producto, 0.0) + medidas_obj[key]
        if not completos:
            avisos.append(f'{criterio}/{destino}: faltan medidas OBJ por orden; se excluyó para no suponer consumos.')
            continue
        coeficientes = {}
        for producto in productos:
            cantidad = producto['cantidad_objeto']
            coeficientes[producto['producto']] = filas_por_producto.get(producto['producto'], 0.0) / cantidad if cantidad else 0.0
        info = inductores.get(criterio) or {}
        capacidades.append({
            'inductor': criterio,
            'destino': destino,
            'nombre': medida.get('destino_nombre') or destino,
            'unidad': info.get('unidad') or '',
            'capacidad': capacidad,
            'coeficientes': coeficientes,
        })
    if not capacidades:
        if not any('faltan medidas OBJ' in aviso or 'no hay una traza' in aviso for aviso in avisos):
            avisos.append('El resultado REAL no trae medidas CAP; el modelo queda limitado por demanda y no representa capacidad escasa.')
        else:
            avisos.append('No se pudo construir una restricción de capacidad completa; revisa MEDIDA CAP, medidas OBJ y trazas del periodo.')
    return {'productos': productos, 'capacidades': capacidades, 'avisos': avisos}


def _solver_libro(resultados, destino):
    """Libro de programación lineal listo para configurar/ejecutar con Solver de Excel."""
    from openpyxl.workbook.defined_name import DefinedName

    modelo = _modelo_solver(resultados)
    productos = modelo['productos']
    capacidades = modelo['capacidades']
    libro = Workbook()
    hoja = libro.active
    hoja.title = 'Modelo'
    hoja['A1'] = 'Mezcla óptima de producción · resultado REAL'
    hoja['A1'].font = Font(bold=True, size=14)
    hoja['A2'] = 'Margen de contribución total (S/) · objetivo'
    hoja['B2'] = '=SUMPRODUCT(B6:B' + str(5 + len(productos)) + ',C6:C' + str(5 + len(productos)) + ')'
    hoja['B2'].number_format = '#,##0.00'
    headers = ['Producto', 'MC unitario REAL (S/)', 'Unidades [solver_adj]', 'Mínimo (SUPUESTO)', 'Máximo (SUPUESTO)', 'Vendido REAL']
    for col, value in enumerate(headers, 1):
        c = hoja.cell(5, col, value); c.font = Font(bold=True)
    amarillo = PatternFill('solid', fgColor='FFF2CC')
    first = 6
    for i, producto in enumerate(productos):
        row = first + i
        hoja.cell(row, 1, producto['producto'])
        hoja.cell(row, 2, producto['mc_unitario'])
        hoja.cell(row, 3, 0.0)
        hoja.cell(row, 4, producto['minimo'])
        hoja.cell(row, 5, producto['maximo'])
        hoja.cell(row, 6, producto['vendido'])
        for col in (4, 5): hoja.cell(row, col).fill = amarillo
        for col in (2, 4, 5, 6): hoja.cell(row, col).number_format = '#,##0.00'
    last = first + len(productos) - 1
    hoja['A3'] = 'Las celdas amarillas son supuestos editables; las unidades de la columna C son variables de decisión.'

    seccion = last + 3
    hoja.cell(seccion, 1, 'Restricciones del modelo')
    hoja.cell(seccion, 1).font = Font(bold=True)
    restriccion_header = seccion + 1
    columnas_producto = list(range(2, 2 + len(productos)))
    lhs_col = 2 + len(productos)
    rel_col, rhs_col = lhs_col + 1, lhs_col + 2
    hoja.cell(restriccion_header, 1, 'Recurso / demanda')
    for j, producto in enumerate(productos): hoja.cell(restriccion_header, columnas_producto[j], producto['producto'])
    hoja.cell(restriccion_header, lhs_col, 'Uso calculado')
    hoja.cell(restriccion_header, rel_col, 'solver_rel (1 ≤, 2 =, 3 ≥)')
    hoja.cell(restriccion_header, rhs_col, 'Límite')
    for cell in hoja[restriccion_header]: cell.font = Font(bold=True)
    restricciones = []
    for cap in capacidades:
        restricciones.append((f"{cap['nombre']} · {cap['inductor']} ({cap['unidad']})".strip(),
                              [cap['coeficientes'].get(p['producto'], 0.0) for p in productos], '<=', cap['capacidad']))
    for j, producto in enumerate(productos):
        vector = [1.0 if i == j else 0.0 for i in range(len(productos))]
        restricciones.append((f"Mínimo de {producto['producto']} (SUPUESTO)", vector, '>=', producto['minimo']))
        restricciones.append((f"Máximo de {producto['producto']} (SUPUESTO)", vector, '<=', producto['maximo']))
    for n, (nombre, coef, relation, rhs) in enumerate(restricciones, 1):
        row = restriccion_header + n
        hoja.cell(row, 1, nombre)
        for j, value in enumerate(coef): hoja.cell(row, columnas_producto[j], value)
        start_var = f'$C${first}:$C${last}'
        start_coef = f'${hoja.cell(1, columnas_producto[0]).column_letter}${row}:${hoja.cell(1, columnas_producto[-1]).column_letter}${row}'
        hoja.cell(row, lhs_col, f'=SUMPRODUCT({start_var},{start_coef})')
        hoja.cell(row, rel_col, {'<=': 1, '=': 2, '>=': 3}[relation])
        hoja.cell(row, rhs_col, rhs)
        hoja.cell(row, rhs_col).number_format = '#,##0.00'

    # Solver conserva su configuración como nombres definidos; el complemento Excel
    # guarda fórmulas OOXML en inglés aunque la interfaz las muestre como SUMAPRODUCTO.
    col_lhs, col_rel, col_rhs = (hoja.cell(1, col).column_letter for col in (lhs_col, rel_col, rhs_col))
    first_constraint, last_constraint = restriccion_header + 1, restriccion_header + len(restricciones)
    names = {
        'solver_opt': '=$B$2',
        'solver_adj': f'=$C${first}:$C${last}',
        # Los rangos completos son cómodos para inspección; el complemento usa además
        # los nombres numerados de cada restricción.
        'solver_rel': f'=${col_rel}${first_constraint}:${col_rel}${last_constraint}',
        'solver_rhs': f'=${col_rhs}${first_constraint}:${col_rhs}${last_constraint}',
        'solver_num': f'={len(restricciones)}',
        'solver_typ': '=1',       # maximizar
        'solver_lin': '=1',       # modelo lineal
        'solver_neg': '=1',       # variables no negativas
        'solver_eng': '=2',       # Simplex LP
    }
    for i in range(len(restricciones)):
        row = first_constraint + i
        names[f'solver_lhs{i + 1}'] = f'=${col_lhs}${row}'
        names[f'solver_rhs{i + 1}'] = f'=${col_rhs}${row}'
        names[f'solver_rel{i + 1}'] = f'=${col_rel}${row}'
    for name, reference in names.items():
        hoja.defined_names.add(DefinedName(name, attr_text=reference, hidden=True))
    hoja.freeze_panes = 'A6'
    for col, width in {'A': 38, 'B': 21, 'C': 23, 'D': 23, 'E': 23, 'F': 18}.items(): hoja.column_dimensions[col].width = width
    for col in range(lhs_col, rhs_col + 1): hoja.column_dimensions[hoja.cell(1, col).column_letter].width = 20

    instrucciones = libro.create_sheet('Instrucciones')
    instrucciones.append(['Cómo resolver en Excel Solver'])
    instrucciones['A1'].font = Font(bold=True, size=14)
    instrucciones.append(['1', 'Abra Datos > Solver. El modelo queda guardado en los nombres internos del complemento: objetivo solver_opt, variables solver_adj y restricciones solver_lhsN/solver_relN/solver_rhsN.'])
    instrucciones.append(['2', 'Compruebe que el método sea Simplex LP y pulse Resolver. El libro guarda maximización, linealidad y no negatividad.'])
    instrucciones.append(['3', 'Conserve la solución y marque Informe de sensibilidad en el cuadro de resultados.'])
    instrucciones.append([])
    instrucciones.append(['Las fórmulas se guardan en formato de Excel (SUMPRODUCT); Excel en español las presenta como SUMAPRODUCTO.'])
    instrucciones.column_dimensions['A'].width = 12; instrucciones.column_dimensions['B'].width = 112
    for row in instrucciones.iter_rows():
        for cell in row: cell.alignment = Alignment(wrap_text=True, vertical='top')
    lectura = libro.create_sheet('Lectura')
    lectura.append(['Cómo leer la solución'])
    lectura['A1'].font = Font(bold=True, size=14)
    lectura.append(['Precio sombra', 'Valor marginal de una unidad adicional del recurso, dentro del rango válido.'])
    lectura.append(['Rango permitido', 'La solución sigue siendo óptima solo dentro de los rangos de aumento/disminución permitidos del informe de sensibilidad; fuera de ellos, vuelva a resolver.'])
    lectura.append(['Supuestos', 'Los límites de demanda min./máx. son editables. El máximo inicial equivale a 1.5 veces lo vendido en el periodo REAL; el mínimo inicial es cero.'])
    if modelo['avisos']:
        lectura.append(['Advertencia', ' '.join(modelo['avisos'])])
    lectura.column_dimensions['A'].width = 24; lectura.column_dimensions['B'].width = 115
    for row in lectura.iter_rows():
        for cell in row: cell.alignment = Alignment(wrap_text=True, vertical='top')
    libro.save(destino)
    libro.close()



def _hojas_valores(valor, ruta):
    """Aplana el JSON de manera reversible: números permanecen como números."""
    if isinstance(valor, dict):
        for clave, item in valor.items():
            yield from _hojas_valores(item, ruta + '.' + str(clave))
    elif isinstance(valor, list):
        for i, item in enumerate(valor):
            yield from _hojas_valores(item, ruta + '[' + str(i) + ']')
    elif valor is not None:
        yield ruta, valor

def _tabla_en_hoja(hoja, rows):
    columnas = _columnas(rows)
    if not columnas:
        hoja.append(['Sin datos disponibles']); return
    hoja.append([ETIQUETAS_XLS.get(c, c) for c in columnas])
    for cell in hoja[hoja.max_row]: cell.font = Font(bold=True)
    for row in rows: hoja.append([_celda(row.get(c)) for c in columnas])


ETIQUETAS_XLS = {'objeto': 'Orden', 'elemento': 'Elemento', 'etapa': 'Etapa', 'origen_nombre': 'De', 'destino_nombre': 'A',
                 'criterio_nombre': 'Inductor', 'cantidad_destino': 'Cantidad del destino', 'total_criterio': 'Total del inductor',
                 'tasa': 'Tasa', 'monto': 'Monto atribuido S/', 'raiz': 'Es origen'}


def _hojas_ruta_y_modelo(libro, r):
    """Como la consulta de costeo del prototipo: una hoja por etapa del reparto (P1…P7) y el modelo ABC."""
    trazas = r.get('trazas') or []
    cols = ['objeto', 'elemento', 'origen_nombre', 'destino_nombre', 'criterio_nombre', 'cantidad_destino', 'total_criterio', 'tasa', 'monto', 'raiz']
    for etapa in sorted({t['etapa'] for t in trazas}):
        hoja = libro.create_sheet(('Ruta ' + etapa)[:31]); hoja.freeze_panes = 'A2'
        _tabla_en_hoja(hoja, [{c: t.get(c) for c in cols} for t in trazas if t['etapa'] == etapa])
    inv = r.get('inventarios') or {}
    for nombre, filas in (('Inventario PT', inv.get('kardex_pt')), ('Saldos PT', inv.get('saldos_pt')), ('En proceso', inv.get('en_proceso')),
                          ('Ajustes D14', inv.get('ajustes_d14')), ('Coproductos', inv.get('coproductos')), ('Pérdidas anormales', r.get('perdidas')),
                          ('Capacidad ociosa', r.get('capacidad_ociosa')), ('Costeo normal', (r.get('costeo_normal') or {}).get('ordenes')),
                          ('Variaciones material', r.get('variaciones'))):
        if filas:
            hoja = libro.create_sheet(nombre[:31]); hoja.freeze_panes = 'A2'; _tabla_en_hoja(hoja, filas)
    m = r.get('modelo') or {}
    for nombre, campo in (('Modelo - Reglas', 'reglas'), ('Modelo - Recursos', 'recursos'), ('Modelo - Actividades', 'actividades'),
                          ('Modelo - Inductores', 'inductores'), ('Modelo - Centros', 'centros')):
        if m.get(campo):
            hoja = libro.create_sheet(nombre[:31]); hoja.freeze_panes = 'A2'; _tabla_en_hoja(hoja, m[campo])


def _entrada(destino, resultados=None):
    """Datos de entrada = el libro DBD exacto con que se calculó (el que valida libro_dbd y sella el resultado),
    con una hoja LEEME al inicio. Los archivos de origen del ERP pertenecen al adaptador de cada empresa."""
    import shutil
    from .calculo_local import libros
    from . import libro_dbd as B
    disp = libros(destino.parent.parent) if destino.parent.name == 'exportaciones' else libros(destino.parent)
    nombre = Path(((resultados or {}).get('sello') or {}).get('libro', 'frenosa.xlsx')).stem
    origen = disp.get(nombre) or next(iter(disp.values()))
    shutil.copy(origen, destino)
    from openpyxl import load_workbook
    libro = load_workbook(destino); ws = libro.create_sheet('LEEME', 0)
    ws.append(['Datos de entrada del Sistema de Costos Reyna (formato DBD)']); ws['A1'].font = Font(bold=True)
    ws.append(['Libro', origen.name]); ws.append(['Huella SHA-256 del libro original', B.huella(origen)])
    ws.append(['Empresa', ' · '.join(B.empresa(origen))]); ws.append([])
    ws.append(['Hoja', 'Contenido'])
    for n in B.OBLIGATORIAS + B.OPCIONALES: ws.append([n, B.DESCRIPCION.get(n, '')])
    libro.save(destino); libro.close()


def _numero(v):
    if not v or (len(v) > 1 and v[0] == '0' and v[1] != '.'):     # códigos con cero inicial siguen siendo texto
        return v
    try:
        return float(v) if any(c in v for c in '.eE') else int(v)
    except (TypeError, ValueError):
        return v
    libro.close()


ETIQUETAS = {
    'ventas': 'Ventas (S/)', 'costo_total': 'Costo total (S/)', 'margen_operativo': 'Margen operativo (S/)', 'margen': 'Margen (S/)',
    'rentabilidad': 'Rentabilidad', 'costo_unitario_prom': 'Costo unitario promedio (S/)', 'resultado_antes_impuestos': 'Resultado antes de impuestos (S/)',
    'codigo': 'Código', 'producto': 'Producto', 'cantidad': 'Cantidad', 'md': 'Material directo', 'mod': 'Mano de obra directa', 'cif': 'CIF',
    'admin': 'Administración', 'gasto_venta': 'Gasto de venta', 'financiero': 'Financiero', 'costo_unitario': 'Costo unitario', 'ingreso': 'Ingreso',
    'periodo': 'Periodo', 'tipo': 'Tipo', 'p05': 'P05', 'p50': 'P50 (mediana)', 'p95': 'P95', 'elemento': 'Elemento', 'importe': 'Importe (S/)',
    'porcentaje': '%', 'acumulado': '% acumulado', 'critico': 'Crítico', 'referencia': 'Referencia', 'mensaje': 'Hallazgo', 'impacto': 'Impacto (S/)',
    'causa': 'Causa', 'variacion': 'Variación', 'nombre': 'Escenario', 'supuestos': 'Supuestos', 'margen_p05': 'Margen P05', 'margen_p50': 'Margen P50',
    'margen_p95': 'Margen P95', 'prob_perdida': 'Prob. de pérdida', 'descripcion': 'Descripción', 'impacto_anual': 'Impacto anual (S/)',
    'plazo': 'Plazo', 'responsable': 'Responsable', 'cu_total': 'Costo unitario estimado', 'metodo': 'Método', 'mase': 'MASE',
    'HISTORICO': 'Histórico', 'ACTUAL': 'Actual', 'PROYECTADO_DET': 'Proyección determinística', 'PROYECTADO_EST': 'Proyección estocástica (rango 90 %)',
}
PORCENTAJES = {'rentabilidad', 'porcentaje', 'acumulado', 'variacion', 'prob_perdida'}
MESES = ('enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre')


def _fmt(campo, v):
    if isinstance(v, bool):
        return 'Sí' if v else 'No'
    if isinstance(v, (int, float)):
        if campo in PORCENTAJES:
            return f'{v * 100:,.1f} %'
        return f'{v:,.4f}' if abs(v) < 100 and v != int(v) else f'{v:,.2f}'
    if isinstance(v, dict):
        return ', '.join(f'{k}: {x}' for k, x in v.items())
    return ETIQUETAS.get(str(v), str(v)) if v is not None else '—'


def _html(resultados, destino):
    def tabla(rows):
        columnas = _columnas(rows)
        if not columnas:
            return '<p>Sin datos disponibles.</p>'
        head = ''.join('<th>' + escape(ETIQUETAS.get(c, c)) + '</th>' for c in columnas)
        body = ''.join('<tr>' + ''.join('<td' + (f' class="n" data-valor="{r.get(c)}"' if isinstance(r.get(c), (int, float)) and not isinstance(r.get(c), bool) else '') + '>'
                                        + escape(_fmt(c, r.get(c))) + '</td>' for c in columnas) + '</tr>' for r in rows)
        return '<table><thead><tr>' + head + '</tr></thead><tbody>' + body + '</tbody></table>'
    kpis = ''.join('<div class="kpi"><span>' + escape(ETIQUETAS.get(k, k)) + '</span><b data-valor="' + escape(str(v)) + '">' + escape(_fmt(k, v)) + '</b></div>'
                   for k, v in resultados['kpi'].items())
    secciones = ''.join('<h2>' + escape(nombre) + '</h2>' + tabla(resultados.get(campo) or [])
                        for nombre, campo in [*SECCIONES['resultados'], *SECCIONES['analitica'], *SECCIONES['proyeccion']])
    trazas = resultados.get('trazas') or []
    if trazas:
        resumen = {}
        for t in trazas:
            if t.get('raiz'):
                k = (t['objeto'], t['elemento'], t['origen_nombre']); resumen[k] = resumen.get(k, 0) + float(t['monto'])
        filas = [dict(objeto=o, elemento=e, origen=n, monto=round(v, 2)) for (o, e, n), v in sorted(resumen.items())]
        secciones += ('<h2>Ruta del costo: de qué recurso sale cada elemento de cada orden</h2><p class="nota">Suma de los tramos de origen '
                      '(algoritmo ALG-11); el detalle tramo por tramo está en el Excel de resultados (hojas «Ruta P1…P7»).</p>' + tabla(filas))
    reglas = (resultados.get('modelo') or {}).get('reglas') or []
    if reglas:
        secciones += '<h2>Modelo ABC: reglas de reparto por etapa</h2>' + tabla(reglas)
    # Dibuja valores publicados; la banda corresponde al margen P05–P95.
    serie = resultados['serie']
    chart = ''
    if serie:
        periodos = sorted({str(x['periodo']) for x in serie})
        valores = [float(x[k]) for x in serie for k in ('ventas','costo_total','margen','p05','p50','p95') if isinstance(x.get(k), (int,float))]
        minimo, maximo = min(0, *valores), max(1, *valores)
        x = lambda periodo: 40 + 700 * periodos.index(str(periodo)) / max(1, len(periodos)-1)
        y = lambda value: 190 - 150 * (value-minimo) / (maximo-minimo)
        grupos = []
        banda = sorted((r for r in serie if r.get('tipo')=='PROYECTADO_EST' and isinstance(r.get('p05'),(int,float)) and isinstance(r.get('p95'),(int,float))), key=lambda r:r['periodo'])
        if banda:
            puntos = [f"{x(r['periodo']):.2f},{y(r['p95']):.2f}" for r in banda] + [f"{x(r['periodo']):.2f},{y(r['p05']):.2f}" for r in reversed(banda)]
            grupos.append('<polygon data-banda="p05-p95" fill="#c1e4db" points="'+' '.join(puntos)+'"/>')
            grupos.append('<polyline fill="none" stroke="#118067" stroke-dasharray="3 3" points="'+' '.join(f"{x(r['periodo']):.2f},{y(r['p50']):.2f}" for r in banda if isinstance(r.get('p50'),(int,float)))+'"/>')
        for campo, color in [('ventas','#315d6f'),('costo_total','#ce8334'),('margen','#118067')]:
            for tipo in ('HISTORICO','PROYECTADO_DET'):
                filas = sorted((r for r in serie if r.get('tipo') in (tipo,'ACTUAL') and isinstance(r.get(campo),(int,float))),key=lambda r:r['periodo'])
                puntos = ' '.join(f"{x(r['periodo']):.2f},{y(r[campo]):.2f}" for r in filas)
                grupos.append(f'<polyline fill="none" stroke="{color}" stroke-width="2" stroke-dasharray="{("5 5" if tipo == "PROYECTADO_DET" else "none")}" points="{puntos}"/>')
        ejes = (f'<line x1="40" x2="740" y1="{y(0):.2f}" y2="{y(0):.2f}" stroke="#8a97a8" stroke-dasharray="2 3"/>'
                f'<text x="0" y="{y(maximo)+4:.2f}" class="eje">{maximo/1000:,.0f} mil</text><text x="0" y="{y(0)+4:.2f}" class="eje">0</text>'
                f'<text x="0" y="{y(minimo)+4:.2f}" class="eje">{minimo/1000:,.0f} mil</text>'
                f'<text x="40" y="212" class="eje">{periodos[0]}</text><text x="700" y="212" class="eje">{periodos[-1]}</text>')
        leyenda = ('<p class="leyenda"><i style="background:#315d6f"></i>Ventas <i style="background:#ce8334"></i>Costo total '
                   '<i style="background:#118067"></i>Margen <i style="background:#c1e4db"></i>Rango 90 % del margen (P05–P95) · '
                   'línea sólida: histórico · punteada: proyección determinística</p>')
        chart = '<h2>Ventas, costo y margen</h2>' + leyenda + '<svg viewBox="0 0 780 220" role="img" aria-label="Evolución">'+ejes+''.join(grupos)+'</svg>'
    info = resultados.get('proyeccion_info') or {}
    if info:
        chart += ('<p class="nota">Modelos elegidos por menor error fuera de muestra — ventas: ' + escape(str(info.get('modelo_ventas'))) + ' · costo: '
                  + escape(str(info.get('modelo_costo'))) + ' · margen: ' + escape(str(info.get('modelo_margen'))) + ' (MASE ' + escape(str(info.get('mase_margen')))
                  + '; menor que 1 = mejor que repetir el último mes) · ' + escape(str(info.get('simulaciones'))) + ' simulaciones Monte Carlo, semilla '
                  + escape(str(info.get('semilla'))) + '.</p>')
    if not any(str(r.get('tipo','')).startswith('PROYECTADO') for r in serie):
        chart += '<p>Se necesitan más de 6 meses para proyectar</p>'
    if resultados.get('sintesis') == 'CONTABLE':
        chart += '<p>Financieros fuera del inventario (NIC 2 / NIIF 18)</p>'
    if resultados.get('sintesis') == 'ESTIMADO':
        chart += '<h2>Estimación estadística fuera de muestra (no es un estándar)</h2>' + tabla([dict(producto=k, **v) for k,v in (resultados.get('estimacion') or {}).items()])
    escenarios = resultados['escenarios']
    rangos = [r for r in escenarios if all(isinstance(r.get(k),(int,float)) for k in ('margen_p05','margen_p50','margen_p95'))]
    if rangos:
        bajo = min(0, *(r['margen_p05'] for r in rangos))
        alto = max(1, *(r['margen_p95'] for r in rangos))
        escala = lambda v: 240 + 520 * (v-bajo)/(alto-bajo)
        figuras = []
        for i,r in enumerate(rangos):
            y_r = 25 + i * 170 / max(1,len(rangos))
            figuras.append(f'<text x="5" y="{y_r+4:.2f}">{escape(str(r.get("nombre", "")))}</text><line x1="{escala(r["margen_p05"]):.2f}" x2="{escala(r["margen_p95"]):.2f}" y1="{y_r:.2f}" y2="{y_r:.2f}" stroke="#118067" stroke-width="5"/><circle cx="{escala(r["margen_p50"]):.2f}" cy="{y_r:.2f}" r="5" fill="#243f80"/>')
        figuras.append(f'<line x1="{escala(0):.2f}" x2="{escala(0):.2f}" y1="10" y2="200" stroke="#b85142" stroke-dasharray="3 3"/><text x="{escala(0)+4:.2f}" y="212" class="eje">margen 0</text>')
        chart += '<h2>Rango de escenarios</h2><p class="leyenda">Barra: margen P05–P95 · punto: mediana · línea roja: pérdida</p><svg viewBox="0 0 780 220" role="img" aria-label="Escenarios">'+''.join(figuras)+'</svg>'
    chart += '<p><b>Impacto anual total de las propuestas: S/ ' + escape(f"{sum(float(x.get('impacto_anual',0)) for x in resultados['propuestas']):,.2f}") + '</b></p>'
    objetos = resultados['objetos']
    if objetos:
        keys = ('md', 'mod', 'cif', 'admin', 'gasto_venta', 'financiero')
        colors = ('#116b61', '#47988b', '#82bdb1', '#d0a35c', '#dc7650', '#845a78')
        maximum = max(1, *(float(o.get('costo_total', 0)) for o in objetos))
        width = 650 / len(objetos)
        bars = []
        for index, obj in enumerate(objetos):
            y = 190
            for key, color in zip(keys, colors):
                height = max(0, float(obj.get(key, 0))) * 150 / maximum
                y -= height
                bars.append(f'<rect x="{60+index*width:.2f}" y="{y:.2f}" width="{width*.6:.2f}" height="{height:.2f}" fill="{color}"/>')
            bars.append(f'<text x="{60+index*width:.2f}" y="215">{escape(str(obj.get("codigo", "")))}</text>')
        chart += '<h2>Costos por objeto</h2><svg viewBox="0 0 780 230" role="img" aria-label="Costos por objeto">' + ''.join(bars) + '</svg>'
    relevancia = resultados['relevancia']
    if relevancia:
        maximum = max(1, *(float(x.get('importe', 0)) for x in relevancia))
        width = 650 / len(relevancia)
        barras, puntos = [], []
        for index, item in enumerate(relevancia):
            x = 60 + index * width
            height = max(0, float(item.get('importe', 0))) * 150 / maximum
            color = '#b85142' if item.get('critico') else '#47988b'
            barras.append(f'<rect x="{x:.2f}" y="{190-height:.2f}" width="{width*.6:.2f}" height="{height:.2f}" fill="{color}"/>')
            puntos.append(f'{x+width*.3:.2f},{190-float(item.get("acumulado",0))*150:.2f}')
        chart += '<h2>Relevancia</h2><svg viewBox="0 0 780 220" role="img" aria-label="Relevancia">' + ''.join(barras) + '<polyline fill="none" stroke="#243f80" stroke-width="2" points="' + ' '.join(puntos) + '"/></svg>'
    a, m = str(resultados['periodo_actual']).split('-')[:2] if '-' in str(resultados['periodo_actual']) else (resultados['periodo_actual'], '0')
    mes = (MESES[int(m) - 1] + ' ' + a) if m.isdigit() and 1 <= int(m) <= 12 else str(resultados['periodo_actual'])
    explica = {'REAL': 'Costo integral (producción, administración, ventas y financieros) con ABC por etapas.',
               'CONTABLE': 'Costo de inventario según NIC 2; administración, ventas y financieros van a resultados (NIIF 18).',
               'ESTIMADO': 'Estimación estadística fuera de muestra con banda P05–P95 (no es un estándar).'}.get(resultados['sintesis'], '')
    documento = ('<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                 '<title>Resultados de costos</title><style>:root{color-scheme:light}body{font:15px/1.5 system-ui,Segoe UI,sans-serif;margin:0;'
                 'background:#f4f7fa;color:#15253d}main{max-width:1100px;margin:auto;padding:1.5rem}header{background:#15253d;color:#fff;padding:1.2rem 1.5rem}'
                 'header h1{margin:0;font-size:1.5rem}header p{margin:.3rem 0 0;opacity:.85}h2{margin-top:2rem;border-bottom:2px solid #c1e4db;padding-bottom:.3rem}'
                 '.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:.8rem}.kpi{background:#fff;border-radius:8px;padding:.8rem;'
                 'box-shadow:0 1px 3px #0002}.kpi span{display:block;font-size:.8rem;color:#55657a}.kpi b{font-size:1.25rem}svg{background:#fff;border-radius:8px;'
                 'width:100%;height:auto}.eje{font-size:11px;fill:#55657a}.leyenda i{display:inline-block;width:12px;height:12px;margin:0 .3rem 0 .8rem;'
                 'vertical-align:middle;border-radius:2px}.nota{font-size:.85rem;color:#55657a}table{border-collapse:collapse;display:block;overflow:auto;'
                 'margin-bottom:1.5rem;background:#fff}td,th{border:1px solid #dbe3ec;padding:.4rem .6rem;text-align:left}td.n{text-align:right;'
                 'font-variant-numeric:tabular-nums}th{background:#e8eff8;font-size:.85rem}</style><header><h1>Sistema de Costos Reyna · '
                 + escape(str(resultados['empresa'].get('nombre', ''))) + '</h1><p>' + escape(mes) + ' · Síntesis ' + escape(resultados['sintesis'])
                 + ' · ' + escape(explica) + ('' if '_nota' not in resultados else ' · ' + escape(str(resultados['_nota']))) + '</p></header><main>'
                 '<h2>Indicadores</h2><div class="kpis">' + kpis + '</div>' + chart + secciones
                 + '<p class="nota">Archivo generado sin conexión: todos los datos vienen del resultado calculado; no requiere internet.</p></main></html>')
    destino.write_text(documento, encoding='utf-8')


def _informe(r, destino):
    """Informe fiel al contrato; no completa datos ni supone efectos futuros."""
    from docx import Document
    doc = Document()
    doc.add_heading('Informe técnico de costos', 0)
    doc.add_paragraph(f"{r['empresa'].get('nombre', '')} · {r['periodo_actual']} · {r['sintesis']} · {r['moneda']}")
    def text(value):
        if value is None: return 'No disponible'
        if isinstance(value, float):
            from decimal import Decimal
            precision = max(2, -Decimal(str(value)).as_tuple().exponent)
            return f'{value:,.{precision}f}'
        return str(value)
    def rows(items, fields):
        if not items:
            doc.add_paragraph('Sin información disponible en el contrato.')
            return
        table = doc.add_table(rows=1, cols=len(fields)); table.style = 'Table Grid'
        for cell, (_, label) in zip(table.rows[0].cells, fields): cell.text = label
        for item in items:
            cells = table.add_row().cells
            for cell, (key, _) in zip(cells, fields): cell.text = text(item.get(key))
    doc.add_heading('1. Resumen ejecutivo', level=1)
    rows([r['kpi']], [('ventas','Ventas'),('costo_total','Costo total'),('margen_operativo','Margen operativo'),('rentabilidad','Rentabilidad')])
    doc.add_paragraph('Sello: ' + text(r.get('sello')))
    doc.add_heading('2. Análisis', level=1)
    doc.add_heading('Descriptivo', level=2)
    rows([x for x in r['serie'] if x.get('tipo') in ('HISTORICO','ACTUAL')], [('periodo','Periodo'),('ventas','Ventas'),('costo_total','Costo'),('margen','Margen')])
    doc.add_heading('Diagnóstico y causa', level=2)
    rows(r['hallazgos'], [('mensaje','Hallazgo'),('causa','Causa'),('impacto','Impacto')])
    doc.add_heading('Relevancia (Pareto)', level=2)
    rows(r['relevancia'], [('elemento','Elemento'),('importe','Importe'),('porcentaje','Participación'),('critico','Crítico')])
    doc.add_heading('Predictivo y banda', level=2)
    projected = [x for x in r['serie'] if x.get('tipo') == 'PROYECTADO_EST']
    if not projected: doc.add_paragraph('Banda no estimable o no disponible en el contrato.')
    rows(projected, [('periodo','Periodo'),('margen','Margen'),('p05','P05'),('p50','P50'),('p95','P95')])
    doc.add_heading('Escenarios', level=2)
    rows(r['escenarios'], [('nombre','Escenario'),('margen','Margen'),('margen_p05','P05'),('margen_p95','P95')])
    doc.add_heading('3. Conclusiones', level=1)
    for h in r['hallazgos']: doc.add_paragraph(str(h.get('mensaje') or 'Hallazgo sin descripción.'), style='List Bullet')
    for x in r['relevancia']:
        if x.get('critico'): doc.add_paragraph(f"Elemento crítico: {text(x.get('elemento'))}; importe {text(x.get('importe'))}.", style='List Bullet')
    exclusions = (r.get('costeo_variable') or {}).get('no_controlables') or []
    excluded_codes = {str(x.get('codigo') or x.get('propuesta')) for x in exclusions if isinstance(x,dict) and (x.get('codigo') or x.get('propuesta'))}
    proposal_codes = {str(p.get('codigo')) for p in r['propuestas'] if p.get('codigo')}
    ambiguous = bool(exclusions) and (len(excluded_codes) < len(exclusions) or not excluded_codes <= proposal_codes)
    proposals = [] if ambiguous else [p for p in r['propuestas'] if str(p.get('codigo')) not in excluded_codes]
    doc.add_heading('4. Propuestas', level=1)
    if 'costeo_variable' not in r: doc.add_paragraph('Controlabilidad no informada: no se puede verificar el filtro de costos compartidos.')
    if ambiguous: doc.add_paragraph('Propuestas omitidas: hay exclusiones sin código de propuesta y no se pueden cotejar con seguridad.')
    rows(proposals, [('codigo','Código'),('descripcion','Propuesta'),('impacto_anual','Impacto anual'),('causa','Causa'),('responsable','Responsable')])
    doc.add_heading('5. Plan de implementación', level=1)
    ordered = sorted(proposals, key=lambda p: float(p.get('impacto_anual') or 0), reverse=True)
    rows(ordered, [('codigo','Propuesta'),('impacto_anual','Impacto anual'),('responsable','Responsable'),('plazo','Plazo'),('mes_medicion','Mes de medición'),('cu_objetivo','Costo unitario objetivo')])
    doc.add_heading('6. Impacto económico futuro', level=1)
    doc.add_paragraph(f"Suma de impactos anuales informados: {sum(float(p.get('impacto_anual') or 0) for p in proposals):,.2f} {r['moneda']}.")
    doc.add_paragraph('Proyección sin aplicar propuestas:')
    rows([x for x in r['serie'] if x.get('tipo') == 'PROYECTADO_DET'], [('periodo','Periodo'),('ventas','Ventas'),('costo_total','Costo'),('margen','Margen')])
    doc.add_paragraph('Resultado con propuestas: no disponible en el contrato; no se supone una distribución mensual de impactos.')
    doc.add_heading('6b. Gestión estratégica del costo', level=1)
    doc.add_paragraph('Ciclo de referencia: costea → diagnostica → propone → decide → aprende. Costo objetivo: precio de mercado menos margen objetivo; kaizen: seguimiento medido de las mejoras.')
    doc.add_paragraph('Costo de calidad y gobierno del dato: usar categorías, responsables y evidencia cuando el contrato los informe; no se infieren datos faltantes.')
    doc.add_paragraph('Arquitectura objetivo futura: captura MES/IoT mediante adaptador, MFCA ISO 14051, flujo de valor y benchmarking. No implica que estén implementados.')
    doc.add_heading('7. Anexos', level=1)
    doc.add_paragraph('Modelo de costeo de W. Oria; miradas REAL y CONTABLE; costo PROYECTADO por el mismo motor y su precisión.')
    rows(r.get('control') or [], [('control','Control'),('ok','Cumple'),('detalle','Detalle')])
    biggest = max(r['objetos'], key=lambda o: o.get('costo_total',0), default=None)
    if biggest:
        doc.add_heading('Ruta de la orden de mayor costo', level=2)
        rows([t for t in r.get('trazas',[]) if t.get('objeto') == biggest['codigo']], [('etapa','Etapa'),('origen_nombre','Origen'),('destino_nombre','Destino'),('monto','Monto')])
    doc.save(destino)


def _presentacion_html(r, destino):
    """Alternativa imprimible mientras no se compruebe python-pptx en Windows."""
    def fmt(v):
        if v is None: return 'No disponible'
        if isinstance(v, (int, float)) and not isinstance(v, bool): return f'{v:,.2f}'
        return str(v)
    def rows(data, fields):
        if not data: return '<p>Sin datos disponibles.</p>'
        head = ''.join('<th>' + escape(label) + '</th>' for _, label in fields)
        body = ''.join('<tr>' + ''.join('<td>' + escape(fmt(row.get(key))) + '</td>' for key, _ in fields) + '</tr>' for row in data)
        return '<table><thead><tr>' + head + '</tr></thead><tbody>' + body + '</tbody></table>'
    slides = []
    def slide(title, body): slides.append('<section><h1>' + escape(title) + '</h1>' + body + '</section>')
    slide('Presentación ejecutiva', '<p>' + escape(fmt(r['empresa'].get('nombre'))) + ' · ' + escape(fmt(r['periodo_actual'])) + ' · ' + escape(fmt(r['sintesis'])) + '</p><p>Sello: ' + escape(fmt(r.get('sello'))) + '</p>')
    slide('Indicadores', rows([r['kpi']], [('ventas','Ventas'),('costo_total','Costo total'),('margen_operativo','Margen operativo'),('rentabilidad','Rentabilidad')]))
    slide('Costo por producto', rows(r['objetos'], [('producto','Producto'),('cantidad','Cantidad'),('costo_total','Costo total'),('costo_unitario','Costo unitario')]))
    slide('Relevancia (Pareto)', rows(r['relevancia'], [('elemento','Elemento'),('importe','Importe'),('porcentaje','Participación'),('acumulado','Acumulado'),('critico','Crítico')]))
    slide('Hallazgos y causa', rows(r['hallazgos'], [('mensaje','Hallazgo'),('causa','Causa'),('impacto','Impacto')]))
    projected = [x for x in r['serie'] if x.get('tipo') == 'PROYECTADO_EST']
    slide('Proyección a seis meses', rows(projected, [('periodo','Periodo'),('margen','Margen'),('p05','P05'),('p50','P50'),('p95','P95')]) if projected else '<p>Banda no estimable o no disponible.</p>')
    slide('Propuestas', rows(r['propuestas'], [('descripcion','Propuesta'),('impacto_anual','Impacto anual'),('responsable','Responsable')]))
    proposals = sorted(r['propuestas'], key=lambda p:float(p.get('impacto_anual') or 0), reverse=True)
    slide('Plan de implementación', rows(proposals, [('descripcion','Propuesta'),('impacto_anual','Impacto anual'),('responsable','Responsable'),('plazo','Plazo')]))
    page = '<!doctype html><html lang="es"><meta charset="utf-8"><title>Presentación ejecutiva</title><style>body{font:16px sans-serif;color:#17202b}section{min-height:85vh;padding:2rem;break-after:page}table{border-collapse:collapse;width:100%}th,td{border:1px solid #aaa;padding:.4rem;text-align:left}@media print{section{min-height:0;page-break-after:always}}</style><body>' + ''.join(slides) + '</body></html>'
    destino.write_text(page, encoding='utf-8')



def obtener_proyeccion(resultados, carpeta, empresa_id=None):
    """Invoca C21 para el libro de la empresa sellado en el resultado, sin modificarlo."""
    from .calculo_local import ruta_libro
    from .libro_dbd import empresa, huella
    from .proyeccion import proyectar_granular
    import re
    if not isinstance(resultados, dict):
        raise ValueError('Se requieren resultados para proyectar.')
    sello = resultados.get('sello') or {}
    if not isinstance(sello, dict):
        raise ValueError('El sello del resultado no es válido.')
    if not empresa_id:
        nombre = sello.get('libro', '')
        if not isinstance(nombre, str) or Path(nombre).name != nombre:
            raise ValueError('El resultado no identifica un libro válido para proyectar.')
        empresa_id = Path(nombre).stem
    if not isinstance(empresa_id, str) or not re.fullmatch(r'[a-z0-9_]{1,60}', empresa_id):
        raise ValueError('La empresa elegida no es válida.')
    libro = ruta_libro(carpeta, empresa_id)
    codigo, _ = empresa(libro)
    if codigo != (resultados.get('empresa') or {}).get('codigo'):
        raise ValueError('La empresa del resultado no coincide con el libro de proyección.')
    if not sello.get('huella_libro') or sello['huella_libro'] != huella(libro):
        raise ValueError('El libro cambió o el resultado no tiene huella: vuelve a calcular antes de proyectar.')
    return proyectar_granular(libro, codigo, meses=6, carpeta_aprendizaje=carpeta)

def exportar(resultados, tipo, carpeta, proyeccion_granular=None):
    if tipo not in TIPOS:
        raise ValueError('El tipo de reporte no existe.')
    if tipo not in SIN_RESULTADOS:
        if not isinstance(resultados, dict):
            raise ValueError('Se requieren resultados para exportar.')
        try:
            errores = validar(resultados)
        except (TypeError, KeyError, ValueError):
            raise ValueError('Los resultados no cumplen el contrato.') from None
        if errores:
            raise ValueError('Los resultados no cumplen el contrato: ' + '; '.join(errores))
    carpeta = Path(carpeta).resolve()
    carpeta.mkdir(parents=True, exist_ok=True, mode=0o700)
    destino = carpeta / (tipo + '-' + uuid4().hex + TIPOS[tipo])
    try:
        if tipo == 'solver':
            _solver_libro(resultados, destino)
        elif tipo in SECCIONES:
            _libro(resultados, tipo, destino, proyeccion_granular=proyeccion_granular)
        elif tipo == 'html':
            _html(resultados, destino)
        elif tipo == 'informe':
            _informe(resultados, destino)
        elif tipo == 'presentacion':
            _presentacion_html(resultados, destino)
        elif tipo == 'sistema':
            _sistema_desde_carpeta(resultados, destino)
        elif tipo == 'entrada':
            _entrada(destino, resultados if isinstance(resultados, dict) else None)
        else:
            from .codigo_fuente import generar_word
            generar_word(destino)
    except Exception:
        destino.unlink(missing_ok=True)
        raise
    return destino


SHIM_OFFLINE = """<script>
(function(){
  const D = window.__DATOS; if (!D) return;
  const resp = (o, st) => Promise.resolve(new Response(JSON.stringify(o), {status: st || 200, headers: {'Content-Type': 'application/json'}}));
  window.fetch = (url, opt) => {
    opt = opt || {}; const u = new URL(url, 'http://local'), q = u.searchParams;
    if (u.pathname === '/api/resultados') {
      const k = (q.get('empresa') || D.libro.id) + '_' + q.get('periodo') + '_' + q.get('sintesis');
      return D.resultados[k] ? resp(D.resultados[k]) : resp({error: 'Ese periodo no está incluido en este archivo.'}, 404);
    }
    if (u.pathname === '/api/libros' && (opt.method || 'GET') === 'GET') return resp({libros: [D.libro]});
    if (u.pathname === '/api/sello') return resp({estado: 'SIN_VERIFICAR_OFFLINE'});
    return resp({error: 'Esta función necesita el programa (ReynaCostos.exe). El HTML sin conexión consulta resultados ya calculados.'}, 503);
  };
  const css = document.createElement('style');
  css.textContent = '#result-calcular,#cargar-libro,#importar,#espacios,#operar,#consultar,#close-form,.page-heading,.scope,.nav-erp,[data-exportar]{display:none!important}';
  document.head.appendChild(css);
  document.addEventListener('DOMContentLoaded', () => {
    const b = document.createElement('p'); b.className = 'data-badge';
    b.textContent = 'Versión HTML sin conexión: ' + D.libro.nombre + ', ' + D.libro.periodos.length + ' meses × 3 síntesis ya calculados (' + D.generado + '). Para calcular o cargar otra empresa usa ReynaCostos.exe.';
    const m = document.getElementById('principal'); if (m) m.prepend(b);
  });
})();
</script>"""


def sistema_html(resultados_por_clave, libro, destino):
    """Entregable 12: el MISMO sistema (pantallas de gestión) en un solo archivo HTML que funciona sin servidor ni internet,
    con los resultados ya calculados incrustados. Calcular y cargar empresas quedan en el EXE."""
    from datetime import date
    pagina = (Path(__file__).parent / 'web' / 'index.html').read_text(encoding='utf-8')
    datos = json.dumps(dict(libro=libro, resultados=resultados_por_clave, generado=date.today().isoformat()), ensure_ascii=False, separators=(',', ':'))
    datos = datos.replace('</', '<\\/')
    pagina = pagina.replace('<script>', '<script>window.__DATOS=' + datos + ';</script>' + SHIM_OFFLINE + '<script>', 1)
    Path(destino).write_text(pagina, encoding='utf-8')
    return Path(destino)


def _sistema_desde_carpeta(resultados, destino):
    """Reúne todos los resultados calculados de la empresa (del usuario y publicados) y arma el HTML interactivo."""
    from .calculo_local import catalogo
    base = destino.parent.parent
    emp = Path((resultados.get('sello') or {}).get('libro', 'frenosa.xlsx')).stem
    lib = next((l for l in catalogo(base) if l['id'] == emp), None) or dict(id=emp, nombre=resultados['empresa']['nombre'], periodos=[])
    todos = {}
    for carpeta in (RAIZ / 'datos' / 'resultados', base / 'resultados'):
        for f in sorted(carpeta.glob(f'{emp}_*.json')) if carpeta.is_dir() else []:
            try:
                r = json.loads(f.read_text(encoding='utf-8'))
                if not validar(r): todos[f.stem] = r
            except (OSError, ValueError):
                continue
    todos[f"{emp}_{resultados['periodo_actual']}_{resultados['sintesis']}"] = resultados
    lib['periodos'] = sorted({k.split('_')[-2] for k in todos})
    sistema_html(todos, lib, destino)
