"""Los cinco Word abren y conservan títulos, resultados y límites declarados."""
import importlib.util
from pathlib import Path
from docx import Document

ROOT = Path(__file__).resolve().parents[1]


def test_cinco_documentos_con_junit_controlado(tmp_path):
    spec = importlib.util.spec_from_file_location('documentos', ROOT / 'tools/documentos/generar.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    junit = tmp_path / 'pruebas.xml'
    junit.write_text('<testsuites><testsuite><testcase classname="tests.test_foo" name="test_muestra"/><testcase classname="tests.test_foo" name="test_otro"><failure>falló</failure></testcase></testsuite></testsuites>')
    rutas = module.generar(tmp_path / 'salida', junit)
    assert len(rutas) == 5
    documentos = [Document(path) for path in rutas]
    for document in documentos:
        assert document.sections and any('Índice' in p.text for p in document.paragraphs)
        assert any(p.style.name.startswith('Heading') for p in document.paragraphs)
    pruebas = '\n'.join(p.text for p in documentos[2].paragraphs)
    assert 'test_muestra' in pruebas and 'APROBADA' in pruebas and 'FALLIDA' in pruebas
    descriptivo = '\n'.join(p.text for p in documentos[3].paragraphs)
    assert descriptivo.count('[CLAUDE]') == 6
    manual = '\n'.join(p.text for p in documentos[4].paragraphs)
    assert all(x in manual for x in ('Cargar', 'Importar', 'Cerrar', 'Calcular', 'Dashboard', 'Reportes'))
    assert len(documentos[1].tables) > 0
