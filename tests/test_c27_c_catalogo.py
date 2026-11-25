import hashlib
from pathlib import Path
from reyna_local.catalogo_dbd import catalogo


def test_catalogo_extrae_encabezados_sin_modificar_fuente():
    p=Path(__file__).resolve().parents[1]/'casos/libros/frenosa.xlsx'
    antes=hashlib.sha256(p.read_bytes()).digest(); rows=catalogo(p)
    empresa=next(x for x in rows if x['tabla']=='EMPRESA')
    assert empresa['presente'] and empresa['obligatoria'] and 'EMP_COD' in empresa['campos']
    assert hashlib.sha256(p.read_bytes()).digest()==antes
