"""Verificación automática de la pieza 25 (MONOGRAFIA_1_textos.docx).

Uso:
    python -I verificar_pieza25.py <repo> <SERVITEC_sintetico.xlsx> [MONOGRAFIA_1_textos.docx]

<repo> es la raíz del repositorio con fuente/DBD_Fuente.xlsx y casos/plantilla_dbd.xlsx. No modifica nada.
Comprueba:
  1. que estén las secciones pedidas (marco teórico, arquitectura, límites, fuentes);
  2. que los 6 límites pedidos estén en la tabla de límites;
  3. que TODAS las cifras del documento coincidan con lo que da hoy el repo (calcular() de julio, catálogo TRX,
     líneas de código, módulos), recalculadas aquí;
  4. que cada ruta de archivo citada exista y que cada afirmación sobre el código esté en el código;
  5. que cada fuente citada en el texto aparezca en «Fuentes»;
  6. lista las marcas POR VERIFICAR.
Sale con código 1 si algo falla.
"""
import re
import sys
import tempfile
from pathlib import Path

REPO, LIBRO = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
DOCX = Path(sys.argv[3]).resolve() if len(sys.argv) > 3 else Path(__file__).resolve().parent / "MONOGRAFIA_1_textos.docx"
sys.path.insert(0, str(REPO / "src"))

import docx                                      # python-docx (dependencia del repo)
from openpyxl import load_workbook

fallas, avisos = [], []


def falla(t):
    fallas.append(t)


def texto_docx(p):
    d = docx.Document(p)
    bloques = [(par.style.name, par.text) for par in d.paragraphs]
    tablas = [[[c.text for c in fila.cells] for fila in t.rows] for t in d.tables]
    return bloques, tablas


def n0(x):
    return f"{x:,.0f}" if float(x).is_integer() else f"{x:,.2f}"


bloques, tablas = texto_docx(DOCX)
todo = "\n".join(t for _, t in bloques) + "\n" + "\n".join(" | ".join(f) for t in tablas for f in t)
titulos = [t for s, t in bloques if s.startswith("Heading")]

# 1. secciones ---------------------------------------------------------------------------------------
for h in ["1. Marco teórico", "1.1 Costeo basado en actividades", "1.2 La metodología de W. Oria", "Elementos del costo",
          "Actividades e inductores", "Modelos 1, 2 y 3", "Escalonado y recíproco", "Las etapas P1–P7 y las dos matrices",
          "1.3 El enfoque MCD/DBD de Tino Reyna", "Misión", "Funciones", "Eventos", "2. Arquitectura del sistema",
          "3. Límites del modelo", "Fuentes"]:
    if h not in titulos:
        falla(f"falta la sección «{h}»")

# 2. límites -----------------------------------------------------------------------------------------
tabla_lim = next((t for t in tablas if t and t[0][0] == "Límite"), None)
if tabla_lim is None:
    falla("no está la tabla de límites")
else:
    nombres = [f[0] for f in tabla_lim[1:]]
    for clave in ["lineal por tramo", "días de capacidad", "P05–P95", "Una restricción en Decidir", "Un usuario", "SERVITEC es sintético"]:
        if not any(clave in n for n in nombres):
            falla(f"límite faltante: {clave}")

# 3. cifras recalculadas -------------------------------------------------------------------------------
wb = load_workbook(LIBRO, read_only=True)
trx = [r for r in wb["TRX"].iter_rows(min_row=2, values_only=True) if r[0]]
esperado_txt = [
    f"{len(trx)} transacciones",
    f"{sum(1 for r in trx if r[2] == 'ONLINE')} en línea",
    f"{sum(1 for r in trx if r[2] == 'BATCH')} por lote",
    f"describe {sum(1 for r in wb['TABLAS_LOGICAS'].iter_rows(min_row=2, values_only=True) if r[0])} tablas lógicas",
    f"tiene {len(wb.sheetnames)} hojas",
    f"carga {sum(1 for r in wb['REGLA_REPARTO'].iter_rows(min_row=2, values_only=True) if r[0])} reglas de reparto",
    f"src/reyna_local tiene {len(list((REPO / 'src/reyna_local').glob('*.py')))} módulos",
    f"src/metodos {len(list((REPO / 'src/metodos').glob('*.py')))}",
]
for f in ["reyna_local/libro_dbd.py", "reyna_local/motor_espejo.py", "reyna_local/store.py", "reyna_local/flujo.py",
          "metodos/reparto_etapas.py", "reyna_local/resultados.py", "reyna_local/contrato.py", "reyna_local/calculo_local.py",
          "reyna_local/__main__.py", "reyna_local/exportar.py", "reyna_local/decidir.py"]:
    nl = len((REPO / "src" / f).read_text(encoding="utf-8").splitlines())
    esperado_txt.append(f"{Path(f).name} ({nl})")
