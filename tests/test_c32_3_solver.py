import json
from pathlib import Path

from openpyxl import load_workbook
from scipy.optimize import linprog

from reyna_local.exportar import _modelo_solver, _solver_libro, exportar


ROOT = Path(__file__).resolve().parents[1]


def _caso_a_mano():
    return {
        'sintesis': 'REAL',
        'objetos': [
            {'codigo': 'OT-A', 'producto': 'A', 'cantidad': 100},
            {'codigo': 'OT-B', 'producto': 'B', 'cantidad': 100},
        ],
        'decidir': {'er_gerencial': {'productos': [
            {'producto': 'A', 'cantidad': 100, 'margen_contribucion': 3000},
            {'producto': 'B', 'cantidad': 100, 'margen_contribucion': 2000},
        ]}},
        'datos_libro': {
            'ventas': [{'producto': 'A', 'cantidad': 100}, {'producto': 'B', 'cantidad': 100}],
            'medidas': [
                {'inductor': 'MAQ', 'nivel': 'CAP', 'destino': 'MÁQUINA', 'destino_nombre': 'Máquina', 'cantidad': 100},
                {'inductor': 'MO', 'nivel': 'CAP', 'destino': 'PERSONAL', 'destino_nombre': 'Mano de obra', 'cantidad': 80},
                {'inductor': 'MAQ', 'nivel': 'OBJ', 'destino': 'OT-A', 'cantidad': 200},
                {'inductor': 'MAQ', 'nivel': 'OBJ', 'destino': 'OT-B', 'cantidad': 100},
                {'inductor': 'MO', 'nivel': 'OBJ', 'destino': 'OT-A', 'cantidad': 100},
                {'inductor': 'MO', 'nivel': 'OBJ', 'destino': 'OT-B', 'cantidad': 100},
            ],
        },
        'modelo': {'inductores': [{'codigo': 'MAQ', 'unidad': 'h'}, {'codigo': 'MO', 'unidad': 'h'}]},
        'trazas': [
            {'criterio': 'MAQ', 'origen': 'MÁQUINA', 'destino': 'OT-A'},
            {'criterio': 'MO', 'origen': 'PERSONAL', 'destino': 'OT-B'},
        ],
    }


def test_solver_exporta_formulas_nombres_y_caso_optimo(tmp_path):
    caso = _caso_a_mano()
    modelo = _modelo_solver(caso)
    productos = modelo['productos']
    capacidades = modelo['capacidades']
    resultado = linprog(
        c=[-p['mc_unitario'] for p in productos],
        A_ub=[[r['coeficientes'][p['producto']] for p in productos] for r in capacidades],
        b_ub=[r['capacidad'] for r in capacidades],
        bounds=[(p['minimo'], p['maximo']) for p in productos],
        method='highs',
    )
    assert resultado.success
    assert resultado.x.tolist() == [20.0, 60.0]
    assert -resultado.fun == 1800.0

    destino = tmp_path / 'solver.xlsx'
    _solver_libro(caso, destino)
    libro = load_workbook(destino, data_only=False)
    hoja = libro['Modelo']
    assert hoja['B2'].value == '=SUMPRODUCT(B6:B7,C6:C7)'
    assert any(isinstance(c.value, str) and c.value.startswith('=SUMPRODUCT(')
               for row in hoja.iter_rows() for c in row)
    nombres = libro['Modelo'].defined_names
    assert {'solver_opt', 'solver_adj', 'solver_lhs1', 'solver_lhs6', 'solver_rel', 'solver_rel1', 'solver_rel6',
            'solver_rhs', 'solver_rhs1', 'solver_rhs6', 'solver_num', 'solver_typ', 'solver_lin', 'solver_neg', 'solver_eng'} <= set(nombres)
    assert nombres['solver_opt'].attr_text == '=$B$2'
    assert nombres['solver_num'].attr_text == '=6'
    assert nombres['solver_typ'].attr_text == '=1'
    assert nombres['solver_eng'].attr_text == '=2'
    libro.close()


def test_solver_frenosa_explica_ausencia_de_capacidad(tmp_path):
    resultado = json.loads((ROOT / 'datos/resultados/frenosa_2010-07_REAL.json').read_text(encoding='utf-8'))
    ruta = exportar(resultado, 'solver', tmp_path)
    assert ruta.suffix == '.xlsx'
    libro = load_workbook(ruta, data_only=False)
    lectura = '\n'.join(str(cell.value) for row in libro['Lectura'].iter_rows() for cell in row if cell.value)
    assert 'no trae medidas CAP' in lectura
    assert 'solver_opt' in libro['Modelo'].defined_names
    libro.close()


def test_solver_rechaza_sintesis_no_real():
    caso = _caso_a_mano()
    caso['sintesis'] = 'CONTABLE'
    try:
        _modelo_solver(caso)
    except ValueError as exc:
        assert 'resultado REAL' in str(exc)
    else:
        raise AssertionError('Solver debe aceptar únicamente resultados REAL.')
