"""Pieza 30 · oraculo_SERVITEC.xlsx — recálculo A MANO (fórmulas de Excel) del costo de julio de SERVITEC por etapas P1–P7.

Uso: python -I hacer_oraculo.py <SERVITEC_sintetico.xlsx> <motor.json> <salida.xlsx>
  motor.json = salida de motor_julio.py (calcular() del motor real): se pega como VALORES en COMPARACION_MOTOR.
Los datos de entrada se copian del libro como valores (azul) con su hoja y fila de origen; todo lo demás son fórmulas.
"""
import json
import sys
from pathlib import Path

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as L

LIBRO, MOTOR, SALIDA = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
PER = "2025-07"

AZUL = Font(name="Arial", size=10, color="0000FF")
NEG = Font(name="Arial", size=10)
BOLD = Font(name="Arial", size=10, bold=True)
TIT = Font(name="Arial", size=13, bold=True)
GRIS = Font(name="Arial", size=9, italic=True, color="5B6474")
BLANCO = Font(name="Arial", size=10, bold=True, color="FFFFFF")
F_HEAD = PatternFill("solid", fgColor="DCEAFB")
F_SEC = PatternFill("solid", fgColor="5B6474")
F_RES = PatternFill("solid", fgColor="FFE9B8")
F_OK = PatternFill("solid", fgColor="DFF3E9")
FINO = Side(style="thin", color="C9CED6")
BOX = Border(left=FINO, right=FINO, top=FINO, bottom=FINO)
S = '#,##0.00;(#,##0.00);"-"'
S4 = '#,##0.0000;(#,##0.0000);"-"'
Q = '#,##0.00'
PCT = '0.00%'

wb = Workbook()
wb.remove(wb.active)
N = {}          # nombre -> referencia absoluta 'HOJA'!$C$5


def ref(ws, fila, col):
    return f"'{ws.title}'!${L(col)}${fila}" if ws is not None else None


def put(ws, fila, col, valor, fmt=None, font=None, fill=None, box=True, nombre=None, wrap=False):
    c = ws.cell(fila, col, valor)
    es_f = isinstance(valor, str) and valor.startswith("=")
    c.font = font or (NEG if es_f or not isinstance(valor, (int, float)) else AZUL)
    if fmt:
        c.number_format = fmt
    if fill:
        c.fill = fill
    if box:
        c.border = BOX
    if wrap:
        c.alignment = Alignment(wrap_text=True, vertical="top")
    if nombre:
        N[nombre] = f"'{ws.title}'!${L(col)}${fila}"
    return c


def head(ws, fila, col, textos, ancho=None):
    for j, t in enumerate(textos):
        c = ws.cell(fila, col + j, t)
        c.font = BOLD
        c.fill = F_HEAD
        c.border = BOX
        c.alignment = Alignment(wrap_text=True, horizontal="center", vertical="center")
    ws.row_dimensions[fila].height = 30


def sec(ws, fila, texto, ancho=10):
    ws.cell(fila, 1, texto).font = BLANCO
    for j in range(1, ancho + 1):
        ws.cell(fila, j).fill = F_SEC


