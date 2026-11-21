"""Conecta el servicio local con el cálculo. Entrada única: libros con formato DBD validados (libro_dbd).
Libros de la carpeta de datos del usuario (<datos>/libros/*.xlsx) más el libro de demostración incluido (casos/libros)."""
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import tempfile
from threading import Lock

from .contrato import validar
from . import libro_dbd as B

from .raiz import RAIZ
_lock = Lock()
_cache = {}


def libros(carpeta):
    """{slug: ruta} — los del usuario tienen prioridad sobre los de demostración."""
    out = {}
    for base in (RAIZ / "casos" / "libros", Path(carpeta) / "libros"):
        for p in sorted(base.glob("*.xlsx")) if base.is_dir() else []:
            out[p.stem] = p
    return out


def catalogo(carpeta):
    filas = []
    for s, p in libros(carpeta).items():
        try:
            cod, nom = B.empresa(p)
            from openpyxl import load_workbook
            wb = load_workbook(p, read_only=True); pers = sorted(str(r[0]) for r in wb["PERIODO"].iter_rows(min_row=2, values_only=True) if r and r[0]); wb.close()
            filas.append(dict(id=s, codigo=cod, nombre=nom, periodos=pers, demostracion=str(p).startswith(str(RAIZ / "casos"))))
        except Exception:
            continue
    return filas


class YaExiste(Exception):
    """Arrepentimiento (DBD p. 26): reemplazar un libro existente exige confirmación explícita."""
    def __init__(self, ficha): super().__init__(ficha["nombre"]); self.ficha = ficha


def versiones(carpeta, s):
    d = Path(carpeta) / "libros" / "_versiones"
    return [p.name for p in sorted(d.glob(f"{s}__*.xlsx"), reverse=True)] if d.is_dir() else []


def restaurar(carpeta, s, version):
    """Vuelve a la versión anterior elegida; la actual se guarda también como versión (nada se pierde)."""
    d = Path(carpeta) / "libros"; v = d / "_versiones" / version
    if not v.name.startswith(f"{s}__") or not v.is_file() or "/" in version or "\\" in version:
        raise ValueError("Esa versión no existe.")
    actual = d / f"{s}.xlsx"
    if actual.is_file(): _guardar_version(d, s, actual)
    shutil.copy(v, actual); _cache.pop(s, None)
    cod, nom = B.empresa(actual); return dict(id=s, codigo=cod, nombre=nom)


def _guardar_version(d, s, archivo):
    (d / "_versiones").mkdir(parents=True, exist_ok=True)
    shutil.copy(archivo, d / "_versiones" / f"{s}__{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}.xlsx")


def registrar(carpeta, contenido, nombre_archivo="libro.xlsx", reemplazar=False):
    """Valida un libro subido; si cumple el formato DBD lo guarda como <slug de la empresa>.xlsx. Devuelve (ficha, errores).
    Si la empresa ya tiene libro, pide confirmación (YaExiste) y, al reemplazar, guarda la versión anterior."""
    dest_dir = Path(carpeta) / "libros"; dest_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".xlsx", dir=dest_dir, delete=False) as f:
        f.write(contenido); tmp = Path(f.name)
    try:
        errores = B.validar(tmp)
        if errores:
            return None, errores
        cod, nom = B.empresa(tmp); s = B.slug(nom)
        if s in libros(carpeta) and not reemplazar:
            raise YaExiste(dict(id=s, codigo=cod, nombre=nom))
        previo = libros(carpeta).get(s)
        if previo is not None and previo.is_file(): _guardar_version(dest_dir, s, previo)   # también el de demostración
        os.replace(tmp, dest_dir / f"{s}.xlsx"); _cache.pop(s, None)
        return dict(id=s, codigo=cod, nombre=nom), []
    finally:
        tmp.unlink(missing_ok=True)


def _sello(libro, resultado):
    info = resultado.get("proyeccion_info") or {}
    return dict(libro=Path(libro).name, huella_libro=B.huella(libro), version_sistema=B.VERSION,
                metodo="ABC por etapas P1–P7 (ALG-04), kardex promedio ponderado (ALG-01), trazabilidad (ALG-11)",
                semilla=info.get("semilla", 2010), simulaciones=info.get("simulaciones", 2000),
                calculado=datetime.now().isoformat(timespec="seconds"))


def calcular(carpeta, periodo, sintesis, empresa=None):
    from .resultados import construir, calcular_periodos
    carpeta = Path(carpeta); carpeta.mkdir(parents=True, exist_ok=True)
    disp = libros(carpeta)
    if not disp:
        raise ValueError("No hay libros DBD cargados.")
    s = empresa or ("frenosa" if "frenosa" in disp else next(iter(disp)))
    if s not in disp:
        raise ValueError("La empresa elegida no tiene libro cargado.")
    libro = disp[s]
    with _lock:
        errores = B.validar(libro)
        if errores:
            raise ValueError("El libro no cumple el formato DBD: " + "; ".join(errores[:5]))
        h = B.huella(libro)
        if _cache.get(s, (None,))[0] != h:
            cod, _ = B.empresa(libro); _cache[s] = (h, calcular_periodos(str(libro), cod))
        resultado = construir(str(libro), periodo=periodo, sintesis=sintesis, _cache=_cache[s][1])
        resultado["sello"] = _sello(libro, resultado)
        if validar(resultado) or resultado['periodo_actual'] != periodo or resultado['sintesis'] != sintesis:
            raise ValueError('El resultado no cumple el contrato solicitado.')
        destino = carpeta / 'resultados' / f'{s}_{periodo}_{sintesis}.json'
        destino.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=destino.parent, delete=False) as f:
            temporal = Path(f.name)
            try:
                json.dump(resultado, f, ensure_ascii=False, allow_nan=False); f.flush(); os.fsync(f.fileno())
            except BaseException:
                temporal.unlink(missing_ok=True); raise
        try:
            os.replace(temporal, destino)
        finally:
            temporal.unlink(missing_ok=True)
        return resultado


def verificar_sello(carpeta, resultado):
    """¿El libro con que se calculó sigue intacto? Compara la huella guardada con la del libro actual."""
    sello = resultado.get("sello") or {}
    s = Path(sello.get("libro", "")).stem; disp = libros(carpeta)
    if not sello or s not in disp:
        return dict(estado="SIN_SELLO" if not sello else "LIBRO_NO_DISPONIBLE")
    return dict(estado="VIGENTE" if B.huella(disp[s]) == sello.get("huella_libro") else "LIBRO_MODIFICADO")