for e in esperado_txt:
    if e not in todo:
        falla(f"cifra que no coincide con el repo (no aparece «{e}»)")

import reyna_local.calculo_local as CL           # noqa: E402
c = Path(tempfile.mkdtemp(prefix="p25_"))
ficha, err = CL.registrar(c, LIBRO.read_bytes(), LIBRO.name)
if err:
    falla(f"el libro base no pasa validar(): {err[:2]}")
else:
    r = CL.calcular(c, "2025-07", "REAL", ficha["id"])
    tabla_julio = next((t for t in tablas if t and t[0][0] == "Orden"), None)
    if tabla_julio is None:
        falla("no está la tabla del ejemplo SERVITEC")
    for o in r["objetos"]:
        fila = next((f for f in (tabla_julio or [])[1:] if f[0] == o["codigo"]), None)
        if fila is None:
            falla(f"falta la orden {o['codigo']} en la tabla de julio")
            continue
        claves = ["cantidad", "md", "mod", "cif", "admin", "perdida", "ocio", "costo_total"]
        for k, v in zip(claves, fila[1:9]):
            if v != n0(o[k]):
                falla(f"{o['codigo']} {k}: documento {v}, motor {n0(o[k])}")
        if fila[9] != f"{o['costo_unitario']:,.2f}":
            falla(f"{o['codigo']} unitario: documento {fila[9]}, motor {o['costo_unitario']:,.2f}")
        suma = sum(o[k] for k in ("md", "mod", "cif", "admin", "gasto_venta", "financiero", "perdida", "ocio"))
        if abs(suma - o["costo_total"]) > 0.01:
            falla(f"{o['codigo']}: los elementos ({suma}) no suman el costo total ({o['costo_total']})")
    k = r["kpi"]
    for et, v in (("Ventas del mes", k["ventas"]), ("costo total", k["costo_total"]), ("margen operativo", k["margen_operativo"])):
        if f"{et} {n0(v)}" not in todo:
            falla(f"KPI «{et}» no coincide con el motor ({n0(v)})")

# 4. rutas y afirmaciones sobre el código -------------------------------------------------------------------
for ruta in sorted(set(re.findall(r"(?:src/)?(?:reyna_local|metodos)/[A-Za-z_]+\.(?:py|html)", todo))):
    p = REPO / ("" if ruta.startswith("src/") else "src") / ruta
    if not p.exists():
        falla(f"ruta citada que no existe: {ruta}")
AFIRMA = [
    ("src/metodos/reparto_etapas.py", r"Modelos ABC de Oria \(GE704W sem\. 07\)"),
    ("src/metodos/reparto_etapas.py", r"Modelo 3 escalonado EC→CA→ACE→ACA→ACO→OC"),
    ("src/metodos/reparto_etapas.py", r"el ideal y el mejor"),
    ("src/metodos/reparto_etapas.py", r"N = \(I − P\)⁻¹"),
    ("src/metodos/reparto_etapas.py", r"I8: .*suma cero"),
    ("src/metodos/reparto_etapas.py", r"R-52: .*no tiene regla de reparto vigente"),
    ("src/metodos/reparto_etapas.py", r"I1: la etapa .* no conserva"),
    ("src/reyna_local/plazo_pedido.py", r"días de capacidad"),
    ("src/reyna_local/pedido.py", r"supone independencia"),
    ("src/reyna_local/pedido.py", r"lineal en los parámetros"),
    ("src/reyna_local/exportar.py", r"'solver'"),
    ("src/reyna_local/motor_espejo.py", r"Clave duplicada en"),
    ("src/reyna_local/calculo_local.py", r"RESULTADO_ALTERADO|huella_resultado"),
    ("src/reyna_local/libro_dbd.py", r"Nunca corrige: rechaza y explica"),
]
for f, patron in AFIRMA:
    if not re.search(patron, (REPO / f).read_text(encoding="utf-8")):
        falla(f"afirmación sin respaldo en {f}: /{patron}/")
