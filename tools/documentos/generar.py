"""Genera documentos de entrega a partir de fuentes locales y resultados observados."""
import argparse
import ast
from datetime import datetime
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

ROOT = Path(__file__).resolve().parents[2]


def campo(parrafo, instruccion):
    run = parrafo.add_run()
    element = OxmlElement('w:fldSimple')
    element.set(qn('w:instr'), instruccion)
    run._r.addnext(element)


def nuevo(titulo):
    doc = Document()
    doc.add_heading('Sistema de Costos Reyna', 0)
    doc.add_paragraph(titulo, style='Title')
    doc.add_paragraph('Monografía MN_01 · Documento generado para revisión')
    doc.add_page_break()
    doc.add_heading('Índice', 1)
    campo(doc.add_paragraph(), 'TOC \\o "1-3" \\h \\z \\u')
    doc.add_paragraph('Actualice el índice en Word para ver las páginas.')
    footer = doc.sections[0].footer.paragraphs[0]
    footer.add_run('Página ')
    campo(footer, 'PAGE')
    doc.add_page_break()
    doc.add_heading(titulo, 1)
    return doc


def incorporar_md(doc, ruta):
    doc.add_heading(ruta.relative_to(ROOT).as_posix(), 2)
    lines = ruta.read_text(encoding='utf-8', errors='replace').splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('|') and i + 1 < len(lines) and re.fullmatch(r"[|: \-]+", lines[i+1]):
            header = [c.strip() for c in line.strip('|').split('|')]
            tabla = doc.add_table(rows=1, cols=len(header)); tabla.style = 'Table Grid'
            for cell, value in zip(tabla.rows[0].cells, header): cell.text = value
            i += 2
            while i < len(lines) and lines[i].startswith('|'):
                cells = [c.strip() for c in lines[i].strip('|').split('|')]
                for cell, value in zip(tabla.add_row().cells, cells): cell.text = value
                i += 1
            continue
        if line.startswith('#'):
            t = line.lstrip('#').strip()
            if t: doc.add_heading(t[:200], min(4, len(line) - len(line.lstrip('#')) + 2))
        elif line.strip():
            doc.add_paragraph(line)
        i += 1


def imagen(doc, ruta):
    if ruta.is_file():
        doc.add_picture(str(ruta), width=Cm(15))
        doc.add_paragraph(ruta.relative_to(ROOT).as_posix(), style='Caption')
    else:
        doc.add_paragraph('Captura pendiente: ' + ruta.relative_to(ROOT).as_posix())


def chats(doc):
    files = sorted((ROOT / 'docs/entrega/chats').glob('*.md'), key=lambda p:p.name)
    if not files:
        doc.add_paragraph('Pendiente: colocar las conversaciones exportadas como archivos Markdown en docs/entrega/chats/.')
    for p in files:
        incorporar_md(doc, p)


def etapas(doc):
    for rel in ('docs/planificacion/PLAN_MONOGRAFIA_Y_SISTEMA.md', 'docs/planificacion/ESTADO.md', 'docs/planificacion/REGLAS_APRENDIDAS.md'):
        incorporar_md(doc, ROOT / rel)
    for p in sorted((ROOT / 'docs/entrega/evidencias').rglob('*.md')):
        incorporar_md(doc, p)


