"""Copia de trabajo para experimentar sin mutar el libro original."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from openpyxl import load_workbook
from .store import META, RECEIPTS, Problem


def huella(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def crear(store, original):
    origen = store.path(original)
    antes = huella(origen)
    info = store.get(original)
    with tempfile.TemporaryDirectory(prefix='lab-', dir=store.root) as tmp:
        archivo = Path(tmp)/'entrada.xlsx'
        wb = load_workbook(origen)
        try:
            for nombre in (META, RECEIPTS):
                if nombre in wb.sheetnames: del wb[nombre]
            wb.save(archivo)
        finally: wb.close()
        if huella(origen) != antes: raise Problem(409, 'El original cambió durante la copia; inténtalo de nuevo.')
        lab = store.create({'name': 'Laboratorio · ' + str(info['name'])[:130], 'workbook_path': str(archivo)})
    try:
        with (store.path(lab['id']).parent/'laboratorio.json').open('x', encoding='utf-8') as f:
            json.dump({'original': original, 'huella_original': antes}, f)
    except Exception:
        shutil.rmtree(store.path(lab['id']).parent)
        raise
    return {'id': lab['id'], 'original': original, 'huella_original': antes}


def comparar_espacios(store, laboratorio, periodo, sintesis):
    from .calculo_local import calcular, libros
    from .comparar_laboratorio import comparar
    if sintesis not in ('REAL', 'CONTABLE'): raise Problem(400, 'Elige REAL o CONTABLE.')
    import re
    if not isinstance(periodo,str) or not re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])', periodo):
        raise Problem(400, 'Elige un periodo válido.')
    ruta = store.path(laboratorio)
    ficha = ruta.parent/'laboratorio.json'
    if ficha.is_symlink() or not ficha.is_file(): raise Problem(404, 'El espacio no es un laboratorio.')
    try:
        data = json.loads(ficha.read_text(encoding='utf-8'))
        original = store.path(data['original'])
        esperado = data['huella_original']
    except (KeyError, ValueError, TypeError): raise Problem(422, 'La referencia al original es inválida.') from None
    if original == ruta: raise Problem(409, 'El laboratorio y el original deben ser distintos.')
    if huella(original) != esperado: raise Problem(409, 'El original cambió desde que se creó el laboratorio.')
    orig_id='esp_'+data['original'][:12]; lab_id='esp_'+laboratorio[:12]
    disponibles=libros(store.root)
    if disponibles.get(orig_id) != original or disponibles.get(lab_id) != ruta:
        raise Problem(409, 'Identificador de espacio ambiguo.')
    antes=calcular(store.root,periodo,sintesis,orig_id)
    despues=calcular(store.root,periodo,sintesis,lab_id)
    if huella(original) != esperado: raise Problem(409, 'El original cambió durante la comparación.')
    return {'original':data['original'], 'laboratorio':laboratorio, 'periodo':periodo, 'sintesis':sintesis,
            'huella_original':esperado, 'filas':[{k:float(v) if k in ('original','copia','diferencia') else v
                                                  for k,v in row.items()} for row in comparar(antes,despues)]}