med = [r for r in wb["MEDIDA"].iter_rows(min_row=2, values_only=True) if r[0] == "2025-07"]
reparto = {(r[2], r[4]): r[5] for r in med}
if (reparto.get(("MANT", "CA_CAL")), reparto.get(("MANT", "CA_TALLER")), reparto.get(("CAL", "CA_MANT")),
        reparto.get(("CAL", "CA_TALLER"))) != (20, 80, 10, 90):
    falla("los porcentajes del ejemplo recíproco (20/80, 10/90) no coinciden con MEDIDA de julio")
reglas = {(r[0], r[1]) for r in wb["REGLA_REPARTO"].iter_rows(min_row=2, values_only=True) if r[0]}
if not {("P4B", "CA_MANT"), ("P4B", "CA_CAL")} <= reglas:
    falla("mantenimiento y calidad no están en la etapa P4B de REGLA_REPARTO")

# 5. fuentes -----------------------------------------------------------------------------------------------
i = next(k for k, (s, t) in enumerate(bloques) if t == "Fuentes")
j = next(k for k, (s, t) in enumerate(bloques) if t.startswith("Notas para el autor"))
fuentes = "\n".join(t for _, t in bloques[i:j])
cuerpo = "\n".join(t for _, t in bloques[:i]) + "\n" + "\n".join(" | ".join(f) for t in tablas for f in t)
for cita, en_fuentes in [("Kaplan y Cooper", "Kaplan, R. S. y Cooper"), ("Kaplan y Anderson", "Kaplan, R. S. y Anderson"),
                         ("Horngren", "Horngren, C. T."), ("Oria, 2026", "Oria, W. (2026)"), ("MCD, §3.4", "Reyna, T. MCD"),
                         ("NIC 2", "NIC 2"), ("NIIF 18", "NIIF 18")]:
    if cita in cuerpo and en_fuentes not in fuentes:
        falla(f"«{cita}» se cita en el texto pero no está en Fuentes")

# 5b. misión aprobada (v2.1, E-041, ajuste del dueño 28/11) ----------------------------------------------------
MISION = ("El área de Costos existe para ENTREGAR el costo de cada objeto de costo —de producción, de ventas y de administración—, "
          "real, planificado y proyectado, y sus diferencias, distinguiendo lo que es costo del producto de lo que es gasto del periodo "
          "conforme a la normativa vigente, para que la gerencia tome decisiones y la empresa cumpla sus obligaciones de información.")
if MISION not in todo:
    falla("la misión aprobada (v2.1, E-041) no está textual en la sección Misión")
if any("POR VERIFICAR" in t and "misión" in t.lower() for _, t in bloques):
    falla("la misión todavía aparece marcada POR VERIFICAR")

# 6. POR VERIFICAR ---------------------------------------------------------------------------------------
pv = [t for _, t in bloques if "POR VERIFICAR" in t]

print(f"Documento: {DOCX.name} · {len(titulos)} títulos · {len(tablas)} tablas · {len(todo):,} caracteres")
print(f"Cifras recalculadas contra el repo: {len(esperado_txt)} textos + tabla de julio + KPI")
print(f"Afirmaciones sobre el código verificadas: {len(AFIRMA)} + 2 sobre el libro")
print(f"Marcas POR VERIFICAR ({len(pv)}):")
for t in pv:
    print("  -", t[:140])
if fallas:
    print("\nFALLAS:")
    for f in fallas:
        print(" -", f)
    sys.exit(1)
print("\nPIEZA 25: OK")
