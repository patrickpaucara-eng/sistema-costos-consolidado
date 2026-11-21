"""Arma la carpeta de los 13 entregables de la monografía MN_01 (Oria) con un comando.
Uso: python tools/entrega/armar.py --periodo 2010-12 [--salida entrega_MN01] [--junit resultados.xml]
Solo lee resultados publicados (datos/resultados) y el repositorio; no recalcula costos."""
import argparse, json, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'src'))
from reyna_local.exportar import exportar                      # noqa: E402
from reyna_local.contrato import validar                       # noqa: E402

SINTESIS = ('REAL', 'CONTABLE', 'ESTIMADO')
INDICE = [
    ('01', 'Cadena de chats (Word)', '01_cadena_chats.docx'),
    ('02', 'Etapas del desarrollo (Word)', '02_etapas.docx'),
    ('03', 'Código fuente (Word)', '03_codigo_fuente.docx'),
    ('04', 'Prueba de funcionamiento (Word)', '04_pruebas.docx'),
    ('05', 'Datos de entrada (Excel)', '05_datos_entrada.xlsx'),
    ('06', 'Resultados por síntesis (Excel)', '06_resultados_{s}.xlsx'),
    ('07', 'Analítica: relevancia y diagnóstico (Excel)', '07_analitica_{s}.xlsx'),
    ('08', 'Proyección, escenarios y propuestas (Excel)', '08_proyeccion_propuestas_{s}.xlsx'),
    ('09', 'Manual descriptivo (Word)', '09_manual_descriptivo.docx'),
    ('10', 'Manual de usuario (Word)', '10_manual_usuario.docx'),
    ('11', 'Ejecutable Windows (EXE)', 'ReynaCostos.exe — se agrega al compilar en Windows (tools/windows/LEEME.md)'),
    ('12', 'Sistema HTML sin conexión', '12_sistema_sin_conexion_{s}.html'),
    ('13', 'Registro de actividades y tiempos (Excel)', '13_registro_tiempos.xlsx'),
]


def cargar(periodo, sintesis):
    ruta = ROOT / 'datos/resultados' / f'frenosa_{periodo}_{sintesis}.json'
    if not ruta.is_file():
        raise SystemExit(f'No hay resultado publicado para {periodo} {sintesis}. Calcúlelo primero en la interfaz.')
    r = json.loads(ruta.read_text(encoding='utf-8'))
    errores = validar(r)
    if errores:
        raise SystemExit('El resultado publicado no cumple el contrato: ' + '; '.join(errores))
    return r


def mover(origen, destino):
    shutil.move(str(origen), str(destino)); return destino


def armar(periodo, salida, junit=None):
    import importlib.util                                       # por ruta: «generar» también es el módulo de casos/frenosa
    spec = importlib.util.spec_from_file_location('documentos_generar', ROOT / 'tools/documentos/generar.py')
    DOC = importlib.util.module_from_spec(spec); spec.loader.exec_module(DOC)
    salida = Path(salida); salida.mkdir(parents=True, exist_ok=True); tmp = salida / '_tmp'
    hechos = list(DOC.generar(salida, junit))                    # 01, 02, 04, 09, 10
    hechos.append(mover(exportar(None, 'codigo', tmp), salida / '03_codigo_fuente.docx'))
    hechos.append(mover(exportar(None, 'entrada', tmp), salida / '05_datos_entrada.xlsx'))
    for s in SINTESIS:
        r = cargar(periodo, s)
        for tipo, nombre in (('resultados', '06_resultados_{s}.xlsx'), ('analitica', '07_analitica_{s}.xlsx'),
                             ('proyeccion', '08_proyeccion_propuestas_{s}.xlsx'), ('html', '12_sistema_sin_conexion_{s}.html')):
            hechos.append(mover(exportar(r, tipo, tmp), salida / nombre.format(s=s)))
    subprocess.run([sys.executable, str(ROOT / 'tools/consolidar_tiempos.py')], check=True, cwd=ROOT)
    hechos.append(Path(shutil.copy(ROOT / 'docs/entrega/REGISTRO_TIEMPOS.xlsx', salida / '13_registro_tiempos.xlsx')))
    shutil.rmtree(tmp, ignore_errors=True)
    lineas = [f'MONOGRAFÍA MN_01 · Sistema de Costos Reyna · Caso Frenosa · periodo {periodo}', '',
              'Síntesis: REAL (costo integral), CONTABLE (NIC 2 / NIIF 18), ESTIMADO (estadístico fuera de muestra).', '']
    for n, desc, arch in INDICE:
        lineas.append(f'{n}. {desc}: ' + (', '.join(arch.format(s=s) for s in SINTESIS) if '{s}' in arch else arch))
    (salida / 'LEEME.txt').write_text('\n'.join(lineas) + '\n', encoding='utf-8')
    return hechos


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--periodo', default='2010-12'); p.add_argument('--salida', type=Path, default=ROOT / 'entrega_MN01')
    p.add_argument('--junit', type=Path)
    a = p.parse_args()
    junit = a.junit
    if junit is None:
        junit = a.salida / '_pruebas.xml'; a.salida.mkdir(parents=True, exist_ok=True)
        subprocess.run([sys.executable, '-m', 'pytest', 'tests', '-q', '--junitxml=' + str(junit),
                        '--ignore=tests/test_documentos_generados.py', '--ignore=tests/test_entrega_armar.py'],
                       cwd=ROOT, check=False, env={**__import__('os').environ, 'PYTHONPATH': str(ROOT / 'src')})
    for h in armar(a.periodo, a.salida, junit): print(h.name)
    if a.junit is None: junit.unlink(missing_ok=True)
    print('Listo:', a.salida)


if __name__ == '__main__':
    main()
