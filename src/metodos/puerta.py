# -*- coding: utf-8 -*-
"""PUERTA AUTOMÁTICA DE UN PR DEL CONSTRUCTOR (E-111, E-118 OT-002). La corre GitHub Actions en cada PR y a mano:
    python -m metodos.puerta origin/main          (desde kit/)
1. ZONAS: el PR solo toca archivos permitidos al constructor (CONTEXTO_CONSTRUCTOR §2). Si la rama es `ot-###-...`,
   se suman las rutas de la sección «## Zona» de `ordenes/OT-###.md` **leída de main** (no de la rama: un PR no puede
   ampliar su propia zona); una ruta o glob por línea.
2. Por cada método tocado: validar_metodo CONTRA DBD_4 (columnas que existen) y, si FICHA trae «caso», caso_excel.
3. probar_metodos: nada de lo anterior se rompió.
Sale con 0 solo si todo pasa; imprime un informe en Markdown que el workflow pega como comentario del PR."""
import os
import re
import subprocess
import sys

import rutas
import medir_modelo

AQUI = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(AQUI)
RAIZ = os.path.dirname(KIT)
sys.path.insert(0, KIT)

PERMITIDO = [r"^kit/metodos/(?!(validar_metodo|correr_metodos|publicar|caso_excel|_plantilla_metodo|probar_metodos|puerta|__init__)\.py$)[a-z0-9_]+\.py$",
             r"^kit/metodos/casos/Caso_[A-Z0-9_]+_\d+\.xlsx$", r"^\.dsh/", r"^ordenes/OT-\d{3}\.md$"]
HERRAMIENTAS = {"validar_metodo", "correr_metodos", "publicar", "caso_excel", "_plantilla_metodo", "probar_metodos",
                "puerta", "__init__", "semantica", "direccion_capas"}


def cambiados(base):
    out = subprocess.run(["git", "diff", "--name-only", f"{base}...HEAD"], cwd=RAIZ, capture_output=True, encoding="utf-8", errors="replace", check=True).stdout
    return [l for l in out.splitlines() if l.strip()]


DOCUMENTO_REL = "fuente/DBD_Documento.xlsx"


def candado_documento(arch, raiz=None):
    """T-172 (OT-051): DBD_Documento.xlsx es GENERADO. Devuelve (ok, motivo). FALLA si el PR lo toca (aparece en `arch`)
    o si el archivo presente difiere de lo que genera gen_documento.py desde la fuente (DBD_Fuente.xlsx). Sin archivo y sin tocarlo: OK (aún no se versiona)."""
    raiz = raiz or RAIZ
    ruta = os.path.join(raiz, DOCUMENTO_REL)
    if DOCUMENTO_REL in arch:
        return False, f"el PR modifica {DOCUMENTO_REL}: es GENERADO, nunca se edita a mano (se regenera con kit/gen_documento.py desde la fuente)"
    if not os.path.exists(ruta):
        return True, "sin documento versionado"
    fte = os.path.join(raiz, "fuente", "DBD_Fuente.xlsx")
    import gen_documento
    ok, motivo = gen_documento.verificar(fte, ruta)
    return ok, motivo


def rama_actual():
    """En GitHub Actions el HEAD está separado; el nombre de la rama viene en GITHUB_HEAD_REF."""
    rama = os.environ.get("GITHUB_HEAD_REF", "").strip()
    if rama:
        return rama
    try:
        return subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=RAIZ,
                              capture_output=True, encoding="utf-8", errors="replace", check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def glob_a_regex(p):
    p = p.strip().strip("`").replace("\\", "/")
    if p.endswith("/"):
        p += "**"
    out, i = [], 0
    while i < len(p):
        c = p[i]
        if c == "*":
            if i + 1 < len(p) and p[i + 1] == "*":
                out.append(".*")
                i += 2
                if i < len(p) and p[i] == "/":
                    i += 1
                continue
            out.append("[^/]*")
        elif c == "?":
            out.append("[^/]")
        elif c in ".+()|^$[]{}\\":
            out.append("\\" + c)
        else:
            out.append(c)
        i += 1
    return "^" + "".join(out) + "$"


