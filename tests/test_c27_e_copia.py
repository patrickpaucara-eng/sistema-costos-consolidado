"""Verifica solo la separación física existente; no declara laboratorio funcional."""
import hashlib
from pathlib import Path
from openpyxl import load_workbook
from reyna_local.store import Store


def test_copia_de_espacio_no_cambia_el_original(tmp_path):
    source=Path(__file__).resolve().parents[1]/'casos/libros/frenosa.xlsx'
    original=hashlib.sha256(source.read_bytes()).digest()
    espacio=Store(tmp_path).create({'name':'Laboratorio aislado de prueba','workbook_path':str(source)})
    copia=Path(espacio['workbook_path']); assert copia.resolve()!=source.resolve()
    wb=load_workbook(copia); wb['EMPRESA']['B2']='Nombre de prueba'; wb.save(copia); wb.close()
    assert hashlib.sha256(source.read_bytes()).digest()==original
    assert hashlib.sha256(copia.read_bytes()).digest()!=original
