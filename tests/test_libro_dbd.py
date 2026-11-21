"""Entrada única: libro con formato DBD. Se valida, se rechaza con explicación, se carga por la interfaz y se sella."""
import json
from pathlib import Path
import shutil
import threading
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from openpyxl import load_workbook

from reyna_local import libro_dbd as B
from reyna_local.__main__ import ReynaServer

RAIZ = Path(__file__).resolve().parents[1]
FRENOSA = RAIZ / 'casos/libros/frenosa.xlsx'


def test_libro_de_frenosa_cumple_el_formato():
    assert B.validar(FRENOSA) == []
    assert B.empresa(FRENOSA) == ('FRE', 'Frenosa')


def test_libro_defectuoso_se_rechaza_y_se_explica(tmp_path):
    malo = tmp_path / 'malo.xlsx'; shutil.copy(FRENOSA, malo)
    wb = load_workbook(malo)
    del wb['VENTA']                                            # falta una hoja obligatoria
    wb['LINEA'].cell(2, 3).value = 'RECURSO_INEXISTENTE'       # referencia rota
    wb.save(malo)
    errores = B.validar(malo)
    assert any('Falta la hoja VENTA' in e for e in errores)
    shutil.copy(FRENOSA, malo); wb = load_workbook(malo); wb['LINEA'].cell(2, 3).value = 'RECURSO_INEXISTENTE'; wb.save(malo)
    assert any('LIN_REC = «RECURSO_INEXISTENTE» no existe en RECURSO' in e for e in B.validar(malo))
    assert B.validar(tmp_path / 'no_existe.xlsx') == ['El archivo no es un libro Excel (.xlsx) legible.']


def test_plantilla_vacia_trae_instrucciones(tmp_path):
    p = B.plantilla_vacia(tmp_path / 'p.xlsx'); wb = load_workbook(p, read_only=True)
    assert wb.sheetnames[0] == 'LEEME' and 'VENTA' in wb.sheetnames
    assert any('Hoja EMPRESA está vacía' in e for e in B.validar(p))


def _post(url, data, ctype):
    return urlopen(Request(url, data=data, headers={'Content-Type': ctype}, method='POST'), timeout=120)


def test_cargar_otra_empresa_calcular_y_sellar(tmp_path):
    """Otra empresa entra solo con datos (sin tocar código): se carga, se calcula y su sello detecta cambios del libro."""
    otra = tmp_path / 'otra.xlsx'; shutil.copy(FRENOSA, otra)
    wb = load_workbook(otra); wb['EMPRESA'].cell(2, 2).value = 'Metalmecánica Demo'; wb.save(otra)
    datos = tmp_path / 'datos'
    server = ReynaServer(datos, 0); th = threading.Thread(target=server.serve_forever, daemon=True); th.start()
    base = f'http://127.0.0.1:{server.server_port}'
    try:
        try:
            _post(base + '/api/libros', b'no es excel', 'application/octet-stream')
            raise AssertionError('aceptó un archivo inválido')
        except HTTPError as e:
            assert e.code == 422 and json.load(e)['errores']
        ficha = json.load(_post(base + '/api/libros', otra.read_bytes(), 'application/octet-stream'))
        assert ficha['id'] == 'metalmecanica_demo'
        ids = {l['id'] for l in json.load(urlopen(base + '/api/libros'))['libros']}
        assert {'frenosa', 'metalmecanica_demo'} <= ids
        r = json.load(_post(base + '/api/calcular?empresa=metalmecanica_demo&sintesis=REAL&periodo=2010-07', b'{}', 'application/json'))
        assert r['empresa']['nombre'] == 'Metalmecánica Demo' and r['kpi']['ventas'] == 888730
        assert r['sello']['huella_libro'] == B.huella(datos / 'libros/metalmecanica_demo.xlsx')
        sello = lambda: json.load(_post(base + '/api/sello', json.dumps({'resultados': r}).encode(), 'application/json'))['estado']
        assert sello() == 'VIGENTE'
        wb = load_workbook(datos / 'libros/metalmecanica_demo.xlsx'); wb['MEDIDA'].cell(2, 6).value = 999; wb.save(datos / 'libros/metalmecanica_demo.xlsx')
        assert sello() == 'LIBRO_MODIFICADO'
    finally:
        server.shutdown(); th.join(); server.server_close()