def leer_ot_main(ot):
    """La zona se lee de main, no de la rama: un PR no puede ampliar su propia zona."""
    try:
        r = subprocess.run(["git", "show", f"origin/main:ordenes/{ot}.md"], cwd=RAIZ,
                           capture_output=True, encoding="utf-8", errors="replace", check=True)
        return r.stdout
    except (OSError, subprocess.CalledProcessError):
        pass
    try:   # V4.1: órdenes en ordenes/V41/OT-###_<bloque>.md
        ls = subprocess.run(["git", "ls-tree", "--name-only", "origin/main", "ordenes/V41/"], cwd=RAIZ,
                            capture_output=True, encoding="utf-8", errors="replace", check=True).stdout.split()
        f = next((x for x in ls if x.split("/")[-1].startswith(ot + "_")), None)
        if not f:
            return ""
        return subprocess.run(["git", "show", f"origin/main:{f}"], cwd=RAIZ, capture_output=True,
                              encoding="utf-8", errors="replace", check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return ""


def zona_ot():
    """Devuelve (patrones regex, etiqueta) de la sección «## Zona» de la OT de main."""
    rama = rama_actual()
    m = re.match(r"(?:ot|obra/OT)-(\d{3})-", rama)
    if not m:
        return [], ""
    ot = f"OT-{m.group(1)}"
    texto = leer_ot_main(ot)
    if not texto:
        return [], ot + " (sin archivo en main)"
    patrones, dentro = [], False
    for linea in texto.splitlines():
        s = linea.strip()
        if s.startswith("## "):
            dentro = s.lower().startswith("## zona")
        elif dentro and s.startswith("- "):
            patrones.append(glob_a_regex(re.split(r"\s+\(", s[2:].strip(), 1)[0]))   # «ruta  (nota)»: la nota no es parte de la ruta
    return patrones, ot


def main(base):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    from metodos import validar_metodo as VM, caso_excel as CE
    filas, ok = [], True
    arch = cambiados(base)
    zona, ot = zona_ot()
    permitidos = PERMITIDO + zona
    fuera = [a for a in arch if not any(re.match(p, a) for p in permitidos)]
    filas.append(("Zonas", "OK" if not fuera else "FALLA: fuera de zona → " + ", ".join(fuera)))
    ok &= not fuera
    cd_ok, cd_m = candado_documento(arch)
    filas.append(("Candado DBD_Documento (generado, no editable)", "OK · " + cd_m if cd_ok else "FALLA: " + cd_m))
    ok &= cd_ok
    if ot:
        etiqueta = f"{ot}: {len(zona)} patrón(es)" if zona else f"{ot}: sin sección «## Zona», solo fijas"
        filas.append((f"Zona de la OT ({rama_actual()})", etiqueta))
    dbd = os.path.join(rutas.FUENTE, "DBD_Fuente.xlsx")
    for a in [a for a in arch if a.startswith("kit/metodos/") and a.endswith(".py")
              and os.path.splitext(os.path.basename(a))[0] not in HERRAMIENTAS
              and os.path.exists(os.path.join(RAIZ, a))]:
        try:
            m = VM.cargar(os.path.join(RAIZ, a))
            f = VM.validar(m, dbd, permitir_pendiente=True)
            filas.append((f"validar_metodo {os.path.basename(a)}", "OK" if not f else "FALLA: " + "; ".join(f)))
            ok &= not f
            avisos = VM.avisos(m, dbd)
            if avisos:
                filas.append((f"avisos CONSUME {os.path.basename(a)}", "AVISO: " + "; ".join(avisos)))
            deudas = VM.deudas(m, dbd)
            if deudas:
                filas.append((f"deudas RESULTADO {os.path.basename(a)}", "; ".join(deudas)))
            if getattr(m, "PENDIENTE", False):
                filas.append((f"caso_excel {os.path.basename(a)}", "PENDIENTE: cáscara con contrato, sin cálculo"))
                continue
            caso = getattr(m, "FICHA", {}).get("caso")
            if caso:
                m.CASOS = CE.cargar(caso, m.FICHA["nombre"])
                f = VM.validar(m, dbd)
                filas.append((f"caso_excel {caso}", "OK" if not f else "FALLA: " + "; ".join(f)))
                ok &= not f
            else:
                filas.append((f"caso_excel {os.path.basename(a)}", "FALLA: la FICHA no declara «caso»"))
                ok = False
        except Exception as ex:
            filas.append((a, f"FALLA: {ex}"))
            ok = False
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    p = subprocess.run([sys.executable, "-m", "metodos.probar_metodos"], cwd=KIT, capture_output=True, encoding="utf-8", errors="replace", env=env)
    filas.append(("probar_metodos", "OK" if p.returncode == 0 else "FALLA: " + (p.stdout + p.stderr)[-400:]))
    ok &= p.returncode == 0
    # OT-069 (T-191, E-198): dirección entre capas (modo AVISO con V1..V14 conocidas; violación nueva = falla; lista vacía = ESTRICTO).
    try:
        from metodos import direccion_capas
        d_ok, d_txt = direccion_capas.fila_puerta()
        filas.append(("dirección entre capas (E-198)", d_txt))
        ok &= d_ok
    except Exception as ex:
        filas.append(("dirección entre capas (E-198)", f"FALLA: {ex}"))
        ok = False
    # DEVUELTA 1/3: los ataques de RESULTADO por nombre físico y la prueba de renombrado/entidad corren en la puerta.
    pr = subprocess.run([sys.executable, os.path.join(RAIZ, ".dsh", "build", "prueba_ot022.py")], cwd=RAIZ,
                        capture_output=True, encoding="utf-8", errors="replace", env=env)
    ptxt = (pr.stdout or "") + (pr.stderr or "")
    ultima = next((l.strip() for l in reversed(ptxt.splitlines()) if l.strip()), "")
    filas.append(("prueba_ot022 (equivalencia, renombrado, entidad, RESULTADO/PENDIENTE)",
                  "OK · " + ultima if pr.returncode == 0 else "FALLA: " + ptxt[-600:]))
    ok &= pr.returncode == 0
    # OT-036: identidad única del método y excepción por ruta relativa a kit/metodos/.
    p36 = subprocess.run([sys.executable, os.path.join(RAIZ, ".dsh", "build", "prueba_ot036.py")], cwd=RAIZ,
                         capture_output=True, encoding="utf-8", errors="replace", env=env)
    p36txt = (p36.stdout or "") + (p36.stderr or "")
    ultima36 = next((l.strip() for l in reversed(p36txt.splitlines()) if l.strip()), "")
    filas.append(("prueba_ot036 (nombre único, ruta de excepción)",
                  "OK · " + ultima36 if p36.returncode == 0 else "FALLA: " + p36txt[-600:]))
    ok &= p36.returncode == 0
    # OT-028: pruebas completas (regresión / puertos / automatización / coherencia) desde el constructor.
    b = subprocess.run([sys.executable, "construir.py"], cwd=KIT, capture_output=True, encoding="utf-8", errors="replace", env=env)
    txt = (b.stdout or "") + (b.stderr or "")
    m = re.findall(r"TOTAL: (\d+) pruebas · (\d+) PASA · (\d+) FALLA", txt)
    pu = re.findall(r"PUERTOS: (\d+) de (\d+)", txt)
    au = re.findall(r"AUTOMATIZACIÓN: (\d+) de (\d+)", txt)
    co = re.findall(r"Coherencia del DBD: (\d+) error", txt)
    # Total de pruebas de la rama base: ESCENARIO + ESPERADO de fuente/Pruebas.xlsx.
    base_total = None
    try:
        import tempfile
        from openpyxl import load_workbook
        raw = subprocess.run(["git", "show", "origin/main:fuente/Pruebas.xlsx"], cwd=RAIZ,
                             capture_output=True, check=True).stdout
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tf:
            tf.write(raw)
            ruta_tmp = tf.name
        wbp = load_workbook(ruta_tmp, read_only=True, data_only=True)
        base_total = sum(1 for s in ("ESCENARIO", "ESPERADO") if s in wbp.sheetnames
                         for r in wbp[s].iter_rows(min_row=2, values_only=True) if r and r[0] not in (None, ""))
        wbp.close()
        try:
            os.unlink(ruta_tmp)
        except OSError:
            pass
    except Exception:
        base_total = None
    exacto = len(m) == 1 and len(pu) == 1 and len(au) == 1 and len(co) == 1
    build_ok = bool(b.returncode == 0 and exacto and base_total is not None
                    and int(m[0][0]) == int(m[0][1]) and m[0][2] == "0"
                    and int(m[0][0]) == base_total
                    and pu[0][0] == pu[0][1] and au[0][0] == au[0][1] and co[0][0] == "0")
    filas.append(("construir.py (regresión / puertos / automatización / coherencia)",
                  "OK" if build_ok else "FALLA: " + txt[-300:]))
    ok &= build_ok
    # T-180 (E-192): TODAS las pruebas del repositorio (prueba_*.py, informes/*/prueba_*.py, instalador/probar_*.py, validar_dbd4); corren después de construir.py porque leen salida_b/.
    try:
        import importlib.util
        sp = importlib.util.spec_from_file_location("pruebas_todas", os.path.join(RAIZ, ".dsh", "build", "pruebas_todas.py"))
        pt = importlib.util.module_from_spec(sp); sp.loader.exec_module(pt)
        t_ok, t_filas = pt.correr(pt.descubrir(RAIZ), RAIZ, omitir=("prueba_ot022.py", "prueba_ot036.py"))   # esas dos ya tienen su fila
        malas = [f"{r} → {t[-200:]}" for r, c, t in t_filas if c != 0]
        filas.append((f"pruebas del repositorio ({len(t_filas)})", "OK" if t_ok else "FALLA: " + (" || ".join(malas) or "no se encontró ninguna prueba")))
        ok &= t_ok
    except Exception as ex:
        filas.append(("pruebas del repositorio", f"FALLA: {ex}"))
        ok = False
    # OT-037: presupuesto estructural (delta rama - main contra lo declarado en la OT de main).
    ot_m = re.match(r"(?:ot|obra/OT)-(\d{3})-", rama_actual())
    ot_id = f"OT-{ot_m.group(1)}" if ot_m else ""
    try:
        rama_m = medir_modelo.medir(os.path.join(rutas.FUENTE, "DBD_Fuente.xlsx"), rutas.RAIZ)
        base_m = medir_modelo.medir_main(base)
        delta = {k: rama_m[k] - base_m[k] for k in rama_m}
        pres = medir_modelo.presupuesto(ot_id, base) if ot_id else {}
        exceso = [f"{k}: {delta[k]:+d} > {pres.get(k, 0):+d}" for k in delta if delta[k] > pres.get(k, 0)]
        print("\n| Medida | main | rama | neto | presupuesto | estado |\n|---|---|---|---|---|---|")
        for k in rama_m:
            print(f"| {k} | {base_m[k]} | {rama_m[k]} | {delta[k]:+d} | {pres.get(k, 0):+d} | "
                  f"{'OK' if delta[k] <= pres.get(k, 0) else 'FALLA'} |")
        aviso_codigo = delta.get("lineas", 0) > 300 and pres.get("lineas", 0) == 0
        filas.append(("presupuesto estructural", "OK" if not exceso else "FALLA: " + ", ".join(exceso)))
        ok &= not exceso
        if aviso_codigo:
            filas.append(("presupuesto estructural (aviso)", f"AVISO: líneas +{delta['lineas']} sin declarar"))
    except Exception as ex:
        filas.append(("presupuesto estructural", f"FALLA: {ex}"))
        ok = False
    # OT-029: ESTADO_GENERADO.md debe coincidir byte a byte con lo que se regenera de ordenes/, PLAN y PESOS.
    try:
        from estado import generar_estado
        al_dia = generar_estado.estado_al_dia()
        filas.append(("ESTADO_GENERADO.md al día", "OK" if al_dia else "FALLA: difiere de lo generado (correr kit/estado/generar_estado.py)"))
        ok &= al_dia
    except Exception as ex:
        filas.append(("ESTADO_GENERADO.md al día", f"FALLA: {ex}"))
        ok = False
    print("## Puerta automática: " + ("✅ PASA (queda la revisión del arquitecto)" if ok else "❌ NO PASA (se devuelve sin revisar)"))
    print("\n| Comprobación | Resultado |\n|---|---|")
    for a, b in filas:
        print(f"| {a} | {b.replace('|', '/')} |")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "origin/main"))
