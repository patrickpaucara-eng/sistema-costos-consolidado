"""Verificación automática de la pieza 30 (oraculo_SERVITEC.xlsx).

Uso:
    python -I verificar_pieza30.py <repo> <SERVITEC_sintetico.xlsx> [oraculo_SERVITEC.xlsx]

Necesita LibreOffice (soffice) para recalcular las fórmulas, y el repo con fuente/DBD_Fuente.xlsx y casos/plantilla_dbd.xlsx.
No modifica nada. Comprueba:
  1. que el libro recalcule sin errores (#REF!, #DIV/0!, …);
  2. que las hojas de cálculo (P1…RESULTADO) sean FÓRMULAS: ningún número tecleado fuera de DATOS y de la columna del motor;
  3. que cada fila de DATOS siga siendo igual a la fila del libro SERVITEC de donde salió (hoja y fila anotadas);
  4. que el oráculo dé REB 22,975 y MPR 5,165;
  5. que el oráculo coincida con calcular() del motor real, corrido AHORA: por orden y elemento, por cada flecha de cada etapa;
  6. que los valores del motor pegados en COMPARACION_MOTOR sigan siendo los del motor de hoy.
Imprime la diferencia por orden y sale con código 1 si algo no cuadra.
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO, LIBRO = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
ORACULO = Path(sys.argv[3]).resolve() if len(sys.argv) > 3 else Path(__file__).resolve().parent / "oraculo_SERVITEC.xlsx"
AQUI = Path(__file__).resolve().parent
sys.argv = [sys.argv[0], str(REPO / "src"), str(LIBRO), str(Path(tempfile.gettempdir()) / "motor_ver30.json")]
sys.path.insert(0, str(AQUI))
from openpyxl import load_workbook                     # noqa: E402
import motor_julio                                     # noqa: E402  (corre calcular() del repo)

TOL = 0.005
fallas = []


def recalcular(xlsx):
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        raise SystemExit("No se encontró LibreOffice (soffice): instálelo o abra el libro en Excel y guárdelo para recalcular.")
    out = Path(tempfile.mkdtemp(prefix="or30_"))
    perfil = Path(tempfile.mkdtemp(prefix="lo_perfil_"))
    subprocess.run([soffice, f"-env:UserInstallation=file://{perfil}", "--headless", "--calc", "--convert-to", "xlsx",
                    "--outdir", str(out), str(xlsx)], check=True, capture_output=True, timeout=180)
    return out / xlsx.name


# 1 · recálculo ---------------------------------------------------------------------------------------------
calc = recalcular(ORACULO)
wv = load_workbook(calc, data_only=True)
wf = load_workbook(ORACULO)
errores = [(ws.title, c.coordinate, c.value) for ws in wv.worksheets for row in ws.iter_rows() for c in row
           if isinstance(c.value, str) and c.value.startswith("#") and c.value[1:4].isupper()]
if errores:
    fallas.append(f"errores de fórmula: {errores[:5]}")
n_formulas = sum(1 for ws in wf.worksheets for row in ws.iter_rows() for c in row
                 if isinstance(c.value, str) and c.value.startswith("="))

# 2 · solo fórmulas en las hojas de cálculo ---------------------------------------------------------------------
CALCULO = ["P1_MATERIAL", "P2_PERSONAL", "P4A_INDIRECTOS", "P4B_RECIPROCO", "P4D_TALLER", "P4C_ACTIVIDADES", "P5_P7_GASTOS", "RESULTADO"]
for n in CALCULO:
    for row in wf[n].iter_rows(min_row=4):
        for c in row:
            if isinstance(c.value, (int, float)) and not isinstance(c.value, bool):
                fila = wf[n].cell(c.row, 1).value or ""
                if n == "RESULTADO" and "cifra del dueño" in str(fila):
                    continue                              # 22,975 / 5,165: lo esperado, no un cálculo
                fallas.append(f"{n}!{c.coordinate} tiene un número tecleado ({c.value}); debería ser fórmula")

# 3 · DATOS = libro ---------------------------------------------------------------------------------------------
lb = load_workbook(LIBRO, read_only=True, data_only=True)
cache = {}


def fila_libro(hoja, i):
    if hoja not in cache:
        filas = list(lb[hoja].iter_rows(values_only=True))
        cache[hoja] = (filas[0], filas)
    cab, filas = cache[hoja]
    return dict(zip(cab, filas[i - 1]))


ds = wf["DATOS"]
revisadas = 0
for row in ds.iter_rows(min_row=4):
    origen = row[8].value if len(row) > 8 else None
    if not isinstance(origen, str):
        continue
    refs = dict(re.findall(r"([A-Z_]+) f(\d+)", origen))
    v = [c.value for c in row]
    if "MEDIDA" in refs:
        m = fila_libro("MEDIDA", int(refs["MEDIDA"]))
        esperado = [m["MED_CRIT"], m["MED_NIVEL"], m["MED_DEST"], m["MED_CAN"]]
        obtenido = v[0:4]
    elif "REGLA_REPARTO" in refs:
        m = fila_libro("REGLA_REPARTO", int(refs["REGLA_REPARTO"]))
        esperado, obtenido = [m["RRE_ETAPA"], m["RRE_ORIGEN"], m["RRE_CRIT"]], v[0:3]
    elif "LINEA" in refs and "EVENTO" in refs:
        lin = fila_libro("LINEA", int(refs["LINEA"]))
        eve = fila_libro("EVENTO", int(refs["EVENTO"]))
        if eve["EVE_TRX"] == "T17":
            esperado, obtenido = [lin["LIN_REC"], lin["LIN_MTO"]], [v[0], v[4]]
        else:
            esperado = [eve["EVE_NUM"], eve["EVE_FEC"], eve["EVE_TRX"], lin["LIN_CAN"], lin["LIN_EXC"] or 0]
            obtenido = [v[0], v[1], v[4], v[5], v[7]]
    elif "OBJETO" in refs:
        m = fila_libro("OBJETO", int(refs["OBJETO"]))
        esperado, obtenido = [m["OBJ_NUM"], m["OBJ_PRO"], m["OBJ_CAN"]], v[0:3]
    else:
        continue
    revisadas += 1
    if esperado != obtenido:
        fallas.append(f"DATOS fila {row[0].row} ({origen}) no coincide con el libro: {obtenido} ≠ {esperado}")

# 4, 5, 6 · cifras y motor ------------------------------------------------------------------------------------------
m = motor_julio.correr(LIBRO)
cmpv, cmpf = wv["COMPARACION_MOTOR"], wf["COMPARACION_MOTOR"]
por_orden, por_flujo = {}, {}
for r in range(1, cmpv.max_row + 1):
    a = cmpv.cell(r, 1).value
    if not isinstance(a, str):
        continue
    if " · " in a and a.startswith("OT-"):
        ot, el = a.split(" · ")
        por_orden[(ot, el)] = (cmpv.cell(r, 2).value, cmpf.cell(r, 3).value)
    elif re.match(r"P\d[A-E]? · ", a):
        etapa, resto = a.split(" · ")
        o, d = resto.split(" → ")
        por_flujo[f"{etapa}|{o}|{d}"] = (cmpv.cell(r, 2).value, cmpf.cell(r, 3).value)

tabla = []
for (ot, el), (orac, pegado) in sorted(por_orden.items()):
    hoy = m["objetos"][ot][el]
    if abs(orac - hoy) > TOL:
        fallas.append(f"{ot} · {el}: oráculo {orac:,.2f} ≠ motor {hoy:,.2f}")
    if abs(pegado - hoy) > TOL:
        fallas.append(f"{ot} · {el}: el valor del motor pegado ({pegado:,.2f}) ya no es el de hoy ({hoy:,.2f}): regenerar el oráculo")
    if el == "costo_total":
        tabla.append((ot, orac, hoy, orac - hoy))
faltan = set(m["flujos"]) - set(por_flujo)
if faltan:
    fallas.append(f"flechas del motor que el oráculo no tiene: {sorted(faltan)}")
for k, (orac, pegado) in por_flujo.items():
    hoy = m["flujos"].get(k)
    if hoy is None:
        fallas.append(f"flecha del oráculo que el motor ya no publica: {k}")
    elif abs(orac - hoy) > TOL:
        fallas.append(f"etapa {k}: oráculo {orac:,.2f} ≠ motor {hoy:,.2f}")
esperado_dueno = {"REB": 22975.0, "MPR": 5165.0}
for (ot, el), (orac, _) in por_orden.items():
    pro = m["objetos"][ot]["producto"]
    if el == "costo_total" and abs(orac - esperado_dueno[pro]) > TOL:
        fallas.append(f"{pro}: el oráculo da {orac:,.2f}, el dueño espera {esperado_dueno[pro]:,.2f}")

print(f"Oráculo: {ORACULO.name} · {n_formulas} fórmulas · recalculado con LibreOffice · {len(errores)} errores")
print(f"DATOS: {revisadas} filas comparadas contra {LIBRO.name}")
print(f"Motor: calcular(2025-07, REAL) corrido ahora · huella del libro {m['huella_libro'][:16]}…")
print(f"Comparado: {len(por_orden)} cifras por orden y elemento · {len(por_flujo)} flechas por etapa\n")
print(f"{'Orden':22} {'Oráculo':>12} {'Motor':>12} {'Diferencia':>11}")
for ot, a, b, d in tabla:
    print(f"{ot:22} {a:>12,.2f} {b:>12,.2f} {d:>11,.2f}")
if fallas:
    print("\nFALLAS:")
    for f in fallas:
        print(" -", f)
    sys.exit(1)
print("\nPIEZA 30: OK — el oráculo da REB 22,975 y MPR 5,165 y coincide con el motor por orden, elemento y etapa")
