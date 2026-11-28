"""Verificación automática de la pieza 24 (libros_hostiles/).

Uso (desde cualquier carpeta):
    python -I verificar_pieza24.py <repo>/src [carpeta_libros]

Requiere el repo con fuente/DBD_Fuente.xlsx y casos/plantilla_dbd.xlsx. No modifica nada: cada libro se registra en una
carpeta temporal. Comprueba, por archivo:
  1. el mensaje de libro_dbd.validar() (lo que ve el usuario al cargar);
  2. el resultado de calculo_local.calcular(2025-07, REAL): costo por orden o mensaje de rechazo;
  3. que exista la hoja LEEME (salvo el 07, que no se puede abrir).
Sale con código 1 si algo no coincide con lo esperado.
"""
import json
import sys
import tempfile
from pathlib import Path

REPO_SRC = Path(sys.argv[1]).resolve()
CARPETA = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_SRC))

import reyna_local.calculo_local as CL          # noqa: E402
import reyna_local.libro_dbd as B               # noqa: E402
from openpyxl import load_workbook              # noqa: E402

OK_JULIO = {"OT-SRV-REB-2025-07": (10.0, 22975.0), "OT-SRV-MPR-2025-07": (10.0, 5165.0)}
ESPERADO = {
    "00_control_sin_defecto.xlsx": {"validar": [], "calcular": OK_JULIO},
    "01_hoja_obligatoria_borrada.xlsx": {"validar": ["Falta la hoja CRITERIO. Inductores (unidad de medida)."]},
    "02_celdas_vacias_MEDIDA.xlsx": {"validar": [f"Hoja MEDIDA, fila {f}: la cantidad debe ser un número ≥ 0." for f in (184, 185, 186)]},
    "03_texto_en_monto.xlsx": {"validar": ["Hoja VENTA, fila 14: el ingreso (VTA_ING) debe ser un número."]},
    # hallazgos: hoy pasan sin aviso. Cuando otro agente los corrija, esta prueba fallará A PROPÓSITO y habrá que
    # cambiar el «esperado» por el mensaje nuevo (eso confirma la corrección).
    "04_fechas_al_reves.xlsx": {"validar": [], "calcular": OK_JULIO, "hallazgo": True},
    "05_codigo_duplicado.xlsx": {"validar": [], "calcular": {"OT-SRV-REB-2025-07": (12.0, 22975.0),
                                                            "OT-SRV-MPR-2025-07": (10.0, 5165.0)}, "hallazgo": True},
    "06_criterio_suma_cero.xlsx": {"validar": [], "error": "I8: P4C DES tiene monto 5700.00 y su criterio DES_OT suma cero",
                                   "hallazgo": True},
    "07_archivo_truncado.xlsx": {"validar": ["El archivo no es un libro Excel (.xlsx) legible."], "sin_leeme": True},
    "08_columnas_otro_orden.xlsx": {"validar": [], "calcular": OK_JULIO},
}


def calcular(libro):
    carpeta = Path(tempfile.mkdtemp(prefix="p24_"))
    ficha, err = CL.registrar(carpeta, libro.read_bytes(), libro.name)
    if err:
        return {"registrar": err}
    try:
        r = CL.calcular(carpeta, "2025-07", "REAL", ficha["id"])
    except Exception as e:                       # se reporta el mensaje, no la traza
        return {"error": str(e)}
    return {"objetos": {o["codigo"]: (round(o["cantidad"], 4), round(o["costo_total"], 2)) for o in r["objetos"]}}


def main():
    fallas, filas = [], []
    for nombre, esp in ESPERADO.items():
        p = CARPETA / nombre
        if not p.exists():
            fallas.append(f"{nombre}: no existe")
            continue
        v = B.validar(p)
        if v != esp["validar"]:
            fallas.append(f"{nombre}: validar() dio {v}, se esperaba {esp['validar']}")
        if not esp.get("sin_leeme"):
            if "LEEME" not in load_workbook(p, read_only=True).sheetnames:
                fallas.append(f"{nombre}: falta la hoja LEEME")
        obtenido = "—"
        if not esp["validar"]:
            c = calcular(p)
            if "calcular" in esp:
                obtenido = c.get("objetos") or c
                if c.get("objetos") != esp["calcular"]:
                    fallas.append(f"{nombre}: calcular() dio {c}, se esperaba {esp['calcular']}")
            if "error" in esp:
                obtenido = c.get("error", c)
                if c.get("error") != esp["error"]:
                    fallas.append(f"{nombre}: calcular() dio {c}, se esperaba el error «{esp['error']}»")
        filas.append((nombre, v[:1] or "(acepta)", obtenido, "hallazgo" if esp.get("hallazgo") else ""))
    for f in filas:
        print(" | ".join(str(x) for x in f))
    print()
    if fallas:
        print("FALLAS:")
        for f in fallas:
            print(" -", f)
        sys.exit(1)
    print(f"PIEZA 24: OK ({len(ESPERADO)} libros verificados con validar() y calcular())")


if __name__ == "__main__":
    main()
