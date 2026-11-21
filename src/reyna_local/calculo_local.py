"""Conecta el servicio local con el productor de resultados existente."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
from threading import Lock

from .contrato import validar

RAIZ = Path(__file__).resolve().parents[2]
_lock = Lock()


def calcular(carpeta, periodo, sintesis):
    from .resultados import construir
    carpeta = Path(carpeta)
    carpeta.mkdir(parents=True, exist_ok=True)
    with _lock:
        libro = carpeta / 'frenosa.xlsx'
        if not libro.exists():
            spec = importlib.util.spec_from_file_location('generador_frenosa', RAIZ / 'casos/frenosa/generar.py')
            modulo = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(modulo)
            with tempfile.TemporaryDirectory(dir=carpeta) as temp:
                temporal = Path(temp) / 'libro.xlsx'
                modulo.generar(str(RAIZ / 'casos/plantilla_caso.xlsx'), str(temporal))
                os.replace(temporal, libro)
        resultado = construir(str(libro), periodo=periodo, sintesis=sintesis,
                              ventas_csv=str(RAIZ / 'datos/frenosa/Ventas.csv'))
        if validar(resultado) or resultado['periodo_actual'] != periodo or resultado['sintesis'] != sintesis:
            raise ValueError('El resultado no cumple el contrato solicitado.')
        destino = carpeta / 'resultados' / f'frenosa_{periodo}_{sintesis}.json'
        destino.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=destino.parent, delete=False) as f:
            temporal = Path(f.name)
            try:
                json.dump(resultado, f, ensure_ascii=False, allow_nan=False)
                f.flush()
                os.fsync(f.fileno())
            except BaseException:
                temporal.unlink(missing_ok=True)
                raise
        try:
            os.replace(temporal, destino)
        finally:
            temporal.unlink(missing_ok=True)
        return resultado
