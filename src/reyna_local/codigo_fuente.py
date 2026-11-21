"""Genera un documento Word con las fuentes Python, HTML y otros textos del proyecto."""
from pathlib import Path
from docx import Document
from docx.shared import Pt

ROOT = Path(__file__).resolve().parents[2]


def generar_word(destino, raiz=ROOT):
    raiz = Path(raiz)
    rutas = sorted(p for d in ('src', 'tools') for p in (raiz / d).rglob('*')
                   if p.is_file() and not p.is_symlink() and '__pycache__' not in p.parts
                   and p.suffix.lower() in {'.py', '.html', '.css', '.js', '.json', '.txt', '.md', '.ps1', '.bat', '.spec'})
    doc = Document()
    doc.add_heading('Código fuente del proyecto', 0)
    doc.add_heading('Índice', level=1)
    for ruta in rutas:
        doc.add_paragraph(ruta.relative_to(raiz).as_posix(), style='List Bullet')
    for ruta in rutas:
        doc.add_heading(ruta.relative_to(raiz).as_posix(), level=1)
        contenido = ruta.read_text(encoding='utf-8')
        for linea in contenido.splitlines():
            parrafo = doc.add_paragraph()
            run = parrafo.add_run(linea or ' ')
            run.font.name = 'Consolas'
            run.font.size = Pt(8)
    doc.save(destino)
