"""Genera INFORME_PRUEBAS_MN1.docx y PRESENTACION_MN1.pptx a partir de cifras_mn1.json.

Uso:  python docs/entrega/_generador/generar_mn1.py [cifras.json] [carpeta_salida]
Requiere: python-docx y python-pptx (pip install python-docx python-pptx).

Las cifras NO se escriben a mano en los documentos: salen del JSON, que se llena con la corrida final
(tools/verificar.py, tools/e2e_recorrido.py, tests/auditoria_mn1, tests/datos/oraculo_servitec, libros_hostiles).
Cuando una orden corrija un defecto de la auditoría, cambiar su estado de CONFIRMADO a CORREGIDO en el JSON y volver a correr.
"""
import json
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor as PRGB
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt as PPt

AQUI = Path(__file__).resolve().parent
CIF = json.loads(Path(sys.argv[1] if len(sys.argv) > 1 else AQUI / "cifras_mn1.json").read_text(encoding="utf-8"))
SALIDA = Path(sys.argv[2]) if len(sys.argv) > 2 else AQUI.parent
G, A = CIF["compuerta"], CIF["auditoria"]

# ---------------------------------------------------------------- contenido compartido
AUDITORIA = [  # id, severidad, defecto, esperado, obtenido hoy, orden que lo corrige
    ("S1", "Crítica", "Elemento de costo mal escrito o no reconocido (TRE_ELE «IND », «Ind», ADM)",
     "Total 28,140 o rechazo", "Total 19,140 (IND con espacio) o 26,140 (ADM); sin aviso", "C38-1"),
    ("S2", "Crítica", "Línea con monto (LIN_MTO) pero sin costo unitario (LIN_CU_DOC)",
     "Base exacta o rechazo", "Total 26,640 (REB 21,737.50 · MPR 4,902.50); sin aviso", "C38-2"),
    ("S3", "Crítica", "Compra sin monto entra al kardex a valor 0",
     "REB 22,975 con material a 42", "REB 18,675 · MPR 4,591.67; ningún control lo marca", "C38-3"),
    ("S4", "Crítica", "Exceso de merma mayor que el consumo (160 de 150)",
     "Rechazo", "El material negativo cae en otra orden: MPR baja de 5,165 a 4,745", "C38-4"),
    ("S5", "Media", "Exceso de merma escrito como texto («3 kg»)",
     "Pérdida 126 o rechazo", "Pérdida 0 y MD normal 6,300; la pérdida se capitaliza", "C38-6"),
    ("S6", "Crítica", "El control de conservación no detecta lo perdido a la entrada",
     "DIFERENCIA con S1–S3", "OK en todos los casos (26,140 = 26,140; 26,640 = 26,640)", "C38-5"),
    ("S7", "Alta", "El sello del cierre no cubre estado ni historial de aprobaciones",
     "Sello inválido al editar el estado", "verificar() da INTEGRO con estado y aprobación falsos", "C38-7"),
    ("S8", "Baja", "Dos emisiones simultáneas: la segunda pisa a la primera",
     "0 pisadas", f"{A['s8a']} pisadas llamando a emitir; {A['s8b']} con el cálculo real", "C38-8"),
    ("S9", "Baja", "Cantidad de llamadas y trazas al crecer las órdenes",
     "Tiempo razonable", A["s9"] + "; crece de forma lineal", "C38-9"),
]
HOSTILES = [  # archivo, defecto, esperado, obtenido, detecta
    ("00_control_sin_defecto", "ninguno", "Acepta; REB 22,975 / MPR 5,165", "Acepta; REB 22,975 / MPR 5,165", "Control"),
    ("01_hoja_obligatoria_borrada", "Falta la hoja CRITERIO", "Rechazo con el nombre de la hoja", "«Falta la hoja CRITERIO. Inductores (unidad de medida).»", "Sí"),
    ("02_celdas_vacias_MEDIDA", "MED_CAN vacío, filas 184–186", "Rechazo con hoja y fila", "«Hoja MEDIDA, fila 184: la cantidad debe ser un número ≥ 0.» (y 185, 186)", "Sí"),
    ("03_texto_en_monto", "VTA_ING = «30,000» (texto)", "Rechazo con hoja y fila", "«Hoja VENTA, fila 14: el ingreso (VTA_ING) debe ser un número.»", "Sí"),
    ("04_fechas_al_reves", "PER_INI posterior a PER_FIN", "Rechazo", "Acepta y calcula igual; nadie lo nota", "No: hallazgo"),
    ("05_codigo_duplicado", "OT-SRV-REB-2025-07 dos veces", "Rechazo con hoja y fila", "Acepta; REB queda con cantidad 12 y unitario 1,914.58 (correcto 2,297.50)", "No: hallazgo grave"),
    ("06_criterio_suma_cero", "DES_OT = 0 en las dos órdenes", "Aviso al cargar", "Carga sin aviso; calcular() lo frena con la regla I8", "Parcial"),
    ("07_archivo_truncado", "Archivo cortado al 50 %", "Rechazo", "«El archivo no es un libro Excel (.xlsx) legible.»", "Sí"),
    ("08_columnas_otro_orden", "MEDIDA y OBJETO con columnas invertidas", "Acepta y da lo mismo que el control", "Acepta; REB 22,975 / MPR 5,165", "Sí (correcto)"),
]
INK, TEAL, AMBER, LIGHT, MUTED = "12263A", "1F7A8C", "F2A541", "EEF3F6", "5B6B79"


