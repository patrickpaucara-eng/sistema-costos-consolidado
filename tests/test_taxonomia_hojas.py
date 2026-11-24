"""La taxonomía cubre una vez cada hoja y conserva la clasificación acordada."""
import csv
from pathlib import Path
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]


def test_taxonomia_cubre_plantilla_y_dominios():
    book = load_workbook(ROOT / 'casos/plantilla_dbd.xlsx', read_only=True)
    try:
        names = set(book.sheetnames)
    finally:
        book.close()
    with (ROOT / 'docs/diseno/TAXONOMIA_HOJAS.csv').open(encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == len(names)
    assert {r['hoja'] for r in rows} == names
    assert all(r['clase'] in {'CATALOGO', 'MOVIMIENTO', 'CONFIGURACION', 'RESULTADO'} for r in rows)
    assert all(r['quien_la_llena'] and r['frecuencia'] and r['motivo'] for r in rows)
    classes = {r['hoja']: r['clase'] for r in rows}
    for name in ('EMPRESA', 'RECURSO', 'CENTRO', 'ACTIVIDAD', 'CRITERIO', 'OBJETO', 'CLIENTE', 'TIPO_RECURSO', 'COMPONENTE'):
        assert classes[name] == 'CATALOGO'
    for name in ('EVENTO', 'LINEA', 'MEDIDA', 'VENTA'):
        assert classes[name] == 'MOVIMIENTO'
    for name in ('REGLA_REPARTO', 'TRX', 'TRX_CAMPO', 'PERFIL_TRX', 'PARAMETRO'):
        assert classes[name] == 'CONFIGURACION'
    for name in ('KARDEX', 'EXISTENCIA', 'RESULTADO_METODO'):
        assert classes[name] == 'RESULTADO'