def nota(ws, fila, texto, ancho=10):
    c = ws.cell(fila, 1, texto)
    c.font = GRIS
    c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=fila, start_column=1, end_row=fila, end_column=ancho)
    ws.row_dimensions[fila].height = 15 * max(1, len(texto) // 130 + 1)


def hoja(nombre, titulo, sub, anchos):
    ws = wb.create_sheet(nombre)
    ws.sheet_view.showGridLines = False
    for i, a in enumerate(anchos, start=1):
        ws.column_dimensions[L(i)].width = a
    ws["A1"] = titulo
    ws["A1"].font = TIT
    ws["A2"] = sub
    ws["A2"].font = GRIS
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=len(anchos))
    ws["A2"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[2].height = 45
    return ws


def f(txt):
    """Sustituye {nombre} por su referencia."""
    import re
    return re.sub(r"\{([^{}]+)\}", lambda m: N[m.group(1)], txt)


# ====================================================================================== lectura del libro
lb = load_workbook(LIBRO, read_only=True, data_only=True)


def tabla(nombre):
    filas = list(lb[nombre].iter_rows(values_only=True))
    cab = list(filas[0])
    return [(i + 2, dict(zip(cab, r))) for i, r in enumerate(filas[1:]) if r and r[0] is not None]


EVE = {r["EVE_NUM"]: (i, r) for i, r in tabla("EVENTO")}
LIN = tabla("LINEA")
OBJ = [(i, r) for i, r in tabla("OBJETO") if str(r["OBJ_NUM"]).endswith(PER)]
CMP = tabla("COMPONENTE")
RRE = tabla("REGLA_REPARTO")
MED = [(i, r) for i, r in tabla("MEDIDA") if str(r["MED_PER"]) == PER]
REC = {r["REC_COD"]: r for _, r in tabla("RECURSO")}
TRE = {r["TRE_COD"]: r for _, r in tabla("TIPO_RECURSO")}
ACT = tabla("ACTIVIDAD")
CEN = tabla("CENTRO")
motor = json.loads(MOTOR.read_text(encoding="utf-8"))

# ====================================================================================== DATOS
ws = hoja("DATOS", "DATOS · copiados del libro SERVITEC_sintetico.xlsx (valores, en azul)",
          "Estos son los únicos números tecleados del oráculo: vienen del libro, con su hoja y fila de origen. Todo lo demás del "
          "libro son fórmulas que parten de aquí. verificar_pieza30.py comprueba que sigan siendo iguales al libro.",
          [14, 12, 14, 22, 12, 13, 13, 12, 28])
r = 4
sec(ws, r, "A · Movimientos de MAT_COBRE hasta julio (EVENTO + LINEA): base del kardex promedio ponderado", 9); r += 1
head(ws, r, 1, ["EVE_NUM", "Fecha", "Periodo", "Orden (T15)", "TRX", "Cantidad (kg)", "Costo unit. compra", "Exceso declarado (LIN_EXC)", "Origen"]); r += 1
k0 = r
movs = []
for i, l in LIN:
    if l["LIN_REC"] != "MAT_COBRE":
        continue
    fe, e = EVE[l["LIN_EVE"]]
    if str(e["EVE_PER"]) > PER:
        continue
    movs.append((e["EVE_FEC"], e["EVE_NUM"], e, l, fe, i))
movs.sort(key=lambda x: (x[0], x[1]))
for fec, num, e, l, fe, li in movs:
    put(ws, r, 1, num); put(ws, r, 2, fec); put(ws, r, 3, e["EVE_PER"]); put(ws, r, 4, e["EVE_OBJ"] or "")
    put(ws, r, 5, e["EVE_TRX"]); put(ws, r, 6, l["LIN_CAN"], Q)
    put(ws, r, 7, l["LIN_CU_DOC"] if e["EVE_TRX"] == "T14" else None, Q); put(ws, r, 8, l["LIN_EXC"] or 0, Q)
    put(ws, r, 9, f"EVENTO f{fe} · LINEA f{li}", font=GRIS)
    r += 1
k1 = r - 1
N["K_TRX"] = f"DATOS!$E${k0}:$E${k1}"
r += 1
sec(ws, r, "B · Órdenes de julio (OBJETO) y estándar de material (COMPONENTE)", 9); r += 1
head(ws, r, 1, ["Orden", "Producto", "Cantidad", "", "Producto", "Recurso", "kg estándar por unidad", "Merma estándar %", "Origen"]); r += 1
o0 = r
for k, (i, o) in enumerate(OBJ):
    put(ws, r + k, 1, o["OBJ_NUM"], nombre=f"OT{k}"); put(ws, r + k, 2, o["OBJ_PRO"], nombre=f"PRO{k}")
    put(ws, r + k, 3, o["OBJ_CAN"], Q, nombre=f"CAN{k}")
    put(ws, r + k, 9, f"OBJETO f{i}", font=GRIS)
for k, (i, c) in enumerate(CMP):
    put(ws, r + k, 5, c["CMP_PRO"]); put(ws, r + k, 6, c["CMP_REC"]); put(ws, r + k, 7, c["CMP_CAN_EST"], Q)
    put(ws, r + k, 8, c["CMP_MERMA"], Q)
    ws.cell(r + k, 9).value = (ws.cell(r + k, 9).value or "") + f" · COMPONENTE f{i}"
N["CMP_PRO"] = f"DATOS!$E${r}:$E${r + len(CMP) - 1}"
N["CMP_EST"] = f"DATOS!$G${r}:$G${r + len(CMP) - 1}"
N["CMP_MER"] = f"DATOS!$H${r}:$H${r + len(CMP) - 1}"
N["OBJ_NUM"] = f"DATOS!$A${o0}:$A${o0 + len(OBJ) - 1}"
N["OBJ_PRO"] = f"DATOS!$B${o0}:$B${o0 + len(OBJ) - 1}"
r += max(len(OBJ), len(CMP)) + 1
sec(ws, r, "C · Recursos del mes registrados con T17 (EVENTO + LINEA de julio) y su elemento (RECURSO → TIPO_RECURSO)", 9); r += 1
head(ws, r, 1, ["Recurso", "Descripción", "Tipo", "Elemento", "Monto julio (S/)", "", "", "", "Origen"]); r += 1
for i, l in LIN:
    fe, e = EVE[l["LIN_EVE"]]
    if str(e["EVE_PER"]) != PER or e["EVE_TRX"] != "T17":
        continue
    rc = REC[l["LIN_REC"]]
    put(ws, r, 1, l["LIN_REC"]); put(ws, r, 2, rc["REC_DES"]); put(ws, r, 3, rc["REC_TRE"]); put(ws, r, 4, TRE[rc["REC_TRE"]]["TRE_ELE"])
    put(ws, r, 5, l["LIN_MTO"], S, nombre=f"REC_{l['LIN_REC']}")
    put(ws, r, 9, f"EVENTO f{fe} · LINEA f{i}", font=GRIS)
    r += 1
r += 1
sec(ws, r, "D · Matriz de configuración (REGLA_REPARTO): en qué etapa y con qué inductor se reparte cada origen", 9); r += 1
head(ws, r, 1, ["Etapa", "Origen", "Criterio (inductor)", "Clave etapa|origen", "", "", "", "", "Origen"]); r += 1
g0 = r
for i, x in RRE:
    put(ws, r, 1, x["RRE_ETAPA"]); put(ws, r, 2, x["RRE_ORIGEN"]); put(ws, r, 3, x["RRE_CRIT"])
    put(ws, r, 4, f"=A{r}&\"|\"&B{r}"); put(ws, r, 9, f"REGLA_REPARTO f{i}", font=GRIS)
    r += 1
N["RRE_ETA"] = f"DATOS!$A${g0}:$A${r - 1}"
N["RRE_CRIT"] = f"DATOS!$C${g0}:$C${r - 1}"
N["RRE_KEY"] = f"DATOS!$D${g0}:$D${r - 1}"
r += 1
sec(ws, r, f"E · Matriz de cálculo (MEDIDA de {PER}): cuánto inductor consumió cada destino", 9); r += 1
head(ws, r, 1, ["Criterio", "Nivel", "Destino", "Cantidad", "", "", "", "", "Origen"]); r += 1
m0 = r
for i, x in MED:
    put(ws, r, 1, x["MED_CRIT"]); put(ws, r, 2, x["MED_NIVEL"]); put(ws, r, 3, x["MED_DEST"]); put(ws, r, 4, x["MED_CAN"], Q)
    put(ws, r, 9, f"MEDIDA f{i}", font=GRIS)
    r += 1
N["MED_CRIT"] = f"DATOS!$A${m0}:$A${r - 1}"
N["MED_NIV"] = f"DATOS!$B${m0}:$B${r - 1}"
N["MED_DEST"] = f"DATOS!$C${m0}:$C${r - 1}"
N["MED_CAN"] = f"DATOS!$D${m0}:$D${r - 1}"
r += 1
put(ws, r, 1, "Total recursos T17 de julio (S/)", font=BOLD, box=False)
put(ws, r, 5, f"=SUM(E{r - 1 - len(MED) - 4 - len(RRE) - 4 - 5}:E{r - 1 - len(MED) - 4 - len(RRE) - 4})", S)  # placeholder, se reemplaza abajo
fila_total_t17 = r
ws.freeze_panes = "A4"

# total T17 bien referenciado
rec_refs = [v for k, v in N.items() if k.startswith("REC_")]
ws.cell(fila_total_t17, 5).value = "=" + "+".join(x.split("!")[1] for x in rec_refs)
N["T17_TOTAL"] = f"DATOS!$E${fila_total_t17}"


def crit(etapa, origen):
    return f'INDEX({N["RRE_CRIT"]},MATCH("{etapa}|{origen}",{N["RRE_KEY"]},0))'


def medida(crit_cell, dest_cell, nivel_excluir="CAP"):
    return f'SUMIFS({N["MED_CAN"]},{N["MED_CRIT"]},{crit_cell},{N["MED_DEST"]},{dest_cell},{N["MED_NIV"]},"<>{nivel_excluir}")'


# ====================================================================================== P1
ws = hoja("P1_MATERIAL", "P1 · Material directo → orden (kardex promedio ponderado; merma en exceso aparte)",
          "Kardex perpetuo a promedio ponderado: cada salida se valoriza al costo promedio del saldo anterior. La merma que excede el "
          "estándar de COMPONENTE (kg por unidad × cantidad × (1 + merma %)) se separa como PÉRDIDA (NIC 2 §16 a).",
          [10, 11, 10, 22, 12, 12, 13, 13, 13, 13, 13, 13])
r = 4
head(ws, r, 1, ["EVE", "Fecha", "TRX", "Orden", "Entra kg", "Entra S/", "Sale kg", "CPU antes", "Sale S/", "Saldo kg", "Saldo S/", "CPU saldo"]); r += 1
p0 = r
for k in range(k1 - k0 + 1):
    d = k0 + k
    put(ws, r, 1, f"=DATOS!A{d}"); put(ws, r, 2, f"=DATOS!B{d}"); put(ws, r, 3, f"=DATOS!E{d}"); put(ws, r, 4, f"=DATOS!D{d}")
    put(ws, r, 5, f'=IF(C{r}="T14",DATOS!F{d},0)', Q)
    put(ws, r, 6, f"=E{r}*IF(C{r}=\"T14\",DATOS!G{d},0)", S)
    put(ws, r, 7, f'=IF(C{r}="T15",DATOS!F{d},0)', Q)
    prev_q, prev_v = ("0", "0") if r == p0 else (f"J{r - 1}", f"K{r - 1}")
    put(ws, r, 8, f"=IF({prev_q}>0,{prev_v}/{prev_q},0)", S4)
    put(ws, r, 9, f"=G{r}*H{r}", S)
    put(ws, r, 10, f"={prev_q}+E{r}-G{r}", Q)
    put(ws, r, 11, f"={prev_v}+F{r}-I{r}", S)
    put(ws, r, 12, f"=IF(J{r}>0,K{r}/J{r},0)", S4)
    r += 1
p1 = r - 1
N["KDX_SALDO_Q"] = f"'P1_MATERIAL'!$J${p1}"
N["KDX_SALDO_V"] = f"'P1_MATERIAL'!$K${p1}"
r += 1
nota(ws, r, "Saldo final de julio del kardex (lo publica el motor como control «Kardex Cobre»).", 12); r += 1
put(ws, r, 1, "Saldo final kg", font=BOLD); put(ws, r, 3, f"={N['KDX_SALDO_Q']}", Q, nombre="KDX_Q")
put(ws, r, 5, "Saldo final S/", font=BOLD); put(ws, r, 7, f"={N['KDX_SALDO_V']}", S, nombre="KDX_V"); r += 2
sec(ws, r, f"Consumo de julio por orden: estándar, exceso (pérdida) y material normal", 12); r += 1
head(ws, r, 1, ["Orden", "Producto", "Cantidad", "kg reales", "CPU de la salida", "kg estándar", "Exceso kg", "Exceso declarado", "MD normal S/", "PÉRDIDA S/", "Total salida S/", "¿Exceso = declarado?"]); r += 1
for k in range(len(OBJ)):
    put(ws, r, 1, f"={N[f'OT{k}']}"); put(ws, r, 2, f"={N[f'PRO{k}']}"); put(ws, r, 3, f"={N[f'CAN{k}']}", Q)
    put(ws, r, 4, f"=SUMIFS($G${p0}:$G${p1},$D${p0}:$D${p1},A{r},$C${p0}:$C${p1},\"T15\")", Q)
    put(ws, r, 5, f"=IF(D{r}>0,SUMIFS($I${p0}:$I${p1},$D${p0}:$D${p1},A{r})/D{r},0)", S4)
    put(ws, r, 6, f"=SUMIFS({N['CMP_EST']},{N['CMP_PRO']},B{r})*C{r}*(1+SUMIFS({N['CMP_MER']},{N['CMP_PRO']},B{r})/100)", Q)
    put(ws, r, 7, f"=MAX(0,D{r}-F{r})", Q)
    dcol = "DATOS!$H$" + str(k0) + ":$H$" + str(k1)
    put(ws, r, 8, f"=SUMIFS({dcol},DATOS!$D${k0}:$D${k1},A{r})", Q)
    put(ws, r, 9, f"=(D{r}-G{r})*E{r}", S, nombre=f"P1_MD{k}")
    put(ws, r, 10, f"=G{r}*E{r}", S, nombre=f"P1_PER{k}")
    put(ws, r, 11, f"=I{r}+J{r}", S, nombre=f"P1_TOT{k}")
    put(ws, r, 12, f'=IF(ABS(G{r}-H{r})<0.0001,"OK","DIFIERE")')
    r += 1
put(ws, r, 8, "Total salidas julio", font=BOLD)
put(ws, r, 11, "=" + "+".join(N[f"P1_TOT{k}"].split("!")[1] for k in range(len(OBJ))), S, nombre="P1_TOTAL")
ws.freeze_panes = "A5"

# ====================================================================================== utilidades de matriz
def matriz(ws, r, etapa, origenes, destinos, monto_ref, prefijo, titulo, elemento):
    """Escribe una matriz de configuración (origen → criterio) y una matriz de cálculo origen × destino.
    monto_ref: {origen: referencia de su monto}. Devuelve la fila siguiente."""
    sec(ws, r, f"{titulo} · matriz de configuración", 4 + len(destinos)); r += 1
    head(ws, r, 1, ["Origen", "Monto a repartir (S/)", "Criterio (de REGLA_REPARTO)", "Elemento"]); r += 1
    fila_o = {}
    for o in origenes:
        put(ws, r, 1, o); put(ws, r, 2, f"={monto_ref[o]}", S, nombre=f"{prefijo}_M_{o}")
        put(ws, r, 3, "=" + crit(etapa, o), nombre=f"{prefijo}_C_{o}"); put(ws, r, 4, elemento)
        fila_o[o] = r
        r += 1
    r += 1
    sec(ws, r, f"{titulo} · matriz de cálculo: medida (inductor), proporción y monto por destino", 4 + len(destinos)); r += 1
    head(ws, r, 1, ["Origen", "Fila"] + destinos + ["Σ", "Conserva"]); r += 1
    for o in origenes:
        rm, rp, ra = r, r + 1, r + 2
        put(ws, rm, 1, o); put(ws, rm, 2, "medida")
        put(ws, rp, 1, o); put(ws, rp, 2, "proporción")
        put(ws, ra, 1, o, font=BOLD); put(ws, ra, 2, "monto S/", font=BOLD)
        for j, d in enumerate(destinos):
            col = 3 + j
            put(ws, 0 + rm - 0, col, None)
            ws.cell(rm, col).value = f'={medida(N[f"{prefijo}_C_{o}"], chr(34) + d + chr(34))}'
            ws.cell(rm, col).number_format = Q
            put(ws, rp, col, f"=IF({L(3 + len(destinos))}{rm}>0,{L(col)}{rm}/{L(3 + len(destinos))}{rm},0)", PCT)
            put(ws, ra, col, f"={N[f'{prefijo}_M_{o}']}*{L(col)}{rp}", S, nombre=f"{prefijo}_{o}>{d}")
        sc = 3 + len(destinos)
        put(ws, rm, sc, f"=SUM(C{rm}:{L(sc - 1)}{rm})", Q)
        put(ws, rp, sc, f"=SUM(C{rp}:{L(sc - 1)}{rp})", PCT)
        put(ws, ra, sc, f"=SUM(C{ra}:{L(sc - 1)}{ra})", S)
        put(ws, ra, sc + 1, f'=IF(ABS({L(sc)}{ra}-{N[f"{prefijo}_M_{o}"]})<0.005,"OK","NO CONSERVA")')
        r += 4
    head(ws, r, 1, ["Total recibido", ""] + destinos)
    for j, d in enumerate(destinos):
        col = 3 + j
        refs = "+".join(N[f"{prefijo}_{o}>{d}"].split("!")[1] for o in origenes)
        put(ws, r + 1, col, "=" + refs, S, fill=F_RES, nombre=f"{prefijo}_RECIBE_{d}")
    return r + 3


# ====================================================================================== P2
ws = hoja("P2_PERSONAL", "P2 · Personal directo (MOD) → actividades",
          "Monto del destino = monto del origen × medida del destino ÷ Σ medidas del origen. Inductor HORAS_MOD.",
          [14, 14, 14, 14, 14, 14, 12])
ACTS = [a["ACT_COD"] for _, a in ACT]
r = matriz(ws, 4, "P2", ["MOD"], ACTS, {"MOD": N["REC_MOD"]}, "P2", "P2", "PD (MOD)")

# ====================================================================================== P4A
ws = hoja("P4A_INDIRECTOS", "P4A · Indirectos → centros",
          "Alquiler, energía y supervisión van a los centros; administración va a su centro ADM (para P5).",
          [14, 14, 14, 14, 14, 14, 14, 12])
CENS = [c["CEN_COD"] for _, c in CEN if c["CEN_COD"] != "ALM_SRV"]
P4A_OR = [x["RRE_ORIGEN"] for _, x in RRE if x["RRE_ETAPA"] == "P4A"]
r = matriz(ws, 4, "P4A", P4A_OR, CENS, {o: N[f"REC_{o}"] for o in P4A_OR}, "P4A", "P4A", "CIF / GAD")

# ====================================================================================== P4B
ws = hoja("P4B_RECIPROCO", "P4B · Centros de apoyo entre sí → centro productivo (método RECÍPROCO)",
          "Mantenimiento y calidad se prestan servicios mutuos. Se resuelve el sistema X = costo propio + servicios recibidos "
          "(Horngren; Oria: el recíproco es el método preferido). Se muestran la presentación clásica (X) y la efectiva por costo "
          "propio, que es la que publica el motor; ambas entregan lo mismo al taller.",
          [26, 16, 16, 16, 16, 14])
APR = [x["RRE_ORIGEN"] for _, x in RRE if x["RRE_ETAPA"] == "P4B"]       # CA_MANT, CA_CAL
A, Bc = APR[0], APR[1]
r = 4
sec(ws, r, "Matriz de configuración P4B", 6); r += 1
head(ws, r, 1, ["Centro de apoyo", "Costo propio (de P4A)", "Criterio", f"medida → {Bc}", f"medida → CA_TALLER", "Σ medidas"]); r += 1
for c in (A, Bc):
    otro = Bc if c == A else A
    put(ws, r, 1, c); put(ws, r, 2, f"={N['P4A_RECIBE_' + c]}", S, nombre=f"B_C_{c}")
    put(ws, r, 3, "=" + crit("P4B", c), nombre=f"B_K_{c}")
    put(ws, r, 4, f'={medida(f"C{r}", chr(34) + otro + chr(34))}', Q, nombre=f"B_MP_{c}")
    put(ws, r, 5, f'={medida(f"C{r}", chr(34) + "CA_TALLER" + chr(34))}', Q, nombre=f"B_MT_{c}")
    put(ws, r, 6, f"=D{r}+E{r}", Q, nombre=f"B_MS_{c}")
    r += 1
ws.cell(r - 2, 4).value  # noqa
nota(ws, r, f"Columna D: para {A} es su medida hacia {Bc}; para {Bc} es su medida hacia {A} (el par).", 6); r += 2
sec(ws, r, "Proporciones (s) y sistema recíproco", 6); r += 1
put(ws, r, 1, f"s({A}→{Bc})"); put(ws, r, 2, f"={N['B_MP_' + A]}/{N['B_MS_' + A]}", PCT, nombre="sAB"); r += 1
put(ws, r, 1, f"s({A}→TALLER)"); put(ws, r, 2, f"={N['B_MT_' + A]}/{N['B_MS_' + A]}", PCT, nombre="sAT"); r += 1
put(ws, r, 1, f"s({Bc}→{A})"); put(ws, r, 2, f"={N['B_MP_' + Bc]}/{N['B_MS_' + Bc]}", PCT, nombre="sBA"); r += 1
put(ws, r, 1, f"s({Bc}→TALLER)"); put(ws, r, 2, f"={N['B_MT_' + Bc]}/{N['B_MS_' + Bc]}", PCT, nombre="sBT"); r += 2
put(ws, r, 1, f"X({A}) = (C_A + s_BA·C_B) / (1 − s_AB·s_BA)", font=BOLD)
put(ws, r, 2, f"=({N['B_C_' + A]}+{N['sBA']}*{N['B_C_' + Bc]})/(1-{N['sAB']}*{N['sBA']})", S4, nombre="XA"); r += 1
put(ws, r, 1, f"X({Bc}) = C_B + s_AB·X_A", font=BOLD)
put(ws, r, 2, f"={N['B_C_' + Bc]}+{N['sAB']}*{N['XA']}", S4, nombre="XB"); r += 2
sec(ws, r, "Presentación clásica (Oria / Horngren): cada centro reparte su costo total X", 6); r += 1
head(ws, r, 1, ["Flujo", "Monto S/"]); r += 1
put(ws, r, 1, f"{A} → {Bc}"); put(ws, r, 2, f"={N['XA']}*{N['sAB']}", S); r += 1
put(ws, r, 1, f"{A} → CA_TALLER"); put(ws, r, 2, f"={N['XA']}*{N['sAT']}", S, nombre="clasAT"); r += 1
put(ws, r, 1, f"{Bc} → {A}"); put(ws, r, 2, f"={N['XB']}*{N['sBA']}", S); r += 1
put(ws, r, 1, f"{Bc} → CA_TALLER"); put(ws, r, 2, f"={N['XB']}*{N['sBT']}", S, nombre="clasBT"); r += 1
put(ws, r, 1, "Total al taller (clásica)", font=BOLD); put(ws, r, 2, f"={N['clasAT']}+{N['clasBT']}", S, nombre="clasT", fill=F_RES); r += 2
sec(ws, r, "Presentación efectiva (la del motor): N = (I − P)⁻¹ y pesos efectivos por costo propio", 6); r += 1
put(ws, r, 1, "det = 1 − s_AB·s_BA"); put(ws, r, 2, f"=1-{N['sAB']}*{N['sBA']}", S4, nombre="det"); r += 1
put(ws, r, 1, "N_AA = 1/det"); put(ws, r, 2, f"=1/{N['det']}", S4, nombre="NAA"); r += 1
put(ws, r, 1, "N_AB = s_AB/det"); put(ws, r, 2, f"={N['sAB']}/{N['det']}", S4, nombre="NAB"); r += 1
put(ws, r, 1, "N_BA = s_BA/det"); put(ws, r, 2, f"={N['sBA']}/{N['det']}", S4, nombre="NBA"); r += 1
put(ws, r, 1, "N_BB = 1/det"); put(ws, r, 2, f"=1/{N['det']}", S4, nombre="NBB"); r += 1
put(ws, r, 1, f"efectivo({A}→TALLER) = N_AA·s_AT + N_AB·s_BT"); put(ws, r, 2, f"={N['NAA']}*{N['sAT']}+{N['NAB']}*{N['sBT']}", S4, nombre="eA"); r += 1
put(ws, r, 1, f"efectivo({Bc}→TALLER) = N_BA·s_AT + N_BB·s_BT"); put(ws, r, 2, f"={N['NBA']}*{N['sAT']}+{N['NBB']}*{N['sBT']}", S4, nombre="eB"); r += 1
put(ws, r, 1, f"{A} → CA_TALLER (efectivo)", font=BOLD); put(ws, r, 2, f"={N['B_C_' + A]}*{N['eA']}", S, nombre=f"P4B_{A}>CA_TALLER"); r += 1
put(ws, r, 1, f"{Bc} → CA_TALLER (efectivo)", font=BOLD); put(ws, r, 2, f"={N['B_C_' + Bc]}*{N['eB']}", S, nombre=f"P4B_{Bc}>CA_TALLER"); r += 1
put(ws, r, 1, "Total al taller (efectiva)", font=BOLD)
put(ws, r, 2, f"={N['P4B_' + A + '>CA_TALLER']}+{N['P4B_' + Bc + '>CA_TALLER']}", S, nombre="P4B_TOTAL", fill=F_RES); r += 1
put(ws, r, 1, "¿Clásica = efectiva = costo propio de los dos centros?")
put(ws, r, 2, f'=IF(AND(ABS({N["clasT"]}-{N["P4B_TOTAL"]})<0.005,ABS({N["P4B_TOTAL"]}-{N["B_C_" + A]}-{N["B_C_" + Bc]})<0.005),"OK","DIFIERE")')

# ====================================================================================== P4D
ws = hoja("P4D_TALLER", "P4D · Centro productivo → actividades",
          "El taller reparte lo que recibió en P4A más lo que le llegó de los centros de apoyo en P4B. Inductor TALLER_ACT.",
          [14, 14, 14, 14, 14, 14, 12])
r = 4
put(ws, r, 1, "Taller: costo de P4A", font=BOLD); put(ws, r, 3, f"={N['P4A_RECIBE_CA_TALLER']}", S); r += 1
put(ws, r, 1, "Taller: recibido en P4B", font=BOLD); put(ws, r, 3, f"={N['P4B_TOTAL']}", S); r += 1
put(ws, r, 1, "Taller: total a repartir", font=BOLD); put(ws, r, 3, f"=C{r - 2}+C{r - 1}", S, nombre="TALLER_TOT", fill=F_RES); r += 2
r = matriz(ws, r, "P4D", ["CA_TALLER"], ACTS, {"CA_TALLER": N["TALLER_TOT"]}, "P4D", "P4D", "CIF")

# ====================================================================================== P4C
ws = hoja("P4C_ACTIVIDADES", "P4C · Actividades operativas → órdenes (con capacidad práctica: ocio)",
          "Cada actividad reparte su MOD (de P2) y su CIF (de P4D) con su inductor. Si MEDIDA trae la capacidad práctica (nivel CAP), "
          "la parte no usada es OCIO: f = (capacidad − uso) / capacidad; normal = monto × (1 − f) y ocio = monto × f, ambos con la "
          "proporción del inductor (no hay criterio propio de OCIO en REGLA_REPARTO).",
          [10, 8, 13, 12, 10, 10, 10, 13, 13, 13, 13, 13, 13, 10])
OTS = [o["OBJ_NUM"] for _, o in OBJ]
r = 4
head(ws, r, 1, ["Actividad", "Elemento", "Monto S/", "Inductor", f"medida {OTS[0][-11:]}", f"medida {OTS[1][-11:]}", "Uso", "Capacidad (CAP)",
                "f ocio", f"Normal {OTS[0][7:10]}", f"Normal {OTS[1][7:10]}", f"Ocio {OTS[0][7:10]}", f"Ocio {OTS[1][7:10]}", "Conserva"]); r += 1
for a in ACTS:
    for el, fuente in (("PD", f"P2_MOD>{a}"), ("CIF", f"P4D_CA_TALLER>{a}")):
        put(ws, r, 1, a); put(ws, r, 2, el); put(ws, r, 3, f"={N[fuente]}", S)
        put(ws, r, 4, "=" + crit("P4C", a))
        put(ws, r, 5, f'={medida(f"$D{r}", f"{N[chr(79) + chr(84) + chr(48)]}")}', Q)
        put(ws, r, 6, f'={medida(f"$D{r}", f"{N[chr(79) + chr(84) + chr(49)]}")}', Q)
        put(ws, r, 7, f"=E{r}+F{r}", Q)
        put(ws, r, 8, f'=SUMIFS({N["MED_CAN"]},{N["MED_CRIT"]},D{r},{N["MED_NIV"]},"CAP",{N["MED_DEST"]},A{r})', Q)
        put(ws, r, 9, f"=IF(H{r}>G{r},(H{r}-G{r})/H{r},0)", PCT)
        put(ws, r, 10, f"=C{r}*(1-I{r})*E{r}/G{r}", S, nombre=f"C_N0_{a}_{el}")
        put(ws, r, 11, f"=C{r}*(1-I{r})*F{r}/G{r}", S, nombre=f"C_N1_{a}_{el}")
        put(ws, r, 12, f"=C{r}*I{r}*E{r}/G{r}", S, nombre=f"C_O0_{a}_{el}")
        put(ws, r, 13, f"=C{r}*I{r}*F{r}/G{r}", S, nombre=f"C_O1_{a}_{el}")
        put(ws, r, 14, f'=IF(ABS(SUM(J{r}:M{r})-C{r})<0.005,"OK","NO CONSERVA")')
        r += 1
r += 1
head(ws, r, 1, ["Flujo (para comparar con el motor)", "", "Monto S/"]); r += 1
for a in ACTS:
    for k, ot in enumerate(OTS):
        put(ws, r, 1, f"{a} → {ot}")
        refs = [N[f"C_{t}{k}_{a}_{el}"].split("!")[1] for t in ("N", "O") for el in ("PD", "CIF")]
        put(ws, r, 3, "=" + "+".join(refs), S, nombre=f"P4C_{a}>{ot}")
        r += 1

# ====================================================================================== P5, P6, P7
ws = hoja("P5_P7_GASTOS", "P5–P7 · Administración, ventas y financieros → órdenes",
          "P5 reparte el centro de administración con ADM_OT. P6 (ventas) y P7 (financieros): el libro no trae reglas ni recursos de "
          "esos elementos; se comprueba contando las reglas.",
          [14, 22, 22, 14, 12, 12, 12])
r = matriz(ws, 4, "P5", ["ADM_SRV"], OTS, {"ADM_SRV": N["P4A_RECIBE_ADM_SRV"]}, "P5", "P5", "GAD")
put(ws, r, 1, "Reglas P6 en REGLA_REPARTO"); put(ws, r, 3, f'=COUNTIF({N["RRE_ETA"]},"P6")', Q, nombre="NP6"); r += 1
put(ws, r, 1, "Reglas P7 en REGLA_REPARTO"); put(ws, r, 3, f'=COUNTIF({N["RRE_ETA"]},"P7")', Q, nombre="NP7"); r += 1
put(ws, r, 1, "Ventas (P6) y financieros (P7) por orden"); put(ws, r, 3, f'=IF({N["NP6"]}+{N["NP7"]}=0,0,NA())', S, nombre="P67")

# ====================================================================================== RESULTADO
ws = hoja("RESULTADO", "RESULTADO · costo de julio por orden y por producto (síntesis REAL)",
          "Cada columna viene de su etapa. Costo total = MD + MOD + CIF + administración + ventas + financieros + pérdida + ocio.",
          [22, 10, 10, 12, 12, 12, 12, 10, 10, 10, 12, 14, 12])
r = 4
head(ws, r, 1, ["Orden", "Producto", "Cantidad", "MD", "MOD", "CIF", "Adm.", "Ventas", "Financ.", "Pérdida", "Ocio", "COSTO TOTAL", "Unitario"]); r += 1
r0 = r
for k, ot in enumerate(OTS):
    put(ws, r, 1, f"={N[f'OT{k}']}"); put(ws, r, 2, f"={N[f'PRO{k}']}"); put(ws, r, 3, f"={N[f'CAN{k}']}", Q)
    put(ws, r, 4, f"={N[f'P1_MD{k}']}", S, nombre=f"R_md_{k}")
    put(ws, r, 5, "=" + "+".join(N[f"C_N{k}_{a}_PD"] for a in ACTS), S, nombre=f"R_mod_{k}")
    put(ws, r, 6, "=" + "+".join(N[f"C_N{k}_{a}_CIF"] for a in ACTS), S, nombre=f"R_cif_{k}")
    put(ws, r, 7, f"={N['P5_ADM_SRV>' + ot]}", S, nombre=f"R_admin_{k}")
    put(ws, r, 8, f"={N['P67']}", S, nombre=f"R_gasto_venta_{k}")
    put(ws, r, 9, f"={N['P67']}", S, nombre=f"R_financiero_{k}")
    put(ws, r, 10, f"={N[f'P1_PER{k}']}", S, nombre=f"R_perdida_{k}")
    put(ws, r, 11, "=" + "+".join(N[f"C_O{k}_{a}_{el}"] for a in ACTS for el in ("PD", "CIF")), S, nombre=f"R_ocio_{k}")
    put(ws, r, 12, f"=SUM(D{r}:K{r})", S, fill=F_RES, font=BOLD, nombre=f"R_costo_total_{k}")
    put(ws, r, 13, f"=L{r}/C{r}", S, nombre=f"R_costo_unitario_{k}")
    r += 1
put(ws, r, 1, "Total", font=BOLD)
for col in range(4, 13):
    put(ws, r, col, f"=SUM({L(col)}{r0}:{L(col)}{r - 1})", S, font=BOLD)
N["R_TOTAL"] = f"'RESULTADO'!$L${r}"
r += 2
sec(ws, r, "Por producto", 13); r += 1
head(ws, r, 1, ["Producto", "", "Cantidad", "", "", "", "", "", "", "", "", "Costo total", "Unitario"]); r += 1
for k in range(len(OTS)):
    put(ws, r, 1, f"={N[f'PRO{k}']}")
    put(ws, r, 3, f"=SUMIFS($C${r0}:$C${r0 + len(OTS) - 1},$B${r0}:$B${r0 + len(OTS) - 1},A{r})", Q)
    put(ws, r, 12, f"=SUMIFS($L${r0}:$L${r0 + len(OTS) - 1},$B${r0}:$B${r0 + len(OTS) - 1},A{r})", S, nombre=f"PROD_TOT_{k}")
    put(ws, r, 13, f"=L{r}/C{r}", S)
    r += 1
r += 1
sec(ws, r, "Controles", 13); r += 1
head(ws, r, 1, ["Control", "", "", "Esperado", "Oráculo", "Diferencia", "Estado"]); r += 1
esperados = {"REB": 22975, "MPR": 5165}
for k in range(len(OTS)):
    pro = OBJ[k][1]["OBJ_PRO"]
    put(ws, r, 1, f"Costo total {pro} (cifra del dueño)")
    put(ws, r, 4, esperados[pro], S); put(ws, r, 5, f"={N[f'R_costo_total_{k}']}", S); put(ws, r, 6, f"=E{r}-D{r}", S)
    put(ws, r, 7, f'=IF(ABS(F{r})<0.005,"OK","DIFIERE")', nombre=f"CHK_DUENO_{k}")
    r += 1
put(ws, r, 1, "Conservación: recursos de julio (material que salió + T17) = costo de las órdenes")
put(ws, r, 4, f"={N['P1_TOTAL']}+{N['T17_TOTAL']}", S); put(ws, r, 5, f"={N['R_TOTAL']}", S); put(ws, r, 6, f"=E{r}-D{r}", S)
put(ws, r, 7, f'=IF(ABS(F{r})<0.005,"OK","NO CONSERVA")', nombre="CHK_CONS"); r += 1
put(ws, r, 1, "Recíproco: clásica = efectiva")
put(ws, r, 7, f"='P4B_RECIPROCO'!B{ws.parent['P4B_RECIPROCO'].max_row}", nombre="CHK_RECIP"); r += 1

# ====================================================================================== COMPARACION_MOTOR
ws = hoja("COMPARACION_MOTOR", "COMPARACIÓN · oráculo (fórmulas) contra calcular() del motor real",
          f"Valores del motor pegados desde calcular({PER}, REAL) el {motor['calculado']} · huella del libro {motor['huella_libro'][:16]}… "
          "verificar_pieza30.py vuelve a correr calcular() y comprueba que estos valores sigan siendo los del motor.",
          [26, 14, 14, 14, 14, 30])
r = 4
sec(ws, r, "1 · Por orden y elemento", 6); r += 1
head(ws, r, 1, ["Orden · elemento", "Oráculo", "Motor", "Diferencia", "Estado", "Si difiere, etapa a revisar"]); r += 1
ETAPA_DE = {"md": "P1 (kardex / estándar)", "mod": "P2 → P4C", "cif": "P4A → P4B → P4D → P4C", "admin": "P4A → P5",
            "gasto_venta": "P6", "financiero": "P7", "perdida": "P1 (merma en exceso)", "ocio": "P4C (capacidad)",
            "costo_total": "ver filas anteriores", "costo_unitario": "cantidad (OBJETO)"}
c_ini = r
for k, ot in enumerate(OTS):
    mo = motor["objetos"][ot]
    for el in ("md", "mod", "cif", "admin", "gasto_venta", "financiero", "perdida", "ocio", "costo_total", "costo_unitario"):
        put(ws, r, 1, f"{ot} · {el}")
        put(ws, r, 2, f"={N[f'R_{el}_{k}']}", S)
        put(ws, r, 3, mo[el], S)
        put(ws, r, 4, f"=B{r}-C{r}", S)
        put(ws, r, 5, f'=IF(ABS(D{r})<0.005,"OK","DIFIERE")')
        put(ws, r, 6, f'=IF(E{r}="OK","",\"{ETAPA_DE[el]}\")')
        if el == "costo_total":
            for c in range(1, 6):
                ws.cell(r, c).fill = F_RES
        r += 1
c_fin = r - 1
r += 1
sec(ws, r, "2 · Por etapa: cada flecha del reparto (oráculo) contra la suma de las trazas del motor", 6); r += 1
head(ws, r, 1, ["Etapa · origen → destino", "Oráculo", "Motor (Σ trazas)", "Diferencia", "Estado", ""]); r += 1
e_ini = r
for clave, monto in sorted(motor["flujos"].items()):
    etapa, origen, destino = clave.split("|")
    nombre = f"{etapa}_{origen}>{destino}"
    if etapa == "P1":
        k = OTS.index(destino)
        oref = N[f"P1_TOT{k}"]
    else:
        oref = N[nombre]
    put(ws, r, 1, f"{etapa} · {origen} → {destino}")
    put(ws, r, 2, f"={oref}", S); put(ws, r, 3, monto, S); put(ws, r, 4, f"=B{r}-C{r}", S)
    put(ws, r, 5, f'=IF(ABS(D{r})<0.005,"OK","DIFIERE en "&LEFT(A{r},FIND(" ",A{r})-1))')
    r += 1
e_fin = r - 1
r += 1
sec(ws, r, "3 · Otros controles publicados por el motor", 6); r += 1
head(ws, r, 1, ["Control", "Oráculo", "Motor", "Diferencia", "Estado", ""]); r += 1
o_ini = r
ocio_tot = "+".join(N[f"R_ocio_{k}"] for k in range(len(OTS)))
for nom, oref, val in (("Ocio total (capacidad no usada)", f"={ocio_tot}", motor["ocio_total"]),
                       ("Kardex Cobre: saldo final S/", f"={N['KDX_V']}", motor["kardex_saldo_final"]),
                       ("Recursos del periodo = costo de las órdenes", f"={N['R_TOTAL']}", motor["conservacion"])):
    put(ws, r, 1, nom); put(ws, r, 2, oref, S); put(ws, r, 3, val, S); put(ws, r, 4, f"=B{r}-C{r}", S)
    put(ws, r, 5, f'=IF(ABS(D{r})<0.005,"OK","DIFIERE")')
    r += 1
o_fin = r - 1
r += 1
put(ws, r, 1, "ESTADO GENERAL", font=BOLD)
put(ws, r, 2, f'=IF(AND(COUNTIF(E{c_ini}:E{c_fin},"OK")={c_fin - c_ini + 1},COUNTIF(E{e_ini}:E{e_fin},"OK")={e_fin - e_ini + 1},'
              f'COUNTIF(E{o_ini}:E{o_fin},"OK")={o_fin - o_ini + 1}),"OK: el oráculo coincide con el motor","HAY DIFERENCIAS: ver columna F")',
    font=BOLD, fill=F_OK, nombre="ESTADO")
N["CMP_DIF_MAX"] = f"'COMPARACION_MOTOR'!$D${c_ini}:$D${c_fin}"

# ====================================================================================== LEEME
ws = wb.create_sheet("LEEME", 0)
ws.sheet_view.showGridLines = False
ws.column_dimensions["A"].width = 30
ws.column_dimensions["B"].width = 100
ws["A1"] = "Oráculo SERVITEC · costo de julio 2025 recalculado A MANO por etapas P1–P7"
ws["A1"].font = TIT
filas = [
    ("Para qué sirve", "Es la verificación independiente del motor de costos. Reproduce, solo con fórmulas de Excel visibles, el costo de "
                       "julio de cada orden siguiendo las etapas de Oria, y lo compara con lo que devuelve calcular() del motor real."),
    ("Cómo leerlo", "DATOS → P1_MATERIAL → P2_PERSONAL → P4A_INDIRECTOS → P4B_RECIPROCO → P4D_TALLER → P4C_ACTIVIDADES → P5_P7_GASTOS → "
                    "RESULTADO → COMPARACION_MOTOR. Cada etapa tiene su matriz de configuración (origen → criterio, de REGLA_REPARTO) y "
                    "su matriz de cálculo (medidas, proporción y monto por destino, de MEDIDA)."),
    ("Convención", "Azul = dato copiado del libro (con su hoja y fila). Negro = fórmula. Amarillo = resultado de la etapa."),
    ("Caso", "SERVITEC es un caso SINTÉTICO creado para probar el sistema; no representa a una empresa real."),
    ("Costo total REB (oráculo)", f"={N['R_costo_total_0' if OBJ[0][1]['OBJ_PRO'] == 'REB' else 'R_costo_total_1']}"),
    ("Costo total MPR (oráculo)", f"={N['R_costo_total_1' if OBJ[0][1]['OBJ_PRO'] == 'REB' else 'R_costo_total_0']}"),
    ("¿Da 22,975 y 5,165?", f'=IF(AND({N["CHK_DUENO_0"]}="OK",{N["CHK_DUENO_1"]}="OK"),"SÍ","NO: ver RESULTADO")'),
    ("Comparación con el motor", f"={N['ESTADO']}"),
    ("Conservación", f"={N['CHK_CONS']}"),
    ("Verificación automática", "python -I verificar_pieza30.py <repo> SERVITEC_sintetico.xlsx oraculo_SERVITEC.xlsx → recalcula este libro "
                                "con LibreOffice, revisa que los DATOS sigan iguales al libro, vuelve a correr calcular() y reporta la "
                                "diferencia por orden, por elemento y por etapa."),
    ("Fuentes", "Método de Oria (GE704W, etapas P1–P7, modelos ABC); Horngren, Datar y Rajan, método recíproco; NIC 2 §13 y §16 "
                "(capacidad y pérdidas); libro SERVITEC_sintetico.xlsx (hojas EVENTO, LINEA, OBJETO, COMPONENTE, REGLA_REPARTO, MEDIDA)."),
]
for i, (a, b) in enumerate(filas, start=3):
    ws.cell(i, 1, a).font = BOLD
    c = ws.cell(i, 2, b)
    c.font = BOLD if str(b).startswith("=") else NEG
    if str(b).startswith("="):
        c.fill = F_RES
        c.number_format = S
    c.alignment = Alignment(wrap_text=True, vertical="top")

for w in wb.worksheets:
    for row in w.iter_rows():
        for c in row:
            if c.font and c.font.name != "Arial":
                c.font = Font(name="Arial", size=c.font.size or 10, bold=c.font.bold, italic=c.font.italic, color=c.font.color)
wb.save(SALIDA)
print("ok", SALIDA, len(N), "nombres")