def estado_aud(sid, orden):
    return "Corregido" if A["estado"][sid] == "CORREGIDO" else f"Defecto reproducido · pendiente {orden}"


# ---------------------------------------------------------------- informe .docx
def _sombra(celda, hexcolor):
    tcPr = celda._tc.get_or_add_tcPr()
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), hexcolor)
    tcPr.append(sh)


def _texto(celda, txt, negrita=False, size=9, color=None):
    celda.text = ""
    p = celda.paragraphs[0]; p.paragraph_format.space_after = Pt(0)
    r = p.add_run(txt); r.bold = negrita; r.font.size = Pt(size)
    if color:
        r.font.color.rgb = RGBColor.from_string(color)


def tabla(doc, cabecera, filas, anchos_cm, col_estado=None):
    t = doc.add_table(rows=1, cols=len(cabecera)); t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for i, h in enumerate(cabecera):
        _texto(t.rows[0].cells[i], h, True, 9, "FFFFFF"); _sombra(t.rows[0].cells[i], INK)
    for fila in filas:
        cs = t.add_row().cells
        for i, v in enumerate(fila):
            _texto(cs[i], str(v), size=9)
            if col_estado is not None and i == col_estado:
                bien = str(v).startswith(("Cumple", "Corregido", "Sí", "Control"))
                _sombra(cs[i], "E3F1E7" if bien else "FCEBD0")
    for i, w in enumerate(anchos_cm):
        t.columns[i].width = Cm(w)
    for n, fila in enumerate(t.rows):
        for i, w in enumerate(anchos_cm):
            fila.cells[i].width = Cm(w)
        trPr = fila._tr.get_or_add_trPr()
        trPr.append(OxmlElement("w:cantSplit"))            # una fila no se parte entre páginas
        if n == 0:
            trPr.append(OxmlElement("w:tblHeader"))        # la cabecera se repite en cada página
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def informe():
    d = Document()
    s = d.sections[0]
    s.page_width, s.page_height = Cm(21.0), Cm(29.7)
    s.left_margin = s.right_margin = Cm(2.0); s.top_margin = s.bottom_margin = Cm(2.0)
    st = d.styles["Normal"]; st.font.name = "Calibri"; st.font.size = Pt(11)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
    for nom, sz in (("Heading 1", 16), ("Heading 2", 13), ("Title", 24)):
        h = d.styles[nom]; h.font.name = "Cambria"; h.font.size = Pt(sz); h.font.bold = True
        h.font.color.rgb = RGBColor.from_string(INK)
        h.element.rPr.rFonts.set(qn("w:eastAsia"), "Cambria"); h.element.rPr.rFonts.set(qn("w:ascii"), "Cambria"); h.element.rPr.rFonts.set(qn("w:hAnsi"), "Cambria")
        h.paragraph_format.space_before = Pt(14 if nom != "Title" else 0); h.paragraph_format.space_after = Pt(6); h.paragraph_format.keep_with_next = True

    d.add_paragraph("Informe de pruebas · Monografía 1", style="Title")
    p = d.add_paragraph(); r = p.add_run("Sistema de costos ABC (método de W. Oria, datos MCD/DBD de T. Reyna)"); r.font.size = Pt(13); r.font.color.rgb = RGBColor.from_string(TEAL)
    tabla(d, ["Dato", "Valor"], [
        ("Fecha de la corrida", CIF["fecha"]),
        ("Rama y commit", f"{CIF['rama']} · {CIF['commit']}"),
        ("Compuerta (tools/verificar.py)", f"COMPUERTA: {G['veredicto']} · {G['pasadas']} pruebas, {G['subpruebas']} subpruebas, {G['duracion']}; contrato de resultados {G['contrato']}"),
        ("Alcance de la cifra", G["nota"]),
    ], [4.6, 12.4])

    d.add_heading("1. Objetivo", 1)
    d.add_paragraph("Demostrar con evidencia reproducible que el sistema calcula bien el costo de cada orden, que rechaza los datos defectuosos con un mensaje claro y que sus límites están declarados. "
                    "Este informe distingue lo que se comprobó de lo que aún tiene defectos abiertos; no presenta como corregido lo que no lo está.")

    d.add_heading("2. Resultado en una mirada", 1)
    tabla(d, ["Comprobación", "Resultado", "Estado"], [
        ("Suite automática", f"{G['pasadas']} pruebas pasan; compuerta {G['veredicto']}", "Cumple"),
        ("Recorrido de punta a punta", f"{CIF['e2e']['ok']} de {CIF['e2e']['total']} pasos OK (Frenosa y SERVITEC)", "Cumple"),
        ("Oráculo independiente (Excel con fórmulas)", f"Diferencia {CIF['oraculo']['dif_REB']} en REB y {CIF['oraculo']['dif_MPR']} en MPR; {CIF['oraculo']['cifras']} cifras y {CIF['oraculo']['flechas']} flechas por etapa sin diferencias", "Cumple"),
        ("Modelo 3 de Oria (recíproco y escalonado a mano)", f"{CIF['modelo3']['pasadas']} de {CIF['modelo3']['total']} pruebas", "Cumple"),
        ("Controles sin defecto de la auditoría", f"{A['controles_ok']} de {A['controles_total']} pasan: los escenarios de prueba son válidos", "Cumple"),
        ("Defectos de la auditoría independiente", f"{sum(1 for v in A['estado'].values() if v == 'CONFIRMADO')} de 9 sospechas reproducen su defecto hoy", "Abierto: orden C38"),
        ("Libros defectuosos", "4 rechazados con mensaje claro; 3 defectos pasan sin aviso o tarde (04, 05, 06)", "Abierto: sin orden asignada"),
    ], [5.4, 8.6, 3.0], col_estado=2)

    d.add_heading("3. Tipos de prueba", 1)
    tabla(d, ["Tipo", "Qué demuestra", "Dónde"], [
        ("Unitarias y de integración", "Cada módulo y cada pantalla se comportan como se especificó; las pruebas existentes no se editan", "tests/ (compuerta tools/verificar.py)"),
        ("Punta a punta", "Cálculo, sello, exportación, proyección, aprendizaje y cotización por la API local", "tools/e2e_recorrido.py"),
        ("Entorno hostil", "Libros con un defecto cada uno: el sistema debe rechazarlos con hoja, fila y valor, sin trazas", "tests/datos/libros_hostiles/"),
        ("Conservación", "La suma de los recursos es igual a la suma del costo de las órdenes, por naturaleza", "resultados.py (controles del panel)"),
        ("Oráculo SERVITEC", "Un libro Excel con 777 fórmulas visibles rehace el cálculo y se compara con el motor", "tests/datos/oraculo_servitec/"),
        ("Auditoría independiente", "Nueve sospechas convertidas en pruebas contra el motor real, cada una con su control sin defecto", "tests/auditoria_mn1/"),
    ], [3.6, 9.2, 4.2])

    d.add_heading("4. Casos, esperado y obtenido", 1)
    d.add_heading("4.1 Cálculo y controles", 2)
    tabla(d, ["Caso", "Esperado", "Obtenido", "Estado"], [
        ("Suite completa", "Todas las pruebas pasan", f"{G['pasadas']} pasadas, {G['subpruebas']} subpruebas, {G['duracion']}", "Cumple"),
        ("Contrato de resultados", "El resultado de ejemplo cumple el esquema", G["contrato"].capitalize(), "Cumple"),
        ("Recorrido de punta a punta", "Todos los pasos responden como se espera", f"{CIF['e2e']['ok']}/{CIF['e2e']['total']} OK", "Cumple"),
        ("SERVITEC julio 2025, REAL", "REB 22,975 · MPR 5,165 · total 28,140", "REB 22,975 · MPR 5,165 (paso del recorrido y oráculo)", "Cumple"),
        ("Oráculo vs. motor, REB", "Diferencia 0.00", f"22,975.00 vs 22,975.00 → {CIF['oraculo']['dif_REB']}", "Cumple"),
        ("Oráculo vs. motor, MPR", "Diferencia 0.00", f"5,165.00 vs 5,165.00 → {CIF['oraculo']['dif_MPR']}", "Cumple"),
        ("Oráculo, recálculo", "Sin errores de fórmula; solo fórmulas fuera de DATOS", f"{CIF['oraculo']['formulas']} fórmulas, {CIF['oraculo']['errores']} errores; {CIF['oraculo']['filas_datos']} filas de DATOS iguales al libro", "Cumple"),
        ("Modelo 3 de Oria", "Recíproco y escalonado iguales a las cuentas a mano", f"{CIF['modelo3']['pasadas']}/{CIF['modelo3']['total']} pruebas", "Cumple"),
    ], [3.6, 5.0, 6.0, 2.4], col_estado=3)

    d.add_heading("4.2 Libros defectuosos", 2)
    d.add_paragraph(f"Los nueve libros se pasan por validar() y calcular() con tests/datos/libros_hostiles/verificar_pieza24.py: {CIF['hostiles']['verificacion']}. "
                    "Tres casos (04, 05 y 06) están escritos con el comportamiento de hoy; cuando se corrijan, esa verificación fallará a propósito y habrá que actualizar lo esperado.")
    tabla(d, ["Libro", "Defecto", "Esperado", "Obtenido", "Detecta"], [(a, b, c, e, f) for a, b, c, e, f in HOSTILES], [3.4, 3.0, 3.0, 5.6, 2.0], col_estado=4)

    d.add_heading("4.3 Auditoría independiente (S1–S9)", 2)
    d.add_paragraph(f"Cada sospecha es una prueba que afirma el comportamiento correcto: si falla, el defecto está confirmado. Las {A['controles_total']} pruebas de control (mismo escenario sin defecto) pasan, de modo que ningún resultado se debe a un escenario mal armado. "
                    "Base: SERVITEC julio 2025, REAL; sin cambios REB 22,975 · MPR 5,165 · total 28,140.")
    tabla(d, ["Id", "Gravedad", "Defecto", "Esperado", "Obtenido hoy", "Estado"],
          [(i, sv, df, es, ob, estado_aud(i, o)) for i, sv, df, es, ob, o in AUDITORIA], [0.9, 1.9, 4.0, 2.8, 4.4, 3.0], col_estado=5)

    d.add_heading("5. Hallazgos abiertos", 1)
    d.add_paragraph("Estado a la fecha de la corrida. Nada de lo siguiente se presenta como corregido.")
    for txt in (
        "OT-C38 (S1–S9) corrige los nueve defectos de la auditoría: rechazos con hoja, fila y valor, un control de conservación independiente y un sello del cierre que incluye estado e historial. No está unida.",
        "Los libros 04 (fechas al revés), 05 (código de orden duplicado) y 06 (criterio en cero al cargar) no figuran en las líneas de OT-C38. El 05 es el más grave: el costo unitario de REB baja de 2,297.50 a 1,914.58 sin aviso. Falta asignarles orden.",
        "El manual descriptivo dice que el motor rechaza claves repetidas; eso es cierto para lo que crean las transacciones, no para un libro importado con una orden repetida (libro 05). Debe ajustarse el texto o corregirse el defecto.",
        "La prueba del ejecutable de Windows sin internet la hace el dueño con el guion de docs/entrega/GUION_PRUEBA_DUENO.md; todavía no hay resultado.",
    ):
        d.add_paragraph(txt, style="List Bullet")

    d.add_heading("6. Cómo reproducir", 1)
    d.add_paragraph("Desde la raíz del repositorio, en la rama desarrollo/mono. La compuerta tarda unos 15 minutos; córrela sin otra carga en la máquina, porque las pruebas con Chromium son sensibles a la competencia por CPU.")
    for cmd in (
        "python tools/verificar.py",
        "PYTHONPATH=src python tools/e2e_recorrido.py",
        "PYTHONPATH=src python -m pytest tests/test_modelo3_oria.py -q",
        "python -I tests/auditoria_mn1/correr_auditoria.py . tests/auditoria_mn1/datos/SERVITEC_sintetico.xlsx",
        "python -I tests/datos/oraculo_servitec/verificar_pieza30.py . tests/auditoria_mn1/datos/SERVITEC_sintetico.xlsx   (necesita LibreOffice)",
        "python -I tests/datos/libros_hostiles/verificar_pieza24.py src",
        "python docs/entrega/_generador/generar_mn1.py   (regenera este informe y la presentación con cifras_mn1.json)",
    ):
        p = d.add_paragraph(); r = p.add_run(cmd); r.font.name = "Consolas"; r.font.size = Pt(9)
        p.paragraph_format.left_indent = Cm(0.5); p.paragraph_format.space_after = Pt(2)

    d.add_heading("7. Alcance y límites de las pruebas", 1)
    for txt in (
        "SERVITEC es un caso sintético creado para probar el sistema: sus cifras prueban el método, no describen una empresa. El caso real es Frenosa.",
        "SERVITEC tiene un solo centro productivo, así que no distingue el recíproco del escalonado; eso lo prueba test_modelo3_oria.py con cuentas a mano.",
        "El oráculo reproduce los números del motor con otro procedimiento (fórmulas de Excel); no valida que la metodología de Oria esté bien interpretada: esa revisión es del curso.",
        "La compuerta excluye a propósito tests/auditoria_mn1 y tests/datos; se corren con sus propios scripts, como arriba.",
    ):
        d.add_paragraph(txt, style="List Bullet")
    for z in d.settings.element.findall(qn("w:zoom")):   # la plantilla de python-docx deja w:zoom sin percent
        z.set(qn("w:percent"), "100")
    ruta = SALIDA / "INFORME_PRUEBAS_MN1.docx"; d.save(ruta); return ruta