def proposito(nombre):
    parte = nombre.split('[', 1)[0]
    testname = parte.split('.')[-1]
    modulo = next((x for x in parte.split('.') if x.startswith('test_')), parte.split('.')[0])
    ruta = ROOT / 'tests' / (modulo + '.py')
    if ruta.exists():
        try:
            tree = ast.parse(ruta.read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == testname:
                    return ast.get_docstring(node) or ast.get_docstring(tree) or 'Propósito no documentado.'
        except (OSError, SyntaxError):
            pass
    return 'Propósito no documentado.'


def pruebas(doc, junit):
    doc.add_paragraph('Resultados obtenidos de la ejecución indicada; un resultado omitido no es una aprobación.')
    tree = ET.parse(junit)
    for case in tree.iter('testcase'):
        nombre = case.get('classname', '') + '.' + case.get('name', '')
        estado = 'APROBADA'
        for tag, label in [('failure','FALLIDA'), ('error','ERROR'), ('skipped','OMITIDA')]:
            if case.find(tag) is not None: estado = label; break
        doc.add_heading(nombre, 2)
        doc.add_paragraph('Propósito: ' + proposito(nombre))
        doc.add_paragraph('Resultado: ' + estado)
    for folder in ('OT-C01', 'OT-C04'):
        files = sorted((ROOT / 'docs/entrega/evidencias' / folder).glob('*.png'))
        if not files: doc.add_paragraph('Capturas pendientes: ' + folder)
        for file in files: imagen(doc, file)


def manual(doc):
    pasos = [('Inicio','ot-c01-inicio.png','Revise la empresa y seleccione período y síntesis.'),
             ('Cargar y validar','ot-c01-cargar.png','Elija un libro compatible y siga las validaciones visibles.'),
             ('Importar','ot-c01-cargar.png','Importe una copia del libro al espacio local.'),
             ('Cerrar','ot-c01-cerrar.png','Seleccione el período y confirme el cierre cuando corresponda.'),
             ('Calcular','inicio.png','Elija período y síntesis y pulse Calcular cuando OT-C04 esté integrada.'),
             ('Dashboard','ot-c01-dashboard.png','Revise indicadores y detalles disponibles.'),
             ('Reportes','reportes.png','Descargue el reporte deseado cuando OT-C04 esté integrada.')]
    for title, name, text in pasos:
        doc.add_heading(title, 2); doc.add_paragraph(text)
        imagen(doc, ROOT / 'docs/entrega/evidencias' / ('OT-C04' if name in ('inicio.png','reportes.png') else 'OT-C01') / name)


def descriptivo(doc):
    for title in ('Arquitectura', 'DBD y MCD', 'Métodos', 'Síntesis REAL, CONTABLE y ESTIMADO', 'Analítica', 'Seguridad'):
        doc.add_heading(title, 2); doc.add_paragraph('[CLAUDE] Completar y validar el contenido técnico de esta sección.')


def generar(destino, junit=None):
    destino = Path(destino); destino.mkdir(parents=True, exist_ok=True)
    funciones = [('01_cadena_chats.docx', 'Cadena de conversaciones', chats),
                 ('02_etapas.docx', 'Etapas del desarrollo', etapas),
                 ('04_pruebas.docx', 'Prueba de funcionamiento', lambda d: pruebas(d, junit)),
                 ('09_manual_descriptivo.docx', 'Manual descriptivo', descriptivo),
                 ('10_manual_usuario.docx', 'Manual de usuario', manual)]
    for filename, titulo, funcion in funciones:
        doc = nuevo(titulo); funcion(doc); doc.save(destino / filename)
    return [destino / x[0] for x in funciones]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--salida', type=Path, required=True)
    parser.add_argument('--junit', type=Path, help='Usar XML existente en vez de ejecutar pytest')
    args = parser.parse_args()
    status = 0
    if args.junit:
        rutas = generar(args.salida, args.junit)
    else:
        with tempfile.TemporaryDirectory() as temp:
            junit = Path(temp) / 'resultados.xml'
            cmd = [sys.executable, '-m', 'pytest', 'tests', '-q', '--junitxml=' + str(junit), '--ignore=tests/test_documentos_generados.py']
            run = subprocess.run(cmd, cwd=ROOT, check=False)
            if not junit.exists(): raise SystemExit('No se obtuvo el reporte de pytest.')
            rutas = generar(args.salida, junit)
            if run.returncode:
                print('Las pruebas registran fallos; revise el documento.', file=sys.stderr)
                status = run.returncode
    for ruta in rutas: print(ruta)
    return status


if __name__ == '__main__': raise SystemExit(main())
