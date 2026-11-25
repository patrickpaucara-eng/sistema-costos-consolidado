"""Documentos breves con capturas reales; no presenta pasos no ejecutados como aprobados."""
from pathlib import Path
import json
import tempfile
import threading
from urllib.request import Request, urlopen
from docx import Document
from docx.shared import Cm

ROOT = Path(__file__).resolve().parents[2]
PANTALLAS = [
    ('Definir · Modelo', 'modelo', 'Revise recursos, actividades, inductores y reglas del modelo.'),
    ('Estimar · Futuro', 'proyeccion', 'Consulte la proyección disponible para la empresa y síntesis.'),
    ('Registrar · Movimiento', 'operar', 'Seleccione el espacio y registre la operación con sus datos y usuario.'),
    ('Entregar · Órdenes', 'costos', 'Elija una orden para consultar sus costos y ruta.'),
    ('Entregar · Periodos', 'periodos', 'Indique fechas, agrupación y síntesis y pulse Consultar periodos.'),
    ('Entregar · Reportes', 'reportes', 'Descargue el Excel o el HTML correspondiente.'),
    ('Aprender · Seguimiento', 'aprendido', 'Revise el seguimiento y la información aprendida disponible.'),
]


def capturar(carpeta):
    from playwright.sync_api import sync_playwright
    from reyna_local.__main__ import ReynaServer
    with tempfile.TemporaryDirectory(prefix='c24-') as work:
        server = ReynaServer(Path(work), 0)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        base = f'http://127.0.0.1:{server.server_port}'
        try:
            body = json.dumps({'name': 'Copia para capturas', 'workbook_path': str(ROOT/'casos/libros/frenosa.xlsx')}).encode()
            with urlopen(Request(base+'/api/workspaces', data=body, headers={'Content-Type':'application/json'}), timeout=60) as response:
                wid = json.load(response)['id']
            with sync_playwright() as p:
                try: browser = p.chromium.launch(args=['--no-sandbox'])
                except Exception: browser = p.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
                page = browser.new_page(viewport={'width': 1440, 'height': 900})
                page.goto(base); page.get_by_text('Resultados actualizados.').wait_for(timeout=30000)
                page.locator('nav a[href="#espacios"]').click()
                page.locator(f'button[data-workspace-id="{wid}"]').click()
                for _, section, _ in PANTALLAS:
                    page.locator(f'nav a[href="#{section}"]').click()
                    page.locator('#'+section).wait_for(state='visible')
                    page.screenshot(path=str(carpeta/(section+'.png')))
                browser.close()
        finally:
            server.shutdown(); thread.join(); server.server_close()


def nuevo(titulo):
    d = Document(); d.add_heading(titulo, 0)
    d.add_paragraph('Sistema de Costos Reyna · Monografía MN_01')
    d.add_heading('Índice', 1)
    return d


def generar(salida):
    salida = Path(salida)
    with tempfile.TemporaryDirectory(prefix='c24-capturas-') as tmp:
        carpeta = Path(tmp)
        try:
            capturar(carpeta); evidencia = True
        except Exception as exc:
            evidencia = False
            aviso = f'Capturas pendientes: {type(exc).__name__}: {exc}'
        doc = nuevo('Manual de usuario')
        doc.add_paragraph('Seleccione empresa, período y síntesis en la barra superior.')
        for titulo, section, accion in PANTALLAS:
            doc.add_heading(titulo, 1); doc.add_paragraph(accion)
            imagen = carpeta/(section+'.png')
            if imagen.is_file(): doc.add_picture(str(imagen), width=Cm(14))
            else: doc.add_paragraph('Captura pendiente.')
        if not evidencia: doc.add_paragraph(aviso)
        doc.save(salida/'10_manual_usuario.docx')
        doc = nuevo('Prueba de funcionamiento')
        doc.add_paragraph('Capturas de navegación real en Chromium sobre una copia temporal. La navegación no demuestra el recorrido completo.')
        for titulo, section, accion in PANTALLAS:
            doc.add_heading(titulo, 1)
            doc.add_paragraph('Esperado: pantalla accesible. Obtenido: ' + ('captura obtenida.' if (carpeta/(section+'.png')).is_file() else 'pendiente.'))
            if (carpeta/(section+'.png')).is_file(): doc.add_picture(str(carpeta/(section+'.png')), width=Cm(14))
        doc.add_heading('Recorrido y casos manuales pendientes', 1)
        doc.add_paragraph('Pendiente: registrar T14, calcular, inspeccionar la ruta, periodos, proyección, aprendizaje, cotizar y exportar en un recorrido único.')
        doc.add_paragraph('Pendiente verificar en el recorrido: SERVITEC julio REAL/CONTABLE 22 975/21 374 y 5 165/3 880; MINI 1 938,46/861,54; cotizador 3 720.')
        doc.save(salida/'04_pruebas.docx')
    return [salida/'04_pruebas.docx', salida/'10_manual_usuario.docx']