# ---------------------------------------------------------------- presentación .pptx
def rgb(h):
    return PRGB.from_string(h)


def caja(sl, x, y, w, h, fill=LIGHT, forma=MSO_SHAPE.ROUNDED_RECTANGLE, nombre=None):
    s = sl.shapes.add_shape(forma, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid(); s.fill.fore_color.rgb = rgb(fill); s.line.fill.background(); s.shadow.inherit = False
    if forma == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = 0.08
    if nombre:
        s.name = nombre
    return s


def txt(sl, x, y, w, h, partes, size=16, color=INK, bold=False, align=PP_ALIGN.LEFT, font="Calibri", anchor=MSO_ANCHOR.TOP, espacio=4):
    tb = sl.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); tf = tb.text_frame
    tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    partes = [partes] if isinstance(partes, str) else partes
    for i, par in enumerate(partes):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align; p.space_after = PPt(espacio)
        r = p.add_run(); r.text = par; r.font.size = PPt(size); r.font.bold = bold; r.font.name = font; r.font.color.rgb = rgb(color)
    return tb


def insignia(sl, x, y, n, fill=TEAL, color="FFFFFF", d=0.55):
    s = caja(sl, x, y, d, d, fill, MSO_SHAPE.OVAL)
    tf = s.text_frame; tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    r = p.add_run(); r.text = str(n); r.font.size = PPt(18); r.font.bold = True; r.font.name = "Calibri"; r.font.color.rgb = rgb(color)


def lamina(prs, titulo, oscura=False, num=None, nota=""):
    sl = prs.slides.add_slide(prs.slide_layouts[6])
    sl.background.fill.solid(); sl.background.fill.fore_color.rgb = rgb(INK if oscura else "FFFFFF")
    if titulo:
        txt(sl, 0.6, 0.45, 12.1, 0.9, titulo, 34, "FFFFFF" if oscura else INK, True, font="Cambria")
    pie = f"Monografía 1 · Sistema de costos ABC · {CIF['fecha']}"
    txt(sl, 0.6, 7.0, 8, 0.3, pie, 11, "9FB3C4" if oscura else MUTED)
    if num:
        txt(sl, 12.0, 7.0, 0.73, 0.3, str(num), 11, "9FB3C4" if oscura else MUTED, align=PP_ALIGN.RIGHT)
    if nota:
        sl.notes_slide.notes_text_frame.text = nota
    return sl


def presentacion():
    prs = Presentation(); prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)

    # 1 problema
    sl = lamina(prs, None, True, 1, "Abrir con la pregunta: cuánto cuesta una orden y cómo se sabe que la cifra es confiable.")
    txt(sl, 0.8, 0.9, 11.5, 0.4, "MONOGRAFÍA 1 · CURSO GE704W · MÉTODO ABC DE W. ORIA · DATOS MCD/DBD DE T. REYNA", 13, "9FB3C4")
    txt(sl, 0.8, 1.5, 11.8, 1.8, "Cuánto cuesta realmente cada orden", 48, "FFFFFF", True, font="Cambria")
    txt(sl, 0.8, 3.0, 11.5, 0.6, "El problema: costos indirectos que nadie puede explicar ni comprobar.", 20, "CADCE8")
    for i, (t, b) in enumerate([("Una sola base distorsiona", "Repartir por horas de mano de obra hace que una orden con poco taller pague como una que lo usa mucho."),
                                ("Pérdida y ocio se esconden", "Merma en exceso y capacidad no usada terminan dentro del costo del producto sin que se vean."),
                                ("Nadie puede revisar la cifra", "Sin traza ni sello, un número cambia en silencio y la gerencia decide con un dato dudoso.")]):
        x = 0.8 + i * 4.0
        caja(sl, x, 4.1, 3.7, 2.4, "1C3650"); insignia(sl, x + 0.25, 4.3, i + 1, AMBER, INK)
        txt(sl, x + 0.25, 5.0, 3.2, 0.4, t, 18, "FFFFFF", True)
        txt(sl, x + 0.25, 5.45, 3.2, 1.0, b, 14, "CADCE8")

    # 2 MCD/DBD
    sl = lamina(prs, "MCD/DBD: misión, funciones y eventos", False, 2, "La misión v2.1 (E-041): entregar el costo de cada objeto, real, planificado y proyectado, y sus diferencias. Evento = transacción consumada (Reyna, MCD §3.4).")
    caja(sl, 0.6, 1.6, 5.6, 4.9, LIGHT)
    txt(sl, 0.9, 1.85, 5.0, 0.4, "MISIÓN", 13, TEAL, True)
    txt(sl, 0.9, 2.3, 5.0, 2.6, "Entregar el costo de cada objeto de costo, real, planificado y proyectado, y sus diferencias, separando costo del producto de gasto del periodo.", 20, INK, False, font="Cambria")
    txt(sl, 0.9, 4.75, 5.0, 1.6, ["Evento = transacción consumada.", "No se edita ni se borra: un error se corrige con otro evento."], 15, MUTED)
    for i, f in enumerate(["Definir", "Estimar", "Registrar", "Entregar", "Aprender"]):
        y = 1.6 + i * 0.7
        caja(sl, 6.6, y, 3.2, 0.58, TEAL); txt(sl, 6.6, y + 0.1, 3.2, 0.4, f, 18, "FFFFFF", True, align=PP_ALIGN.CENTER)
    for i, (n, l) in enumerate([("47", "transacciones: 26 en línea, 21 por lote"), ("123", "hojas del libro; 103 tablas lógicas")]):
        y = 1.6 + i * 2.5
        caja(sl, 10.1, y, 2.6, 2.3, LIGHT); txt(sl, 10.1, y + 0.2, 2.6, 0.9, n, 48, AMBER if False else TEAL, True, align=PP_ALIGN.CENTER, font="Cambria")
        txt(sl, 10.3, y + 1.2, 2.2, 1.0, l, 14, MUTED, align=PP_ALIGN.CENTER)

    # 3 arquitectura
    sl = lamina(prs, "Arquitectura: una entrada, un motor", False, 3, "Python es el único motor; el libro DBD es la única entrada; las pantallas solo leen el resultado sellado.")
    pasos = [("Libro DBD", "Excel con el modelo y los hechos"), ("Validar y ordenar", "Mensajes claros; kardex a promedio"),
             ("Reparto P1–P7", "Escalonado y recíproco; naturalezas"), ("Resultado único", "Contrato validado y sello SHA-256"),
             ("Pantallas y reportes", "HTML local; Excel, Word, HTML")]
    for i, (t, b) in enumerate(pasos):
        x = 0.6 + i * 2.5
        caja(sl, x, 1.9, 2.25, 2.4, TEAL if i == 2 else LIGHT)
        c = "FFFFFF" if i == 2 else INK
        txt(sl, x + 0.15, 2.15, 1.95, 0.9, t, 18, c, True); txt(sl, x + 0.15, 3.1, 1.95, 1.1, b, 14, "FFFFFF" if i == 2 else MUTED)
        if i < 4:
            f = sl.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x + 2.27), Inches(2.95), Inches(0.2), Inches(0.3)); f.fill.solid(); f.fill.fore_color.rgb = rgb(AMBER); f.line.fill.background()
    for i, (t, b) in enumerate([("Python es el único motor", "Excel guarda datos y reglas; no calcula."), ("Solo se lee el contrato", "Las pantallas nunca recalculan costos."), ("Funciona sin internet", "Servidor local 127.0.0.1 y datos en el equipo.")]):
        x = 0.6 + i * 4.15
        caja(sl, x, 4.8, 3.9, 1.7, LIGHT); txt(sl, x + 0.25, 5.0, 3.4, 0.4, t, 18, INK, True); txt(sl, x + 0.25, 5.5, 3.4, 0.9, b, 15, MUTED)

    # 4 recorrido
    sl = lamina(prs, "Recorrido de un pedido", False, 4, "Del pedido a la ficha de la orden: el usuario no teclea claves; el sistema asigna el código de la OT.")
    pasos = [("Cotizar", "Costo, rango P05–P95, precio y plazo"), ("Aceptar y abrir la OT", "El sistema asigna el código"), ("Registrar hechos", "Compra, consumo, gasto, producción, venta"),
             ("Calcular y sellar", "Valida, reparte y sella el resultado"), ("Ficha de la orden", "Costo por elemento y ruta del costo")]
    for i, (t, b) in enumerate(pasos):
        x = 0.6 + i * 2.5
        insignia(sl, x, 1.8, i + 1, TEAL if i != 3 else AMBER, "FFFFFF" if i != 3 else INK, 0.7)
        caja(sl, x, 2.7, 2.25, 2.6, LIGHT); txt(sl, x + 0.15, 2.9, 1.95, 0.9, t, 18, INK, True); txt(sl, x + 0.15, 3.85, 1.95, 1.4, b, 14, MUTED)
    caja(sl, 0.6, 5.7, 12.1, 0.9, TEAL)
    txt(sl, 0.9, 5.7, 11.5, 0.9, "Ejemplo SERVITEC, julio 2025: OT de REB = 22,975 · OT de MPR = 5,165 · total del periodo 28,140", 20, "FFFFFF", True, anchor=MSO_ANCHOR.MIDDLE)

    # 5 reparto
    sl = lamina(prs, "Reparto P1–P7 y las dos matrices de Oria", False, 5, "Siempre el mismo mecanismo; cambian las dos matrices que se llenan en el libro. Recíproco: N = (I − P)⁻¹.")
    etapas = [("P1", "Material → orden", "Kardex a promedio; merma aparte"), ("P2/P3", "Personal y servicios → actividad u orden", "Minutos u otro inductor"),
              ("P4A", "Indirectos → centros", "m², kWh, porcentajes"), ("P4B", "Centros de apoyo ↔ entre sí → productivos", "Recíproco exacto"),
              ("P4D/E", "Centros → actividades", "Escalonado entre niveles"), ("P4C", "Actividades → órdenes", "Inductor; capacidad separa el ocio"),
              ("P5–P7", "Administración, ventas, financieros → órdenes", "Inductor del gasto")]
    for i, (c, o, b) in enumerate(etapas):
        y = 1.55 + i * 0.7
        caja(sl, 0.6, y, 0.95, 0.58, TEAL); txt(sl, 0.6, y + 0.12, 0.95, 0.4, c, 15, "FFFFFF", True, align=PP_ALIGN.CENTER)
        txt(sl, 1.7, y + 0.02, 4.1, 0.6, o, 14, INK, True, espacio=0); txt(sl, 1.7, y + 0.3, 4.1, 0.3, b, 12, MUTED, espacio=0)
    caja(sl, 6.3, 1.55, 3.1, 3.3, LIGHT); txt(sl, 6.5, 1.75, 2.7, 0.7, "Matriz de configuración", 17, INK, True)
    txt(sl, 6.5, 2.5, 2.7, 2.2, ["Hoja REGLA_REPARTO.", "En qué etapa y con qué inductor se reparte cada origen."], 14, MUTED)
    caja(sl, 9.6, 1.55, 3.1, 3.3, LIGHT); txt(sl, 9.8, 1.75, 2.7, 0.7, "Matriz de cálculo", 17, INK, True)
    txt(sl, 9.8, 2.5, 2.7, 2.2, ["Hoja MEDIDA.", "Cuánto inductor consumió cada destino en el mes."], 14, MUTED)
    caja(sl, 6.3, 5.1, 6.4, 1.5, TEAL)
    txt(sl, 6.55, 5.2, 5.9, 1.3, ["monto del destino = monto del origen × medida del destino ÷ suma de medidas", "Cada etapa conserva el total: si no cuadra, el cálculo se detiene."], 15, "FFFFFF", True, anchor=MSO_ANCHOR.MIDDLE)

    # 6 decidir
    sl = lamina(prs, "Decidir con el costo real", False, 6, "Capacidad y ocio salen del resultado REAL. Una sola restricción; con varias, se exporta a Solver.")
    cards = [("Producir o tercerizar", "Compara el costo propio con el de comprar afuera."), ("Eliminar una línea", "Margen de contribución y relevancia al 10 %."),
             ("Asignar un recurso escaso", "Una restricción: ordena por margen por unidad del recurso. Con varias, Solver."), ("Procesar o vender", "Ingreso adicional contra costo incremental, por unidad.")]
    for i, (t, b) in enumerate(cards):
        x = 0.6 + (i % 2) * 6.15; y = 1.6 + (i // 2) * 2.35
        caja(sl, x, y, 5.95, 2.15, LIGHT); insignia(sl, x + 0.3, y + 0.3, i + 1)
        txt(sl, x + 1.1, y + 0.3, 4.6, 0.5, t, 19, INK, True); txt(sl, x + 1.1, y + 0.95, 4.6, 1.1, b, 15, MUTED)
    caja(sl, 0.6, 6.35, 12.1, 0.55, TEAL)
    txt(sl, 0.9, 6.35, 11.5, 0.55, "Si falta la capacidad o una venta, la pantalla lo pide: no inventa el dato.", 15, "FFFFFF", True, anchor=MSO_ANCHOR.MIDDLE)

    # 7 aprendizaje
    sl = lamina(prs, "Aprender sin tocar el costo real", False, 7, "Recalibra solo con mejora comprobada fuera de muestra y cambio de 20 % o menos; si no, pide aprobación.")
    for i, (t, b) in enumerate([("Proyectar", "Cada recurso con su propia historia, por el mismo motor ABC"), ("Comparar con lo real", "Mes pasado proyectado contra lo ocurrido, por producto"),
                                ("Recalibrar", "Solo si mejora fuera de muestra y cambia 20 % o menos"), ("Pedir aprobación", "Si no cumple, decide una persona")]):
        x = 0.6 + i * 3.1
        caja(sl, x, 1.8, 2.85, 2.9, TEAL if i == 2 else LIGHT); c = "FFFFFF" if i == 2 else INK
        insignia(sl, x + 0.25, 2.0, i + 1, AMBER if i == 2 else TEAL, INK if i == 2 else "FFFFFF", 0.5)
        txt(sl, x + 0.25, 2.7, 2.4, 0.5, t, 18, c, True); txt(sl, x + 0.25, 3.3, 2.4, 1.3, b, 14, "FFFFFF" if i == 2 else MUTED)
    caja(sl, 0.6, 5.1, 12.1, 1.5, INK)
    txt(sl, 0.9, 5.1, 11.5, 1.5, ["El aprendizaje nunca modifica el costo real.", "La precisión de la proyección se mide contra un modelo ingenuo y se declara, también cuando no le gana."], 18, "FFFFFF", True, anchor=MSO_ANCHOR.MIDDLE)

    # 8 pruebas
    sl = lamina(prs, "Pruebas y oráculo independiente", False, 8, "Cifras de la corrida del " + CIF["fecha"] + f", commit {CIF['commit']}. El oráculo es un libro Excel con fórmulas visibles.")
    stats = [(str(G["pasadas"]), "pruebas pasan\n(compuerta " + G["veredicto"] + ")"), (f"{CIF['e2e']['ok']}/{CIF['e2e']['total']}", "pasos de punta a punta"),
             (CIF["oraculo"]["dif_REB"], "diferencia contra el oráculo\nREB 22,975 · MPR 5,165"), (f"{CIF['modelo3']['pasadas']}/{CIF['modelo3']['total']}", "pruebas del modelo 3\nde Oria, a mano")]
    for i, (n, l) in enumerate(stats):
        x = 0.6 + i * 3.1
        caja(sl, x, 1.7, 2.9, 3.0, LIGHT); txt(sl, x, 1.95, 2.9, 1.2, n, 54, TEAL, True, align=PP_ALIGN.CENTER, font="Cambria")
        txt(sl, x + 0.2, 3.35, 2.5, 1.2, l.split("\n"), 14, MUTED, align=PP_ALIGN.CENTER)
    caja(sl, 0.6, 5.0, 12.1, 1.6, LIGHT)
    txt(sl, 0.9, 5.15, 11.5, 1.4, [f"Oráculo: {CIF['oraculo']['formulas']} fórmulas, {CIF['oraculo']['errores']} errores, {CIF['oraculo']['cifras']} cifras y {CIF['oraculo']['flechas']} flechas por etapa sin diferencias.",
                                   "Nueve libros defectuosos: 4 se rechazan con mensaje claro; 3 defectos pasan hoy y están declarados."], 15, INK)

    # 9 auditoría
    sl = lamina(prs, "Auditoría independiente", False, 9, "Nueve sospechas probadas contra el motor real. Corrección: OT-C38, aún sin unir a esta fecha.")
    cd = CategoryChartData(); cd.categories = ["Crítica", "Alta", "Media", "Baja"]; cd.add_series("Hallazgos", (5, 1, 1, 2))
    gf = sl.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.6), Inches(1.6), Inches(5.8), Inches(4.9), cd); ch = gf.chart
    ch.has_legend = False; ch.has_title = True; ch.chart_title.text_frame.text = "Hallazgos por gravedad"
    ch.chart_title.text_frame.paragraphs[0].runs[0].font.size = PPt(16); ch.chart_title.text_frame.paragraphs[0].runs[0].font.name = "Calibri"
    pl = ch.plots[0]; pl.gap_width = 60; pl.has_data_labels = True; pl.data_labels.font.size = PPt(16); pl.data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
    pl.series[0].format.fill.solid(); pl.series[0].format.fill.fore_color.rgb = rgb(TEAL)
    ch.category_axis.tick_labels.font.size = PPt(14); ch.value_axis.tick_labels.font.size = PPt(12); ch.value_axis.has_major_gridlines = False; ch.value_axis.maximum_scale = 6
    n_conf = sum(1 for v in A["estado"].values() if v == "CONFIRMADO")
    for i, (t, b) in enumerate([(f"{n_conf} de 9", "sospechas reproducen su defecto hoy"), (f"{A['controles_ok']} de {A['controles_total']}", "controles sin defecto pasan: los escenarios son válidos"),
                                ("Costo incorrecto sin aviso", "S1–S4: un elemento descartado, una línea a 0, una compra a 0 y una merma mal imputada")]):
        y = 1.6 + i * 1.75
        caja(sl, 6.8, y, 5.9, 1.6, LIGHT); txt(sl, 7.05, y + 0.15, 5.4, 0.6, t, 22 if i < 2 else 19, TEAL, True, font="Cambria"); txt(sl, 7.05, y + 0.85, 5.4, 0.7, b, 14, MUTED)

    # 10 límites
    sl = lamina(prs, "Límites declarados", False, 10, "Están en el manual y en las pantallas; el jurado debe oírlos de nosotros primero.")
    lim = [("Costo variable lineal por tramo", "Lo que no esté en un tramo declarado no aparece."), ("Plazo en días de capacidad", "No es fecha: falta calendario laboral."),
           ("Rango P05–P95 independiente", "Si los recursos suben juntos, el rango real es mayor."), ("Una restricción en Decidir", "Con varias, Solver y su rango de sensibilidad."),
           ("Un usuario a la vez", "Si dos registran juntos, la clave única rechaza al segundo."), ("SERVITEC es sintético", "Prueba el método; no describe una empresa.")]
    for i, (t, b) in enumerate(lim):
        x = 0.6 + (i % 3) * 4.15; y = 1.6 + (i // 3) * 2.6
        caja(sl, x, y, 3.9, 2.4, LIGHT); insignia(sl, x + 0.25, y + 0.25, i + 1, AMBER, INK, 0.5)
        txt(sl, x + 0.25, y + 0.95, 3.4, 0.6, t, 17, INK, True); txt(sl, x + 0.25, y + 1.55, 3.4, 0.8, b, 14, MUTED)

    # 11 demo
    sl = lamina(prs, "Demo en 4 pasos", False, 11, "Demo sin internet con el ejecutable. Guion completo en GUION_PRUEBA_DUENO.md.")
    for i, (t, b) in enumerate([("Cargar la empresa", "Libro de SERVITEC; el sistema lo valida y acepta"), ("Calcular 2025-07", "Síntesis REAL; el sello pasa a VIGENTE"),
                                ("Leer las órdenes", "REB 22,975 · MPR 5,165"), ("Probar un libro roto", "Texto en un monto: rechazo con hoja y fila")]):
        x = 0.6 + i * 3.1
        insignia(sl, x, 1.7, i + 1, TEAL, "FFFFFF", 0.7); caja(sl, x, 2.6, 2.85, 2.5, LIGHT)
        txt(sl, x + 0.2, 2.8, 2.45, 0.9, t, 18, INK, True); txt(sl, x + 0.2, 3.75, 2.45, 1.3, b, 14, MUTED)
    caja(sl, 0.6, 5.5, 12.1, 1.1, TEAL)
    txt(sl, 0.9, 5.5, 11.5, 1.1, "Todo corre en esta computadora, sin conexión a internet.", 22, "FFFFFF", True, anchor=MSO_ANCHOR.MIDDLE)

    # 12 cierre
    sl = lamina(prs, "Cierre", True, 12, "Cerrar con lo entregado, lo que falta dicho con franqueza y lo que viene (MN 02).")
    cols = [("Entregamos", ["Reparto ABC por etapas, escalonado y recíproco", "Resultado sellado y sin recálculo en pantalla", f"{G['pasadas']} pruebas y un oráculo con diferencia {CIF['oraculo']['dif_REB']}"]),
            ("Falta", ["OT-C38: corregir los 9 defectos de la auditoría", "Libros con fecha invertida, código duplicado y criterio en cero", "Prueba del ejecutable sin internet"]),
            ("Sigue", ["MN 02: programación de recursos comprometidos", "Presupuestos como síntesis del plan", "Contrato de costos para planeamiento"])]
    for i, (t, items) in enumerate(cols):
        x = 0.6 + i * 4.15
        caja(sl, x, 1.7, 3.9, 3.9, "1C3650"); txt(sl, x + 0.3, 1.95, 3.3, 0.5, t, 22, AMBER, True, font="Cambria")
        txt(sl, x + 0.3, 2.7, 3.3, 2.8, items, 15, "FFFFFF", espacio=10)
    txt(sl, 0.6, 5.95, 12.1, 0.8, "Un costo que se puede explicar, comprobar y sellar.", 26, "FFFFFF", True, font="Cambria")
    ruta = SALIDA / "PRESENTACION_MN1.pptx"; prs.save(ruta); return ruta


if __name__ == "__main__":
    print(informe()); print(presentacion())
